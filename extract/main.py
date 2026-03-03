#!/usr/bin/env python3
import os
import argparse
from pathlib import Path
from loguru import logger
from rich.console import Console
from rich.panel import Panel
from dotenv import load_dotenv

from phase1.local_parser import DoclingParser
from phase1.vectorstore import VectorStore

# Chargement config
load_dotenv(Path(__file__).parent / ".env")
DEFAULT_DB = os.getenv("CHROMA_DB_PATH", "data/chroma_db_hierarchical")

console = Console()

def run_ingestion(input_path: str, db_path: str = None, collection_name: str = "rfp_hierarchical"):
    """Pipeline Hierarchical RAG."""
    db_path = db_path or DEFAULT_DB
    console.print(Panel.fit(
        "[bold cyan]🏭 Augmented BID IA — Ingestion Hiérarchique[/bold cyan]\n"
        f"Source : {input_path}\n"
        f"Collection : {collection_name}",
        border_style="cyan"
    ))

    # 1. Parsing Hiérarchique & Sémantique
    parser = DoclingParser()
    fragments = parser.parse_to_fragments(input_path)

    # 2. Vectorisation avec métadonnées et multi-collections
    store = VectorStore(db_path=db_path, collection_name=collection_name)
    store.add_fragments_batch(fragments)

    console.print(f"\n✅ [green]{len(fragments)} fragments indexés avec succès dans '{collection_name}'.[/green]")
    console.print(f"📍 Base de données : {db_path}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Ingestion Hiérarchique RFP")
    parser.add_argument("--input", required=True, help="Chemin vers le PDF")
    parser.add_argument("--db", default=DEFAULT_DB, help="Chemin ChromaDB")
    parser.add_argument("--collection", default="rfp_hierarchical", help="Nom de la collection")
    
    args = parser.parse_args()
    run_ingestion(args.input, db_path=args.db, collection_name=args.collection)
