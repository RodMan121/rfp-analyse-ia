import chromadb
from chromadb.utils import embedding_functions
from typing import List, Optional, Any
from loguru import logger
from rank_bm25 import BM25Okapi
import pickle
import os
from pathlib import Path

class VectorStore:
    """
    Gestionnaire de base de données vectorielle ChromaDB avec Recherche Hybride (BM25).
    """

    def __init__(self, db_path: str, collection_name: str = "rfp_hierarchical"):
        self.db_path = Path(db_path)
        self.bm25_path = self.db_path / f"bm25_{collection_name}.pkl"
        
        # 1. Vecteurs
        self.embedding_fn = embedding_functions.SentenceTransformerEmbeddingFunction(
            model_name="paraphrase-multilingual-MiniLM-L12-v2"
        )
        self.client = chromadb.PersistentClient(path=str(db_path))
        self.collection = self.client.get_or_create_collection(
            name=collection_name,
            embedding_function=self.embedding_fn
        )
        
        # 2. Mots-clés (BM25)
        self.bm25 = None
        self.bm25_docs = []
        if self.bm25_path.exists():
            with open(self.bm25_path, "rb") as f:
                data = pickle.load(f)
                self.bm25 = data["index"]
                self.bm25_docs = data["docs"]
                logger.info(f"🔎 Index BM25 '{collection_name}' chargé.")

    def add_fragments_batch(self, fragments: List[Any]) -> int:
        """Ajoute massivement des fragments aux deux moteurs avec Tagging Sémantique."""
        if not fragments: return 0

        ids = [f"{f.source_file}_{i}" for i, f in enumerate(fragments)]
        documents = [f"SECTION: {f.breadcrumbs}\nCATÉGORIE: {f.category}\n\n{f.text}" for f in fragments]
        metadatas = [
            {
                "source": f.source_file, 
                "section": f.section, 
                "breadcrumbs": f.breadcrumbs, 
                "page": f.page,
                "category": f.category
            } 
            for f in fragments
        ]

        # 1. Mise à jour ChromaDB
        self.collection.add(ids=ids, documents=documents, metadatas=metadatas)

        # 2. Mise à jour BM25
        new_docs = [{"text": d, "metadata": m} for d, m in zip(documents, metadatas)]
        self.bm25_docs.extend(new_docs)
        
        tokenized_corpus = [doc["text"].lower().split() for doc in self.bm25_docs]
        self.bm25 = BM25Okapi(tokenized_corpus)
        
        # Sauvegarde persistante
        self.db_path.mkdir(parents=True, exist_ok=True)
        with open(self.bm25_path, "wb") as f:
            pickle.dump({"index": self.bm25, "docs": self.bm25_docs}, f)

        logger.success(f"✅ {len(fragments)} fragments indexés (Vecteurs + BM25 + Tags).")
        return len(fragments)

    def search_hybrid(self, query: str, n_results: int = 20) -> List[dict]:
        """
        Recherche hybride fusionnant Vecteurs et Mots-clés.
        """
        # A. Recherche Vectorielle (20 candidats)
        vec_results = self.search(query, n_results=n_results)
        
        # B. Recherche BM25 (20 candidats)
        bm25_results = []
        if self.bm25:
            tokenized_query = query.lower().split()
            bm25_scores = self.bm25.get_scores(tokenized_query)
            import numpy as np
            top_indices = np.argsort(bm25_scores)[-n_results:][::-1]
            for idx in top_indices:
                if bm25_scores[idx] > 0:
                    bm25_results.append(self.bm25_docs[idx])

        # C. Fusion simple (Priority to BM25 if very high score, else Vector)
        # On combine et dédoublonne sur le texte
        seen_texts = set()
        final_results = []
        
        # On alterne pour favoriser la diversité
        for v, b in zip(vec_results + [None]*max(0, len(bm25_results)-len(vec_results)), 
                        bm25_results + [None]*max(0, len(vec_results)-len(bm25_results))):
            if v and v["text"] not in seen_texts:
                final_results.append(v)
                seen_texts.add(v["text"])
            if b and b["text"] not in seen_texts:
                final_results.append(b)
                seen_texts.add(b["text"])
                
        return final_results[:n_results]

    def search(self, query: str, n_results: int = 5) -> List[dict]:
        """
        Effectue une recherche sémantique par similarité cosinus.
        
        Args:
            query: La question de l'utilisateur.
            n_results: Nombre de fragments à remonter.
            
        Returns:
            List[dict]: Fragments les plus proches thématiquement.
        """
        results = self.collection.query(
            query_texts=[query],
            n_results=n_results
        )

        formatted_results = []
        if results["documents"]:
            for i in range(len(results["documents"][0])):
                formatted_results.append({
                    "text": results["documents"][0][i],
                    "metadata": results["metadatas"][0][i]
                })
        return formatted_results
