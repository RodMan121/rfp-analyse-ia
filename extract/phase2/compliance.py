import ollama
import json
from pathlib import Path
from loguru import logger
from typing import List, Dict
from concurrent.futures import ThreadPoolExecutor
from phase1.vectorstore import VectorStore
from phase1.reranker import LocalReranker

TEXT_MODEL = "qwen2.5:7b"

class ComplianceAuditAgent:
    """Agent d'Audit avec Gap Analysis parallélisée."""

    def __init__(self, db_path: str = "data/chroma_db_hierarchical"):
        self.rfp_store = VectorStore(db_path=db_path, collection_name="rfp_hierarchical")
        self.catalog_store = VectorStore(db_path=db_path, collection_name="service_catalog")
        self.reranker = LocalReranker()
        self.model = TEXT_MODEL
        logger.info(f"🛡️ Agent d'Audit parallélisé prêt.")

    def extract_requirements(self, category: str = "GENERAL") -> List[Dict]:
        """Extraction séquentielle des exigences (nécessite du contexte)."""
        logger.info(f"🔎 Audit de la catégorie : {category}...")
        fragments = self.rfp_store.search_hybrid(query=f"CATÉGORIE: {category}", n_results=15)
        if not fragments: return []

        all_requirements = []
        for frag in fragments:
            prompt = f"FRAGMENT :\n{frag['text']}\n\nExtraie les exigences précises en JSON : [{\"exigence\": \"...\", \"priorite\": \"...\"}]"
            try:
                response = ollama.generate(model=self.model, prompt=prompt, format="json")
                raw_json = response.get('response', '[]')
                reqs = json.loads(raw_json)
                for r in reqs:
                    r['source'] = f"{frag['metadata']['breadcrumbs']} (P.{frag['metadata']['page']})"
                    all_requirements.append(r)
            except Exception as e:
                logger.warning(f"⚠️ Échec extraction : {e}")
        return all_requirements

    def _analyze_single_gap(self, req: Dict) -> Dict:
        """Méthode interne pour l'analyse d'une seule exigence (pour parallélisation)."""
        know_how = self.catalog_store.search_hybrid(query=req['exigence'], n_results=3)
        context = "\n".join([k['text'] for k in know_how]) if know_how else "AUCUN SAVOIR-FAIRE TROUVÉ."
        
        prompt = f"EXIGENCE : {req['exigence']}\nSAVOIR-FAIRE : {context}\n\nDétermine la conformité en JSON : {\"statut\": \"...\", \"justification\": \"...\", \"score_confiance\": 0}"
        try:
            response = ollama.generate(model=self.model, prompt=prompt, format="json")
            raw_json = response.get('response', '{}')
            gap = json.loads(raw_json)
            req.update(gap)
        except Exception as e:
            logger.warning(f"⚠️ Échec Gap Analysis pour '{req['exigence'][:30]}' : {e}")
            req.update({"statut": "ERREUR", "score_confiance": 0})
        return req

    def analyze_gap(self, requirements: List[Dict]) -> List[Dict]:
        """Analyse parallélisée (ThreadPool) pour gain de temps."""
        logger.info(f"🧠 Gap Analysis parallélisée sur {len(requirements)} points...")
        with ThreadPoolExecutor(max_workers=4) as executor:
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
    with open("data/gap_analysis_report.md", "w", encoding="utf-8") as f:
        f.write(audit.generate_report(results))
    logger.success("✅ Audit terminé (parallélisé).")
