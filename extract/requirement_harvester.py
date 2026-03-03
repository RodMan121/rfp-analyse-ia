import os
import sys
import asyncio
import json
from pathlib import Path
from loguru import logger
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TimeElapsedColumn
from dataclasses import asdict
from dotenv import load_dotenv

# Fix pour les imports
sys.path.append(str(Path(__file__).parent))
load_dotenv(Path(__file__).parent / ".env")

from phase1.vectorstore import VectorStore
from phase2.micro_agents import FSMPipeline, RequirementState
from utils.factory_log import factory_logger
from document_context import DocumentContext

console = Console()

OR_KEY = os.getenv("OPENROUTER_API_KEY")
FSM_CONCURRENT = int(os.getenv("FSM_CONCURRENT_REQUESTS", "2"))
MAX_CONCURRENT_REQUESTS = 20 if (OR_KEY and len(OR_KEY) > 10) else FSM_CONCURRENT

class RequirementHarvester:
    def __init__(self, db_path: str = "data/chroma_db_hierarchical"):
        self.store = VectorStore(db_path=db_path)
        # Charge le contexte documentaire (généré lors de l'ingestion main.py)
        doc_context = DocumentContext.load_or_generic()
        self.pipeline = FSMPipeline(doc_context=doc_context)

    async def _process_single_fragment(self, doc, meta, fid, semaphore, progress, task):
        async with semaphore:
            try:
                fsm_data = await self.pipeline.run_factory(doc, uid=fid, metadata=meta)
                progress.update(task, advance=1)
                return fsm_data
            except Exception as e:
                logger.error(f"❌ Erreur fragment {fid}: {e}")
                progress.update(task, advance=1)
            return None

    async def harvest_all(self, collection: str = "rfp_hierarchical"):
        """Moissonnage asynchrone avec contexte documentaire."""
        factory_logger.log_event("HARVEST", "START", "Lancement moissonnage v12.")
        
        try:
            target_col = self.store.client.get_collection(collection)
            all_fragments = target_col.get()
        except Exception:
            all_fragments = self.store.collection.get()
            
        documents = all_fragments.get("documents", [])
        metadatas = all_fragments.get("metadatas", [])
        ids = all_fragments.get("ids", [])

        logger.info(f"🚜 Moissonnage ASYNC de {len(documents)} fragments...")

        semaphore = asyncio.Semaphore(MAX_CONCURRENT_REQUESTS)
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            TimeElapsedColumn(),
            console=console
        ) as progress:
            task = progress.add_task("[green]Usine FSM...", total=len(documents))
            jobs = [
                self._process_single_fragment(doc, meta, fid, semaphore, progress, task)
                for doc, meta, fid in zip(documents, metadatas, ids)
            ]
            results = await asyncio.gather(*jobs)

        # Logique de déduplication sémantique
        fsm_objects = [r for r in results if r is not None and r.state != RequirementState.ERROR]
        
        seen_quotes = {}
        deduplicated = []
        for r in fsm_objects:
            quote_key = " ".join(r.source_quote.lower().split())[:150]
            if not quote_key: continue
            if quote_key in seen_quotes:
                logger.debug(f"♻️ Doublon éliminé [{r.uid[:8]}]")
                continue
            seen_quotes[quote_key] = r.uid
            deduplicated.append(r)

        logger.info(f"🧹 Déduplication : {len(fsm_objects)} → {len(deduplicated)} exigences uniques")
        self._save_registry(deduplicated)
        logger.success(f"✅ Moissonnage terminé : {len(deduplicated)} exigences en attente.")

    def _save_registry(self, fsm_requirements):
        output_path = Path("data/fsm_registry.json")
        serializable = []
        for r in fsm_requirements:
            d = asdict(r)
            d["state"] = r.state.value
            serializable.append(d)
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(serializable, f, indent=2, ensure_ascii=False)

async def main():
    harvester = RequirementHarvester()
    await harvester.harvest_all()

if __name__ == "__main__":
    asyncio.run(main())
