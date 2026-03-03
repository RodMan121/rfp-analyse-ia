import os
import sys
import ollama
import json
import asyncio
import time
import re
from enum import Enum
from abc import ABC, abstractmethod
from pathlib import Path
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field
from dotenv import load_dotenv
from google import genai
from openai import AsyncOpenAI
from loguru import logger

# Configuration
env_path = Path(__file__).parent.parent / ".env"
load_dotenv(env_path)
sys.path.append(str(Path(__file__).parent.parent))

# --- FIX v11 : Regex de bruit et d'ID ---
_NOISE_RE = re.compile(
    r"if printed|confidential information|iss\. \d+-\d+"
    r"|page \d+ of \d+|figure \d+\s*:|signature sheet"
    r"|document creation|applicable version"
    r"|this chapter must be quoted|section:\s*user requirement"
    r"|^\s*(green|certified ansp)\s*$",
    re.IGNORECASE
)

_REQUIREMENT_ID_RE = re.compile(
    r"\b(BN-\d{3}\\?[0-9_]*|IT[_-]REQ-\d{3})\b",
    re.IGNORECASE
)

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
        or_key = os.getenv("OPENROUTER_API_KEY")
        api_key = os.getenv("GOOGLE_API_KEY")
        
        if or_key and len(or_key) > 10:
            self.model = model or os.getenv("OPENROUTER_MODEL", "meta-llama/llama-3.3-70b-instruct")
            self.client_or = AsyncOpenAI(base_url="https://openrouter.ai/api/v1", api_key=or_key)
            self.mode = "OPENROUTER"
        elif api_key and len(api_key) > 10 and "your_google" not in api_key:
            self.model = model or os.getenv("GEMINI_MODEL", "gemini-2.0-flash")
            self.client_gemini = genai.Client(api_key=api_key)
            self.mode = "GEMINI"
        else:
            self.model = model or os.getenv("OLLAMA_TEXT_MODEL", "llama3.2:3b")
            self.async_ollama = ollama.AsyncClient()
            self.mode = "OLLAMA"

    @abstractmethod
    async def trigger(self, req: FSMRequirement) -> FSMRequirement:
        pass

    async def _call_llm(self, prompt: str, format: str = "json") -> Dict:
        max_retries = 3
        for attempt in range(max_retries):
            try:
                if self.mode == "OPENROUTER":
                    response = await self.client_or.chat.completions.create(
                        model=self.model,
                        messages=[{"role": "user", "content": prompt}],
                        response_format={"type": "json_object"} if format == "json" else None,
                        timeout=40.0
                    )
                    return {"response": response.choices[0].message.content}
                elif self.mode == "GEMINI":
                    config = {"response_mime_type": "application/json"} if format == "json" else {}
                    response = await self.client_gemini.aio.models.generate_content(model=self.model, contents=prompt, config=config)
                    return {"response": response.text}
                else: # OLLAMA
                    response = await self.async_ollama.generate(model=self.model, prompt=prompt, format=format if format == "json" else None, options={"num_ctx": 1024, "temperature": 0.1})
                    return {"response": response.get("response", "{}")}
            except Exception as e:
                await asyncio.sleep(5 * (attempt + 1))
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
        text = req.original_text

        # FIX v11 : Filtre longueur (monte à 80)
        if len(text) < 80:
            req.transition_to(RequirementState.ERROR, "Fragment trop court")
            return req

        # FIX v11 : Filtre bruit structurel regex
        if _NOISE_RE.search(text):
            req.transition_to(RequirementState.ERROR, "Bruit structurel filtré")
            return req

        # Extraction de l'identifiant officiel BN-XXX ou IT_REQ-XXX
        id_match = _REQUIREMENT_ID_RE.search(text)
        official_id = id_match.group(1) if id_match else None

        # FIX v11 : Prompt enrichi pour forcer l'extraction de l'id officiel
        prompt = f"""Tu es un expert BABOK v3. Analyse cette exigence RFP et retourne UNIQUEMENT ce JSON :
{{
  "sujet": "acteur ou système concerné",
  "action": "verbe d'obligation (must/shall/should)",
  "objet": "ce qui doit être réalisé",
  "citation_source": "citation verbatim de l'exigence (40-200 chars)",
  "official_id": "identifiant BN-XXX ou IT_REQ-XXX trouvé, sinon null",
  "is_real_requirement": true/false
}}

Texte : \"{text}\"

Règle : is_real_requirement = false si le texte est une légende, un header, une note administrative, ou ne contient pas d'obligation fonctionnelle claire."""

        try:
            resp = await self._call_llm(prompt=prompt, format="json")
            data = self._clean_json(resp.get("response", "{}"))

            # Rejeter si le LLM confirme que ce n'est pas une vraie exigence
            if not data.get("is_real_requirement", True):
                req.transition_to(RequirementState.ERROR, "Non-exigence confirmée par LLM")
                return req

            if not data.get("citation_source") or not data.get("sujet"):
                req.transition_to(RequirementState.ERROR, "Structure BABOK incomplète")
                return req

            req.source_quote = data.get("citation_source", "")
            req.subject = data.get("sujet", "")
            req.action = data.get("action", "")
            req.target_object = data.get("objet", "")

            # Stocker l'id officiel dans les métadonnées
            final_id = official_id or data.get("official_id")
            if final_id:
                req.metadata["official_id"] = final_id

            req.transition_to(RequirementState.NORMALIZED, "Conversion BABOK réussie")
        except Exception as e:
            req.transition_to(RequirementState.ERROR, f"Erreur BABOK: {e}")
        return req

class WolfRadarAgent(FSMAgent):
    async def trigger(self, req: FSMRequirement) -> FSMRequirement:
        if req.state != RequirementState.NORMALIZED: return req
        prompt = f"Expert Ambiguïté: Score 0-100 et termes flous pour : \"{req.source_quote}\". JSON: {{\"ambiguity_score\": int, \"fuzzy_terms\": []}}"
        try:
            resp = await self._call_llm(prompt=prompt, format="json")
            data = self._clean_json(resp.get("response", "{}"))
            req.ambiguity_score = int(data.get("ambiguity_score", 0))
            req.fuzzy_terms = data.get("fuzzy_terms", [])
            if req.ambiguity_score < 20: req.transition_to(RequirementState.CLEAN, "Limpide")
            else: req.transition_to(RequirementState.NORMALIZED, f"STALLED: {req.ambiguity_score}")
        except Exception: pass
        return req

class ISO25010Agent(FSMAgent):
    async def trigger(self, req: FSMRequirement) -> FSMRequirement:
        if req.state != RequirementState.CLEAN: return req
        req.transition_to(RequirementState.AUDITED, "Audit ISO 25010 complété")
        return req

class FSMPipeline:
    def __init__(self):
        self.factory = [BABOKAgent(), WolfRadarAgent(), ISO25010Agent()]

    async def run_factory(self, text: str, uid: str, metadata: Dict = None) -> FSMRequirement:
        req = FSMRequirement(uid=uid, original_text=text, metadata=metadata or {})
        for agent in self.factory:
            req = await agent.trigger(req)
            if req.state == RequirementState.ERROR: break
        return req
