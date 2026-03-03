import os
import sys
import ollama
import json
import hashlib
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
        """Réassemble les fragments AUDITED en une Baseline immuable."""
        
        # 1. Sélection des exigences ayant atteint l'état final validé
        final_set = [r for r in audited_requirements if r.state == RequirementState.AUDITED]
        
        # 2. Construction MoSCoW
        matrix_data = self._construct_moscow(final_set)
        
        # 3. Scoring d'Intégrité Reverse TOGAF
        integrity_data = self._scoring_integrity(matrix_data)
        
        # 4. Scellage immuable (Transition BASELINE)
        import datetime
        serializable_reqs = []
        for r in final_set:
            r.transition_to(RequirementState.BASELINE, "Sceau d'immuabilité ALM Ready")
            req_dict = asdict(r)
            req_dict['state'] = r.state.value  # Conversion Enum pour JSON
            serializable_reqs.append(req_dict)

        # Génération du UID unique du projet basé sur le contenu total
        project_signature = hashlib.md5(json.dumps(serializable_reqs).encode()).hexdigest()

        baseline = TechnicalBaseline(
            project_uid=f"ALM-{project_signature[:12].upper()}",
            timestamp=datetime.datetime.now().isoformat(),
            requirements_count=len(final_set),
            validated_requirements=serializable_reqs,
            moscow_matrix=matrix_data.get("moscow", {}),
            integrity_score=integrity_data.get("score", 3)
        )

        self._export_artifact(baseline)
        return baseline

    def _export_artifact(self, baseline: TechnicalBaseline):
        """Sauvegarde l'artefact technique final (Output Node)."""
        output_path = Path("data/technical_baseline_alm.json")
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(asdict(baseline), f, indent=2, ensure_ascii=False)
        logger.success(f"💎 Technical Baseline Immuable générée : {output_path}")

    def _construct_moscow(self, requirements: List[FSMRequirement]) -> Dict:
        req_texts = [r.original_text for r in requirements]
        prompt = f"Expert MoSCoW: Priorise ces exigences JSON : {json.dumps(req_texts)}"
        try:
            resp = ollama.generate(model=self.model, prompt=prompt, format="json")
            return json.loads(resp.get('response', '{}'))
        except: return {"moscow": {}}

    def _scoring_integrity(self, matrix_data: Dict) -> Dict:
        prompt = f"Expert TOGAF: Score l'intégrité système (1-5) en JSON : {json.dumps(matrix_data)}"
        try:
            resp = ollama.generate(model=self.model, prompt=prompt, format="json")
            return json.loads(resp.get('response', '{}'))
        except: return {"score": 3}

if __name__ == "__main__":
    # Test unitaire de la phase de composition
    composer = ArchitectureComposer()
    mock_audited = FSMRequirement(uid="REQ-TEST", original_text="Le système doit être sécurisé.")
    mock_audited.state = RequirementState.AUDITED
    composer.assemble_baseline([mock_audited])
