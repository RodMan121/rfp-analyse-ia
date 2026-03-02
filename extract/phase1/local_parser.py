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
    """Fragment enrichi pour RAG hiérarchique."""
    text: str
    section: str = "Général"
    breadcrumbs: str = ""
    page: int = 0
    fragment_type: str = "texte"
    source_file: str = ""

class DoclingParser:
    """
    Parser avancé stable avec capture PNG des pages.
    """

    def __init__(self, image_output_dir: str = "data/output_images"):
        logger.info("🤖 Initialisation du Parser Hiérarchique avec Vision...")
        
        # Configuration pour capturer les pages en images
        pipeline_options = PdfPipelineOptions()
        pipeline_options.generate_page_images = True
        pipeline_options.images_scale = 2.0
        
        self.converter = DocumentConverter(
            format_options={
                InputFormat.PDF: PdfFormatOption(pipeline_options=pipeline_options)
            }
        )
        self.image_output_dir = pathlib.Path(image_output_dir)
        self.image_output_dir.mkdir(parents=True, exist_ok=True)

    def parse_to_fragments(self, filepath: str | pathlib.Path) -> list[LocalRawFragment]:
        """Analyse structurelle + Sauvegarde des images de pages."""
        logger.info(f"📄 Analyse de : {filepath}")
        result = self.converter.convert(filepath)
        doc = result.document
        source_name = pathlib.Path(filepath).name
        
        # 1. Sauvegarde des images de pages (pour le mode Vision)
        doc_stem = pathlib.Path(filepath).stem
        for page in result.pages:
            if page.image:
                image_path = self.image_output_dir / f"{doc_stem}_page_{page.page_no + 1}.png"
                page.image.save(image_path)
        
        logger.success(f"📸 {len(result.pages)} pages capturées en PNG.")

        # 2. Extraction des fragments
        fragments = []
        title_stack = [] 

        for item, level in doc.iterate_items():
            label = item.label.lower()
            try:
                item_text = item.text if hasattr(item, "text") else ""
                if not item_text:
                    if hasattr(item, "export_to_markdown"):
                        item_text = item.export_to_markdown()
                
                item_text = item_text.strip()
                if not item_text: continue
            except: continue

            if "heading" in label or "title" in label or "header" in label:
                depth = level if level is not None else 0
                title_stack = title_stack[:depth]
                title_stack.append(item_text)
                continue

            if len(item_text) < 30: continue

            breadcrumbs = " > ".join(title_stack) if title_stack else "Racine"
            current_section = title_stack[-1] if title_stack else "Général"
            
            page_no = 0
            if item.prov and len(item.prov) > 0:
                page_no = item.prov[0].page_no + 1

            fragments.append(LocalRawFragment(
                text=item_text,
                section=current_section,
                breadcrumbs=breadcrumbs,
                page=page_no,
                source_file=source_name,
                fragment_type="table" if "table" in label else "text"
            ))

        return fragments
