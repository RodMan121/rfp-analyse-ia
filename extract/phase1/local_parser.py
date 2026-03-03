import os
import re
import hashlib
import time
from pathlib import Path
from loguru import logger
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from docling.datamodel.base_models import InputFormat
from docling.datamodel.pipeline_options import PdfPipelineOptions
from docling.document_converter import DocumentConverter, PdfFormatOption
from docling_core.types.doc.document import PictureItem, TextItem, SectionHeaderItem

# Import optionnel du contexte documentaire (évite import circulaire)
try:
    import sys
    sys.path.insert(0, str(Path(__file__).parent.parent))
    from document_context import DocumentContext as _DocumentContext
except ImportError:
    _DocumentContext = None

# Filtres de bruit structurels GÉNÉRIQUES (indépendants du document)
_NOISE_PATTERNS_GENERIC = re.compile(
    r"if printed,?\s*make sure"
    r"|this document contains confidential"
    r"|page \d+\s+of\s+\d+"
    r"|figure \d+\s*:"
    r"|this signature sheet was generated"
    r"|document creation"
    r"|document's signature sheet"
    r"|applicable version"
    r"|this chapter must be quoted"
    r"|\biss\.\s*\d{2}-\d{2}\b"
    r"|\bcertified\s+ansp\s+by\b"
    r"|\bif\s+printed\b",
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

    def __init__(self, doc_context=None):
        """
        Args:
            doc_context: instance de DocumentContext pour adapter le filtrage
                         au type de document. Si None, filtrage générique.
        """
        self.doc_context = doc_context

        # Combine les patterns génériques + patterns spécifiques au document
        if doc_context is not None:
            extra_re = doc_context.get_extra_noise_regex()
            if extra_re:
                combined = f"(?:{_NOISE_PATTERNS_GENERIC.pattern})|(?:{extra_re.pattern})"
                self._noise_re = re.compile(combined, re.IGNORECASE)
                logger.info(f"🔧 Filtre bruit étendu avec {len(doc_context.extra_noise_patterns)} pattern(s) documentaire(s)")
            else:
                self._noise_re = _NOISE_PATTERNS_GENERIC
        else:
            self._noise_re = _NOISE_PATTERNS_GENERIC

        # Configuration de la Vision et de l'extraction d'images
        pipeline_options = PdfPipelineOptions()
        pipeline_options.do_ocr = True
        pipeline_options.do_table_structure = True
        
        # ACTIVER L'EXTRACTION D'IMAGES (Maquettes, schémas)
        pipeline_options.images_scale = 2.0  # Haute résolution pour les maquettes
        pipeline_options.generate_picture_images = True
        pipeline_options.do_picture_classification = True
        
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

        # Utilisation de iterate_items pour Docling v2
        for item, level in doc.iterate_items():
            label = getattr(item, "label", "text").lower()
            category = "GENERAL"
            text_clean = ""
            image_path = None

            try:
                # 1. TRAITEMENT DU TEXTE
                raw_text = getattr(item, "text", "")
                text_clean = raw_text.strip()

                # 2. TRAITEMENT DES IMAGES (Maquettes / Schémas)
                if isinstance(item, PictureItem):
                    pil_img = item.get_image(doc)
                    if pil_img:
                        page_no = item.prov[0].page_no if item.prov else 0
                        img_hash = hashlib.md5(text_clean.encode() if text_clean else str(time.time()).encode()).hexdigest()[:8]
                        img_name = f"page_{page_no}_{img_hash}.png"
                        image_path = str(self.img_dir / img_name)
                        
                        pil_img.save(image_path)
                        logger.debug(f"📸 Image extraite : {img_name}")
                        
                        category = "IMAGE"
                        text_clean = f"[IMAGE SOURCE: {img_name}] {text_clean or 'Schéma/Maquette sans légende'}"

                # Filtrage du bruit textuel (uniquement si ce n'est pas une image)
                if category != "IMAGE":
                    if len(text_clean) < _MIN_CONTENT_LENGTH: continue
                    if self._noise_re.search(text_clean): continue

            except Exception as e:
                logger.error(f"⚠️ Erreur item : {e}")
                continue

            if isinstance(item, SectionHeaderItem):
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

        logger.success(f"✅ Extraction terminée : {len(decompositions)} fragments.")
        return decompositions

# Alias pour compatibilité avec le reste du pipeline
DoclingDecomposer = LocalParser
