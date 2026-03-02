import chromadb
from chromadb.utils import embedding_functions
from typing import List, Optional, Any
from .models import AtomicFragment
from loguru import logger

class VectorStore:
    """
    Base de données vectorielle avec support des métadonnées hiérarchiques.
    """

    def __init__(self, db_path: str):
        self.db_path = db_path
        self.embedding_fn = embedding_functions.SentenceTransformerEmbeddingFunction(
            model_name="paraphrase-multilingual-MiniLM-L12-v2"
        )
        self.client = chromadb.PersistentClient(path=db_path)
        self.collection = self.client.get_or_create_collection(
            name="rfp_hierarchical",
            embedding_function=self.embedding_fn
        )
        logger.info(f"🗄️ ChromaDB Hiérarchique prêt : {db_path}")

    def add_fragments_batch(self, fragments: List[Any]) -> int:
        """Ajoute des fragments avec fil d'ariane et page."""
        if not fragments: return 0

        ids = [f"{f.source_file}_{i}" for i, f in enumerate(fragments)]
        
        # On enrichit le texte indexé avec le fil d'ariane pour améliorer la recherche
        documents = [f"SECTION: {f.breadcrumbs}\n\n{f.text}" for f in fragments]
        
        metadatas = [
            {
                "source": f.source_file,
                "section": f.section,
                "breadcrumbs": f.breadcrumbs,
                "page": f.page
            }
            for f in fragments
        ]

        self.collection.add(
            ids=ids,
            documents=documents,
            metadatas=metadatas
        )
        logger.success(f"✅ {len(fragments)} fragments (avec métadonnées) indexés.")
        return len(fragments)

    def search(self, query: str, n_results: int = 5) -> List[dict]:
        """Recherche sémantique enrichie."""
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
