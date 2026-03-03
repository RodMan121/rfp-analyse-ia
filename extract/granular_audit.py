import os
import sys
import argparse
from pathlib import Path
from loguru import logger
from rich.console import Console
from rich.table import Table
from rich.progress import Progress

# Fix pour les imports
sys.path.append(str(Path(__file__).parent))

from phase2.compliance import ComplianceAuditAgent
from phase2.micro_agents import GranularAnalysisEngine

console = Console()

def run_granular_audit(category: str = "TECHNIQUE"):
    """
    Lance l'analyse granulaire sur une catégorie d'exigences.
    """
    logger.info(f"🚀 Démarrage de l'Audit Granulaire — Catégorie : {category}")
    
    audit_agent = ComplianceAuditAgent()
    granular_engine = GranularAnalysisEngine()
    
    # 1. Extraction des exigences brutes
    raw_requirements = audit_agent.extract_requirements(category=category)
    if not raw_requirements:
        logger.warning("⚠️ Aucune exigence trouvée à analyser.")
        return

    # 2. Analyse via Micro-Agents
    granular_results = []
    
    with Progress() as progress:
        task = progress.add_task("[cyan]Analyse granulaire...", total=len(raw_requirements))
        
        for req in raw_requirements:
            logger.info(f"🔬 Analyse de : {req['exigence'][:50]}...")
            analysis = granular_engine.process_requirement(req['exigence'])
            
            # Fusion des données source et analyse
            result = {
                "original": req['exigence'],
                "source": req['source'],
                "priority": req['priorite'],
                "granular": analysis
            }
            granular_results.append(result)
            progress.update(task, advance=1)

    # 3. Génération du rapport Markdown
    generate_markdown_report(granular_results, category)
    
    # 4. Affichage d'un résumé console
    display_summary_table(granular_results)

def generate_markdown_report(results, category):
    output_path = Path("data/granular_audit_report.md")
    
    report = f"# 🔬 Rapport d'Analyse Granulaire & Désambiguïsation
"
    report += f"**Domaine :** {category} | **Date :** {Path('data').stat().st_mtime}

"
    
    report += "## 🚩 Exigences Ambiguës (À clarifier)
"
    report += "Ces points contiennent des termes flous qui présentent un risque contractuel.

"
    report += "| Score | Exigence Originale | Termes Flous | Suggestion BABOK |
"
    report += "|:---:|---|---|---|
"
    
    for r in results:
        g = r['granular']
        if g.status == "PENDING_CLARIFICATION":
            fuzzy = ", ".join(g.fuzzy_terms)
            babok = f"{g.subject} doit {g.action} {g.target_object} ({g.constraint})"
            report += f"| {g.ambiguity_score} | {r['original']} | `{fuzzy}` | {babok} |
"
            
    report += "
## 🛡️ Suggestions de Complétude (ISO 25010)
"
    report += "Fonctionnalités implicites détectées comme manquantes ou nécessaires.

"
    report += "| Exigence | Manquements Détectés | Tickets d'Écart suggérés |
"
    report += "|---|---|---|
"
    
    for r in results:
        g = r['granular']
        if g.missing_implications:
            missing = ", ".join(g.missing_implications)
            tickets = "<br>".join(g.gap_tickets)
            report += f"| {r['original']} | {missing} | {tickets} |
"
            
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(report)
    
    logger.success(f"✅ Rapport granulaire généré : {output_path}")

def display_summary_table(results):
    table = Table(title="Résumé de l'Audit Granulaire")
    table.add_column("Statut", justify="center")
    table.add_column("Exigence (Extrait)", style="dim")
    table.add_column("Score Loup", justify="right")
    
    for r in results:
        g = r['granular']
        status_style = "bold red" if g.status == "PENDING_CLARIFICATION" else "green"
        table.add_row(
            f"[{status_style}]{g.status}[/]",
            r['original'][:60] + "...",
            str(g.ambiguity_score)
        )
    
    console.print(table)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Audit Granulaire des exigences")
    parser.add_argument("--cat", default="TECHNIQUE", help="Catégorie à analyser")
    args = parser.parse_args()
    
    run_granular_audit(args.cat)
