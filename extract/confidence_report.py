"""
confidence_report.py — Rapport de confiance après ingestion et Gap Analysis
"""

import os
import json
import ollama
import argparse
from pathlib import Path
from datetime import datetime
from loguru import logger
from dotenv import load_dotenv
from phase1.vectorstore import VectorStore
from phase1.reranker import LocalReranker

# Config robuste
load_dotenv(Path(__file__).parent / ".env")
CATEGORIES = ["ADMIN", "TECHNIQUE", "FINANCIER", "JURIDIQUE", "PLANNING", "SECURITE"]
TEXT_MODEL = os.getenv("OLLAMA_TEXT_MODEL", "qwen2.5:7b")
VISION_MODEL = os.getenv("OLLAMA_VISION_MODEL", "llama3.2-vision")
DEFAULT_DB = os.getenv("CHROMA_DB_PATH", "data/chroma_db_hierarchical")
DEFAULT_IMAGES = os.getenv("OUTPUT_IMAGE_DIR", "data/output_images")

def audit_ingestion(store: VectorStore, image_dir: Path) -> dict:
    """Analyse la qualité de l'ingestion par catégorie."""
    logger.info("🔍 Audit de l'ingestion en cours...")
    rapport = {
        "date": datetime.now().strftime("%d/%m/%Y %H:%M"),
        "categories": [], "schemas": [], "questions_humain": []
    }

    for cat in CATEGORIES:
        fragments = store.search_hybrid(query=f"CATÉGORIE: {cat}", n_results=10)
        if not fragments:
            rapport["categories"].append({
                "nom": cat, "nb_fragments": 0, "confiance": "FAIBLE",
                "resume": "Aucun fragment trouvé.", "points_flous": ["Section non reconnue."]
            })
            continue

        context = "\n---\n".join([f['text'][:500] for f in fragments[:5]])
        prompt = f"Évalue la qualité de l'extraction pour {cat} en JSON : " \
                 "{\"confiance\": \"ÉLEVÉE/MOYENNE/FAIBLE\", \"resume\": \"...\", \"points_flous\": []}\n\n" \
                 f"FRAGMENTS :\n{context}"

        try:
            response = ollama.generate(model=TEXT_MODEL, prompt=prompt, format="json")
            data = json.loads(response.get('response', '{}'))
            data["nom"] = cat; data["nb_fragments"] = len(fragments)
            rapport["categories"].append(data)

            if data.get("confiance") == "FAIBLE":
                for point in data.get("points_flous", []):
                    rapport["questions_humain"].append({"categorie": cat, "question": f"[{cat}] {point}"})
        except Exception as e:
            logger.warning(f"⚠️ Erreur analyse {cat} : {e}")

    if image_dir.exists():
        images = list(image_dir.glob("*.png"))
        for img_path in images[:5]:
            page_no = img_path.stem.split("_")[-1]
            prompt = f"Analyse cette image RFP en JSON : " \
                     "{\"page\": \""+page_no+"\", \"lisibilite\": \"BONNE/MOYENNE/MAUVAISE\", \"elements_identifies\": [], \"questions_pour_humain\": []}"
            try:
                response = ollama.generate(model=VISION_MODEL, prompt=prompt, images=[str(img_path)], format="json")
                data = json.loads(response.get('response', '{}'))
                data["fichier"] = img_path.name
                rapport["schemas"].append(data)
                if data.get("lisibilite") == "MAUVAISE":
                    for q in data.get("questions_pour_humain", []):
                        rapport["questions_humain"].append({"categorie": f"VISUEL P.{page_no}", "question": q})
            except Exception as e:
                logger.warning(f"⚠️ Erreur image {img_path.name} : {e}")

    return rapport

def audit_gap_analysis(rfp_store: VectorStore, catalog_store: VectorStore) -> list:
    """Gap Analysis avec score de confiance."""
    logger.info("🛡️ Gap Analysis de confiance...")
    results = []
    for cat in ["TECHNIQUE", "SECURITE"]:
        fragments = rfp_store.search_hybrid(query=f"CATÉGORIE: {cat}", n_results=10)
        if not fragments: continue
        for frag in fragments[:3]:
            try:
                # 1. Extraction exigence
                r1 = ollama.generate(model=TEXT_MODEL, prompt=f"Extrais exigence en JSON : {frag['text'][:800]}", format="json")
                req = json.loads(r1.get('response', '{}'))
                req['source'] = f"{frag['metadata']['breadcrumbs']} (P.{frag['metadata']['page']})"; req['categorie'] = cat

                # 2. Match catalogue
                know_how = catalog_store.search_hybrid(query=req.get('exigence', ''), n_results=3)
                context = "\n".join([k['text'][:400] for k in know_how]) if know_how else "AUCUN SAVOIR-FAIRE."

                # 3. Analyse
                r2 = ollama.generate(model=TEXT_MODEL, format="json", prompt=f"EXIGENCE : {req.get('exigence')}\nSAVOIR-FAIRE : {context}\n" \
                             "Réponds en JSON : {\"statut\": \"...\", \"score_confiance\": 0, \"justification\": \"...\", \"incertitude\": \"...\"}")
                gap = json.loads(r2.get('response', '{}'))
                req.update(gap); results.append(req)
            except Exception as e:
                logger.warning(f"⚠️ Erreur gap : {e}")
    return results

def generate_markdown_report(ingestion: dict, gap: list, rfp_name: str) -> str:
    rapport = f"# 📋 Rapport de Confiance — {rfp_name}\n**Généré le :** {ingestion['date']}\n\n---\n"
    rapport += "## PARTIE 1 — Compréhension Système\n\n| Section | Confiance | Résumé |\n|---|---|---|\n"
    for cat in ingestion["categories"]:
        emoji = "✅" if cat["confiance"] == "ÉLEVÉE" else "⚠️" if cat["confiance"] == "MOYENNE" else "❌"
        rapport += f"| {cat['nom']} | {emoji} {cat['confiance']} | {cat.get('resume', '-')} |\n"
    
    if ingestion["questions_humain"]:
        rapport += "\n### ❓ Questions bloquantes\n"
        for i, q in enumerate(ingestion["questions_humain"], 1): rapport += f"{i}. **[{q['categorie']}]** {q['question']}\n"

    rapport += "\n---\n## PARTIE 2 — Gap Analysis\n\n| Statut | Confiance | Exigence | Justification |\n|---|---|---|---|\n"
    for r in gap:
        s_emoji = "✅" if r.get("statut") == "CONFORME" else "⚠️" if r.get("statut") == "PARTIEL" else "❌"
        rapport += f"| {s_emoji} | {r.get('score_confiance', 0)}% | {r.get('exigence','?')[:50]} | {r.get('justification','?')[:60]} |\n"
    return rapport

if __name__ == "__main__":
    parser = argparse.ArgumentParser(); parser.add_argument("--rfp", required=True); args = parser.parse_args()
    rfp_s = VectorStore(db_path=DEFAULT_DB, collection_name="rfp_hierarchical")
    cat_s = VectorStore(db_path=DEFAULT_DB, collection_name="service_catalog")
    ing = audit_ingestion(rfp_s, Path(DEFAULT_IMAGES))
    gap = audit_gap_analysis(rfp_s, cat_s)
    with open("data/confidence_report.md", "w", encoding="utf-8") as f: f.write(generate_markdown_report(ing, gap, args.rfp))
    logger.success("✅ Rapport généré.")
