import os
import pathlib
import re
import json
import unicodedata
from dataclasses import dataclass
from loguru import logger
from docling.document_converter import DocumentConverter, PdfFormatOption
from docling.datamodel.pipeline_options import PdfPipelineOptions
from docling.datamodel.base_models import InputFormat
from dotenv import load_dotenv

# Chargement configuration
load_dotenv(pathlib.Path(__file__).parent.parent / ".env")

@dataclass
class LocalRawFragment:
    """Fragment enrichi pour RAG hiérarchique et sémantique."""
    text: str
    section: str = "Général"
    breadcrumbs: str = ""
    page: int = 0
    fragment_type: str = "texte"
    source_file: str = ""
    category: str = "NON_CLASSE"

class DoclingParser:
    """Parser avec Cache et chemins configurables via .env."""

    def __init__(self, image_output_dir: str = None, cache_dir: str = None):
        logger.info("🤖 Initialisation du Parser Hiérarchique...")
        
        self.image_output_dir = pathlib.Path(image_output_dir or os.getenv("OUTPUT_IMAGE_DIR", "data/output_images"))
        self.cache_dir = pathlib.Path(cache_dir or os.getenv("OUTPUT_JSON_DIR", "data/output_json"))
        
        self.image_output_dir.mkdir(parents=True, exist_ok=True)
        self.cache_dir.mkdir(parents=True, exist_ok=True)

        pipeline_options = PdfPipelineOptions()
        pipeline_options.generate_page_images = True
        pipeline_options.images_scale = 2.0
        pipeline_options.do_ocr = True
        
        self.converter = DocumentConverter(
            allowed_formats=[InputFormat.PDF],
            format_options={InputFormat.PDF: PdfFormatOption(pipeline_options=pipeline_options)}
        )

        self.categories = {
            "ADMIN": ["administratif", "candidature", "justificatif", "éligibilité", "assurance", "attestation", "agrément"],
            "TECHNIQUE": ["spécification", "besoin", "exigence", "fonctionnement", "architecture", "technique", "solution", "logiciel", "matériel", "infrastructure"],
            "FINANCIER": ["prix", "coût", "facturation", "budget", "montant", "paiement", "pénalité", "unitaire", "forfait", "devis"],
            "JURIDIQUE": ["clause", "contrat", "litige", "résiliation", "droit", "propriété", "juridique", "responsabilité", "loi"],
            "PLANNING": ["délai", "calendrier", "jalon", "livraison", "durée", "planning", "planning", "planning", "mise en service"],
            "SECURITE": ["iso", "sécurité", "rgpd", "données", "confidentialité", "protection", "habilité", "authentification", "chiffrement"]
        }

    def _strip_accents(self, s):
        return ''.join(c for c in unicodedata.normalize('NFD', s) if unicodedata.category(c) != 'Mn')

    def _get_semantic_category(self, text: str, breadcrumbs: str) -> str:
        """Détermine la catégorie métier par score de mots-clés robuste."""
        context = self._strip_accents((text + " " + breadcrumbs).lower())
        scores = {cat: 0 for cat in self.categories}
        
        for cat, keywords in self.categories.items():
            for kw in keywords:
                kw_clean = self._strip_accents(kw.lower())
                if kw_clean in context:
                    # Plus le mot clé est long, plus il a de poids
                    scores[cat] += len(kw_clean)
        
        if not scores: return "GENERAL"
        
        best_cat = max(scores, key=scores.get)
        return best_cat if scores[best_cat] > 0 else "GENERAL"

    def _safe_chunk(self, text: str, max_chars: int = 1500, overlap: int = 200) -> list[str]:
        if len(text) <= max_chars: return [text]
        chunks, start = [], 0
        while start < len(text):
            end = min(start + max_chars, len(text))
            chunks.append(text[start:end])
            if end == len(text): break
            start = end - overlap
        return chunks

    def parse_to_fragments(self, filepath: str | pathlib.Path) -> list[LocalRawFragment]:
        filepath = pathlib.Path(filepath)
        source_name = filepath.name
        fragment_cache = self.cache_dir / f"{filepath.stem}.fragments.json"

        # On force le re-parsing si on vient de modifier la logique de tagging
        # Pour ce test, on va supprimer le cache si présent ou juste l'ignorer
        # if fragment_cache.exists(): os.remove(fragment_cache)

        logger.info(f"📄 Analyse complète : {filepath}")
        result = self.converter.convert(filepath)
        doc = result.document
        fragments = self._extract_from_doc(doc, source_name)
        
        try:
            import dataclasses
            with open(fragment_cache, "w", encoding="utf-8") as f:
                json.dump([dataclasses.asdict(fr) for fr in fragments], f, ensure_ascii=False, indent=2)
        except Exception as e: logger.error(f"❌ Cache non sauvegardé : {e}")

        for page in result.pages:
            if page.image:
                img_path = self.image_output_dir / f"{filepath.stem}_page_{page.page_no + 1}.png"
                if not img_path.exists(): page.image.save(img_path)
        
        return fragments

    def _extract_from_doc(self, doc, source_name: str) -> list[LocalRawFragment]:
        fragments, title_stack = [], []
        for item, level in doc.iterate_items():
            label = item.label.lower()
            is_table = "table" in label
            try:
                if is_table:
                    raw_text = f"\n[TABLEAU]\n{item.export_to_markdown()}\n[/TABLEAU]\n" if hasattr(item, "export_to_markdown") else item.text
                else: raw_text = item.text if hasattr(item, "text") else ""
                if not raw_text or len(raw_text.strip()) < 5: continue
            except Exception as e: logger.debug(f"⚠️ Fragment sauté : {e}"); continue

            if "heading" in label or "title" in label or "header" in label:
                depth = level if level is not None else 0
                title_stack = title_stack[:depth]
                title_stack.append(raw_text)
                continue

            if not is_table and len(raw_text) < 40: continue

            breadcrumbs = " > ".join(title_stack) if title_stack else "Racine"
            category = self._get_semantic_category(raw_text, breadcrumbs)
            page_no = item.prov[0].page_no + 1 if item.prov else 1

            for chunk in self._safe_chunk(raw_text):
                fragments.append(LocalRawFragment(
                    text=chunk, section=title_stack[-1] if title_stack else "Général",
                    breadcrumbs=breadcrumbs, page=page_no, source_file=source_name,
                    fragment_type="table" if is_table else "text", category=category
                ))
        return fragments
