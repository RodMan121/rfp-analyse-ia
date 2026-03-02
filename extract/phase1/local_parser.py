import os
import pathlib
import re
from dataclasses import dataclass
from loguru import logger
from docling.document_converter import DocumentConverter, PdfFormatOption
from docling.datamodel.pipeline_options import PdfPipelineOptions
from docling.datamodel.base_models import InputFormat

@dataclass
class LocalRawFragment:
    """Fragment enrichi pour RAG hiérarchique et sémantique."""
    text: str
    section: str = "Général"
    breadcrumbs: str = ""
    page: int = 0
    fragment_type: str = "texte"
    source_file: str = ""
    category: str = "NON_CLASSE" # Nouvelle étiquette métier

class DoclingParser:
    """
    Parser avancé avec capture PNG et Tagging Sémantique.
    """

    def __init__(self, image_output_dir: str = "data/output_images", cache_dir: str = "data/output_json"):
        logger.info("🤖 Initialisation du Parser Hiérarchique avec Vision...")
        
        # Configuration Docling
        pipeline_options = PdfPipelineOptions()
        pipeline_options.generate_page_images = True
        pipeline_options.images_scale = 2.0
        pipeline_options.do_ocr = True
        
        self.converter = DocumentConverter(
            allowed_formats=[InputFormat.PDF],
            format_options={InputFormat.PDF: PdfFormatOption(pipeline_options=pipeline_options)}
        )
        
        self.image_output_dir = pathlib.Path(image_output_dir)
        self.cache_dir = pathlib.Path(cache_dir)
        self.image_output_dir.mkdir(parents=True, exist_ok=True)
        self.cache_dir.mkdir(parents=True, exist_ok=True)

        self.categories = {
            "ADMIN": ["administratif", "candidature", "justificatif", "éligibilité", "assurance"],
            "TECHNIQUE": ["spécification", "besoin", "exigence", "fonctionnement", "architecture", "technique"],
            "FINANCIER": ["prix", "coût", "facturation", "budget", "montant", "paiement", "pénalité"],
            "JURIDIQUE": ["clause", "contrat", "litige", "résiliation", "droit", "propriété intellectuelle"],
            "PLANNING": ["délai", "calendrier", "jalon", "livraison", "durée", "planning"],
            "SECURITE": ["iso", "sécurité", "rgpd", "données", "confidentialité", "protection"]
        }

    def _get_semantic_category(self, text: str, breadcrumbs: str) -> str:
        """Détermine la catégorie métier du fragment."""
        context = (text + " " + breadcrumbs).lower()
        for cat, keywords in self.categories.items():
            if any(kw in context for kw in keywords):
                return cat
        return "GENERAL"

    def parse_to_fragments(self, filepath: str | pathlib.Path) -> list[LocalRawFragment]:
        """Analyse structurelle avec système de cache JSON."""
        filepath = pathlib.Path(filepath)
        source_name = filepath.name
        cache_file = self.cache_dir / f"{filepath.stem}.json"

        if cache_file.exists():
            logger.info(f"♻️ Chargement du document depuis le cache : {cache_file.name}")
        
        logger.info(f"📄 Analyse de : {filepath}")
        result = self.converter.convert(filepath)
        doc = result.document
        
        with open(cache_file, "w", encoding="utf-8") as f:
            import json
            json.dump(doc.export_to_dict(), f, ensure_ascii=False, indent=2)
        
        doc_stem = filepath.stem
        for page in result.pages:
            if page.image:
                image_path = self.image_output_dir / f"{doc_stem}_page_{page.page_no + 1}.png"
                if not image_path.exists():
                    page.image.save(image_path)
        
        logger.success(f"📸 {len(result.pages)} pages traitées (JSON + PNG).")

        fragments = []
        title_stack = [] 

        for item, level in doc.iterate_items():
            label = item.label.lower()
            item_text = ""
            is_table = "table" in label

            try:
                # Logique d'extraction spécialisée
                if is_table:
                    # Export Markdown pour conserver la structure colonnes/lignes
                    if hasattr(item, "export_to_markdown"):
                        item_text = f"\n[DÉBUT TABLEAU]\n{item.export_to_markdown()}\n[FIN TABLEAU]\n"
                else:
                    item_text = item.text if hasattr(item, "text") else ""
                
                if not item_text:
                    if hasattr(item, "export_to_markdown"):
                        item_text = item.export_to_markdown()
                
                item_text = item_text.strip()
                if not item_text: continue
            except Exception as e:
                logger.debug(f"⚠️ Erreur fragment : {e}")
                continue

            # Nettoyage et filtrage du bruit
            if not is_table and len(item_text) < 40: continue
            if is_table and len(item_text) < 20: continue # Un petit tableau peut être important

            if "heading" in label or "title" in label or "header" in label:
                depth = level if level is not None else 0
                title_stack = title_stack[:depth]
                title_stack.append(item_text)
                continue

            breadcrumbs = " > ".join(title_stack) if title_stack else "Racine"
            current_section = title_stack[-1] if title_stack else "Général"
            
            page_no = 0
            if item.prov and len(item.prov) > 0:
                page_no = item.prov[0].page_no + 1

            category = self._get_semantic_category(item_text, breadcrumbs)

            fragments.append(LocalRawFragment(
                text=item_text,
                section=current_section,
                breadcrumbs=breadcrumbs,
                page=page_no,
                source_file=source_name,
                fragment_type="table" if is_table else "text",
                category=category
            ))

        return fragments
