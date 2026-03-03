import os
import sys
import ollama
import json
from enum import Enum
from abc import ABC, abstractmethod
from pathlib import Path
from loguru import logger
from typing import List, Dict, Optional, Any
from dataclasses import dataclass, asdict, field
from dotenv import load_dotenv

# Configuration
env_path = Path(__file__).parent.parent / ".env"
load_dotenv(env_path)
sys.path.append(str(Path(__file__).parent.parent))

class RequirementState(Enum):
    RAW = "RAW"
    CLASSIFIED = "CLASSIFIED"
    NORMALIZED = "NORMALIZED"
    CLEAN = "CLEAN"
    AUDITED = "AUDITED"
    BASELINE = "BASELINE"

@dataclass
class FSMRequirement:
    """Entité centrale avec traçabilité d'état (FSM)."""
    uid: str
    original_text: str
    state: RequirementState = RequirementState.RAW
    state_history: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    # Données enrichies par les agents
    subject: str = ""
    action: str = ""
    target_object: str = ""
    constraint: str = ""
    ambiguity_score: int = 0
    fuzzy_terms: List[str] = field(default_factory=list)
    missing_implications: List[str] = field(default_factory=list)
    gap_tickets: List[str] = field(default_factory=list)

    def transition_to(self, new_state: RequirementState, reason: str):
        """Gère le changement d'état avec traçabilité."""
        old_state = self.state.value
        self.state = new_state
        self.state_history.append(f"{old_state} -> {new_state.value} ({reason})")
        logger.debug(f"ID:{self.uid[:8]} | {old_state} -> {new_state.value}")

# --- SERVICES AUTONOMES (MICRO-SERVICES FSM) ---

class FSMAgent(ABC):
    def __init__(self, model: str = None):
        self.model = model or os.getenv("OLLAMA_TEXT_MODEL", "qwen2.5:7b")

    @abstractmethod
    def trigger(self, req: FSMRequirement) -> FSMRequirement:
        pass

    def _clean_json(self, raw_resp: str) -> Dict:
        try:
            clean = raw_resp.strip()
            if "```json" in clean: clean = clean.split("```json")[1].split("```")[0]
            elif "```" in clean: clean = clean.split("```")[1].split("```")[0]
            return json.loads(clean)
        except Exception as e:
            logger.error(f"❌ Erreur JSON : {e}")
            return {}

class BABOKAgent(FSMAgent):
    """RAW/CLASSIFIED -> NORMALIZED"""
    def trigger(self, req: FSMRequirement) -> FSMRequirement:
        prompt = f"Agent BABOK: Normalise en Sujet/Action/Objet JSON : \"{req.original_text}\""
        resp = ollama.generate(model=self.model, prompt=prompt, format="json")
        data = self._clean_json(resp.get('response', '{}'))
        req.subject, req.action = data.get('sujet', ''), data.get('action', '')
        req.target_object, req.constraint = data.get('objet', ''), data.get('contrainte', '')
        req.transition_to(RequirementState.NORMALIZED, "Normalisation BABOK effectuée")
        return req

class WolfRadarAgent(FSMAgent):
    """NORMALIZED -> CLEAN (ou bloqué)"""
    def trigger(self, req: FSMRequirement) -> FSMRequirement:
        prompt = f"Agent Radar: Traque les adjectifs flous en JSON : \"{req.original_text}\""
        resp = ollama.generate(model=self.model, prompt=prompt, format="json")
        data = self._clean_json(resp.get('response', '{}'))
        req.ambiguity_score = data.get('ambiguity_score', 0)
        req.fuzzy_terms = data.get('fuzzy_terms', [])
        
        # Logique de blocage FSM
        if req.ambiguity_score == 0:
            req.transition_to(RequirementState.CLEAN, "Zéro ambiguïté détectée")
        else:
            logger.warning(f"🚨 FSM Bloqué pour {req.uid[:8]} : Ambiguïté > 0")
            req.state_history.append(f"STALLED at {req.state.value} (Ambiguity: {req.ambiguity_score})")
        return req

class CompletenessAgent(FSMAgent):
    """CLEAN -> AUDITED"""
    def trigger(self, req: FSMRequirement) -> FSMRequirement:
        if req.state != RequirementState.CLEAN: return req
        prompt = f"Agent ISO 25010: Identifie manques (Sécurité, archivage) JSON : \"{req.original_text}\""
        resp = ollama.generate(model=self.model, prompt=prompt, format="json")
        data = self._clean_json(resp.get('response', '{}'))
        req.missing_implications = data.get('missing_implications', [])
        req.gap_tickets = data.get('gap_tickets', [])
        req.transition_to(RequirementState.AUDITED, "Audit de complétude terminé")
        return req

# --- ORCHESTRATEUR DE L'USINE (FSM ENGINE) ---

class FSMPipeline:
    """Orchestre les transitions d'état de l'Usine à RFP."""
    def __init__(self):
        self.factory = [BABOKAgent(), WolfRadarAgent(), CompletenessAgent()]

    def run_factory(self, text: str, uid: str, metadata: Dict = None) -> FSMRequirement:
        req = FSMRequirement(uid=uid, original_text=text, metadata=metadata or {})
        
        for agent in self.factory:
            req = agent.trigger(req)
            # Si un agent n'a pas pu faire passer l'état à la suite, on arrête
            # (Ex: WolfRadar bloque si score > 0)
        return req

if __name__ == "__main__":
    pipeline = FSMPipeline()
    logger.info("🏭 Lancement de l'Usine à RFP (FSM-Driven)")
    
    # Test 1 : Exigence Claire
    res1 = pipeline.run_factory("Le système doit sauvegarder les données.", "UID-001")
    
    # Test 2 : Exigence Floue (va bloquer au Radar)
    res2 = pipeline.run_factory("Le système doit être moderne et ergonomique.", "UID-002")
    
    print("\n--- TRACE FSM UID-001 ---")
    print(json.dumps(asdict(res1), indent=2, ensure_ascii=False))
    print("\n--- TRACE FSM UID-002 ---")
    print(json.dumps(asdict(res2), indent=2, ensure_ascii=False))
