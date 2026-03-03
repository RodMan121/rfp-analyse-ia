import sys
import argparse
import hashlib
import json
from pathlib import Path
from loguru import logger
from rich.console import Console
from rich.table import Table
from rich.progress import Progress
from dotenv import load_dotenv
from dataclasses import asdict

# Fix pour les imports et configuration
sys.path.append(str(Path(__file__).parent))
load_dotenv(Path(__file__).parent / ".env")

from phase2.compliance import ComplianceAuditAgent  # noqa: E402
from phase2.micro_agents import FSMPipeline, RequirementState  # noqa: E402
from utils.factory_log import factory_logger  # noqa: E402

console = Console()


def run_granular_audit(category: str = "TECHNIQUE"):
    """
    Orchestre l'analyse granulaire et sauvegarde le registre FSM pour la Phase 3.
    """
    factory_logger.log_event("PHASE_2", "START", f"Début audit granulaire : {category}")

    audit_agent = ComplianceAuditAgent()
    fsm_pipeline = FSMPipeline()

    # 1. Extraction des exigences sources
    raw_requirements = audit_agent.extract_requirements(category=category)
    if not raw_requirements:
        factory_logger.log_event("PHASE_2", "WARNING", "Aucune exigence trouvée.")
        logger.warning("⚠️ Aucune exigence trouvée à analyser.")
        return

    # 2. Analyse chirurgicale via la Machine à État (FSM)
    results = []
    fsm_objects = []

    with Progress() as progress:
        task = progress.add_task(
            "[cyan]Traitement dans l'usine FSM...", total=len(raw_requirements)
        )

        for req in raw_requirements:
            label = req.get("exigence", "Inconnue")
            uid = hashlib.md5(label.encode()).hexdigest()[:10]

            # Passage dans l'usine
            fsm_data = fsm_pipeline.run_factory(label, uid=uid)
            fsm_objects.append(fsm_data)

            # Log détaillé du statut FSM
            factory_logger.log_event(
                "PHASE_2",
                "FSM_STEP",
                f"REQ:{uid} -> {fsm_data.state.value}",
                {
                    "ambiguity": fsm_data.ambiguity_score,
                    "fuzzy_terms": fsm_data.fuzzy_terms,
                },
            )

            results.append(
                {
                    "original": label,
                    "source": req.get("source", "N/A"),
                    "priority": req.get("priorite", "MOYENNE"),
                    "fsm": fsm_data,
                }
            )
            progress.update(task, advance=1)

    # 3. Sauvegarde du REGISTRE FSM (pour la Phase 3)
    save_fsm_registry(fsm_objects)

    # 4. Rapports de sortie
    generate_markdown_report(results, category)
    display_summary_table(results)

    factory_logger.log_event(
        "PHASE_2", "COMPLETED", f"Audit terminé. {len(results)} exigences traitées."
    )


def save_fsm_registry(fsm_requirements):
    output_path = Path("data/fsm_registry.json")
    serializable = []
    for r in fsm_requirements:
        d = asdict(r)
        d["state"] = r.state.value
        serializable.append(d)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(serializable, f, indent=2, ensure_ascii=False)


def generate_markdown_report(results: list, category: str):
    output_path = Path("data/granular_audit_report.md")
    report = "# 🔬 Rapport d'Analyse Granulaire & Audit FSM\n"
    report += f"**Domaine :** {category}\n\n"
    report += "## 🚩 Exigences Bloquées ou Ambiguës\n\n"
    report += "| UID | Statut Final | Exigence Originale | Termes Flous |\n"
    report += "|:---:|:---:|---|---|\n"
    for r in results:
        f = r["fsm"]
        if f.state != RequirementState.AUDITED:
            fuzzy = ", ".join(f.fuzzy_terms) if f.fuzzy_terms else "N/A"
            report += (
                f"| {f.uid} | **{f.state.value}** | {r['original']} | `{fuzzy}` |\n"
            )

    report += "\n## 🛡️ Complétude & Inférence (ISO 25010)\n\n"
    report += "| UID | Exigence | Manques Détectés |\n"
    report += "|:---:|---|---|\n"
    for r in results:
        f = r["fsm"]
        if f.state == RequirementState.AUDITED:
            missing = (
                ", ".join(f.missing_implications) if f.missing_implications else "Aucun"
            )
            report += f"| {f.uid} | {r['original']} | {missing} |\n"
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(report)


def display_summary_table(results: list):
    table = Table(title="Résumé de l'Usine à RFP (Cycle FSM)")
    table.add_column("UID", justify="center", style="cyan")
    table.add_column("État Final", justify="center")
    table.add_column("Ambiguïté", justify="right")
    for r in results:
        f = r["fsm"]
        state_style = "green" if f.state == RequirementState.AUDITED else "bold red"
        table.add_row(
            f.uid, f"[{state_style}]{f.state.value}[/]", f"{f.ambiguity_score}/100"
        )
    console.print(table)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--cat", default="TECHNIQUE")
    args = parser.parse_args()
    run_granular_audit(args.cat)
