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

console = Console()

# Limite de concurrence optimale pour 4Go de VRAM
MAX_CONCURRENT_REQUESTS = 2

class RequirementHarvester:
    def __init__(self, db_path: str = "data/chroma_db_hierarchical"):
        self.store = VectorStore(db_path=db_path)
        self.pipeline = FSMPipeline()

    async def _process_single_fragment(self, doc, meta, fid, semaphore, progress, task):
        """Traite un fragment unique à travers la FSM (Async)."""
        async with semaphore:
            if len(doc) < 40:
                progress.update(task, advance=1)
                return None
            
            try:
                # Appel asynchrone à l'usine
                fsm_data = await self.pipeline.run_factory(doc, uid=fid, metadata=meta)
                progress.update(task, advance=1)
                
                if fsm_data.state != RequirementState.ERROR:
                    return fsm_data
            except Exception as e:
                logger.error(f"❌ Erreur fragment {fid}: {e}")
                progress.update(task, advance=1)
            
            return None

    async def harvest_all(self, collection: str = "rfp_hierarchical"):
        """Moissonnage asynchrone ultra-rapide."""
        factory_logger.log_event("HARVEST", "START", "Lancement moissonnage ASYNC.")
        
        all_fragments = self.store.collection.get()
        documents = all_fragments.get("documents", [])
        metadatas = all_fragments.get("metadatas", [])
        ids = all_fragments.get("ids", [])

        logger.info(f"🚜 Moissonnage ASYNC de {len(documents)} fragments (Concurrence: {MAX_CONCURRENT_REQUESTS})...")

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
            
            # Création de toutes les tâches
            jobs = [
                self._process_single_fragment(doc, meta, fid, semaphore, progress, task)
                for doc, meta, fid in zip(documents, metadatas, ids)
            ]
            
            # Exécution concurrente
            results = await asyncio.gather(*jobs)

        # Filtrage des résultats
        fsm_objects = [r for r in results if r is not None]
        
        self._save_registry(fsm_objects)
        logger.success(f"✅ Moissonnage ASYNC terminé : {len(fsm_objects)} exigences en attente.")

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
