import os
import sys
import asyncio
from pathlib import Path
from rich.console import Console
from rich.table import Table
from dotenv import load_dotenv

# Fix pour les imports et configuration
sys.path.append(str(Path(__file__).parent))
load_dotenv(Path(__file__).parent / ".env")

from phase2.compliance import ComplianceAuditAgent # noqa: E402
from phase2.micro_agents import FSMPipeline, RequirementState # noqa: E402
from utils.factory_log import factory_logger # noqa: E402

console = Console()

async def run_granular_audit(category: str = "TECHNIQUE"):
    """Audit granulaire asynchrone pour éviter le blocage coroutine."""
    console.print(f"\n[bold blue]🔬 Audit Granulaire : {category}[/bold blue]")
    
    audit = ComplianceAuditAgent()
    fsm_pipeline = FSMPipeline()
    
    # 1. Extraction des fragments
    raw_reqs = audit.extract_requirements(category=category)
    if not raw_reqs:
        console.print("[yellow]⚠️ Aucun fragment trouvé.[/yellow]")
        return

    # 2. Passage dans la FSM (Async)
    results = []
    for req in raw_reqs[:10]: # On limite l'échantillon
        label = req.get("exigence", "")
        uid = f"DBG-{hash(label) % 10000}"
        
        # FIX P1.1 : Appel asynchrone correct avec await
        fsm_data = await fsm_pipeline.run_factory(label, uid=uid)
        results.append(fsm_data)

    # 3. Affichage du rapport
    _display_report(results)
    
    # 4. Export Markdown
    report_path = Path("data/granular_audit_report.md")
    with open(report_path, "w", encoding="utf-8") as f:
        f.write(_generate_markdown_report(results, category))
    
    console.print(f"\n[green]✅ Rapport exporté : {report_path}[/green]")

def _display_report(results):
    table = Table(title="Résultats FSM (Échantillon)")
    table.add_column("UID", style="dim")
    table.add_column("État Final")
    table.add_column("Score Ambiguïté")
    table.add_column("Sujet BABOK")

    for r in results:
        status_color = "green" if r.state == RequirementState.CLEAN else "red" if r.state == RequirementState.ERROR else "yellow"
        table.add_row(
            r.uid,
            f"[{status_color}]{r.state.value}[/{status_color}]",
            str(r.ambiguity_score),
            r.subject
        )
    console.print(table)

def _generate_markdown_report(results, category):
    md = f"# 🔬 Rapport d'Audit Granulaire - {category}\n\n"
    
    md += "## 🛑 Blocages & Ambiguïtés (STALLED)\n"
    for r in results:
        # FIX P1.3 : Utilisation de l'état NORMALIZED avec score > 0 pour les blocages
        if r.ambiguity_score > 0:
            md += f"### Exigence {r.uid}\n"
            md += f"- **Texte brut** : {r.original_text}\n"
            md += f"- **Score d'ambiguïté** : {r.ambiguity_score}/100\n"
            md += f"- **Termes flous** : {', '.join(r.fuzzy_terms) if r.fuzzy_terms else 'N/A'}\n\n"

    md += "## ✅ Exigences Prêtes (CLEAN)\n"
    for r in results:
        if r.state == RequirementState.CLEAN:
            md += f"- **[{r.uid}]** {r.subject} {r.action} {r.target_object}\n"
            
    return md

if __name__ == "__main__":
    asyncio.run(run_granular_audit())
