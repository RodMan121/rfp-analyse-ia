"""
document_context.py — Contexte documentaire générique
======================================================
Permet de décrire n'importe quel type de document en entrée
afin que tous les agents du pipeline s'y adaptent dynamiquement.
"""

import json
import re
import os
import asyncio
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import List, Optional
from loguru import logger

# Chemin de persistance du contexte
CONTEXT_PATH = Path("data/document_context.json")


@dataclass
class DocumentContext:
    """
    Représente le contexte sémantique d'un document analysé.
    """

    raw_description: str = ""
    document_type: str = "UNKNOWN"
    domain: str = "UNKNOWN"
    language: str = "fr"
    requirement_id_pattern: str = ""
    requirement_id_example: str = ""
    content_types: List[str] = field(default_factory=list)
    extra_noise_patterns: List[str] = field(default_factory=list)
    llm_context_hint: str = ""

    @classmethod
    def from_description(cls, description: str) -> "DocumentContext":
        ctx = cls(raw_description=description)
        ctx._detect_from_text(description)
        ctx._build_llm_hint()
        logger.info(f"📄 Contexte détecté : type={ctx.document_type} | domaine={ctx.domain}")
        return ctx

    @classmethod
    async def from_description_async(cls, description: str, llm_caller=None) -> "DocumentContext":
        ctx = cls.from_description(description)
        if llm_caller is None:
            return ctx

        prompt = f"""Tu es un expert en analyse documentaire.
Un utilisateur décrit son document ainsi :
"{description}"

Analyse et retourne UNIQUEMENT ce JSON (sans markdown) :
{{
  "document_type": "RFP|CCTP|SPEC|CONTRACT|TECHNICAL_NOTE|UNKNOWN",
  "domain": "IT|INFRASTRUCTURE|METIER|JURIDIQUE|UNKNOWN",
  "language": "fr|en|mixed",
  "requirement_id_pattern": "regex Python pour les identifiants d'exigences, ex: BN-\\\\d{{3}} ou REQ-\\\\d+",
  "requirement_id_example": "ex: BN-039 ou REQ-001",
  "content_types": ["liste", "des types", "de contenu"],
  "extra_noise_patterns": ["patterns regex de bruit spécifiques"],
  "summary_for_llm": "phrase courte décrivant le document"
}}"""

        try:
            raw = await llm_caller(prompt)
            clean = raw.strip().replace("```json", "").replace("```", "").strip()
            data = json.loads(clean)
            ctx.document_type = data.get("document_type", ctx.document_type)
            ctx.domain = data.get("domain", ctx.domain)
            ctx.language = data.get("language", ctx.language)
            if data.get("requirement_id_pattern"):
                ctx.requirement_id_pattern = data["requirement_id_pattern"]
            if data.get("requirement_id_example"):
                ctx.requirement_id_example = data["requirement_id_example"]
            if data.get("content_types"):
                ctx.content_types = data["content_types"]
            if data.get("extra_noise_patterns"):
                ctx.extra_noise_patterns = data["extra_noise_patterns"]
            if data.get("summary_for_llm"):
                ctx.llm_context_hint = data["summary_for_llm"]
            ctx._build_llm_hint()
            logger.success(f"✅ Contexte LLM enrichi")
        except Exception as e:
            logger.warning(f"⚠️ Enrichissement LLM échoué ({e})")

        return ctx

    @classmethod
    def load(cls) -> Optional["DocumentContext"]:
        if not CONTEXT_PATH.exists(): return None
        with open(CONTEXT_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
        return cls(**data)

    @classmethod
    def load_or_generic(cls) -> "DocumentContext":
        ctx = cls.load()
        return ctx if ctx is not None else cls._generic()

    @classmethod
    def _generic(cls) -> "DocumentContext":
        return cls(raw_description="Générique", llm_context_hint="Extraction toute obligation.")

    def save(self):
        CONTEXT_PATH.parent.mkdir(parents=True, exist_ok=True)
        with open(CONTEXT_PATH, "w", encoding="utf-8") as f:
            json.dump(asdict(self), f, indent=2, ensure_ascii=False)

    def get_requirement_id_regex(self) -> Optional[re.Pattern]:
        if not self.requirement_id_pattern: return None
        try: return re.compile(self.requirement_id_pattern, re.IGNORECASE)
        except: return None

    def get_extra_noise_regex(self) -> Optional[re.Pattern]:
        if not self.extra_noise_patterns: return None
        try:
            combined = "|".join(f"(?:{p})" for p in self.extra_noise_patterns)
            return re.compile(combined, re.IGNORECASE)
        except: return None

    def build_babok_prompt_context(self) -> str:
        parts = [f"Contexte : {self.llm_context_hint}"]
        if self.requirement_id_example:
            parts.append(f"Identifiants type '{self.requirement_id_example}'.")
        return "\n".join(parts)

    def build_is_requirement_hint(self) -> str:
        return "is_real_requirement = false si légende, footer, note administrative."

    def _detect_from_text(self, text: str):
        lower = text.lower()
        if "rfp" in lower: self.document_type = "RFP"
        elif "cctp" in lower: self.document_type = "CCTP"
        if "bn-" in lower:
            self.requirement_id_pattern = r"BN-\d{3}(?:\\[0-9_]*)?"
            self.requirement_id_example = "BN-039"

    def _build_llm_hint(self):
        self.llm_context_hint = f"{self.document_type} {self.domain}".strip() or self.raw_description[:100]
