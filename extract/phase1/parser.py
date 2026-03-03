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
  "diagrams_extracted": [{"section": "...", "relations": [{"from": "A", "to": "B", "label": "..."}]}]
}
Langue : français."""

@dataclass
class RawFragment:
    text: str
    section: str
    page: int
    source_file: str
    fragment_type: str = "texte"

@dataclass
class DiagramRelation:
    from_component: str
    to_component: str
    label: str
    source_file: str
    section: str

class GeminiDocumentParser:
    MIME_TYPES = {
        ".pdf":  "application/pdf",
        ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        ".png":  "image/png",
        ".jpg":  "image/jpeg",
        ".jpeg": "image/jpeg",
    }

    def __init__(self, model: str = None):
        api_key = os.getenv("GOOGLE_API_KEY")
        if not api_key:
            raise EnvironmentError("❌ GOOGLE_API_KEY manquante dans le fichier .env")
        
        self.client = genai.Client(api_key=api_key)
        self.model = model or os.getenv("GEMINI_MODEL", "gemini-2.0-flash")
        logger.info(f"🤖 Gemini Parser prêt ({self.model})")

    def parse(self, filepath: str | pathlib.Path) -> tuple[list[RawFragment], list[DiagramRelation]]:
        path = pathlib.Path(filepath)
        if not path.exists():
            raise FileNotFoundError(f"Fichier introuvable : {path}")
            
        suffix = path.suffix.lower()
        if suffix not in self.MIME_TYPES:
            raise ValueError(f"Format non supporté : {suffix}. Acceptés : {', '.join(self.MIME_TYPES)}")
            
        mime_type = self.MIME_TYPES[suffix]
        logger.info(f"📤 Upload Gemini : {path.name}")
        
        uploaded_file = self._upload_file(path, mime_type)
        
        logger.info("🧠 Analyse multimodale Gemini...")
        raw_response = self._call_gemini(uploaded_file)
        
        try:
            self.client.files.delete(name=uploaded_file.name)
        except Exception as e:
            logger.debug(f"Nettoyage upload Gemini échoué : {e}")
            
        return self._parse_response(raw_response, path.name)

    def _upload_file(self, path: pathlib.Path, mime_type: str):
        uploaded = self.client.files.upload(
            file=path, 
            config={"display_name": path.name, "mime_type": mime_type}
        )
        
        max_wait, waited = 120, 0
        while uploaded.state == "PROCESSING" and waited < max_wait:
            time.sleep(3)
            waited += 3
            uploaded = self.client.files.get(name=uploaded.name)
            
        if uploaded.state != "ACTIVE":
            raise RuntimeError(f"Échec upload Gemini (Etat: {uploaded.state})")
            
        return uploaded

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
    def _call_gemini(self, uploaded_file) -> str:
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
            frags = []
            for f in data.get('fragments', []):
                if len(f.get('text', '')) > 10:
                    frags.append(RawFragment(
                        text=f['text'], section=f['section'], 
                        page=f['page'], source_file=source_file,
                        fragment_type=f.get('fragment_type', 'texte')
                    ))
            rels = []
            for d in data.get("diagrams_extracted", []):
                section = d.get("section", "Diagramme")
                for r in d.get("relations", []):
                    rels.append(DiagramRelation(
                        from_component=r.get("from", "?"),
                        to_component=r.get("to", "?"),
                        label=r.get("label", "→"),
                        source_file=source_file,
                        section=section
                    ))
            return frags, rels
        except (json.JSONDecodeError, Exception) as e:
            logger.warning(f"⚠️ Fallback JSON (Gemini) : {e}")
            return [RawFragment(
                text=raw_response[:1000], section="Extraction brute", 
                page=0, source_file=source_file
            )], []
