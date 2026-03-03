import os
import sys
import argparse
from pathlib import Path
from loguru import logger
from rich.console import Console
from rich.table import Table
from rich.progress import Progress
from dotenv import load_dotenv

# Fix pour les imports et configuration
sys.path.append(str(Path(__file__).parent))
load_dotenv(Path(__file__).parent / ".env")

from phase2.compliance import ComplianceAuditAgent
from phase2.micro_agents import GranularAnalysisEngine

console = Console()

def run_granular_audit(category: str = "TECHNIQUE"):
    """
    Orchestre l'analyse granulaire sur un ensemble d'exigences métier.
    """
    logger.info(f"🚀 Démarrage de l'Audit Granulaire — Domaine : {category}")
    
    audit_agent = ComplianceAuditAgent()
    granular_engine = GranularAnalysisEngine()
    
    # 1. Extraction des exigences sources
    raw_requirements = audit_agent.extract_requirements(category=category)
    if not raw_requirements:
        logger.warning(f"⚠️ Aucune exigence '{category}' trouvée.")
        return

    # 2. Analyse chirurgicale via micro-agents
    results = []
    with Progress() as progress:
        task = progress.add_task("[cyan]Analyse en chaîne de montage...", total=len(raw_requirements))
        
        for req in raw_requirements:
            label = req.get('exigence', 'Inconnue')
            logger.debug(f"🔬 Analyse : {label[:40]}...")
            
            granular_data = granular_engine.process_requirement(label)
            results.append({
                "original": label,
                "source": req.get('source', 'N/A'),
                "priority": req.get('priorite', 'MOYENNE'),
                "granular": granular_data
            })
            progress.update(task, advance=1)

    # 3. Rapports de sortie
    generate_markdown_report(results, category)
    display_summary_table(results)

def generate_markdown_report(results: list, category: str):
    """Génère le rapport de désambiguïsation Markdown."""
    output_path = Path("data/granular_audit_report.md")
    
    report = f"# 🔬 Rapport d'Analyse Granulaire & Désambiguïsation\n"
    report += f"**Domaine :** {category} | **Généré le :** {Path(output_path).parent.stat().st_mtime}\n\n"
    
    report += "## 🚩 Exigences Ambiguës (À clarifier)\n"
    report += "Ces points contiennent des termes qualitatifs présentant un risque contractuel.\n\n"
    report += "| Score | Exigence Originale | Termes Flous | Suggestion de structure BABOK |\n"
    report += "|:---:|---|---|---|\n"
    
    for r in results:
        g = r['granular']
        if g.status == "PENDING_CLARIFICATION":
            fuzzy = ", ".join(g.fuzzy_terms)
            babok = f"**{g.subject}** doit **{g.action}** **{g.target_object}** ({g.constraint})"
            report += f"| {g.ambiguity_score} | {r['original']} | `{fuzzy}` | {babok} |\n"
            
    report += "\n## 🛡️ Complétude & Inférence (ISO 25010)\n"
    report += "Fonctionnalités non écrites mais nécessaires à la qualité du système.\n\n"
    report += "| Exigence | Manques Détectés | Actions / Tickets suggérés |\n"
    report += "|---|---|---|\n"
    
    for r in results:
        g = r['granular']
        if g.missing_implications:
            missing = ", ".join(g.missing_implications)
            tickets = "<br>".join(g.gap_tickets)
            report += f"| {r['original']} | {missing} | {tickets} |\n"
            
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(report)
    logger.success(f"✅ Rapport granulaire disponible : {output_path}")

def display_summary_table(results: list):
    """Affiche un résumé visuel dans la console."""
    table = Table(title="Résumé de l'Audit Granulaire")
    table.add_column("Statut", justify="center")
    table.add_column("Exigence (Extrait)", style="dim")
    table.add_column("Ambiguïté", justify="right")
    
    for r in results:
        g = r['granular']
        style = "bold red" if g.status == "PENDING_CLARIFICATION" else "green"
        table.add_row(
            f"[{style}]{g.status}[/]",
            r['original'][:60] + "...",
            f"{g.ambiguity_score}/100"
        )
    console.print(table)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Audit Granulaire des exigences")
    parser.add_argument("--cat", default="TECHNIQUE", help="Catégorie (TECHNIQUE, SECURITE, etc.)")
    args = parser.parse_args()
    run_granular_audit(args.cat)
