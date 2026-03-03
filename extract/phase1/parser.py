# phase1/parser.py  — Niveau 2 : Gemini Flash (Multimodal)
import os
import time
import json
import pathlib
from dataclasses import dataclass
from loguru import logger
from google import genai
from google.genai import types
from dotenv import load_dotenv
from tenacity import retry, stop_after_attempt, wait_exponential

load_dotenv()

EXTRACTION_PROMPT = """Tu es un expert Business Analyst spécialisé dans l'analyse d'appels d'offres (RFP/CCTP).
Analyse ce document et retourne UNIQUEMENT un objet JSON :
{
  "fragments": [{"text": "...", "section": "...", "page": 0, "fragment_type": "texte|tableau|diagramme"}],
  "diagrams_extracted": [{"type": "...", "relations": [{"from": "A", "to": "B"}]}]
}
Langue : français."""

@dataclass
class RawFragment:
    text: str; section: str; page: int; source_file: str
    fragment_type: str = "texte"; visual_context: str | None = None

@dataclass
class DiagramRelation:
    from_component: str; to_component: str; label: str; source_file: str; section: str

class GeminiDocumentParser:
    def __init__(self, model: str = None):
        api_key = os.getenv("GOOGLE_API_KEY")
        if not api_key: raise EnvironmentError("GOOGLE_API_KEY manquante.")
        self.client = genai.Client(api_key=api_key)
        self.model = model or os.getenv("GEMINI_MODEL", "gemini-2.0-flash")
        logger.info(f"🤖 Gemini Parser prêt ({self.model})")

    def parse(self, filepath: str | pathlib.Path) -> tuple[list[RawFragment], list[DiagramRelation]]:
        path = pathlib.Path(filepath)
        mime_type = "application/pdf" if path.suffix == ".pdf" else "image/png"
        uploaded_file = self._upload_file(path, mime_type)
        raw_response = self._call_gemini(uploaded_file)
        try: self.client.files.delete(name=uploaded_file.name)
        except: pass
        return self._parse_response(raw_response, path.name)

    def _upload_file(self, path: pathlib.Path, mime_type: str):
        uploaded = self.client.files.upload(file=path, config={"display_name": path.name, "mime_type": mime_type})
        while uploaded.state == "PROCESSING":
            time.sleep(3)
            uploaded = self.client.files.get(name=uploaded.name)
        return uploaded

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
    def _call_gemini(self, uploaded_file) -> str:
        """Appel Gemini avec retry automatique en cas de rate limit ou timeout."""
        response = self.client.models.generate_content(
            model=self.model,
            contents=[uploaded_file, EXTRACTION_PROMPT],
            config=types.GenerateContentConfig(temperature=0.1, max_output_tokens=8192)
        )
        return response.text

    def _parse_response(self, raw_response: str, source_file: str):
        clean = raw_response.strip().replace("```json", "").replace("```", "").strip()
        try:
            data = json.loads(clean)
            frags = [RawFragment(text=f['text'], section=f['section'], page=f['page'], source_file=source_file) for f in data.get('fragments', [])]
            rels = [] # Extraction simplifiée
            return frags, rels
        except:
            return [RawFragment(text=raw_response[:1000], section="Doc", page=0, source_file=source_file)], []
