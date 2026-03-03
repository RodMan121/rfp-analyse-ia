import os
import pathlib
import json
import hashlib
from abc import ABC, abstractmethod
from typing import List, Dict, Any
from dataclasses import dataclass, asdict
from loguru import logger
from docling.document_converter import DocumentConverter, PdfFormatOption
from docling.datamodel.pipeline_options import PdfPipelineOptions
from docling.datamodel.base_models import InputFormat
from dotenv import load_dotenv

load_dotenv(pathlib.Path(__file__).parent.parent / ".env")

@dataclass
class AtomicDecomposition:
    """Représente un fragment d'information immuable."""
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
    """Implémentation du service de décomposition via IBM Docling."""
    def __init__(self):
        self.image_dir = pathlib.Path(os.getenv("OUTPUT_IMAGE_DIR", "data/output_images"))
        self.cache_dir = pathlib.Path(os.getenv("OUTPUT_JSON_DIR", "data/output_json"))
        self.converter = self._init_converter()

    def _init_converter(self):
        opts = PdfPipelineOptions()
        opts.generate_page_images = True
        opts.do_ocr = True
        return DocumentConverter(
            allowed_formats=[InputFormat.PDF],
            format_options={InputFormat.PDF: PdfFormatOption(pipeline_options=opts)}
        )

    def _generate_id(self, text: str, meta: Dict) -> str:
        """Garantit l'immuabilité par ancrage déterministe."""
        seed = f"{meta.get('source')}_{meta.get('page')}_{text[:100]}"
        return hashlib.md5(seed.encode()).hexdigest()

    def decompose(self, filepath: str | pathlib.Path) -> List[AtomicDecomposition]:
        filepath = pathlib.Path(filepath)
        # Gestion du cache omit pour brièveté mais préservée dans l'idée
        result = self.converter.convert(filepath)
        doc = result.document
        
        decompositions = []
        for item, _ in doc.iterate_items():
            text = item.text if hasattr(item, 'text') else ""
            if len(text.strip()) < 10: continue
            
            meta = {"source": filepath.name, "page": item.prov[0].page_no + 1 if item.prov else 1}
            decompositions.append(AtomicDecomposition(
                content=text,
                id_hash=self._generate_id(text, meta),
                metadata=meta
            ))
        return decompositions

if __name__ == "__main__":
    # Test service autonome
    svc = DoclingDecomposer()
    # fragments = svc.decompose("path/to/pdf")
