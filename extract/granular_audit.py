import os
import sys
import argparse
import hashlib
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
from phase2.micro_agents import FSMPipeline, RequirementState

console = Console()

def run_granular_audit(category: str = "TECHNIQUE"):
    """
    Orchestre l'analyse granulaire sur un ensemble d'exigences métier via le moteur FSM.
    """
    logger.info(f"🚀 Démarrage de l'Audit Granulaire FSM — Domaine : {category}")
    
    audit_agent = ComplianceAuditAgent()
    fsm_pipeline = FSMPipeline()
    
    # 1. Extraction des exigences sources
    raw_requirements = audit_agent.extract_requirements(category=category)
    if not raw_requirements:
        logger.warning(f"⚠️ Aucune exigence '{category}' trouvée.")
        return

    # 2. Analyse chirurgicale via la Machine à État (FSM)
    results = []
    with Progress() as progress:
        task = progress.add_task("[cyan]Traitement dans l'usine FSM...", total=len(raw_requirements))
        
        for req in raw_requirements:
            label = req.get('exigence', 'Inconnue')
            # Génération d'un UID pour le suivi FSM
            uid = hashlib.md5(label.encode()).hexdigest()[:10]
            
            logger.debug(f"🔬 FSM Run pour REQ:{uid}...")
            
            # Passage dans l'usine (BABOK -> Radar -> ISO)
            fsm_data = fsm_pipeline.run_factory(label, uid=uid)
            
            results.append({
                "original": label,
                "source": req.get('source', 'N/A'),
                "priority": req.get('priorite', 'MOYENNE'),
                "fsm": fsm_data
            })
            progress.update(task, advance=1)

    # 3. Rapports de sortie
    generate_markdown_report(results, category)
    display_summary_table(results)

def generate_markdown_report(results: list, category: str):
    """Génère le rapport de désambiguïsation Markdown basé sur les états FSM."""
    output_path = Path("data/granular_audit_report.md")
    
    report = f"# 🔬 Rapport d'Analyse Granulaire & Audit FSM\n"
    report += f"**Domaine :** {category} | **Généré le :** {Path(output_path).parent.stat().st_mtime}\n\n"
    
    report += "## 🚩 Exigences Bloquées ou Ambiguës\n"
    report += "Ces points n'ont pas atteint l'état 'CLEAN' et nécessitent une clarification.\n\n"
    report += "| UID | Statut Final | Exigence Originale | Termes Flous | Historique FSM |\n"
    report += "|:---:|:---:|---|---|---|\n"
    
    for r in results:
        f = r['fsm']
        if f.state != RequirementState.AUDITED:
            fuzzy = ", ".join(f.fuzzy_terms) if f.fuzzy_terms else "N/A"
            history = "<br>".join(f.state_history)
            report += f"| {f.uid} | **{f.state.value}** | {r['original']} | `{fuzzy}` | {history} |\n"
            
    report += "\n## 🛡️ Complétude & Inférence (ISO 25010)\n"
    report += "Exigences ayant atteint l'état 'AUDITED' avec suggestions de complétude.\n\n"
    report += "| UID | Exigence | Manques Détectés | Tickets d'Écart |\n"
    report += "|:---:|---|---|---|\n"
    
    for r in results:
        f = r['fsm']
        if f.state == RequirementState.AUDITED:
            missing = ", ".join(f.missing_implications) if f.missing_implications else "Aucun"
            tickets = "<br>".join(f.gap_tickets) if f.gap_tickets else "N/A"
            report += f"| {f.uid} | {r['original']} | {missing} | {tickets} |\n"
            
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(report)
    logger.success(f"✅ Rapport granulaire FSM disponible : {output_path}")

def display_summary_table(results: list):
    """Affiche un résumé visuel des transitions d'états."""
    table = Table(title="Résumé de l'Usine à RFP (Cycle FSM)")
    table.add_column("UID", justify="center", style="cyan")
    table.add_column("État Final", justify="center")
    table.add_column("Exigence (Extrait)", style="dim")
    table.add_column("Ambiguïté", justify="right")
    
    for r in results:
        f = r['fsm']
        state_style = "green" if f.state == RequirementState.AUDITED else "bold red"
        table.add_row(
            f.uid,
            f"[{state_style}]{f.state.value}[/]",
            r['original'][:60] + "...",
            f"{f.ambiguity_score}/100"
        )
    console.print(table)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Audit Granulaire FSM")
    parser.add_argument("--cat", default="TECHNIQUE", help="Catégorie (TECHNIQUE, SECURITE, etc.)")
    args = parser.parse_args()
    run_granular_audit(args.cat)
