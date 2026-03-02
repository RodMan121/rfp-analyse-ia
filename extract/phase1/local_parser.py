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
    """Fragment brut extrait par Docling."""
    text: str
    section: str = "Général"
    page: int = 0
    fragment_type: str = "texte"
    source_file: str = ""

class DoclingParser:
    """
    Parser local basé sur Docling avec capture de pages entières (Snapshots).
    """

    def __init__(self, image_output_dir: str = "data/output_images"):
        logger.info("🤖 Initialisation de Docling avec captures de pages...")
        
        pipeline_options = PdfPipelineOptions()
        pipeline_options.images_scale = 2.0  # Haute résolution (300 DPI approx)
        pipeline_options.generate_page_images = True # Active la capture des pages
        pipeline_options.do_ocr = True
        
        self.converter = DocumentConverter(
            format_options={
                InputFormat.PDF: PdfFormatOption(pipeline_options=pipeline_options)
            }
        )
        self.image_output_dir = pathlib.Path(image_output_dir)
        self.image_output_dir.mkdir(parents=True, exist_ok=True)

    def parse_to_markdown(self, filepath: str | pathlib.Path) -> str:
        """Convertit un document et capture chaque page en image."""
        logger.info(f"📄 Snapshot des pages (Docling) : {filepath}")
        result = self.converter.convert(filepath)
        
        # Sauvegarde de chaque page du PDF en tant qu'image PNG
        doc_name = pathlib.Path(filepath).stem
        count = 0
        for page in result.pages:
            count += 1
            if page.image:
                # Sauvegarde de la page en tant qu'image PNG
                image_filename = f"{doc_name}_page_{page.page_no + 1}.png"
                image_path = self.image_output_dir / image_filename
                page.image.save(image_path)
                logger.debug(f"  📸 Page {page.page_no + 1} capturée")
        
        logger.success(f"✅ {count} pages capturées dans {self.image_output_dir}")
        return result.document.export_to_markdown()

    def parse_to_fragments(self, filepath: str | pathlib.Path) -> list[LocalRawFragment]:
        """Convertit le document en fragments via Markdown."""
        full_markdown = self.parse_to_markdown(filepath)
        source_name = pathlib.Path(filepath).name
        return self.parse_to_fragments_from_markdown(full_markdown, source_name)

    def parse_to_fragments_from_markdown(self, full_markdown: str, source_name: str) -> list[LocalRawFragment]:
        """Découpe un texte Markdown en fragments structurés."""
        sections = re.split(r'\n(?=#+ )', full_markdown)
        fragments = []
        current_section = "Introduction"
        
        for section_content in sections:
            section_content = section_content.strip()
            if not section_content:
                continue
                
            first_line = section_content.split('\n')[0]
            if first_line.startswith('#'):
                current_section = first_line.replace('#', '').strip()
            
            if len(section_content) > 2000:
                paragraphs = section_content.split('\n\n')
                for p in paragraphs:
                    p = p.strip()
                    if len(p) > 40:
                        fragments.append(LocalRawFragment(
                            text=p,
                            section=current_section,
                            source_file=source_name,
                            fragment_type="texte"
                        ))
            else:
                if len(section_content) > 40:
                    fragments.append(LocalRawFragment(
                        text=section_content,
                        section=current_section,
                        source_file=source_name,
                        fragment_type="section"
                    ))
            
        logger.success(f"✅ {len(fragments)} fragments extraits.")
        return fragments
