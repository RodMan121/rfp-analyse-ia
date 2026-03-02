from flashrank import Ranker, RerankRequest
from loguru import logger
from typing import List

class LocalReranker:
    """
    Reranker local utilisant un modèle de type Cross-Encoder.
    
    Le reranking est la pièce maîtresse d'un RAG de qualité 'Production'.
    Il résout le problème principal du RAG thématique : certains fragments 
    peuvent contenir les bons mots-clés sans répondre à la question.
    Le Cross-Encoder analyse la relation réelle entre la question et le fragment.
    """

    def __init__(self, model_name: str = "ms-marco-MiniLM-L-12-v2"):
        """
        Initialise le moteur de re-classement.
        
        Args:
            model_name: Modèle léger optimisé pour le reranking (par défaut ms-marco).
        """
        logger.info(f"🎯 Initialisation du Reranker ({model_name})...")
        # Le cache_dir est configuré dans 'data' pour isoler les modèles du code
        self.ranker = Ranker(model_name=model_name, cache_dir="data/models_cache")

    def rerank(self, query: str, documents: List[dict], top_n: int = 5) -> List[dict]:
        """
        Ré-ordonne les documents par score de pertinence sémantique réelle.
        
        Args:
            query: La question posée par l'utilisateur.
            documents: Liste de fragments remontés par ChromaDB.
            top_n: Nombre final de fragments à envoyer au LLM.
            
        Returns:
            List[dict]: Les top_n fragments les plus pertinents pour la réponse.
        """
        if not documents:
            return []

        # Formatage des données pour le moteur FlashRank
        passages = [
            {"id": i, "text": doc["text"], "meta": doc["metadata"]}
            for i, doc in enumerate(documents)
        ]

        # Calcul du score de pertinence croisée (Query <-> Fragment)
        rerank_request = RerankRequest(query=query, passages=passages)
        results = self.ranker.rerank(rerank_request)

        # On sélectionne les meilleurs résultats
        final_results = []
        for r in results[:top_n]:
            final_results.append({
                "text": r["text"],
                "metadata": r["meta"],
                "score": round(float(r["score"]), 4)
            })

        logger.info(f"🎯 Reranking terminé : {len(final_results)} documents d'élite sélectionnés.")
        return final_results
