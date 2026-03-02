import ollama
import json
from pathlib import Path
from loguru import logger
from typing import List, Dict
from phase1.vectorstore import VectorStore
from phase1.reranker import LocalReranker

class ComplianceAuditAgent:
    """
    Agent spécialisé dans l'Audit de Conformité et la Gap Analysis (Phase 2).
    """

    def __init__(self, db_path: str = "data/chroma_db_hierarchical"):
        # Store pour le RFP (L'appel d'offres)
        self.rfp_store = VectorStore(db_path=db_path, collection_name="rfp_hierarchical")
        # Store pour le Catalogue de Services (Votre savoir-faire)
        self.catalog_store = VectorStore(db_path=db_path, collection_name="service_catalog")
        
        self.reranker = LocalReranker()
        self.model = "qwen2.5:7b"
        logger.info(f"🛡️ Agent d'Audit & Gap Analysis initialisé (Modèle : {self.model})")

    def extract_requirements(self, category: str = "GENERAL") -> List[Dict]:
        """Extraie les exigences depuis le RFP."""
        logger.info(f"🔎 Audit de la catégorie : {category}...")
        fragments = self.rfp_store.search_hybrid(query=f"CATÉGORIE: {category}", n_results=15)
        
        if not fragments: return []

        all_requirements = []
        for frag in fragments:
            text = frag['text']
            source = f"{frag['metadata']['breadcrumbs']} (Page {frag['metadata']['page']})"
            
            prompt = f"FRAGMENT :\n{text}\n\nExtraie les exigences précises. Réponds UNIQUEMENT en JSON :\n" \
                     "[{\"exigence\": \"...\", \"priorite\": \"HAUTE/MOYENNE/BASSE\"}]"

            try:
                response = ollama.generate(model=self.model, prompt=prompt, format="json")
                reqs = json.loads(response['response'])
                for r in reqs:
                    r['source'] = source
                    all_requirements.append(r)
            except: continue

        return all_requirements

    def analyze_gap(self, requirements: List[Dict]) -> List[Dict]:
        """Compare chaque exigence avec le catalogue de services (Gap Analysis)."""
        logger.info(f"🧠 Analyse d'écart (Gap Analysis) sur {len(requirements)} points...")
        results = []

        for req in requirements:
            # 1. Chercher des preuves de savoir-faire dans le catalogue
            know_how = self.catalog_store.search_hybrid(query=req['exigence'], n_results=3)
            context_catalog = "\n".join([k['text'] for k in know_how]) if know_how else "AUCUN SAVOIR-FAIRE TROUVÉ."

            # 2. IA Compare l'exigence avec le savoir-faire
            prompt = f"""EXIGENCE CLIENT : {req['exigence']}
            NOTRE SAVOIR-FAIRE : {context_catalog}
            
            Détermine la conformité. Réponds UNIQUEMENT en JSON :
            {{
              "statut": "CONFORME / PARTIEL / NON_CONFORME",
              "justification": "Explique pourquoi par rapport à notre savoir-faire.",
              "preuve": "Cite l'élément du catalogue (si trouvé)."
            }}"""

            try:
                response = ollama.generate(model=self.model, prompt=prompt, format="json")
                gap = json.loads(response['response'])
                # Fusion des données
                req.update(gap)
                results.append(req)
            except: 
                req.update({"statut": "NON_CLASSE", "justification": "Erreur d'analyse."})
                results.append(req)

        return results

    def generate_report(self, analysis: List[Dict]) -> str:
        """Génère le rapport final GTM + Gap Analysis."""
        report = "# 📋 Matrice de Conformité & Gap Analysis (GTM)\n\n"
        report += "| Statut | Priorité | Exigence | Source | Justification |\n"
        report += "|--------|----------|----------|--------|---------------|\n"
        
        for r in analysis:
            status_emoji = "✅" if r['statut'] == "CONFORME" else "⚠️" if r['statut'] == "PARTIEL" else "❌"
            prio_emoji = "🔴" if r['priorite'] == "HAUTE" else "🟡"
            
            report += f"| {status_emoji} | {prio_emoji} | {r['exigence']} | {r['source']} | {r['justification']} |\n"
            
        return report

if __name__ == "__main__":
    audit = ComplianceAuditAgent()
    
    # 1. Extraction (RFP)
    reqs = audit.extract_requirements(category="TECHNIQUE")
    
    # 2. Analyse d'Écart (Si catalogue présent)
    results = audit.analyze_gap(reqs)
    
    # 3. Rapport
    report = audit.generate_report(results)
    with open("data/gap_analysis_report.md", "w", encoding="utf-8") as f:
        f.write(report)
    
    logger.success("✅ Analyse de Conformité & Gap Analysis terminée.")
