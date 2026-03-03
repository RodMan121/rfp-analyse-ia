import os
import sys
import ollama
import json
import asyncio
import time
from enum import Enum
from abc import ABC, abstractmethod
from pathlib import Path
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field
from dotenv import load_dotenv
from google import genai
from loguru import logger

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
    uid: str
    original_text: str
    source_quote: str = ""
    state: RequirementState = RequirementState.RAW
    state_history: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    subject: str = ""
    action: str = ""
    target_object: str = ""
    constraint: str = ""
    condition: str = ""
    ambiguity_score: int = 0
    fuzzy_terms: List[str] = field(default_factory=list)
    missing_implications: List[str] = field(default_factory=list)
    gap_tickets: List[str] = field(default_factory=list)

    def transition_to(self, new_state: RequirementState, reason: str):
        old_state = self.state.value
        self.state = new_state
        self.state_history.append(f"{old_state} -> {new_state.value} ({reason})")

class FSMAgent(ABC):
    def __init__(self, model: Optional[str] = None):
        api_key = os.getenv("GOOGLE_API_KEY")
        if api_key and len(api_key) > 10 and "your_google" not in api_key:
            self.model = model or os.getenv("GEMINI_MODEL", "gemini-2.0-flash")
            self.client = genai.Client(api_key=api_key)
            self.is_gemini = True
        else:
            self.model = model or os.getenv("OLLAMA_TEXT_MODEL", "qwen2.5:7b")
            self.is_gemini = False
            self.async_ollama = ollama.AsyncClient()

    @abstractmethod
    async def trigger(self, req: FSMRequirement) -> FSMRequirement:
        pass

    async def _call_llm(self, prompt: str, format: str = "json") -> Dict:
        """Appelle le LLM de manière asynchrone avec retry."""
        max_retries = 3
        for attempt in range(max_retries):
            try:
                if self.is_gemini:
                    config = {"response_mime_type": "application/json"} if format == "json" else {}
                    # Utilisation de l'API asynchrone de Gemini (SDK v1+)
                    response = await self.client.aio.models.generate_content(
                        model=self.model, contents=prompt, config=config
                    )
                    return {"response": response.text}
                else:
                    # Ajout d'options pour optimiser la VRAM (num_ctx=1024)
                    response = await self.async_ollama.generate(
                        model=self.model, 
                        prompt=prompt, 
                        format=format if format == "json" else None,
                        options={
                            "num_ctx": 1024,
                            "temperature": 0.1,
                            "num_predict": 1024
                        }
                    )
                    return {"response": response.get("response", "{}")}
            except Exception as e:
                delay = 2 * (attempt + 1)
                await asyncio.sleep(delay)
        return {"response": "{}"}

    def _clean_json(self, raw_resp: str) -> Dict:
        try:
            clean = raw_resp.strip()
            if "```json" in clean: clean = clean.split("```json")[1].split("```")[0]
            elif "```" in clean: clean = clean.split("```")[1].split("```")[0]
            return json.loads(clean)
        except Exception: return {}

class BABOKAgent(FSMAgent):
    async def trigger(self, req: FSMRequirement) -> FSMRequirement:
        prompt = f"Expert BABOK: Extrais Sujet/Action/Objet/Citation en JSON pour : \"{req.original_text}\""
        try:
            resp = await self._call_llm(prompt=prompt, format="json")
            data = self._clean_json(resp.get("response", "{}"))
            req.source_quote = data.get("citation_source", "")
            req.subject = data.get("sujet", "")
            req.action = data.get("action", "")
            req.target_object = data.get("objet", "")
            req.transition_to(RequirementState.NORMALIZED, "Conversion BABOK réussie")
        except Exception: req.transition_to(RequirementState.ERROR, "Erreur BABOK")
        return req

class WolfRadarAgent(FSMAgent):
    async def trigger(self, req: FSMRequirement) -> FSMRequirement:
        if req.state == RequirementState.ERROR: return req
        prompt = f"Expert Ambiguïté: Score 0-100 et termes flous JSON pour : \"{req.source_quote or req.original_text}\""
        try:
            resp = await self._call_llm(prompt=prompt, format="json")
            data = self._clean_json(resp.get("response", "{}"))
            req.ambiguity_score = int(data.get("ambiguity_score", 0))
            if req.ambiguity_score == 0: req.transition_to(RequirementState.CLEAN, "Limpide")
            else: req.transition_to(RequirementState.NORMALIZED, f"STALLED: {req.ambiguity_score}")
        except Exception: pass
        return req

class FSMPipeline:
    def __init__(self):
        self.factory = [BABOKAgent(), WolfRadarAgent()]

    async def run_factory(self, text: str, uid: str, metadata: Dict = None) -> FSMRequirement:
        req = FSMRequirement(uid=uid, original_text=text, metadata=metadata or {})
        for agent in self.factory:
            req = await agent.trigger(req)
        return req
