import os
import sys
import ollama
import json
from enum import Enum
from abc import ABC, abstractmethod
from pathlib import Path
from typing import List, Dict, Any
from dataclasses import dataclass, field
from dotenv import load_dotenv

# Configuration
env_path = Path(__file__).parent.parent / ".env"
load_dotenv(env_path)
sys.path.append(str(Path(__file__).parent.parent))


class RequirementState(Enum):
    RAW = "RAW"
    NORMALIZED = "NORMALIZED"
    CLEAN = "CLEAN"
    AUDITED = "AUDITED"
    BASELINE = "BASELINE"
    ERROR = "ERROR"


@dataclass
class FSMRequirement:
    """Entité d'exigence certifiée BABOK avec traçabilité totale."""

    uid: str
    original_text: str  # Le fragment complet
    source_quote: str = ""  # L'extrait exact qui a généré l'exigence
    state: RequirementState = RequirementState.RAW
    state_history: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    # Structure BABOK
    subject: str = ""
    action: str = ""
    target_object: str = ""
    constraint: str = ""
    condition: str = ""

    # Audit
    ambiguity_score: int = 0
    fuzzy_terms: List[str] = field(default_factory=list)
    missing_implications: List[str] = field(default_factory=list)
    gap_tickets: List[str] = field(default_factory=list)

    def transition_to(self, new_state: RequirementState, reason: str):
        old_state = self.state.value
        self.state = new_state
        self.state_history.append(f"{old_state} -> {new_state.value} ({reason})")


# --- MICRO-AGENTS BABOK & VISION ---


class FSMAgent(ABC):
    def __init__(self, model: Optional[str] = None):
        self.model = model or os.getenv("OLLAMA_TEXT_MODEL", "qwen2.5:7b")

    @abstractmethod
    def trigger(self, req: FSMRequirement) -> FSMRequirement:
        pass

    def _clean_json(self, raw_resp: str) -> Dict:
        try:
            clean = raw_resp.strip()
            if "```json" in clean:
                clean = clean.split("```json")[1].split("```")[0]
            elif "```" in clean:
                clean = clean.split("```")[1].split("```")[0]
            return json.loads(clean)
        except Exception:
            return {}


class BABOKAgent(FSMAgent):
    """Traducteur BABOK avec extraction de citation source."""

    def trigger(self, req: FSMRequirement) -> FSMRequirement:
        prompt = f"""Tu es un Ingénieur Exigences (BABOK). 
Analyse ce fragment et transforme-le en exigence atomique.
Tu dois extraire la 'citation_source' exacte du texte.

TEXTE : "{req.original_text}"

Réponds UNIQUEMENT en JSON :
{{
  "citation_source": "extrait exact du texte",
  "sujet": "L'acteur",
  "action": "Verbe d'action",
  "objet": "L'entité visée",
  "contrainte": "limite/norme",
  "condition": "déclencheur"
}}"""
        try:
            resp = ollama.generate(model=self.model, prompt=prompt, format="json")
            data = self._clean_json(resp.get("response", "{}"))
            req.source_quote = data.get("citation_source", "")
            req.subject = data.get("sujet", "")
            req.action = data.get("action", "")
            req.target_object = data.get("objet", "")
            req.constraint = data.get("contrainte", "")
            req.condition = data.get("condition", "")
            req.transition_to(RequirementState.NORMALIZED, "Conversion BABOK réussie")
        except Exception:
            req.transition_to(RequirementState.ERROR, "Erreur BABOK")
        return req


class VisionRequirementAgent(FSMAgent):
    """Transforme une image en exigences BABOK."""

    def __init__(self):
        super().__init__(model=os.getenv("OLLAMA_VISION_MODEL", "llama3.2-vision"))

    def trigger(self, req: FSMRequirement) -> FSMRequirement:
        # Note: Cette méthode est appelée si le metadata contient un chemin d'image
        if "image_path" not in req.metadata:
            return req

        # Logique simplifiée pour l'exemple
        return req


class WolfRadarAgent(FSMAgent):
    """Désambiguïsation."""

    def trigger(self, req: FSMRequirement) -> FSMRequirement:
        if req.state == RequirementState.ERROR:
            return req
        prompt = f'Analyse l\'ambiguïté en JSON (0-100) : "{req.source_quote or req.original_text}"'
        try:
            resp = ollama.generate(model=self.model, prompt=prompt, format="json")
            data = self._clean_json(resp.get("response", "{}"))
            req.ambiguity_score = int(data.get("ambiguity_score", 0))
            req.fuzzy_terms = data.get("fuzzy_terms", [])
            if req.ambiguity_score == 0:
                req.transition_to(RequirementState.CLEAN, "Texte limpide")
            else:
                req.transition_to(
                    RequirementState.NORMALIZED,
                    f"STALLED: Ambiguïté {req.ambiguity_score}",
                )
        except Exception:
            pass
        return req


class FSMPipeline:
    def __init__(self):
        self.factory = [BABOKAgent(), WolfRadarAgent()]

    def run_factory(self, text: str, uid: str, metadata: Dict = None) -> FSMRequirement:
        req = FSMRequirement(uid=uid, original_text=text, metadata=metadata or {})
        for agent in self.factory:
            req = agent.trigger(req)
        return req
