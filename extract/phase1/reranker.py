import os
from flashrank import Ranker, RerankRequest
from loguru import logger
from typing import List
from pathlib import Path
from dotenv import load_dotenv

# Config cache modèles
load_dotenv(Path(__file__).parent.parent / ".env")
DEFAULT_CACHE = os.getenv("MODELS_CACHE_DIR", "data/models_cache")

class LocalReranker:
    """
    Reranker local utilisant FlashRank.
    """

    def __init__(self, model_name: str = "ms-marco-MiniLM-L-12-v2"):
        logger.info(f"🎯 Initialisation du Reranker ({model_name})...")
        self.ranker = Ranker(model_name=model_name, cache_dir=DEFAULT_CACHE)

    def rerank(self, query: str, documents: List[dict], top_n: int = 5) -> List[dict]:
        if not documents: return []
        passages = [{"id": i, "text": doc["text"], "meta": doc["metadata"]} for i, doc in enumerate(documents)]
        rerank_request = RerankRequest(query=query, passages=passages)
        results = self.ranker.rerank(rerank_request)
        
        final_results = []
        for r in results[:top_n]:
            final_results.append({
                "text": r["text"], "metadata": r["meta"], "score": round(float(r["score"]), 4)
            })
        logger.info(f"🎯 Reranking terminé : {len(final_results)} sélectionnés.")
        return final_results
