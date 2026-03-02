from flashrank import Ranker, RerankRequest
from loguru import logger
from typing import List

class LocalReranker:
    """
    Reranker local pour affiner les résultats de recherche.
    Passe d'une recherche 'thématique' à une recherche 'pertinente'.
    """

    def __init__(self, model_name: str = "ms-marco-MiniLM-L-12-v2"):
        logger.info(f"🎯 Initialisation du Reranker ({model_name})...")
        self.ranker = Ranker(model_name=model_name, cache_dir="data/models_cache")

    def rerank(self, query: str, documents: List[dict], top_n: int = 5) -> List[dict]:
        """
        Ré-ordonne les documents par rapport à la question.
        documents attendu : list de {'text': '...', 'metadata': {...}}
        """
        if not documents:
            return []

        # Préparation pour FlashRank
        passages = [
            {"id": i, "text": doc["text"], "meta": doc["metadata"]}
            for i, doc in enumerate(documents)
        ]

        rerank_request = RerankRequest(query=query, passages=passages)
        results = self.ranker.rerank(rerank_request)

        # On ne garde que les top_n meilleurs
        final_results = []
        for r in results[:top_n]:
            final_results.append({
                "text": r["text"],
                "metadata": r["meta"],
                "score": round(float(r["score"]), 4)
            })

        logger.info(f"🎯 Reranking terminé : {len(final_results)} documents conservés.")
        return final_results
