import os
import sys
from pathlib import Path
from loguru import logger
from rich.console import Console
from rich.progress import Progress
from dotenv import load_dotenv

# Fix pour les imports
sys.path.append(str(Path(__file__).parent))
load_dotenv(Path(__file__).parent / ".env")

from phase1.vectorstore import VectorStore  # noqa: E402
from phase2.micro_agents import FSMPipeline, RequirementState  # noqa: E402
from utils.factory_log import factory_logger  # noqa: E402

console = Console()


class RequirementHarvester:
    """Moissonneur industriel d'exigences (Texte & Vision)."""

    def __init__(self, db_path: str = "data/chroma_db_hierarchical"):
        self.store = VectorStore(db_path=db_path)
        self.pipeline = FSMPipeline()
        self.image_dir = Path(os.getenv("OUTPUT_IMAGE_DIR", "data/output_images"))

    def harvest_all(self, collection: str = "rfp_hierarchical"):
        """Scanne tout le document pour extraire et traiter chaque exigence."""
        factory_logger.log_event(
            "HARVEST", "START", f"Moissonnage complet de la collection: {collection}"
        )

        # 1. Récupération de TOUS les fragments du document
        # On utilise une recherche large pour tout remonter
        all_fragments = self.store.collection.get()
        documents = all_fragments.get("documents", [])
        metadatas = all_fragments.get("metadatas", [])
        ids = all_fragments.get("ids", [])

        logger.info(f"🚜 Moissonnage de {len(documents)} fragments...")

        fsm_objects = []
        with Progress() as progress:
            task = progress.add_task("[green]Moissonnage...", total=len(documents))

            for doc, meta, fid in zip(documents, metadatas, ids):
                # On ne traite que les fragments qui ressemblent à des exigences
                # (L'agent BABOK fera le tri final)
                if len(doc) < 40:
                    progress.update(task, advance=1)
                    continue

                # Passage dans l'usine FSM (BABOK -> Radar)
                fsm_data = self.pipeline.run_factory(doc, uid=fid, metadata=meta)

                # On ne garde que les exigences qui ont au moins été normalisées
                if fsm_data.state != RequirementState.ERROR:
                    fsm_objects.append(fsm_data)

                progress.update(task, advance=1)

        # 2. Sauvegarde du registre pour Phase 3
        self._save_registry(fsm_objects)
        factory_logger.log_event(
            "HARVEST", "COMPLETED", f"{len(fsm_objects)} exigences identifiées."
        )
        logger.success(
            f"✅ Moissonnage terminé : {len(fsm_objects)} exigences en attente de certification."
        )

    def _save_registry(self, fsm_requirements):
        import json
        from dataclasses import asdict

        output_path = Path("data/fsm_registry.json")
        serializable = []
        for r in fsm_requirements:
            d = asdict(r)
            d["state"] = r.state.value
            serializable.append(d)
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(serializable, f, indent=2, ensure_ascii=False)


if __name__ == "__main__":
    harvester = RequirementHarvester()
    harvester.harvest_all()
