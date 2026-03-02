#!/usr/bin/env python3
# main.py — Niveau 2 : Gemini Flash (Multimodal)
"""
Augmented BID IA — Phase 1 : Ingestion & Décomposition
Point d'entrée principal.

Usage:
  python main.py --input data/input/mon_rfp.pdf
  python main.py --search "exigences de sécurité AES-256"
  python main.py --search "disponibilité 99.9" --domain Infrastructure
  python main.py --stats
"""

import argparse
import json
from pathlib import Path
from datetime import datetime, timezone
from loguru import logger
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich import print as rprint

from phase1.local_parser import DoclingParser, LocalRawFragment
from phase1.classifier import RuleBasedClassifier
from phase1.vectorstore import VectorStore
from phase1.models import AtomicFragment, FragmentMetadata, FragmentClassification

console = Console()


# ─────────────────────────────────────────────────────────
# Pipeline principal
# ─────────────────────────────────────────────────────────

def run_ingestion(
    input_path: str,
    output_dir: str = "data/output_json",
    db_path: str = "data/chroma_db",
) -> list[AtomicFragment]:
    """
    Pipeline complet Phase 1 (Stratégie Optimale) :
    Document → Docling (Local) → Markdown → Classification → JSON + ChromaDB
    """

    console.print(Panel.fit(
        "[bold cyan]🏭 Augmented BID IA — Phase 1 : Ingestion & Décomposition[/bold cyan]\n"
        "[dim]Moteur : Docling (Local) + Gemini (Analyse Cognitive)[/dim]\n"
        f"[dim]Source : {input_path}[/dim]",
        border_style="cyan"
    ))

    # 1. Parse local via Docling
    console.print("\n[bold]📄 Étape 1/4 — Parsing local (Docling)...[/bold]")
    parser = DoclingParser()
    
    # Sauvegarde du Markdown complet pour consultation
    full_md = parser.parse_to_markdown(input_path)
    md_output_dir = Path("data/output_markdown")
    md_output_dir.mkdir(parents=True, exist_ok=True)
    md_file = md_output_dir / f"{Path(input_path).stem}.md"
    with open(md_file, "w", encoding="utf-8") as f:
        f.write(full_md)
    console.print(f"  → [green]Markdown complet sauvegardé : {md_file}[/green]")

    raw_fragments = parser.parse_to_fragments_from_markdown(full_md, Path(input_path).name)

    console.print(f"  → [green]{len(raw_fragments)} fragments structurés extraits localement[/green]")

    # 2. Classification sémantique
    console.print("\n[bold]🧠 Étape 2/4 — Classification et Normalisation...[/bold]")
    classifier = RuleBasedClassifier()
    atomic_fragments = []

    for raw in raw_fragments:
        classification = classifier.classify(raw)

        fragment = AtomicFragment(
            metadata=FragmentMetadata(
                source_file=raw.source_file,
                section=raw.section,
                page=raw.page,
                raw_text=raw.text,
                char_count=len(raw.text),
            ),
            classification=classification,
        )
        atomic_fragments.append(fragment)

    console.print(f"  → [green]{len(atomic_fragments)} fragments classifiés[/green]")

    # 3. Export JSON atomique
    console.print("\n[bold]💾 Étape 3/4 — Export JSON atomique...[/bold]")
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    source_name = Path(input_path).stem
    json_file = output_path / f"{source_name}_{timestamp}.json"

    with open(json_file, "w", encoding="utf-8") as fp:
        json.dump([f.model_dump() for f in atomic_fragments], fp, ensure_ascii=False, indent=2)

    console.print(f"  → [green]JSON : {json_file}[/green]")

    # 4. Vectorisation ChromaDB
    console.print("\n[bold]🗄️  Étape 4/4 — Vectorisation et stockage...[/bold]")
    store = VectorStore(db_path=db_path)
    nb_inserted = store.add_fragments_batch(atomic_fragments)
    console.print(f"  → [green]{nb_inserted} fragments vectorisés dans ChromaDB[/green]")

    _print_summary(atomic_fragments)
    return atomic_fragments


def run_search(
    query: str,
    domain: str | None = None,
    priority: str | None = None,
    db_path: str = "data/chroma_db",
    n_results: int = 5,
):
    """Recherche sémantique dans la base vectorielle."""
    console.print(Panel.fit(
        f"[bold cyan]🔍 Recherche sémantique[/bold cyan]\n[dim]\"{query}\"[/dim]",
        border_style="cyan"
    ))

    store = VectorStore(db_path=db_path)
    results = store.search(query=query, n_results=n_results,
                           filter_domain=domain, filter_priority=priority)

    if not results:
        console.print("[yellow]⚠️  Aucun résultat trouvé.[/yellow]")
        return

    table = Table(title=f"Top {len(results)} résultats", show_lines=True)
    table.add_column("Rang", style="cyan", width=5)
    table.add_column("Score", style="green", width=7)
    table.add_column("Domaine", width=14)
    table.add_column("Type", width=10)
    table.add_column("Priorité", width=10)
    table.add_column("Extrait", width=70)

    for r in results:
        table.add_row(
            str(r["rank"]),
            str(r["similarity_score"]),
            r["metadata"].get("domaine", "?"),
            r["metadata"].get("type_babok", "?"),
            r["metadata"].get("priorite_esn", "?"),
            r["text"][:100] + "..." if len(r["text"]) > 100 else r["text"],
        )
    console.print(table)


def run_stats(db_path: str = "data/chroma_db"):
    store = VectorStore(db_path=db_path)
    stats = store.stats()
    rprint(Panel(
        f"[bold]Total fragments :[/bold] [green]{stats['total_fragments']}[/green]\n"
        f"[bold]Collection      :[/bold] {stats['collection']}\n"
        f"[bold]DB Path         :[/bold] {stats['db_path']}\n"
        f"[bold]Modèle embedding:[/bold] {stats['embedding_model']}",
        title="📊 Statistiques Phase 1",
        border_style="blue"
    ))


def _print_summary(fragments: list[AtomicFragment]):
    domain_counts: dict[str, int] = {}
    type_counts: dict[str, int] = {}
    high_priority = 0

    for f in fragments:
        d = f.classification.domaine
        domain_counts[d] = domain_counts.get(d, 0) + 1
        t = f.metadata.raw_text[:5]  # proxy pour fragment_type — améliorer si besoin
        if f.classification.priorite_esn == "Haute":
            high_priority += 1

    table = Table(title="\n📊 Résumé de l'ingestion", show_lines=True)
    table.add_column("Domaine", style="cyan")
    table.add_column("Fragments", justify="right", style="green")
    table.add_column("% du total", justify="right")

    total = len(fragments)
    for domain, count in sorted(domain_counts.items(), key=lambda x: -x[1]):
        table.add_row(domain, str(count), f"{count / total * 100:.1f}%")

    table.add_section()
    table.add_row("[bold]TOTAL[/bold]", f"[bold]{total}[/bold]", "[bold]100%[/bold]")
    console.print(table)
    console.print(
        f"\n[bold yellow]⚡ Fragments priorité ESN Haute :[/bold yellow] "
        f"[green]{high_priority}[/green] / {total}"
    )
    console.print("\n[bold green]✅ Phase 1 terminée avec succès ![/bold green]\n")


# ─────────────────────────────────────────────────────────
# CLI
# ─────────────────────────────────────────────────────────

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Augmented BID IA — Phase 1 (Niveau 2 : Gemini Flash)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemples :
  python main.py --input data/input/rfp.pdf
  python main.py --search "exigences sécurité" --domain Sécurité
  python main.py --stats
        """
    )
    parser.add_argument("--input",    help="Chemin vers le document RFP (PDF ou DOCX)")
    parser.add_argument("--output",   default="data/output_json")
    parser.add_argument("--search",   help="Requête de recherche sémantique")
    parser.add_argument("--domain",   help="Filtrer par domaine")
    parser.add_argument("--priority", help="Filtrer par priorité ESN (Haute/Normale)")
    parser.add_argument("--stats",    action="store_true")
    parser.add_argument("--db",       default="data/chroma_db")
    parser.add_argument("--n",        type=int, default=5)

    args = parser.parse_args()

    if args.input:
        run_ingestion(args.input, output_dir=args.output, db_path=args.db)
    elif args.search:
        run_search(args.search, domain=args.domain, priority=args.priority,
                   db_path=args.db, n_results=args.n)
    elif args.stats:
        run_stats(db_path=args.db)
    else:
        parser.print_help()
