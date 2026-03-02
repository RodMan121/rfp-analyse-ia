import PyPDF2
from pathlib import Path
from loguru import logger

def extract_sample(input_pdf: str, output_pdf: str, max_pages: int = 100):
    input_path = Path(input_pdf)
    if not input_path.exists():
        logger.error(f"❌ Fichier introuvable : {input_pdf}")
        return False
    
    try:
        with open(input_path, "rb") as file:
            reader = PyPDF2.PdfReader(file)
            writer = PyPDF2.PdfWriter()
            
            total_pages = len(reader.pages)
            pages_to_extract = min(max_pages, total_pages)
            
            logger.info(f"📄 Extraction de {pages_to_extract} pages sur {total_pages}...")
            
            for i in range(pages_to_extract):
                writer.add_page(reader.pages[i])
                
            with open(output_pdf, "wb") as output_file:
                writer.write(output_file)
        
        logger.success(f"✅ Échantillon créé : {output_pdf}")
        return True
    except Exception as e:
        logger.error(f"❌ Erreur lors du découpage : {e}")
        return False

if __name__ == "__main__":
    extract_sample("data/input/RFP.pdf", "data/input/RFP_sample.pdf", max_pages=100)
