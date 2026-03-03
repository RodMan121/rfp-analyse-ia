import os
import re
import hashlib
from pathlib import Path
from loguru import logger
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from docling.datamodel.base_models import InputFormat
from docling.datamodel.pipeline_options import PdfPipelineOptions
from docling.document_converter import DocumentConverter, PdfFormatOption

# FIX v11 : Filtres de bruit structurels
_NOISE_PATTERNS = re.compile(
    r"if printed,?\s*make sure"
    r"|this document contains confidential"
    r"|essp-rd-\d+\s+iss\."
    r"|page \d+\s+of\s+\d+"
    r"|figure \d+\s*:"
    r"|this signature sheet was generated"
    r"|document creation"
    r"|document's signature sheet"
    r"|applicable version"
    r"|this chapter must be quoted",
    re.IGNORECASE
)
_MIN_CONTENT_LENGTH = 80

@dataclass
class AtomicDecomposition:
    content: str
    id_hash: str
    metadata: Dict[str, Any]
    category: str = "GENERAL"

class LocalParser:
    """Analyseur local utilisant Docling avec filtrage de bruit v11."""

    def __init__(self):
        pipeline_options = PdfPipelineOptions()
        pipeline_options.do_ocr = True
        pipeline_options.do_table_structure = True
        self.converter = DocumentConverter(
            format_options={
                InputFormat.PDF: PdfFormatOption(pipeline_options=pipeline_options)
            }
        )

    def _generate_id(self, text: str, metadata: Dict) -> str:
        anchor = f"{text[:100]}-{metadata.get('page', 0)}"
        return hashlib.md5(anchor.encode()).hexdigest()

    def decompose(self, pdf_path: str) -> List[AtomicDecomposition]:
        logger.info(f"📄 Décomposition structurelle de : {Path(pdf_path).name}")
        result = self.converter.convert(pdf_path)
        doc = result.document
        
        decompositions = []
        title_stack = []

        for item, level in doc.iterate_sections():
            label = item.label.lower()
            try:
                raw_text = item.text if hasattr(item, "text") else ""
                
                # --- FIX v11 : Filtrage de bruit ---
                text_clean = raw_text.strip()
                if len(text_clean) < _MIN_CONTENT_LENGTH:
                    continue
                if _NOISE_PATTERNS.search(text_clean):
                    logger.debug(f"🗑️ Bruit filtré: {text_clean[:60]}...")
                    continue
                # ------------------------------------

            except Exception:
                continue

            if "heading" in label or "title" in label:
                depth = level if level is not None else 0
                title_stack = title_stack[:depth]
                title_stack.append(text_clean)
                continue

            category = "GENERAL"
            text_lower = text_clean.lower()
            if any(k in text_lower for k in ["doit", "doivent", "shall", "must", "should"]):
                category = "REQUIREMENT"
            if any(k in text_lower for k in ["sécurité", "security", "accès", "authentification"]):
                category = "SECURITE"
            if any(k in text_lower for k in ["performance", "ms", "seconde", "charge"]):
                category = "TECHNIQUE"

            meta = {
                "source": Path(pdf_path).name,
                "page": item.prov[0].page_no if item.prov else 0,
                "breadcrumbs": " > ".join(title_stack) if title_stack else "Racine"
            }

            decompositions.append(
                AtomicDecomposition(
                    content=text_clean,
                    id_hash=self._generate_id(text_clean, meta),
                    metadata=meta,
                    category=category,
                )
            )

        logger.success(f"✅ {len(decompositions)} fragments utiles extraits.")
        return decompositions
