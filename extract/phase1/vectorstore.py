import chromadb
from chromadb.utils import embedding_functions
from typing import List, Optional, Any
from .models import AtomicFragment
from loguru import logger

class VectorStore:
    """
    Base de données vectorielle (ChromaDB) pour stocker et rechercher les fragments.
    Utilise sentence-transformers localement pour l'embedding (Coût $0).
    """

    def __init__(self, db_path: str):
        self.db_path = db_path
        # Utilisation d'un modèle d'embedding local (léger et efficace pour le français)
        self.embedding_fn = embedding_functions.SentenceTransformerEmbeddingFunction(
            model_name="paraphrase-multilingual-MiniLM-L12-v2"
        )
        self.client = chromadb.PersistentClient(path=db_path)
        self.collection = self.client.get_or_create_collection(
            name="rfp_fragments",
            embedding_function=self.embedding_fn
        )
        logger.info(f"🗄️ ChromaDB initialisé à l'emplacement : {db_path}")

    def add_fragments_batch(self, fragments: List[AtomicFragment]) -> int:
        """Ajoute une liste de fragments à la base vectorielle."""
        if not fragments:
            return 0

        ids = [f"{f.metadata.source_file}_{i}" for i, f in enumerate(fragments)]
        documents = [f.metadata.raw_text for f in fragments]
        metadatas = [
            {
                "source": f.metadata.source_file,
                "section": f.metadata.section,
                "domaine": f.classification.domaine,
                "type": f.classification.type_babok,
                "priorite": f.classification.priorite_esn
            }
            for f in fragments
        ]

        self.collection.add(
            ids=ids,
            documents=documents,
            metadatas=metadatas
        )
        logger.success(f"✅ {len(fragments)} fragments indexés dans ChromaDB.")
        return len(fragments)

    def search(self, query: str, n_results: int = 5, filter_domain: Optional[str] = None, filter_priority: Optional[str] = None) -> List[dict]:
        """Recherche sémantique avec filtres optionnels."""
        where = {}
        if filter_domain:
            where["domaine"] = filter_domain
        if filter_priority:
            where["priorite"] = filter_priority

        results = self.collection.query(
            query_texts=[query],
            n_results=n_results,
            where=where if where else None
        )

        formatted_results = []
        if results["documents"]:
            for i in range(len(results["documents"][0])):
                formatted_results.append({
                    "rank": i + 1,
                    "text": results["documents"][0][i],
                    "metadata": results["metadatas"][0][i],
                    "similarity_score": round(1 - results["distances"][0][i], 4) if "distances" in results else 0
                })
        return formatted_results

    def stats(self) -> dict:
        return {
            "total_fragments": self.collection.count(),
            "collection": "rfp_fragments",
            "db_path": self.db_path,
            "embedding_model": "paraphrase-multilingual-MiniLM-L12-v2"
        }
