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
        # Lit data/document_context.md et adapte le pipeline au document
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

        # --- DÉDUPLICATION v14 : par ID officiel en priorité, puis par citation normalisée ---
        #
        # Stratégie à deux niveaux :
        #   Niveau 1 — ID officiel : si deux exigences partagent le même BN-XXX ou IT_REQ-XXX,
        #              on garde celle dont la citation_source est la plus longue (la plus complète).
        #   Niveau 2 — Citation normalisée : pour les exigences sans ID, on déduplique
        #              par similarité de préfixe sur les 120 premiers caractères normalisés.
        #              Deux citations dont le préfixe à 80 chars est identique → doublon.

        # Étape 1 : regrouper par ID officiel, garder la citation la plus longue
        by_id: dict = {}
        no_id_list = []
        for r in fsm_objects:
            oid = (r.metadata.get("official_id") or "").strip().upper()
            if oid and oid not in ("NULL", "AUCUN", "BN-XXX"):
                if oid not in by_id:
                    by_id[oid] = r
                else:
                    # Garder la plus longue citation (plus informative)
                    if len(r.source_quote) > len(by_id[oid].source_quote):
                        logger.debug(f"♻️ Doublon ID {oid} : remplacement par citation plus longue")
                        by_id[oid] = r
                    else:
                        logger.debug(f"♻️ Doublon ID {oid} : citation courte ignorée")
            else:
                no_id_list.append(r)

        # Étape 2 : dédupliquer les sans-ID par préfixe de citation (80 chars)
        seen_prefix: dict = {}
        unique_no_id = []
        for r in no_id_list:
            prefix = " ".join(r.source_quote.lower().split())[:80]
            if not prefix or len(prefix) < 15:
                continue  # Citation trop courte = bruit résiduel
            if prefix in seen_prefix:
                logger.debug(f"♻️ Doublon citation [{r.uid[:8]}] ≈ [{seen_prefix[prefix][:8]}]")
                continue
            seen_prefix[prefix] = r.uid
            unique_no_id.append(r)

        deduplicated = list(by_id.values()) + unique_no_id

        nb_id_dedup = len(fsm_objects) - len(by_id) - len(no_id_list) + (len(no_id_list) - len(unique_no_id))
        logger.info(
            f"🧹 Déduplication v14 : {len(fsm_objects)} → {len(deduplicated)} exigences uniques "
            f"({len(by_id)} avec ID officiel, {len(unique_no_id)} sans ID, {nb_id_dedup} doublons supprimés)"
        )
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
