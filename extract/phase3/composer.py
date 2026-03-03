import os
import sys
import ollama
import json
import hashlib
import datetime
from pathlib import Path
from loguru import logger
from typing import List, Dict, Any
from dataclasses import dataclass, asdict
from dotenv import load_dotenv

# Fix pour les imports
sys.path.append(str(Path(__file__).parent.parent))
from phase2.micro_agents import FSMRequirement, RequirementState

# Configuration
env_path = Path(__file__).parent.parent / ".env"
load_dotenv(env_path)

@dataclass
class TechnicalBaseline:
    """Produit final immuable prêt pour ALM (ALM Ready)."""
    project_uid: str
    timestamp: str
    requirements_count: int
    validated_requirements: List[Dict]
    moscow_matrix: Dict[str, List[str]]
    integrity_score: int
    state: str = "BASELINE"

class ArchitectureComposer:
    """Phase 3 : Synthèse & Baseline (État : BASELINE)."""

    def __init__(self, model: str = None):
        self.model = model or os.getenv("OLLAMA_TEXT_MODEL", "qwen2.5:7b")

    def assemble_baseline(self, audited_requirements: List[FSMRequirement]) -> TechnicalBaseline:
        """Réassemble les fragments AUDITED en une Baseline immuable (JSON + MD)."""
        
        # 1. Sélection des exigences validées
        final_set = [r for r in audited_requirements if r.state == RequirementState.AUDITED]
        
        # 2. Construction MoSCoW
        matrix_data = self._construct_moscow(final_set)
        
        # 3. Scoring d'Intégrité Reverse TOGAF
        integrity_data = self._scoring_integrity(matrix_data)
        
        # 4. Scellage immuable
        serializable_reqs = []
        for r in final_set:
            r.transition_to(RequirementState.BASELINE, "Sceau d'immuabilité certifié")
            req_dict = asdict(r)
            req_dict['state'] = r.state.value
            serializable_reqs.append(req_dict)

        project_signature = hashlib.md5(json.dumps(serializable_reqs).encode()).hexdigest()

        baseline = TechnicalBaseline(
            project_uid=f"ALM-{project_signature[:12].upper()}",
            timestamp=datetime.datetime.now().isoformat(),
            requirements_count=len(final_set),
            validated_requirements=serializable_reqs,
            moscow_matrix=matrix_data.get("moscow", {}),
            integrity_score=integrity_data.get("score", 3)
        )

        # 5. Export des deux formats
        self._export_json(baseline)
        self._export_markdown(baseline)
        
        return baseline

    def _export_json(self, baseline: TechnicalBaseline):
        output_path = Path("data/technical_baseline_alm.json")
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(asdict(baseline), f, indent=2, ensure_ascii=False)
        logger.success(f"💾 JSON certifié : {output_path}")

    def _export_markdown(self, baseline: TechnicalBaseline):
        """Génère le document de Technical Baseline pour les humains."""
        output_path = Path("data/technical_baseline_final.md")
        
        md = f"# 📦 Technical Baseline — Projet {baseline.project_uid}\n\n"
        md += f"**Date de certification :** {baseline.timestamp}\n"
        md += f"**Nombre d'exigences validées :** {baseline.requirements_count}\n"
        md += f"**Score d'intégrité système :** {baseline.integrity_score}/5\n\n"
        
        md += "## 🎯 Matrice de Priorisation (MoSCoW)\n\n"
        for prio, reqs in baseline.moscow_matrix.items():
            md += f"### {prio}\n"
            if not reqs: md += "_Aucune exigence._\n"
            for r in reqs:
                # Gérer si r est une string ou un dict
                text = r.get('exigence', r) if isinstance(r, dict) else r
                md += f"- {text}\n"
            md += "\n"
            
        md += "## 📋 Catalogue des Exigences Certifiées\n\n"
        md += "| UID | Sujet | Action | Objet | Contrainte | Historique FSM |\n"
        md += "|:---:|---|---|---|---|---|\n"
        
        for r in baseline.validated_requirements:
            hist = " ➔ ".join([h.split(" (")[0] for h in r['state_history']])
            md += f"| {r['uid'][:8]} | {r['subject']} | {r['action']} | {r['target_object']} | {r['constraint']} | {hist} |\n"
            
        md += "\n---\n*Ce document est une Technical Baseline immuable générée par Augmented BID IA.*"
        
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(md)
        logger.success(f"📄 Markdown certifié : {output_path}")

    def _construct_moscow(self, requirements: List[FSMRequirement]) -> Dict:
        req_texts = [r.original_text for r in requirements]
        prompt = f"Expert MoSCoW: Priorise ces exigences en Must/Should/Could/Won't JSON : {json.dumps(req_texts)}"
        try:
            resp = ollama.generate(model=self.model, prompt=prompt, format="json")
            return json.loads(resp.get('response', '{}'))
        except: return {"moscow": {}}

    def _scoring_integrity(self, matrix_data: Dict) -> Dict:
        prompt = f"Expert TOGAF: Score l'intégrité (1-5) en JSON : {json.dumps(matrix_data)}"
        try:
            resp = ollama.generate(model=self.model, prompt=prompt, format="json")
            return json.loads(resp.get('response', '{}'))
        except: return {"score": 3}

if __name__ == "__main__":
    composer = ArchitectureComposer()
    mock_audited = FSMRequirement(uid="REQ-TEST", original_text="Le système doit être sécurisé.")
    mock_audited.state = RequirementState.AUDITED
    mock_audited.subject, mock_audited.action = "Le Système", "Sécuriser"
    composer.assemble_baseline([mock_audited])
