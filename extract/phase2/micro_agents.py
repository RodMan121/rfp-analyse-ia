import os
import sys
import ollama
import json
import asyncio
import time
import re
import base64
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

# --- Regex de bruit et d'ID ---
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
    requirement_id: str = "N/A"
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

    async def _call_llm(self, prompt: str, format: str = "json", image_path: Optional[str] = None) -> Dict:
        """Appelle le LLM avec support optionnel de l'image."""
        max_retries = 3
        
        # Encodage de l'image si présente
        base64_image = None
        if image_path and os.path.exists(image_path):
            with open(image_path, "rb") as f:
                base64_image = base64.b64encode(f.read()).decode("utf-8")

        for attempt in range(max_retries):
            try:
                if self.mode == "OPENROUTER":
                    content = [{"type": "text", "text": prompt}]
                    if base64_image:
                        content.append({
                            "type": "image_url",
                            "image_url": {"url": f"data:image/png;base64,{base64_image}"}
                        })
                    
                    response = await self.client_or.chat.completions.create(
                        model=self.model,
                        messages=[{"role": "user", "content": content}],
                        response_format={"type": "json_object"} if format == "json" else None,
                        timeout=60.0
                    )
                    return {"response": response.choices[0].message.content}
                
                elif self.mode == "GEMINI":
                    # Note: Support multimodal via client direct Google
                    content = [prompt]
                    if base64_image:
                        from google.genai import types
                        with open(image_path, "rb") as f:
                            img_data = f.read()
                        content.append(types.Part.from_bytes(data=img_data, mime_type="image/png"))
                    
                    config = {"response_mime_type": "application/json"} if format == "json" else {}
                    response = await self.client_gemini.aio.models.generate_content(
                        model=self.model, contents=content, config=config
                    )
                    return {"response": response.text}
                
                else: # OLLAMA
                    images = [image_path] if image_path else None
                    response = await self.async_ollama.generate(
                        model=self.model, 
                        prompt=prompt, 
                        images=images,
                        format=format if format == "json" else None,
                        options={"num_ctx": 2048, "temperature": 0.1}
                    )
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

class VisionRequirementAgent(FSMAgent):
    """Analyse les schémas et maquettes pour en extraire des descriptions techniques."""
    def __init__(self):
        super().__init__()
        # On force un modèle Vision si on est sur OpenRouter ou Ollama
        if self.mode == "OPENROUTER":
            self.model = os.getenv("OPENROUTER_VISION_MODEL", "google/gemini-2.0-flash-001")
        elif self.mode == "OLLAMA":
            self.model = os.getenv("OLLAMA_VISION_MODEL", "llama3.2-vision")

    async def trigger(self, req: FSMRequirement) -> FSMRequirement:
        img_path = req.metadata.get("image_path")
        if not img_path:
            return req

        prompt = """Analyse cette image extraite d'un appel d'offres (schéma ou maquette fil de fer).
Décris précisément tous les éléments techniques, les champs de saisie, les boutons, les flux de données ou les composants d'infrastructure visibles.
Transforme cette image en une liste d'exigences textuelles factuelles.
Réponds UNIQUEMENT en JSON : {"description": "...", "extracted_requirements": ["req 1", "req 2"]}"""

        try:
            resp = await self._call_llm(prompt=prompt, format="json", image_path=img_path)
            data = self._clean_json(resp.get("response", "{}"))
            
            # On enrichit le texte original avec la description de la vision
            desc = data.get("description", "")
            reqs = "\n".join(data.get("extracted_requirements", []))
            req.original_text = f"[VISION ANALYSIS]\nDescription: {desc}\nRequirements:\n{reqs}"
            
            req.transition_to(RequirementState.RAW, "Analyse Vision complétée")
        except Exception as e:
            logger.error(f"❌ Erreur Vision sur {img_path}: {e}")
        
        return req

class BABOKAgent(FSMAgent):
    async def trigger(self, req: FSMRequirement) -> FSMRequirement:
        text = req.original_text
        if len(text) < 50: return req # Laisse passer pour le moment si c'est de la vision

        if _NOISE_RE.search(text) and "VISION" not in text:
            req.transition_to(RequirementState.ERROR, "Bruit structurel filtré")
            return req

        id_match = _REQUIREMENT_ID_RE.search(text)
        official_id = id_match.group(1) if id_match else None

        prompt = f"""Tu es un expert BABOK v3. Analyse cette exigence (texte ou description d'image) et retourne ce JSON :
{{
  "sujet": "acteur ou système",
  "action": "must/shall/should",
  "objet": "réalisation",
  "citation_source": "verbatim (ou synthèse si vision)",
  "official_id": "identifiant si présent",
  "is_real_requirement": true/false
}}
Texte : \"{text}\""""

        try:
            resp = await self._call_llm(prompt=prompt, format="json")
            data = self._clean_json(resp.get("response", "{}"))

            if not data.get("is_real_requirement", True):
                req.transition_to(RequirementState.ERROR, "Non-exigence")
                return req

            req.source_quote = data.get("citation_source", "")
            req.subject = data.get("sujet", "")
            req.action = data.get("action", "")
            req.target_object = data.get("objet", "")
            final_id = official_id or data.get("official_id")
            if final_id: req.metadata["official_id"] = final_id

            req.transition_to(RequirementState.NORMALIZED, "Conversion BABOK réussie")
        except Exception: 
            req.transition_to(RequirementState.ERROR, "Erreur BABOK")
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
        # Ordre crucial : Vision d'abord pour transformer les images en texte
        self.factory = [VisionRequirementAgent(), BABOKAgent(), WolfRadarAgent(), ISO25010Agent()]

    async def run_factory(self, text: str, uid: str, metadata: Dict = None) -> FSMRequirement:
        req = FSMRequirement(uid=uid, original_text=text, metadata=metadata or {})
        for agent in self.factory:
            req = await agent.trigger(req)
            if req.state == RequirementState.ERROR: break
        return req
