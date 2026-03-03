import os
import pathlib
import hashlib
import unicodedata
from abc import ABC, abstractmethod
from typing import List, Dict, Any
from dataclasses import dataclass
from loguru import logger
from docling.document_converter import DocumentConverter, PdfFormatOption
from docling.datamodel.pipeline_options import PdfPipelineOptions
from docling.datamodel.base_models import InputFormat
from dotenv import load_dotenv

load_dotenv(pathlib.Path(__file__).parent.parent / ".env")


@dataclass
class AtomicDecomposition:
    """Représente un fragment d'information immuable et structuré."""

    content: str
    id_hash: str
    metadata: Dict[str, Any]
    category: str = "GENERAL"


class DecomposerService(ABC):
    """Interface pour les services de dissociation."""

    @abstractmethod
    def decompose(self, source: Any) -> List[AtomicDecomposition]:
        pass


class DoclingDecomposer(DecomposerService):
    """Implémentation du service de décomposition via IBM Docling avec hiérarchie."""

    def __init__(self):
        self.image_dir = pathlib.Path(
            os.getenv("OUTPUT_IMAGE_DIR", "data/output_images")
        )
        self.cache_dir = pathlib.Path(os.getenv("OUTPUT_JSON_DIR", "data/output_json"))
        self.converter = self._init_converter()

        self.categories = {
            "ADMIN": [
                "administratif",
                "candidature",
                "justificatif",
                "éligibilité",
                "assurance",
                "attestation",
                "agrément",
            ],
            "TECHNIQUE": [
                "spécification",
                "besoin",
                "exigence",
                "fonctionnement",
                "architecture",
                "technique",
                "solution",
                "logiciel",
                "matériel",
                "infrastructure",
            ],
            "FINANCIER": [
                "prix",
                "coût",
                "facturation",
                "budget",
                "montant",
                "paiement",
                "pénalité",
                "unitaire",
                "forfait",
                "devis",
            ],
            "JURIDIQUE": [
                "clause",
                "contrat",
                "litige",
                "résiliation",
                "droit",
                "propriété",
                "juridique",
                "responsabilité",
                "loi",
            ],
            "PLANNING": [
                "délai",
                "calendrier",
                "jalon",
                "livraison",
                "durée",
                "planning",
                "mise en service",
            ],
            "SECURITE": [
                "iso",
                "sécurité",
                "rgpd",
                "données",
                "confidentialité",
                "protection",
                "habilité",
                "authentification",
                "chiffrement",
            ],
        }

    def _init_converter(self):
        opts = PdfPipelineOptions()
        opts.generate_page_images = True
        opts.do_ocr = True
        return DocumentConverter(
            allowed_formats=[InputFormat.PDF],
            format_options={InputFormat.PDF: PdfFormatOption(pipeline_options=opts)},
        )

    def _strip_accents(self, s):
        return "".join(
            c
            for c in unicodedata.normalize("NFD", s)
            if unicodedata.category(c) != "Mn"
        )

    def _get_semantic_category(self, text: str, breadcrumbs: str) -> str:
        context = self._strip_accents((text + " " + breadcrumbs).lower())
        scores = {cat: 0 for cat in self.categories}
        for cat, keywords in self.categories.items():
            for kw in keywords:
                kw_clean = self._strip_accents(kw.lower())
                if kw_clean in context:
                    scores[cat] += len(kw_clean)
        best_cat = max(scores, key=scores.get)
        return best_cat if scores[best_cat] > 0 else "GENERAL"

    def _generate_id(self, text: str, meta: Dict) -> str:
        seed = f"{meta.get('source')}_{meta.get('page')}_{text[:100]}"
        return hashlib.md5(seed.encode()).hexdigest()

    def decompose(self, filepath: str | pathlib.Path) -> List[AtomicDecomposition]:
        filepath = pathlib.Path(filepath)
        source_name = filepath.name

        logger.info(f"📄 Décomposition structurelle de : {source_name}")
        result = self.converter.convert(filepath)
        doc = result.document

        decompositions = []
        title_stack = []

        for item, level in doc.iterate_items():
            label = item.label.lower()
            try:
                raw_text = item.text if hasattr(item, "text") else ""
                if not raw_text or len(raw_text.strip()) < 10:
                    continue
            except Exception:
                continue

            if "heading" in label or "title" in label:
                depth = level if level is not None else 0
                title_stack = title_stack[:depth]
                title_stack.append(raw_text)
                continue

            breadcrumbs = " > ".join(title_stack) if title_stack else "Racine"
            category = self._get_semantic_category(raw_text, breadcrumbs)
            page_no = item.prov[0].page_no + 1 if item.prov else 1

            meta = {
                "source": source_name,
                "page": page_no,
                "breadcrumbs": breadcrumbs,
                "section": title_stack[-1] if title_stack else "Général",
            }

            decompositions.append(
                AtomicDecomposition(
                    content=raw_text,
                    id_hash=self._generate_id(raw_text, meta),
                    metadata=meta,
                    category=category,
                )
            )

        # Sauvegarde des images de pages
        for page in result.pages:
            if page.image:
                img_path = (
                    self.image_dir / f"{filepath.stem}_page_{page.page_no + 1}.png"
                )
                if not img_path.exists():
                    page.image.save(img_path)

        logger.success(f"✅ {len(decompositions)} fragments atomiques extraits.")
        return decompositions
