import os
import pathlib
import re
from dataclasses import dataclass
from loguru import logger
from docling.document_converter import DocumentConverter

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
    Parser avancé stable utilisant les propriétés natives de Docling.
    """

    def __init__(self):
        logger.info("🤖 Initialisation du Parser Hiérarchique (Propriétés Natives)...")
        self.converter = DocumentConverter()

    def parse_to_fragments(self, filepath: str | pathlib.Path) -> list[LocalRawFragment]:
        """Pipeline stable avec extraction sémantique directe."""
        logger.info(f"📄 Analyse structurelle de : {filepath}")
        result = self.converter.convert(filepath)
        doc = result.document
        source_name = pathlib.Path(filepath).name
        
        fragments = []
        title_stack = [] 

        for item, level in doc.iterate_items():
            label = item.label.lower()
            
            # Récupération du texte de l'item (soit via .text, soit via export simple)
            try:
                item_text = ""
                if hasattr(item, "text"):
                    item_text = item.text
                else:
                    # Pour les tableaux ou autres, on tente un export simple
                    item_text = item.export_to_markdown() if hasattr(item, "export_to_markdown") else ""
                
                item_text = item_text.strip()
                if not item_text: continue
            except:
                continue

            # 1. Gestion des titres pour le fil d'ariane
            if "heading" in label or "title" in label or "header" in label:
                depth = level if level is not None else 0
                title_stack = title_stack[:depth]
                title_stack.append(item_text)
                continue

            # 2. Filtrage des fragments courts
            if len(item_text) < 30: continue

            # Construction des métadonnées
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

        logger.success(f"✅ {len(fragments)} fragments extraits via propriétés natives.")
        return fragments
