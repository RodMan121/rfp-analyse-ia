import os
import sys
import ollama
import json
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
    """Produit final immuable prêt pour ALM."""
    project_uid: str
    validated_requirements: List[Dict]
    moscow_matrix: Dict[str, List[str]]
    integrity_score: int  # Basé sur Reverse TOGAF
    state: str = "BASELINE"

class ArchitectureComposer:
    """Phase 3 : Synthèse & Baseline (AUDITED -> BASELINE)."""

    def __init__(self, model: str = None):
        self.model = model or os.getenv("OLLAMA_TEXT_MODEL", "qwen2.5:7b")

    def assemble_baseline(self, audited_requirements: List[FSMRequirement]) -> TechnicalBaseline:
        """Réassemble les fragments AUDITED en une Baseline cohérente."""
        
        # Filtrer uniquement les exigences qui ont atteint l'état AUDITED
        final_set = [r for r in audited_requirements if r.state == RequirementState.AUDITED]
        
        # 1. MoSCoW & Transitions
        matrix_data = self._construct_moscow(final_set)
        
        # 2. Reverse TOGAF Scoring
        integrity_data = self._scoring_integrity(matrix_data)
        
        # Marquer la transition finale vers BASELINE
        for r in final_set:
            r.transition_to(RequirementState.BASELINE, "Intégration dans la Technical Baseline")

        return TechnicalBaseline(
            project_uid=hashlib.md5(str(matrix_data).encode()).hexdigest()[:12] if 'hashlib' in globals() else "PROJ-V1",
            validated_requirements=[asdict(r) for r in final_set],
            moscow_matrix=matrix_data.get("moscow", {}),
            integrity_score=integrity_data.get("score", 3)
        )

    def _construct_moscow(self, requirements: List[FSMRequirement]) -> Dict:
        """Constructeur Matrice MoSCoW."""
        req_texts = [r.original_text for r in requirements]
        prompt = f"Expert MoSCoW: Classe ces exigences en Must/Should/Could/Won't JSON : {json.dumps(req_texts)}"
        try:
            resp = ollama.generate(model=self.model, prompt=prompt, format="json")
            return json.loads(resp.get('response', '{}'))
        except: return {"moscow": {}}

    def _scoring_integrity(self, matrix_data: Dict) -> Dict:
        """Moteur Reverse TOGAF : Scoring d'Intégrité Système."""
        prompt = f"Expert TOGAF: Score l'intégrité (1-5) de cette matrice technique en JSON : {json.dumps(matrix_data)}"
        try:
            resp = ollama.generate(model=self.model, prompt=prompt, format="json")
            return json.loads(resp.get('response', '{}'))
        except: return {"score": 3}

if __name__ == "__main__":
    import hashlib
    composer = ArchitectureComposer()
    
    # Simulation d'une exigence ayant passé tout le pipeline FSM
    req = FSMRequirement(uid="REQ-001", original_text="Authentification MFA obligatoire.")
    req.state = RequirementState.AUDITED
    
    baseline = composer.assemble_baseline([req])
    print("\n📦 TECHNICAL BASELINE GÉNÉRÉE")
    print(json.dumps(asdict(baseline), indent=2, ensure_ascii=False))
