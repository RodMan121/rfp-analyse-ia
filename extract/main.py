#!/usr/bin/env python3
import os
import argparse
from pathlib import Path
from rich.console import Console
from rich.panel import Panel
from dotenv import load_dotenv

from phase1.local_parser import DoclingDecomposer
from phase1.vectorstore import VectorStore
from utils.factory_log import factory_logger
from document_context import DocumentContext

load_dotenv(Path(__file__).parent / ".env")
DEFAULT_DB = os.getenv("CHROMA_DB_PATH", "data/chroma_db_hierarchical")
console = Console()


def run_ingestion(
    input_path: str,
    db_path: str = None,
    collection_name: str = "rfp_hierarchical",
    doc_context: DocumentContext = None,
):
    """Pipeline Phase 1 : Dissocier."""
    factory_logger.log_event("PHASE_1", "START", f"Début ingestion : {input_path}")
    db_path = db_path or DEFAULT_DB

    ctx_line = ""
    if doc_context:
        ctx_line = (
            f"\nContexte : [bold]{doc_context.document_type}[/bold] | "
            f"{doc_context.domain} | "
            f"Pattern ID : {doc_context.requirement_id_pattern or 'générique'}"
        )

    console.print(Panel.fit(
        "[bold cyan]🏭 Augmented BID IA — Phase 1 : Dissocier[/bold cyan]\n"
        f"Source : {input_path}\n"
        f"Collection : {collection_name}"
        f"{ctx_line}",
        border_style="cyan",
    ))

    decomposer = DoclingDecomposer(doc_context=doc_context)
    fragments = decomposer.decompose(input_path)

    store = VectorStore(db_path=db_path, collection_name=collection_name)
    store.add_fragments_batch(fragments)

    factory_logger.log_event("PHASE_1", "COMPLETED", f"{len(fragments)} fragments indexés.")
    console.print(f"\n✅ [green]{len(fragments)} fragments atomiques indexés.[/green]")
    console.print(f"📍 Collection : {collection_name} | Base : {db_path}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Ingestion & Décomposition — Pipeline générique",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemples :
  # Première utilisation : générer le template à compléter
  python main.py --init-context

  # Lancement normal (lit data/document_context.md automatiquement)
  python main.py --input ESSP-RD-40001.pdf

  # Pointer vers un fichier .md spécifique
  python main.py --input doc.pdf --context-file mon_contexte.md

  # Sans contexte (extraction générique)
  python main.py --input doc.pdf
        """
    )
    parser.add_argument("--input", required=False, help="Chemin vers le PDF")
    parser.add_argument("--db", default=DEFAULT_DB, help="Chemin ChromaDB")
    parser.add_argument("--collection", default="rfp_hierarchical", help="Nom collection")
    parser.add_argument(
        "--context-file", default=None,
        help="Chemin vers le fichier .md décrivant le document "
             "(défaut : data/document_context.md s'il existe)"
    )
    parser.add_argument(
        "--init-context", action="store_true",
        help="Génère un template data/document_context.md vide à compléter"
    )

    args = parser.parse_args()

    # --- Option : générer le template vide ---
    if args.init_context:
        DocumentContext.create_template()
        console.print(Panel(
            "[bold green]✅ Template créé : data/document_context.md[/bold green]\n\n"
            "Complétez ce fichier en texte libre,\n"
            "puis relancez sans [bold]--init-context[/bold].",
            border_style="green"
        ))
        import sys; sys.exit(0)

    if not args.input:
        parser.error("--input est requis sauf avec --init-context")

    # --- Chargement du contexte ---
    # Priorité 1 : fichier .md explicite via --context-file
    if args.context_file:
        doc_context = DocumentContext.from_file(args.context_file)
    # Priorité 2 : data/document_context.md par défaut (si présent)
    else:
        doc_context = DocumentContext.load_or_generic()

    console.print(Panel(
        "[bold green]✅ Contexte documentaire actif[/bold green]\n\n"
        f"Type       : [bold]{doc_context.document_type}[/bold]\n"
        f"Domaine    : {doc_context.domain}\n"
        f"Langue     : {doc_context.language}\n"
        f"ID pattern : [bold]{doc_context.requirement_id_pattern or 'aucun (générique)'}[/bold]\n"
        f"Exemple ID : {doc_context.requirement_id_example or 'N/A'}\n"
        f"Contenus   : {', '.join(doc_context.content_types) or 'non spécifiés'}\n"
        f"Hint LLM   : [italic]{doc_context.llm_context_hint[:120]}[/italic]",
        border_style="green"
    ))

    run_ingestion(
        args.input,
        db_path=args.db,
        collection_name=args.collection,
        doc_context=doc_context,
    )
