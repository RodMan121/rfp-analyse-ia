import os
import sys
import ollama
import json
import hashlib
import datetime
import asyncio
import time
from pathlib import Path
from loguru import logger
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, asdict
from dotenv import load_dotenv
from google import genai
from openai import AsyncOpenAI

# Fix pour les imports
sys.path.append(str(Path(__file__).parent.parent))
from phase2.micro_agents import FSMRequirement, RequirementState
from utils.factory_log import factory_logger

# Configuration
env_path = Path(__file__).parent.parent / ".env"
load_dotenv(env_path)

TEXT_MODEL = os.getenv("OLLAMA_TEXT_MODEL", "llama3.2:3b")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.0-flash")

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
        or_key = os.getenv("OPENROUTER_API_KEY")
        api_key = os.getenv("GOOGLE_API_KEY")
        
        if or_key and len(or_key) > 10:
            self.model = model or os.getenv("OPENROUTER_MODEL", "google/gemini-2.0-flash-001")
            self.client_or = AsyncOpenAI(base_url="https://openrouter.ai/api/v1", api_key=or_key)
            self.mode = "OPENROUTER"
        elif api_key and len(api_key) > 10 and "your_google" not in api_key:
            self.model = model or GEMINI_MODEL
            self.client_gemini = genai.Client(api_key=api_key)
            self.mode = "GEMINI"
        else:
            self.model = model or TEXT_MODEL
            self.mode = "OLLAMA"
            self.async_ollama = ollama.AsyncClient()

    async def _call_llm(self, prompt: str, format: str = "json") -> Dict:
        """FIX P2.7 : Unification du mécanisme de retry."""
        max_retries = 3
        for attempt in range(max_retries):
            try:
                if self.mode == "OPENROUTER":
                    response = await self.client_or.chat.completions.create(
                        model=self.model,
                        messages=[{"role": "user", "content": prompt}],
                        response_format={"type": "json_object"} if format == "json" else None,
                        timeout=30.0
                    )
                    return {"response": response.choices[0].message.content}
                elif self.mode == "GEMINI":
                    config = {"response_mime_type": "application/json"} if format == "json" else {}
                    response = await self.client_gemini.aio.models.generate_content(model=self.model, contents=prompt, config=config)
                    return {"response": response.text}
                else:
                    response = await self.async_ollama.generate(model=self.model, prompt=prompt, format=format if format == "json" else None, options={"num_ctx": 2048, "temperature": 0.1})
                    return {"response": response.get("response", "{}")}
            except Exception as e:
                delay = 5 * (attempt + 1) if "429" in str(e) else 2 * (attempt + 1)
                await asyncio.sleep(delay)
        return {"response": "{}"}

    def _clean_json(self, raw_resp: str) -> Dict:
        try:
            clean = raw_resp.strip()
            if "```json" in clean: clean = clean.split("```json")[1].split("```")[0]
            elif "```" in clean: clean = clean.split("```")[1].split("```")[0]
            return json.loads(clean)
        except Exception: return {}

    def load_registry(self) -> List[FSMRequirement]:
        path = Path("data/fsm_registry.json")
        if not path.exists(): return []
        with open(path, "r", encoding="utf-8") as f: data = json.load(f)
        reqs = []
        for d in data:
            # FIX P2.4 : Ne pas muter le dict original avec pop()
            d_copy = {k: v for k, v in d.items() if k != "state"}
            r = FSMRequirement(**d_copy)
            r.state = RequirementState(d["state"])
            reqs.append(r)
        return reqs

    async def assemble_baseline(self, audited_requirements: List[FSMRequirement]) -> TechnicalBaseline:
        # On accepte CLEAN, NORMALIZED et AUDITED (nouvel état v9)
        final_set = [r for r in audited_requirements if r.state in [RequirementState.CLEAN, RequirementState.NORMALIZED, RequirementState.AUDITED] and len(r.source_quote) > 5]
        
        # FIX P2.6 : Log explicite en cas d'absence d'exigences
        if not final_set:
            logger.error("🚫 Échec certification : Aucune exigence validée (CLEAN/NORMALIZED/AUDITED) trouvée.")
            return None

        # 1. MoSCoW
        moscow_data = {"Must": [], "Should": [], "Could": [], "Won't": []}
        batch_size = 10
        for i in range(0, min(len(final_set), 50), batch_size):
            batch = final_set[i:i+batch_size]
            partial_moscow = await self._construct_moscow(batch)
            for key in moscow_data:
                moscow_data[key].extend(partial_moscow.get(key, []))

        # 2. Scoring d'intégrité
        integrity_data = await self._scoring_integrity(moscow_data)

        serializable_reqs = []
        for r in final_set:
            r.transition_to(RequirementState.BASELINE, "Certification finale")
            req_dict = asdict(r)
            req_dict["state"] = r.state.value
            serializable_reqs.append(req_dict)

        project_signature = hashlib.md5(json.dumps(serializable_reqs).encode()).hexdigest()
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
        logger.success(f"📦 Baseline {baseline.project_uid} certifiée avec succès.")
        return baseline

    def _export_json(self, baseline: TechnicalBaseline):
        output_path = Path("data/technical_baseline_alm.json")
        with open(output_path, "w", encoding="utf-8") as f: json.dump(asdict(baseline), f, indent=2, ensure_ascii=False)

    def _export_markdown(self, baseline: TechnicalBaseline):
        output_path = Path("data/technical_baseline_final.md")
        md = f"# 📦 Technical Baseline — Projet {baseline.project_uid}\n\n"
        md += f"**Date de certification :** {baseline.timestamp}\n"
        md += f"**Nombre d'exigences certifiées :** {baseline.requirements_count}\n"
        md += f"**Score d'intégrité système :** {baseline.integrity_score}/5\n\n"
        md += "## 🎯 Matrice de Priorisation (MoSCoW)\n\n"
        for prio in ["Must", "Should", "Could", "Won't"]:
            md += f"### {prio}\n"
            reqs = baseline.moscow_matrix.get(prio, [])
            if not reqs: md += "_Aucune exigence._\n"
            else:
                for r in reqs:
                    text = r.get("exigence", r) if isinstance(r, dict) else r
                    md += f"- {text}\n"
            md += "\n"
        md += "## 📋 Catalogue des Exigences Certifiées\n\n"
        md += "| UID | Structure BABOK | Citation Source | Page / Section | Historique FSM |\n"
        md += "|:---:|---|---|---|---|\n"
        for r in baseline.validated_requirements:
            hist = " ➔ ".join([h.split(" (")[0] for h in r["state_history"]])
            babok = f"**{r.get('subject', '?')}** {r.get('action', '?')} {r.get('target_object', '?')}"
            quote = f"« {r.get('source_quote', 'N/A')} »"
            meta = f"P.{r['metadata'].get('page', '?')} ({r['metadata'].get('breadcrumbs', '?')})"
            md += f"| {r['uid'][:8]} | {babok} | {quote} | {meta} | {hist} |\n"
        with open(output_path, "w", encoding="utf-8") as f: f.write(md)

    async def _construct_moscow(self, batch: List[FSMRequirement]) -> Dict:
        req_texts = [{"id": r.uid[:5], "text": r.source_quote} for r in batch]
        prompt = f"Expert MoSCoW: Classe ces exigences techniques en JSON (Must, Should, Could, Won't) : {json.dumps(req_texts)}"
        resp = await self._call_llm(prompt=prompt, format="json")
        return self._clean_json(resp.get("response", "{}"))

    async def _scoring_integrity(self, matrix_data: Dict) -> Dict:
        prompt = f"Expert TOGAF: Analyse la cohérence de cette matrice et donne un score (1-5) JSON : {json.dumps(matrix_data)}"
        resp = await self._call_llm(prompt=prompt, format="json")
        return self._clean_json(resp.get("response", "{}"))

async def main():
    composer = ArchitectureComposer()
    audited_reqs = composer.load_registry()
    if audited_reqs: await composer.assemble_baseline(audited_reqs)

if __name__ == "__main__":
    asyncio.run(main())
