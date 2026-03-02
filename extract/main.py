#!/usr/bin/env python3
import argparse
import sys
from pathlib import Path
from loguru import logger
from rich.console import Console
from rich.panel import Panel

from phase1.local_parser import DoclingParser
from phase1.vectorstore import VectorStore

console = Console()

def run_ingestion(input_path: str, db_path: str = "data/chroma_db_hierarchical"):
    """Pipeline Hierarchical RAG."""
    console.print(Panel.fit(
        "[bold cyan]🏭 Augmented BID IA — Ingestion Hiérarchique[/bold cyan]\n"
        f"Source : {input_path}",
        border_style="cyan"
    ))

    # 1. Parsing Hiérarchique
    parser = DoclingParser()
    fragments = parser.parse_to_fragments(input_path)

    # 2. Vectorisation avec métadonnées
    store = VectorStore(db_path=db_path)
    store.add_fragments_batch(fragments)

    console.print(f"\n✅ [green]{len(fragments)} fragments indexés avec succès.[/green]")
    console.print(f"📍 Base de données : {db_path}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Ingestion Hiérarchique RFP")
    parser.add_argument("--input", required=True, help="Chemin vers le PDF")
    parser.add_argument("--db", default="data/chroma_db_hierarchical", help="Chemin ChromaDB")
    
    args = parser.parse_args()
    run_ingestion(args.input, db_path=args.db)
