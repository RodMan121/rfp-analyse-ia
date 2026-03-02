# phase1/parser.py  — Niveau 2 : Gemini Flash (Multimodal)
"""
Parser universel pour documents RFP.
Moteur : Gemini 2.0 Flash via Google Files API.

Ce que Gemini gère nativement (plus besoin de libs locales) :
  ✅ PDF natif (texte)
  ✅ PDF scanné (OCR intégré)
  ✅ Word .docx
  ✅ Images embarquées, tableaux, diagrammes
  ✅ Schémas PlantUML / architecturaux → relations logiques extraites

Tier gratuit : 1500 requêtes/jour (gemini-2.0-flash)
Doc officielle : https://ai.google.dev/gemini-api/docs/document-processing
"""

import os
import time
import json
import pathlib
from dataclasses import dataclass
from loguru import logger
from google import genai
from google.genai import types
from dotenv import load_dotenv

load_dotenv()

# ─────────────────────────────────────────────────────────
# Prompt d'extraction — le cœur du parser
# ─────────────────────────────────────────────────────────

EXTRACTION_PROMPT = """
Tu es un expert Business Analyst spécialisé dans l'analyse d'appels d'offres (RFP/CCTP).

Analyse ce document en intégralité, y compris :
- Le texte (toutes les sections)
- Les tableaux (extrais chaque ligne comme un fragment)
- Les images et diagrammes (décris les relations logiques, pas juste le visuel)
- Les schémas d'architecture (extrais les composants et leurs connexions)
- Les notes de bas de page et annexes

Retourne UNIQUEMENT un objet JSON valide (sans texte avant ni après, sans balises markdown)
avec cette structure exacte :

{
  "document_title": "titre du document",
  "detected_sections": ["section1", "section2"],
  "fragments": [
    {
      "text": "contenu textuel du fragment (phrase ou paragraphe autonome)",
      "section": "nom de la section parente",
      "page": 0,
      "fragment_type": "texte|tableau|diagramme|image|note",
      "visual_context": "description si fragment issu d'un élément visuel, sinon null"
    }
  ],
  "diagrams_extracted": [
    {
      "type": "architecture|flux|organigramme|autre",
      "components": ["composant1", "composant2"],
      "relations": [{"from": "A", "to": "B", "label": "relation"}],
      "section": "section parente"
    }
  ]
}

Règles importantes :
- Chaque fragment doit être autonome et compréhensible seul (min 20 caractères)
- Pour les diagrammes PlantUML ou UML : extrais TOUTES les flèches comme des relations
- Pour les tableaux : chaque ligne = un fragment avec le contexte des en-têtes
- Ne perds aucune information technique (SLA, pourcentages, standards comme AES-256)
- Langue de sortie : français
"""


@dataclass
class RawFragment:
    """Fragment brut avant classification."""
    text: str
    section: str
    page: int
    source_file: str
    fragment_type: str = "texte"
    visual_context: str | None = None


@dataclass
class DiagramRelation:
    """Relation extraite d'un diagramme."""
    from_component: str
    to_component: str
    label: str
    source_file: str
    section: str


class GeminiDocumentParser:
    """
    Parser multimodal basé sur Gemini 2.0 Flash.
    Un seul appel API traite tout : texte, images, tableaux, diagrammes.
    """

    SUPPORTED_FORMATS = {
        ".pdf":  "application/pdf",
        ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        ".doc":  "application/msword",
        ".png":  "image/png",
        ".jpg":  "image/jpeg",
        ".jpeg": "image/jpeg",
    }

    def __init__(self, model: str = "gemini-2.0-flash"):
        api_key = os.getenv("GOOGLE_API_KEY")
        if not api_key:
            raise EnvironmentError(
                "❌ GOOGLE_API_KEY manquante.\n"
                "   1. Obtenir une clé sur : https://aistudio.google.com/apikey\n"
                "   2. Ajouter dans .env :  GOOGLE_API_KEY=votre_cle\n"
                "   Tier gratuit : 1500 req/jour avec gemini-2.0-flash"
            )
        self.client = genai.Client(api_key=api_key)
        self.model = model
        logger.info(f"🤖 Gemini Parser initialisé — modèle : {self.model}")

    # ─────────────────────────────────────────────
    # Point d'entrée principal
    # ─────────────────────────────────────────────

    def parse(self, filepath: str | pathlib.Path) -> tuple[list[RawFragment], list[DiagramRelation]]:
        """
        Parse un document avec Gemini.
        Retourne (fragments, relations_diagrammes).

        Gemini gère nativement :
          - PDF natif et scanné (vision + OCR intégré)
          - Word .docx
          - Images PNG/JPG
          - Diagrammes, tableaux, schémas PlantUML
        """
        path = pathlib.Path(filepath)
        if not path.exists():
            raise FileNotFoundError(f"Fichier introuvable : {filepath}")

        suffix = path.suffix.lower()
        if suffix not in self.SUPPORTED_FORMATS:
            raise ValueError(
                f"Format non supporté : {suffix}. "
                f"Acceptés : {', '.join(self.SUPPORTED_FORMATS)}"
            )

        mime_type = self.SUPPORTED_FORMATS[suffix]
        logger.info(f"📤 Upload vers Gemini Files API : {path.name}")

        # 1. Upload du fichier
        uploaded_file = self._upload_file(path, mime_type)

        # 2. Appel Gemini (1 seul appel = tout le document)
        logger.info("🧠 Analyse multimodale en cours...")
        raw_response = self._call_gemini(uploaded_file)

        # 3. Nettoyage de l'upload (bonne pratique + quota)
        try:
            self.client.files.delete(name=uploaded_file.name)
            logger.debug("  🗑️  Fichier temporaire supprimé de Gemini Files API")
        except Exception:
            pass  # Non bloquant

        # 4. Parse de la réponse JSON
        fragments, relations = self._parse_response(raw_response, path.name)

        logger.success(
            f"  ✅ {len(fragments)} fragments extraits "
            f"({len(relations)} relations de diagrammes)"
        )
        return fragments, relations

    # ─────────────────────────────────────────────
    # Upload Gemini Files API
    # ─────────────────────────────────────────────

    def _upload_file(self, path: pathlib.Path, mime_type: str):
        """Upload le fichier et attend qu'il soit ACTIVE."""
        uploaded = self.client.files.upload(
            file=path,
            config={"display_name": path.name, "mime_type": mime_type}
        )

        # Attente du traitement (nécessaire pour les gros fichiers)
        max_wait = 120  # secondes
        waited = 0
        while uploaded.state == "PROCESSING" and waited < max_wait:
            logger.info(f"  ⏳ Traitement Gemini en cours... ({waited}s)")
            time.sleep(3)
            waited += 3
            uploaded = self.client.files.get(name=uploaded.name)

        if uploaded.state == "FAILED":
            raise RuntimeError(f"❌ Echec du traitement Gemini : {uploaded.name}")

        logger.debug(f"  ✅ Fichier actif : {uploaded.uri}")
        return uploaded

    # ─────────────────────────────────────────────
    # Appel Gemini
    # ─────────────────────────────────────────────

    def _call_gemini(self, uploaded_file) -> str:
        """Envoie le document à Gemini avec le prompt d'extraction."""
        response = self.client.models.generate_content(
            model=self.model,
            contents=[uploaded_file, EXTRACTION_PROMPT],
            config=types.GenerateContentConfig(
                temperature=0.1,        # Réponses déterministes pour le parsing
                max_output_tokens=8192,
            )
        )
        return response.text

    # ─────────────────────────────────────────────
    # Parse de la réponse JSON
    # ─────────────────────────────────────────────

    def _parse_response(
        self,
        raw_response: str,
        source_file: str
    ) -> tuple[list[RawFragment], list[DiagramRelation]]:
        """Transforme la réponse JSON de Gemini en objets Python."""

        # Nettoyage des éventuelles balises markdown résiduelles
        clean = raw_response.strip()
        if clean.startswith("```"):
            clean = clean.split("\n", 1)[1]
            clean = clean.rsplit("```", 1)[0]
        clean = clean.strip()

        try:
            data = json.loads(clean)
        except json.JSONDecodeError as e:
            logger.error(f"❌ Réponse Gemini non-JSON : {e}")
            logger.debug(f"Réponse brute (500 premiers chars) : {raw_response[:500]}")
            # Fallback : fragment unique avec la réponse brute
            return [RawFragment(
                text=raw_response[:1000],
                section="Document complet",
                page=0,
                source_file=source_file,
                fragment_type="texte",
            )], []

        # Fragments (texte, tableau, image...)
        fragments = []
        for item in data.get("fragments", []):
            text = item.get("text", "").strip()
            if len(text) < 20:
                continue
            fragments.append(RawFragment(
                text=text,
                section=item.get("section", "Non défini"),
                page=item.get("page", 0),
                source_file=source_file,
                fragment_type=item.get("fragment_type", "texte"),
                visual_context=item.get("visual_context"),
            ))

        # Relations extraites des diagrammes
        relations = []
        for diagram in data.get("diagrams_extracted", []):
            section = diagram.get("section", "Diagramme")
            for rel in diagram.get("relations", []):
                relations.append(DiagramRelation(
                    from_component=rel.get("from", "?"),
                    to_component=rel.get("to", "?"),
                    label=rel.get("label", "→"),
                    source_file=source_file,
                    section=section,
                ))

        return fragments, relations
