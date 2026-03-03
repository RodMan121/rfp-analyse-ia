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
from openai import AsyncOpenAI
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
        or_key = os.getenv("OPENROUTER_API_KEY")
        api_key = os.getenv("GOOGLE_API_KEY")
        
        if or_key and len(or_key) > 10:
            self.model = model or os.getenv("OPENROUTER_MODEL", "google/gemini-2.0-flash-001")
            self.client_or = AsyncOpenAI(
                base_url="https://openrouter.ai/api/v1",
                api_key=or_key,
            )
            self.mode = "OPENROUTER"
            logger.info(f"🌐 Agent {self.__class__.__name__} sur OpenRouter ({self.model})")
        elif api_key and len(api_key) > 10 and "your_google" not in api_key:
            self.model = model or os.getenv("GEMINI_MODEL", "gemini-2.0-flash")
            self.client_gemini = genai.Client(api_key=api_key)
            self.mode = "GEMINI"
            logger.info(f"✨ Agent {self.__class__.__name__} sur direct Gemini ({self.model})")
        else:
            self.model = model or os.getenv("OLLAMA_TEXT_MODEL", "llama3.2:3b")
            self.async_ollama = ollama.AsyncClient()
            self.mode = "OLLAMA"
            logger.info(f"🏠 Agent {self.__class__.__name__} sur Ollama local ({self.model})")

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
                        response_format={"type": "json_object"} if format == "json" else None
                    )
                    return {"response": response.choices[0].message.content}
                
                elif self.mode == "GEMINI":
                    config = {"response_mime_type": "application/json"} if format == "json" else {}
                    response = await self.client_gemini.aio.models.generate_content(
                        model=self.model, contents=prompt, config=config
                    )
                    return {"response": response.text}
                
                else: # OLLAMA
                    response = await self.async_ollama.generate(
                        model=self.model, 
                        prompt=prompt, 
                        format=format if format == "json" else None,
                        options={"num_ctx": 1024, "temperature": 0.1}
                    )
                    return {"response": response.get("response", "{}")}
            except Exception as e:
                if "429" in str(e):
                    await asyncio.sleep(5 * (attempt + 1))
                else:
                    await asyncio.sleep(2 * (attempt + 1))
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
        noise_keywords = ["page", "section", "figure", "catégorie", "essp-rd"]
        text_lower = req.original_text.lower()
        if len(req.original_text) < 50 or any(k in text_lower and len(req.original_text) < 80 for k in noise_keywords):
            req.transition_to(RequirementState.ERROR, "Bruit détecté")
            return req

        prompt = f"""Tu es un Ingénieur Exigences senior. Extrais l'exigence technique au format JSON.
Exemple :
Texte : "Le système doit sauvegarder les données chaque soir à 20h."
Réponse : {{"citation_source": "doit sauvegarder les données chaque soir à 20h", "sujet": "Le système", "action": "sauvegarder", "objet": "les données", "contrainte": "chaque soir à 20h"}}

Texte à analyser : "{req.original_text}"
Réponds UNIQUEMENT en JSON."""
        
        try:
            resp = await self._call_llm(prompt=prompt, format="json")
            data = self._clean_json(resp.get("response", "{}"))
            if not data.get("citation_source") or not data.get("sujet"):
                req.transition_to(RequirementState.ERROR, "Extraction incomplète")
                return req

            req.source_quote = data.get("citation_source", "")
            req.subject = data.get("sujet", "")
            req.action = data.get("action", "")
            req.target_object = data.get("objet", "")
            req.constraint = data.get("contrainte", "")
            req.transition_to(RequirementState.NORMALIZED, "Conversion BABOK réussie")
        except Exception: 
            req.transition_to(RequirementState.ERROR, "Erreur technique agent")
        return req

class WolfRadarAgent(FSMAgent):
    async def trigger(self, req: FSMRequirement) -> FSMRequirement:
        if req.state != RequirementState.NORMALIZED: return req
        prompt = f"Expert Ambiguïté: Score 0-100 (0=parfait) et termes flous JSON pour : \"{req.source_quote}\". Structure: {{\"ambiguity_score\": int, \"fuzzy_terms\": []}}"
        try:
            resp = await self._call_llm(prompt=prompt, format="json")
            data = self._clean_json(resp.get("response", "{}"))
            req.ambiguity_score = int(data.get("ambiguity_score", 0))
            if req.ambiguity_score < 20: 
                req.transition_to(RequirementState.CLEAN, "Limpide")
            else: 
                req.transition_to(RequirementState.NORMALIZED, f"STALLED: {req.ambiguity_score}")
        except Exception: pass
        return req

class FSMPipeline:
    def __init__(self):
        self.factory = [BABOKAgent(), WolfRadarAgent()]

    async def run_factory(self, text: str, uid: str, metadata: Dict = None) -> FSMRequirement:
        req = FSMRequirement(uid=uid, original_text=text, metadata=metadata or {})
        for agent in self.factory:
            req = await agent.trigger(req)
            if req.state == RequirementState.ERROR: break
        return req
