import chromadb
import pickle
import hashlib
import numpy as np
from chromadb.utils import embedding_functions
from typing import List, Optional, Any
from loguru import logger
from rank_bm25 import BM25Okapi
from pathlib import Path

class VectorStore:
    """
    Gestionnaire de base de données vectorielle avec Recherche Hybride résiliente.
    """

    def __init__(self, db_path: str, collection_name: str = "rfp_hierarchical"):
        self.db_path = Path(db_path)
        self.bm25_path = self.db_path / f"bm25_{collection_name}.pkl"
        
        self.embedding_fn = embedding_functions.SentenceTransformerEmbeddingFunction(
            model_name="paraphrase-multilingual-MiniLM-L12-v2"
        )
        self.client = chromadb.PersistentClient(path=str(db_path))
        self.collection = self.client.get_or_create_collection(
            name=collection_name, embedding_function=self.embedding_fn
        )
        
        self.bm25 = None
        self.bm25_docs = []
        if self.bm25_path.exists():
            try:
                with open(self.bm25_path, "rb") as f:
                    data = pickle.load(f)
                    self.bm25 = data["index"]
                    self.bm25_docs = data["docs"]
                    logger.info(f"🔎 Index BM25 '{collection_name}' chargé.")
            except Exception as e:
                logger.warning(f"⚠️ Index BM25 corrompu ({e}).")

    def add_fragments_batch(self, fragments: List[Any]) -> int:
        """Ajout de fragments atomiques avec dédoublonnage et IDs immuables."""
        if not fragments: return 0

        ids, documents, metadatas = [], [], []
        seen_ids = set()
        
        for f in fragments:
            if f.id_hash in seen_ids:
                continue
            seen_ids.add(f.id_hash)
            
            # f est un objet AtomicDecomposition
            content = f"SECTION: {f.metadata.get('breadcrumbs')}\nCATÉGORIE: {f.category}\n\n{f.content}"
            ids.append(f.id_hash)
            documents.append(content)
            
            # Métadonnées complètes pour le RAG
            meta = {**f.metadata, "category": f.category}
            metadatas.append(meta)

        if ids:
            self.collection.upsert(ids=ids, documents=documents, metadatas=metadatas)

        # Mise à jour de l'index textuel BM25
        new_docs = [{"text": d, "metadata": m} for d, m in zip(documents, metadatas)]
        self.bm25_docs.extend(new_docs)
        tokenized_corpus = [doc["text"].lower().split() for doc in self.bm25_docs]
        self.bm25 = BM25Okapi(tokenized_corpus)
        
        self.db_path.mkdir(parents=True, exist_ok=True)
        with open(self.bm25_path, "wb") as f:
            pickle.dump({"index": self.bm25, "docs": self.bm25_docs}, f)

        logger.success(f"✅ {len(fragments)} fragments atomiques indexés dans ChromaDB.")
        return len(fragments)

    def search_hybrid(self, query: str, n_results: int = 20) -> List[dict]:
        """Recherche Hybride avec algorithme RRF (Reciprocal Rank Fusion)."""
        vec_results = self.search(query, n_results=n_results)
        bm25_results = []
        if self.bm25:
            tokenized_query = query.lower().split()
            scores = self.bm25.get_scores(tokenized_query)
            top_indices = np.argsort(scores)[-n_results:][::-1]
            for idx in top_indices:
                if scores[idx] > 0:
                    bm25_results.append(self.bm25_docs[idx])

        # RRF Fusion
        k = 60
        rrf_scores = {}
        all_docs = {}
        for rank, doc in enumerate(vec_results):
            txt = doc["text"]
            all_docs[txt] = doc
            rrf_scores[txt] = rrf_scores.get(txt, 0) + 1.0 / (k + rank + 1)
        for rank, doc in enumerate(bm25_results):
            txt = doc["text"]
            all_docs[txt] = doc
            rrf_scores[txt] = rrf_scores.get(txt, 0) + 1.0 / (k + rank + 1)

        sorted_texts = sorted(rrf_scores.keys(), key=lambda t: rrf_scores[t], reverse=True)
        return [all_docs[t] for t in sorted_texts][:n_results]

    def search(self, query: str, n_results: int = 5) -> List[dict]:
        results = self.collection.query(query_texts=[query], n_results=n_results)
        formatted = []
        if results["documents"]:
            for i in range(len(results["documents"][0])):
                formatted.append({"text": results["documents"][0][i], "metadata": results["metadatas"][0][i]})
        return formatted
