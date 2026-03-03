"""
confidence_report.py — Rapport de confiance après ingestion et Gap Analysis

Ce script génère un rapport complet en deux parties :
  - Partie 1 : Ce que le système a compris (après indexation du PDF)
  - Partie 2 : Les écarts de conformité (après Gap Analysis)
"""

import json
import ollama
import argparse
from pathlib import Path
from datetime import datetime
from loguru import logger
from phase1.vectorstore import VectorStore
from phase1.reranker import LocalReranker

# CONFIGURATION
CATEGORIES = ["ADMIN", "TECHNIQUE", "FINANCIER", "JURIDIQUE", "PLANNING", "SECURITE"]
TEXT_MODEL = "qwen2.5:7b"
VISION_MODEL = "llama3.2-vision"

# PARTIE 1 — Rapport d'ingestion (ce qu'il a bien/mal compris)
# ─────────────────────────────────────────────────────────────────────────────

def audit_ingestion(store: VectorStore, image_dir: Path) -> dict:
    """
    Analyse la qualité de l'ingestion par catégorie et détecte les zones floues.
    """
    logger.info("🔍 Audit de l'ingestion en cours...")
    rapport = {
        "date": datetime.now().strftime("%d/%m/%Y %H:%M"),
        "categories": [],
        "schemas": [],
        "questions_humain": []
    }

    # ── 1. Analyse par catégorie ──────────────────────────────────────────────
    for cat in CATEGORIES:
        fragments = store.search_hybrid(query=f"CATÉGORIE: {cat}", n_results=10)
        if not fragments:
            rapport["categories"].append({
                "nom": cat,
                "nb_fragments": 0,
                "confiance": "FAIBLE",
                "resume": "Aucun fragment trouvé pour cette catégorie.",
                "points_flous": ["Aucune information extraite — section absente ou non reconnue."]
            })
            continue

        # Évaluation de la qualité par le LLM
        context_list = [f['text'][:500] for f in fragments[:5]]
        context = "\n---\n".join(context_list)
        prompt = f"""Tu es un auditeur qualité d'extraction de documents RFP.
Voici des fragments extraits de la catégorie {cat}.

FRAGMENTS :
{context}

Évalue la qualité de l'extraction. Réponds UNIQUEMENT en JSON :
{{
  "confiance": "ÉLEVÉE ou MOYENNE ou FAIBLE",
  "resume": "Résumé en 1 phrase de ce qui a été extrait.",
  "points_flous": ["Point flou 1", "Point flou 2"]
}}"""

        try:
            response = ollama.generate(model=TEXT_MODEL, prompt=prompt, format="json")
            data = json.loads(response['response'])
            data["nom"] = cat
            data["nb_fragments"] = len(fragments)
            rapport["categories"].append(data)

            if data.get("confiance") == "FAIBLE":
                for point in data.get("points_flous", []):
                    rapport["questions_humain"].append({
                        "categorie": cat,
                        "question": f"[{cat}] {point}"
                    })
        except Exception as e:
            logger.warning(f"⚠️ Erreur analyse catégorie {cat} : {e}")
            rapport["categories"].append({
                "nom": cat, "nb_fragments": len(fragments), "confiance": "INCONNUE",
                "resume": "Erreur lors de l'analyse.", "points_flous": []
            })

    # ── 2. Analyse des schémas / images ──────────────────────────────────────
    if image_dir.exists():
        images = list(image_dir.glob("*.png"))
        logger.info(f"🖼️ Analyse de {len(images)} captures visuelles...")

        for img_path in images[:5]: # Limite pour le test
            page_no = img_path.stem.split("_")[-1]
            prompt = f"Analyse cette image de document RFP (Page {page_no}). Évalue sa lisibilité et identifie les éléments. " \
                     "Réponds UNIQUEMENT en JSON sous ce format EXACT : " \
                     "{\"page\": \""+page_no+"\", \"type_visuel\": \"schéma\", \"lisibilite\": \"BONNE\", \"elements_identifies\": [], \"questions_pour_humain\": []}"

            try:
                response = ollama.generate(model=VISION_MODEL, prompt=prompt, images=[str(img_path)], format="json")
                data = json.loads(response['response'])
                data["fichier"] = img_path.name
                rapport["schemas"].append(data)

                if data.get("lisibilite") == "MAUVAISE":
                    for q in data.get("questions_pour_humain", []):
                        rapport["questions_humain"].append({"categorie": f"VISUEL - Page {page_no}", "question": q})
            except Exception as e:
                logger.warning(f"⚠️ Erreur lors du traitement : {e}")
                continue

    return rapport

# PARTIE 2 — Gap Analysis avec niveaux de confiance
# ─────────────────────────────────────────────────────────────────────────────

def audit_gap_analysis(rfp_store: VectorStore, catalog_store: VectorStore) -> list:
    """Effectue la Gap Analysis avec score de confiance explicite."""
    logger.info("🛡️ Gap Analysis avec scores de confiance...")
    results = []

    for cat in ["TECHNIQUE", "SECURITE"]:
        fragments = rfp_store.search_hybrid(query=f"CATÉGORIE: {cat}", n_results=10)
        if not fragments: continue

        for frag in fragments[:3]:
            # 1. Extraction
            ex_prompt = f"Extrais l'exigence principale de ce texte :\n{frag['text'][:800]}\n" \
                        "Réponds en JSON : {\"exigence\": \"...\", \"priorite\": \"HAUTE/MOYENNE/BASSE\"}"
            try:
                r1 = ollama.generate(model=TEXT_MODEL, prompt=ex_prompt, format="json")
                req = json.loads(r1['response'])
                req['source'] = f"{frag['metadata']['breadcrumbs']} (P.{frag['metadata']['page']})"
                req['categorie'] = cat

                # 2. Recherche Catalogue
                know_how = catalog_store.search_hybrid(query=req['exigence'], n_results=3)
                context_catalog = "\n".join([k['text'][:400] for k in know_how]) if know_how else "AUCUN SAVOIR-FAIRE."

                # 3. Gap Analysis
                gap_prompt = f"EXIGENCE : {req['exigence']}\nSAVOIR-FAIRE : {context_catalog}\n" \
                             "Réponds en JSON : {\"statut\": \"CONFORME/PARTIEL/NON_CONFORME\", \"score_confiance\": 0, \"justification\": \"...\", \"incertitude\": \"...\"}"

                r2 = ollama.generate(model=TEXT_MODEL, prompt=gap_prompt, format="json")
                gap = json.loads(r2['response'])
                req.update(gap)
                results.append(req)
            except Exception as e:
                logger.warning(f"⚠️ Erreur lors du traitement : {e}")
                continue

    return results

# GÉNÉRATION DU RAPPORT MARKDOWN
# ─────────────────────────────────────────────────────────────────────────────

def generate_markdown_report(ingestion: dict, gap: list, rfp_name: str) -> str:
    rapport = f"# 📋 Rapport de Confiance — Analyse RFP\n" \
              f"**Document :** {rfp_name} | **Généré le :** {ingestion['date']}\n\n---\n"
    
    rapport += "## PARTIE 1 — Compréhension Système\n\n| Section | Confiance | Résumé |\n|---|---|---|\n"
    for cat in ingestion["categories"]:
        emoji = "✅" if cat["confiance"] == "ÉLEVÉE" else "⚠️" if cat["confiance"] == "MOYENNE" else "❌"
        rapport += f"| {cat['nom']} | {emoji} {cat['confiance']} | {cat.get('resume', '-')} |\n"

    if ingestion["questions_humain"]:
        rapport += "\n### ❓ Questions pour clarification humaine\n"
        for i, q in enumerate(ingestion["questions_humain"], 1):
            rapport += f"{i}. **[{q['categorie']}]** {q['question']}\n"

    rapport += "\n---\n## PARTIE 2 — Gap Analysis\n\n" \
               "| Statut | Confiance | Priorité | Exigence | Justification | Incertitude |\n" \
               "|---|---|---|---|---|---|\n"
    
    for r in gap:
        s_emoji = "✅" if r.get("statut") == "CONFORME" else "⚠️" if r.get("statut") == "PARTIEL" else "❌"
        p_emoji = "🔴" if r.get("priorite") == "HAUTE" else "🟡"
        conf = r.get("score_confiance", 0)
        rapport += f"| {s_emoji} | {conf}% | {p_emoji} | {r.get('exigence','?')[:50]} | {r.get('justification','?')[:60]} | {r.get('incertitude','?')[:50]} |\n"

    return rapport

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Rapport de Confiance RFP")
    parser.add_argument("--rfp", required=True)
    parser.add_argument("--collection", default="rfp_hierarchical")
    parser.add_argument("--catalog", default="service_catalog")
    args = parser.parse_args()

    rfp_store = VectorStore(db_path="data/chroma_db_hierarchical", collection_name=args.collection)
    catalog_store = VectorStore(db_path="data/chroma_db_hierarchical", collection_name=args.catalog)
    
    ingestion_data = audit_ingestion(rfp_store, Path("data/output_images"))
    gap_data = audit_gap_analysis(rfp_store, catalog_store)
    
    report_md = generate_markdown_report(ingestion_data, gap_data, args.rfp)
    
    with open("data/confidence_report.md", "w", encoding="utf-8") as f:
        f.write(report_md)
    
    logger.success("✅ Rapport de confiance généré dans data/confidence_report.md")
