import os
import sys
import ollama
import json
from pathlib import Path

# Fix pour permettre l'importation de phase1 depuis le dossier parent
sys.path.append(str(Path(__file__).parent.parent))

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
        self.rfp_store = VectorStore(
            db_path=db_path, collection_name="rfp_hierarchical"
        )
        self.catalog_store = VectorStore(
            db_path=db_path, collection_name="service_catalog"
        )
        self.reranker = LocalReranker()
        self.model = TEXT_MODEL
        logger.info(f"🛡️ Agent d'Audit prêt (Modèle: {self.model})")

    def extract_requirements(self, category: str = "GENERAL") -> List[Dict]:
        """Extraction des exigences avec prompt assoupli."""
        logger.info(f"🔎 Audit de la catégorie : {category}...")

        # On cherche les fragments de la catégorie
        fragments = self.rfp_store.search_hybrid(
            query=f"CATÉGORIE: {category}", n_results=15
        )
        if not fragments:
            logger.warning(f"⚠️ Aucun fragment trouvé pour {category}")
            return []

        all_requirements = []
        for frag in fragments:
            text = frag["text"]
            # Prompt plus simple et direct
            prompt = f"""Tu es un expert senior en réponse aux appels d'offres.
Lis ce fragment de document et liste TOUTES les obligations, contraintes ou besoins techniques qu'il contient.

FRAGMENT :
{text}

Réponds UNIQUEMENT au format JSON comme ceci :
[
  {{"exigence": "Description de l'obligation", "priorite": "HAUTE/MOYENNE/BASSE"}}
]
Si aucune obligation n'est présente, réponds []."""

            try:
                # Utilisation sans format="json" forcé pour plus de flexibilité, puis nettoyage manuel
                response = ollama.generate(model=self.model, prompt=prompt)
                raw_resp = response.get("response", "[]").strip()

                # Nettoyage Markdown si l'IA en a mis
                if "```json" in raw_resp:
                    raw_resp = raw_resp.split("```json")[1].split("```")[0]
                elif "```" in raw_resp:
                    raw_resp = raw_resp.split("```")[1].split("```")[0]

                reqs = json.loads(raw_resp)

                if isinstance(reqs, list):
                    for r in reqs:
                        if isinstance(r, dict) and "exigence" in r:
                            r["source"] = (
                                f"{frag['metadata']['breadcrumbs']} (P.{frag['metadata']['page']})"
                            )
                            all_requirements.append(r)
            except Exception as e:
                logger.debug(f"⚠️ Erreur parsing exigence : {e}")

        logger.info(f"✅ {len(all_requirements)} exigences extraites pour {category}.")
        return all_requirements

    def _analyze_single_gap(self, req: Dict) -> Dict:
        """Analyse d'une seule exigence."""
        result = {**req}
        know_how = self.catalog_store.search_hybrid(
            query=result["exigence"], n_results=3
        )
        context = (
            "\n".join([k["text"] for k in know_how])
            if know_how
            else "AUCUN SAVOIR-FAIRE TROUVÉ."
        )

        prompt = f"""EXIGENCE CLIENT : {result["exigence"]}
NOTRE RÉFÉRENTIEL : {context}

Détermine notre niveau de conformité.
Réponds UNIQUEMENT en JSON :
{{
  "statut": "CONFORME / PARTIEL / NON_CONFORME",
  "justification": "Explication courte",
  "score_confiance": 0-100
}}"""

        try:
            response = ollama.generate(model=self.model, prompt=prompt)
            raw_resp = response.get("response", "{}").strip()
            if "```json" in raw_resp:
                raw_resp = raw_resp.split("```json")[1].split("```")[0]
            gap = json.loads(raw_resp)
            result.update(gap)
        except Exception:
            result.update({"statut": "ERREUR", "score_confiance": 0})
        return result

    def analyze_gap(self, requirements: List[Dict]) -> List[Dict]:
        if not requirements:
            return []
        workers = int(os.getenv("OLLAMA_NUM_PARALLEL", "1"))
        logger.info(
            f"🧠 Gap Analysis ({workers} workers) sur {len(requirements)} points..."
        )
        with ThreadPoolExecutor(max_workers=workers) as executor:
            results = list(executor.map(self._analyze_single_gap, requirements))
        return results

    def generate_report(self, analysis: List[Dict]) -> str:
        if not analysis:
            return "# 📋 Aucune exigence trouvée."
        report = "# 📋 Matrice de Conformité & Gap Analysis (GTM)\n\n"
        report += (
            "| Statut | Confiance | Priorité | Exigence | Source | Justification |\n"
        )
        report += (
            "|--------|-----------|----------|----------|--------|---------------|\n"
        )
        for r in analysis:
            status = r.get("statut", "INCONNU")
            s_emoji = (
                "✅"
                if "CONFORME" in status and "NON" not in status
                else "⚠️"
                if "PARTIEL" in status
                else "❌"
            )
            conf = f"{r.get('score_confiance', 0)}%"
            report += f"| {s_emoji} {status} | {conf} | {r.get('priorite')} | {r['exigence']} | {r['source']} | {r.get('justification')} |\n"
        return report


if __name__ == "__main__":
    audit = ComplianceAuditAgent()
    all_results = []
    for cat in ["TECHNIQUE", "SECURITE"]:
        reqs = audit.extract_requirements(category=cat)
        results = audit.analyze_gap(reqs)
        all_results.extend(results)

    with open("data/gap_analysis_report.md", "w", encoding="utf-8") as f:
        f.write(audit.generate_report(all_results))
    logger.success("✅ Audit terminé.")
