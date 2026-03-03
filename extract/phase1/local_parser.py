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
    """Analyseur local avec Vision activée pour extraire schémas et maquettes."""

    def __init__(self):
        # Configuration de la Vision et de l'extraction d'images
        pipeline_options = PdfPipelineOptions()
        pipeline_options.do_ocr = True
        pipeline_options.do_table_structure = True
        
        # ACTIVER L'EXTRACTION D'IMAGES (Maquettes, schémas)
        pipeline_options.images_scale = 2.0  # Haute résolution pour les maquettes
        pipeline_options.generate_pictures = True
        
        self.converter = DocumentConverter(
            format_options={
                InputFormat.PDF: PdfFormatOption(pipeline_options=pipeline_options)
            }
        )
        
        # Création du dossier de stockage des images
        self.img_dir = Path("data/output_images")
        self.img_dir.mkdir(parents=True, exist_ok=True)

    def _generate_id(self, text: str, metadata: Dict) -> str:
        anchor = f"{text[:100]}-{metadata.get('page', 0)}-{metadata.get('image_path', '')}"
        return hashlib.md5(anchor.encode()).hexdigest()

    def decompose(self, pdf_path: str) -> List[AtomicDecomposition]:
        logger.info(f"📄 Décomposition Multimodale de : {Path(pdf_path).name}")
        result = self.converter.convert(pdf_path)
        doc = result.document
        
        decompositions = []
        title_stack = []

        for item, level in doc.iterate_sections():
            label = item.label.lower()
            category = "GENERAL"
            text_clean = ""
            image_path = None

            try:
                # 1. TRAITEMENT DU TEXTE
                raw_text = item.text if hasattr(item, "text") else ""
                text_clean = raw_text.strip()

                # 2. TRAITEMENT DES IMAGES (Maquettes / Schémas)
                if label in ["picture", "figure"] and hasattr(item, "image") and item.image:
                    page_no = item.prov[0].page_no if item.prov else 0
                    img_name = f"page_{page_no}_{hashlib.md5(text_clean.encode()).hexdigest()[:8]}.png"
                    image_path = str(self.img_dir / img_name)
                    
                    # Sauvegarde physique de l'image
                    item.image.save(image_path)
                    logger.debug(f"📸 Image extraite : {img_name}")
                    
                    category = "IMAGE"
                    # Si l'image a une légende, on la garde comme contenu
                    text_clean = f"[IMAGE SOURCE: {img_name}] {text_clean}"

                # Filtrage du bruit textuel (uniquement si ce n'est pas une image)
                if category != "IMAGE":
                    if len(text_clean) < _MIN_CONTENT_LENGTH: continue
                    if _NOISE_PATTERNS.search(text_clean): continue

            except Exception as e:
                logger.error(f"⚠️ Erreur item : {e}")
                continue

            if "heading" in label or "title" in label:
                depth = level if level is not None else 0
                title_stack = title_stack[:depth]
                title_stack.append(text_clean)
                continue

            # Catégorisation intelligente
            text_lower = text_clean.lower()
            if any(k in text_lower for k in ["shall", "must", "should"]):
                category = "REQUIREMENT" if category != "IMAGE" else "IMAGE"

            meta = {
                "source": Path(pdf_path).name,
                "page": item.prov[0].page_no if item.prov else 0,
                "breadcrumbs": " > ".join(title_stack) if title_stack else "Racine",
                "image_path": image_path if image_path else ""
            }

            decompositions.append(
                AtomicDecomposition(
                    content=text_clean,
                    id_hash=self._generate_id(text_clean, meta),
                    metadata=meta,
                    category=category,
                )
            )

        logger.success(f"✅ Extraction terminée : {len(decompositions)} fragments (incluant images).")
        return decompositions
