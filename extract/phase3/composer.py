import os
import sys
import ollama
import json
import hashlib
import datetime
from pathlib import Path
from loguru import logger
from typing import List, Dict, Any
from dataclasses import dataclass, asdict
from dotenv import load_dotenv

# Fix pour les imports
sys.path.append(str(Path(__file__).parent.parent))
from phase2.micro_agents import FSMRequirement, RequirementState
from utils.factory_log import factory_logger

# Configuration
env_path = Path(__file__).parent.parent / ".env"
load_dotenv(env_path)


@dataclass
class TechnicalBaseline:
    project_uid: str
    timestamp: str
    requirements_count: int
    validated_requirements: List[Dict]
    moscow_matrix: Dict[str, List[Any]]
    integrity_score: int
    state: str = "BASELINE"


class ArchitectureComposer:
    def __init__(self, model: Optional[str] = None):
        self.model = model or os.getenv("OLLAMA_TEXT_MODEL", "qwen2.5:7b")

    def _clean_json(self, raw_resp: str) -> Dict:
        try:
            clean = raw_resp.strip()
            if "```json" in clean:
                clean = clean.split("```json")[1].split("```")[0]
            elif "```" in clean:
                clean = clean.split("```")[1].split("```")[0]
            return json.loads(clean)
        except Exception:
            return {}

    def load_registry(self) -> List[FSMRequirement]:
        """Charge les exigences depuis le registre JSON de la Phase 2."""
        path = Path("data/fsm_registry.json")
        if not path.exists():
            logger.error("❌ Registre FSM introuvable. Lancez la Phase 2 d'abord.")
            return []
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        reqs = []
        for d in data:
            state_val = d.pop("state")
            r = FSMRequirement(**d)
            r.state = RequirementState(state_val)
            reqs.append(r)
        return reqs

    def assemble_baseline(
        self, audited_requirements: List[FSMRequirement]
    ) -> TechnicalBaseline:
        """Réassemble les fragments AUDITED en une Baseline immuable (JSON + MD)."""
        factory_logger.log_event(
            "PHASE_3", "START", "Début de la certification de la Baseline."
        )

        final_set = [
            r for r in audited_requirements if r.state == RequirementState.AUDITED
        ]
        if not final_set:
            factory_logger.log_event(
                "PHASE_3", "ERROR", "Aucune exigence validée à certifier."
            )
            logger.warning("⚠️ Aucune exigence validée à certifier.")
            return None

        # 1. MoSCoW
        moscow_data = self._construct_moscow(final_set)

        # 2. Scoring
        integrity_data = self._scoring_integrity(moscow_data)

        serializable_reqs = []
        for r in final_set:
            r.transition_to(RequirementState.BASELINE, "Certification finale")
            req_dict = asdict(r)
            req_dict["state"] = r.state.value
            serializable_reqs.append(req_dict)

        project_signature = hashlib.md5(
            json.dumps(serializable_reqs).encode()
        ).hexdigest()

        baseline = TechnicalBaseline(
            project_uid=f"ALM-{project_signature[:12].upper()}",
            timestamp=datetime.datetime.now().isoformat(),
            requirements_count=len(final_set),
            validated_requirements=serializable_reqs,
            moscow_matrix=moscow_data,
            integrity_score=integrity_data.get("score", 3),
        )
        self._export_json(baseline)
        self._export_markdown(baseline)

        factory_logger.log_event(
            "PHASE_3",
            "COMPLETED",
            f"Baseline {baseline.project_uid} générée.",
            {
                "uid": baseline.project_uid,
                "req_count": baseline.requirements_count,
                "integrity": baseline.integrity_score,
            },
        )
        return baseline

    def _export_json(self, baseline: TechnicalBaseline):
        output_path = Path("data/technical_baseline_alm.json")
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(asdict(baseline), f, indent=2, ensure_ascii=False)
        logger.success(f"💾 JSON certifié : {output_path}")

    def _export_markdown(self, baseline: TechnicalBaseline):
        """Génère le document de Technical Baseline pour les humains (Traçabilité BABOK)."""
        output_path = Path("data/technical_baseline_final.md")
        md = f"# 📦 Technical Baseline — Projet {baseline.project_uid}\n\n"
        md += f"**Date de certification :** {baseline.timestamp}\n"
        md += f"**Nombre d'exigences certifiées :** {baseline.requirements_count}\n"
        md += f"**Score d'intégrité système :** {baseline.integrity_score}/5\n\n"

        md += "## 🎯 Matrice de Priorisation (MoSCoW)\n\n"
        for prio in ["Must", "Should", "Could", "Won't"]:
            md += f"### {prio}\n"
            reqs = baseline.moscow_matrix.get(prio, [])
            if not reqs:
                md += "_Aucune exigence._\n"
            else:
                for r in reqs:
                    text = r.get("exigence", r) if isinstance(r, dict) else r
                    md += f"- {text}\n"
            md += "\n"

        md += "## 📋 Catalogue des Exigences Certifiées (Traçabilité Totale)\n\n"
        md += "| UID | Structure BABOK | Citation Source | Page / Section | Historique FSM |\n"
        md += "|:---:|---|---|---|---|\n"

        for r in baseline.validated_requirements:
            hist = " ➔ ".join([h.split(" (")[0] for h in r["state_history"]])
            babok = f"**{r.get('subject', '?')}** {r.get('action', '?')} {r.get('target_object', '?')} *({r.get('constraint', '')})*"
            quote = f"« {r.get('source_quote', 'N/A')} »"
            meta = f"P.{r['metadata'].get('page', '?')} ({r['metadata'].get('breadcrumbs', '?')})"
            md += f"| {r['uid'][:8]} | {babok} | {quote} | {meta} | {hist} |\n"

        with open(output_path, "w", encoding="utf-8") as f:
            f.write(md)
        logger.success(f"📄 Markdown certifié avec traçabilité : {output_path}")

    def _construct_moscow(self, requirements: List[FSMRequirement]) -> Dict:
        req_texts = [{"id": r.uid[:5], "text": r.original_text} for r in requirements]
        prompt = f"Expert MoSCoW: Priorise ces exigences JSON : {json.dumps(req_texts)}"
        try:
            resp = ollama.generate(model=self.model, prompt=prompt, format="json")
            return self._clean_json(resp.get("response", "{}"))
        except Exception:
            return {"Must": [], "Should": [], "Could": [], "Won't": []}

    def _scoring_integrity(self, matrix_data: Dict) -> Dict:
        prompt = (
            f"Expert TOGAF: Score l'intégrité (1-5) JSON : {json.dumps(matrix_data)}"
        )
        try:
            resp = ollama.generate(model=self.model, prompt=prompt, format="json")
            return json.loads(resp.get("response", "{}"))
        except Exception:
            return {"score": 3}


if __name__ == "__main__":
    composer = ArchitectureComposer()
    audited_reqs = composer.load_registry()
    if audited_reqs:
        composer.assemble_baseline(audited_reqs)
