import chromadb
from chromadb.utils import embedding_functions
from typing import List, Optional, Any
from loguru import logger

class VectorStore:
    """
    Gestionnaire de base de données vectorielle ChromaDB.
    
    Cette classe gère le cycle de vie des embeddings et assure la persistance 
    locale des connaissances extraites du document.
    """

    def __init__(self, db_path: str):
        """
        Initialise ChromaDB avec un modèle d'embedding multilingue performant.
        
        Args:
            db_path: Dossier de stockage local pour ChromaDB.
        """
        self.db_path = db_path
        
        # Modèle optimisé pour le français et 100+ langues
        # Fonctionne 100% localement via sentence-transformers
        self.embedding_fn = embedding_functions.SentenceTransformerEmbeddingFunction(
            model_name="paraphrase-multilingual-MiniLM-L12-v2"
        )
        
        self.client = chromadb.PersistentClient(
            path=db_path,
            settings=chromadb.config.Settings(anonymized_telemetry=False)
        )
        self.collection = self.client.get_or_create_collection(
            name="rfp_hierarchical",
            embedding_function=self.embedding_fn
        )
        logger.info(f"🗄️ ChromaDB Hiérarchique prêt : {db_path}")

    def add_fragments_batch(self, fragments: List[Any]) -> int:
        """
        Ajoute massivement des fragments à la base de données.
        
        Note: Le texte indexé est enrichi du 'fil d'ariane' pour permettre au 
        modèle d'embedding de capter le contexte global du document.
        
        Args:
            fragments: Liste d'objets LocalRawFragment.
            
        Returns:
            int: Nombre de fragments réellement indexés.
        """
        if not fragments: return 0

        ids = [f"{f.source_file}_{i}" for i, f in enumerate(fragments)]
        
        # Stratégie d'indexation : Préfixage par la section parente
        # Aide à la recherche sémantique (ex: 'cybersécurité' dans 'Maintenance')
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
