#!/usr/bin/env python3
import os
import asyncio
import argparse
from pathlib import Path
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt
from dotenv import load_dotenv

from phase1.local_parser import DoclingDecomposer
from phase1.vectorstore import VectorStore
from utils.factory_log import factory_logger
from document_context import DocumentContext

load_dotenv(Path(__file__).parent / ".env")
DEFAULT_DB = os.getenv("CHROMA_DB_PATH", "data/chroma_db_hierarchical")
console = Console()


async def build_context(description: str, use_llm: bool = True) -> DocumentContext:
    """Construit le DocumentContext, enrichi par LLM si disponible."""
    if use_llm:
        try:
            from phase2.micro_agents import FSMAgent

            class _TempAgent(FSMAgent):
                async def trigger(self, req): return req

            agent = _TempAgent()

            async def llm_caller(prompt: str) -> str:
                result = await agent._call_llm(prompt, format="json")
                return result.get("response", "{}")

            return await DocumentContext.from_description_async(description, llm_caller=llm_caller)
        except Exception as e:
            console.print(f"[yellow]⚠️  LLM indisponible ({e}), détection par règles.[/yellow]")

    return DocumentContext.from_description(description)


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
  python main.py --input doc.pdf \\
    --context "RFP application métier, exigences BN-XXX, schémas, maquettes fils de fer"

  python main.py --input spec.pdf \\
    --context "Cahier des charges IT, exigences REQ-XXX, pas de maquettes"

  python main.py --input doc.pdf --context-interactive

  python main.py --input doc.pdf   # extraction générique sans contexte
        """
    )
    parser.add_argument("--input", required=True, help="Chemin vers le PDF")
    parser.add_argument("--db", default=DEFAULT_DB, help="Chemin ChromaDB")
    parser.add_argument("--collection", default="rfp_hierarchical", help="Nom collection")
    parser.add_argument("--context", default=None,
                        help="Description libre du document pour guider l'extraction")
    parser.add_argument("--context-interactive", action="store_true",
                        help="Mode interactif : saisie de la description au lancement")
    parser.add_argument("--no-llm-context", action="store_true",
                        help="Détection du contexte par règles uniquement (sans LLM)")

    args = parser.parse_args()

    # --- Résolution de la description ---
    description = args.context

    if args.context_interactive and not description:
        console.print(Panel(
            "[bold yellow]📝 Décrivez le document à analyser[/bold yellow]\n\n"
            "Exemples :\n"
            "  • 'RFP application métier, exigences BN-XXX, schémas, maquettes fils de fer'\n"
            "  • 'Cahier des charges infrastructure cloud, exigences REQ-XXX'\n"
            "  • 'Contrat SLA avec clauses techniques'\n"
            "  • (vide = extraction générique)",
            border_style="yellow"
        ))
        description = Prompt.ask("[bold]Description[/bold]", default="")

    # --- Construction du contexte ---
    if description and description.strip():
        console.print("\n🔍 [cyan]Analyse du contexte documentaire...[/cyan]")
        doc_context = asyncio.run(
            build_context(description.strip(), use_llm=not args.no_llm_context)
        )
        doc_context.save()

        console.print(Panel(
            "[bold green]✅ Contexte documentaire établi[/bold green]\n\n"
            f"Type       : [bold]{doc_context.document_type}[/bold]\n"
            f"Domaine    : {doc_context.domain}\n"
            f"Langue     : {doc_context.language}\n"
            f"ID pattern : [bold]{doc_context.requirement_id_pattern or 'aucun (générique)'}[/bold]\n"
            f"Exemple ID : {doc_context.requirement_id_example or 'N/A'}\n"
            f"Contenus   : {', '.join(doc_context.content_types) or 'non spécifiés'}\n"
            f"Hint LLM   : [italic]{doc_context.llm_context_hint}[/italic]",
            border_style="green"
        ))
    else:
        console.print("[yellow]⚠️  Aucun contexte fourni — extraction générique.[/yellow]")
        doc_context = DocumentContext.load_or_generic()

    run_ingestion(
        args.input,
        db_path=args.db,
        collection_name=args.collection,
        doc_context=doc_context,
    )
