import os
import ollama
import json
from pathlib import Path
from loguru import logger
from typing import List, Dict
from concurrent.futures import ThreadPoolExecutor
from dotenv import load_dotenv
from phase1.vectorstore import VectorStore
from phase1.reranker import LocalReranker

# Chargement configuration robuste
env_path = Path(__file__).parent.parent / ".env"
load_dotenv(env_path)

TEXT_MODEL = os.getenv("OLLAMA_TEXT_MODEL", "qwen2.5:7b")
DEFAULT_DB_PATH = os.getenv("CHROMA_DB_PATH", "data/chroma_db_hierarchical")

class ComplianceAuditAgent:
    """Agent d'Audit avec Gap Analysis sécurisé."""

    def __init__(self, db_path: str = None):
        db_path = db_path or DEFAULT_DB_PATH
        self.rfp_store = VectorStore(db_path=db_path, collection_name="rfp_hierarchical")
        self.catalog_store = VectorStore(db_path=db_path, collection_name="service_catalog")
        self.reranker = LocalReranker()
        self.model = TEXT_MODEL
        logger.info(f"🛡️ Agent d'Audit prêt (Modèle: {self.model})")

    def extract_requirements(self, category: str = "GENERAL") -> List[Dict]:
        """Extraction des exigences."""
        logger.info(f"🔎 Audit de la catégorie : {category}...")
        fragments = self.rfp_store.search_hybrid(query=f"CATÉGORIE: {category}", n_results=15)
        if not fragments: return []

        all_requirements = []
        for frag in fragments:
            prompt = f"FRAGMENT :\n{frag['text']}\n\nExtraie les exigences précises en JSON : [{\"exigence\": \"...\", \"priorite\": \"...\"}]"
            try:
                response = ollama.generate(model=self.model, prompt=prompt, format="json")
                reqs = json.loads(response.get('response', '[]'))
                for r in reqs:
                    r['source'] = f"{frag['metadata']['breadcrumbs']} (P.{frag['metadata']['page']})"
                    all_requirements.append(r)
            except Exception as e:
                logger.warning(f"⚠️ Échec extraction : {e}")
        return all_requirements

    def _analyze_single_gap(self, req: Dict) -> Dict:
        """Analyse d'une seule exigence (copie pour parallélisme)."""
        result = {**req}
        know_how = self.catalog_store.search_hybrid(query=result['exigence'], n_results=3)
        context = "\n".join([k['text'] for k in know_how]) if know_how else "AUCUN SAVOIR-FAIRE TROUVÉ."
        
        prompt = f"EXIGENCE : {result['exigence']}\nSAVOIR-FAIRE : {context}\n\nDétermine la conformité en JSON : {\"statut\": \"...\", \"justification\": \"...\", \"score_confiance\": 0}"
        try:
            response = ollama.generate(model=self.model, prompt=prompt, format="json")
            gap = json.loads(response.get('response', '{}'))
            result.update(gap)
        except Exception as e:
            logger.warning(f"⚠️ Échec Gap Analysis : {e}")
            result.update({"statut": "ERREUR", "score_confiance": 0})
        return result

    def analyze_gap(self, requirements: List[Dict]) -> List[Dict]:
        """Analyse parallélisée."""
        workers = int(os.getenv("OLLAMA_NUM_PARALLEL", "1"))
        logger.info(f"🧠 Gap Analysis ({workers} workers) sur {len(requirements)} points...")
        with ThreadPoolExecutor(max_workers=workers) as executor:
            results = list(executor.map(self._analyze_single_gap, requirements))
        return results

    def generate_report(self, analysis: List[Dict]) -> str:
        report = "# 📋 Matrice de Conformité & Gap Analysis (GTM)\n\n"
        report += "| Statut | Confiance | Priorité | Exigence | Source | Justification |\n"
        report += "|--------|-----------|----------|----------|--------|---------------|\n"
        for r in analysis:
            s_emoji = "✅" if r.get('statut') == "CONFORME" else "⚠️" if r.get('statut') == "PARTIEL" else "❌"
            report += f"| {s_emoji} | {r.get('score_confiance', 0)}% | {r.get('priorite')} | {r['exigence']} | {r['source']} | {r.get('justification')} |\n"
        return report

if __name__ == "__main__":
    audit = ComplianceAuditAgent()
    reqs = audit.extract_requirements(category="TECHNIQUE")
    results = audit.analyze_gap(reqs)
    output_path = Path("data/gap_analysis_report.md")
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(audit.generate_report(results))
    logger.success(f"✅ Audit terminé : {output_path}")
