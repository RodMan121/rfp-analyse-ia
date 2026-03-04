"""
document_context.py — Contexte documentaire générique
======================================================
Permet de décrire n'importe quel type de document en entrée
afin que tous les agents du pipeline s'y adaptent dynamiquement.

Usage :
    ctx = DocumentContext.from_description(
        "RFP pour une application métier. Contient des exigences normées "
        "BN-XXX, des schémas et des maquettes fils de fer."
    )
    ctx.save()   # → data/document_context.json

    ctx = DocumentContext.load()  # chargé par les agents
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
    Toutes les valeurs sont auto-déduites de la description utilisateur,
    éventuellement enrichies par LLM.
    """

    # Texte libre fourni par l'utilisateur
    raw_description: str = ""

    # Type de document détecté
    # Valeurs : RFP | CCTP | SPEC | CONTRACT | TECHNICAL_NOTE | UNKNOWN
    document_type: str = "UNKNOWN"

    # Domaine fonctionnel : IT | INFRASTRUCTURE | MÉTIER | JURIDIQUE | UNKNOWN
    domain: str = "UNKNOWN"

    # Langue principale : fr | en | mixed
    language: str = "fr"

    # Modèle regex des identifiants d'exigences (ex: r"BN-\d{3}" ou r"REQ-\d+")
    # Si vide, aucun ancrage sur identifiant officiel
    requirement_id_pattern: str = ""

    # Exemple d'identifiant pour les prompts (ex: "BN-039", "REQ-001")
    requirement_id_example: str = ""

    # Types de contenu présents dans le document
    # ex: ["exigences normées", "schémas", "maquettes fils de fer", "tableaux"]
    content_types: List[str] = field(default_factory=list)

    # Patterns de bruit supplémentaires spécifiques à ce document
    # (en plus des patterns génériques)
    extra_noise_patterns: List[str] = field(default_factory=list)

    # Contexte court pour les prompts LLM (généré automatiquement)
    llm_context_hint: str = ""

    # ------------------------------------------------------------------ #
    #  Constructeurs                                                        #
    # ------------------------------------------------------------------ #

    @classmethod
    def from_description(cls, description: str) -> "DocumentContext":
        """
        Construit un DocumentContext à partir d'une description libre.
        La détection est faite par règles (rapide, sans LLM).
        Pour une détection enrichie via LLM, utiliser `from_description_async`.
        """
        ctx = cls(raw_description=description)
        ctx._detect_from_text(description)
        ctx._build_llm_hint()
        logger.info(f"📄 Contexte détecté : type={ctx.document_type} | domaine={ctx.domain} | pattern={ctx.requirement_id_pattern or 'aucun'}")
        return ctx

    @classmethod
    async def from_description_async(cls, description: str, llm_caller=None) -> "DocumentContext":
        """
        Construit un DocumentContext enrichi par LLM.
        `llm_caller` est une coroutine async(prompt: str) -> str.
        Si None, fallback sur la détection par règles.
        """
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
  "requirement_id_pattern": "regex Python pour les identifiants d'exigences, ex: BN-\\\\d{{3}} ou REQ-\\\\d+ ou vide si aucun",
  "requirement_id_example": "ex: BN-039 ou REQ-001 ou vide",
  "content_types": ["liste", "des types", "de contenu"],
  "extra_noise_patterns": ["patterns regex de bruit spécifiques à ce type de document"],
  "summary_for_llm": "phrase courte décrivant le document pour guider l'extraction"
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
            logger.success(f"✅ Contexte LLM enrichi : {ctx.document_type} / {ctx.domain}")
        except Exception as e:
            logger.warning(f"⚠️ Enrichissement LLM échoué ({e}), contexte par règles conservé.")

        return ctx

    @classmethod
    def load(cls) -> Optional["DocumentContext"]:
        """Charge le contexte depuis data/document_context.json."""
        if not CONTEXT_PATH.exists():
            logger.warning("⚠️ Aucun contexte documentaire trouvé. Extraction générique sans guidage.")
            return None
        with open(CONTEXT_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
        ctx = cls(**data)
        logger.info(f"📂 Contexte chargé : {ctx.document_type} | {ctx.domain} | pattern={ctx.requirement_id_pattern or 'aucun'}")
        return ctx

    @classmethod
    def load_or_generic(cls) -> "DocumentContext":
        """Charge le contexte ou retourne un contexte générique neutre."""
        ctx = cls.load()
        return ctx if ctx is not None else cls._generic()

    @classmethod
    def _generic(cls) -> "DocumentContext":
        ctx = cls(
            raw_description="Document générique sans contexte spécifié.",
            document_type="UNKNOWN",
            domain="UNKNOWN",
            language="fr",
            llm_context_hint="Document dont le type est inconnu. Extraire toute obligation fonctionnelle."
        )
        return ctx

    def save(self):
        """Persiste le contexte dans data/document_context.json."""
        CONTEXT_PATH.parent.mkdir(parents=True, exist_ok=True)
        with open(CONTEXT_PATH, "w", encoding="utf-8") as f:
            json.dump(asdict(self), f, indent=2, ensure_ascii=False)
        logger.info(f"💾 Contexte sauvegardé : {CONTEXT_PATH}")

    # ------------------------------------------------------------------ #
    #  Helpers pour les agents                                             #
    # ------------------------------------------------------------------ #

    def get_requirement_id_regex(self) -> Optional[re.Pattern]:
        """Retourne le pattern regex compilé pour les IDs d'exigences, ou None."""
        if not self.requirement_id_pattern:
            return None
        try:
            return re.compile(self.requirement_id_pattern, re.IGNORECASE)
        except re.error as e:
            logger.warning(f"⚠️ Pattern ID invalide '{self.requirement_id_pattern}': {e}")
            return None

    def get_extra_noise_regex(self) -> Optional[re.Pattern]:
        """Retourne le pattern de bruit supplémentaire compilé, ou None."""
        if not self.extra_noise_patterns:
            return None
        try:
            combined = "|".join(f"(?:{p})" for p in self.extra_noise_patterns)
            return re.compile(combined, re.IGNORECASE)
        except re.error as e:
            logger.warning(f"⚠️ Pattern bruit invalide: {e}")
            return None

    def build_babok_prompt_context(self) -> str:
        """
        Construit le bloc de contexte à injecter dans le prompt BABOK.
        Adapté dynamiquement au type de document.
        """
        parts = []

        if self.llm_context_hint:
            parts.append(f"Contexte du document : {self.llm_context_hint}")

        if self.requirement_id_example:
            parts.append(
                f"Dans ce document, les exigences sont identifiées par des codes "
                f"du type '{self.requirement_id_example}'. "
                f"Extrais cet identifiant s'il est présent dans le texte."
            )
        else:
            parts.append(
                "Ce document ne semble pas avoir d'identifiants d'exigences normalisés. "
                "Identifie les obligations fonctionnelles à partir des verbes must/shall/should "
                "ou leurs équivalents français (doit, devra, il faut)."
            )

        if "maquette" in self.raw_description.lower() or "fil de fer" in self.raw_description.lower():
            parts.append(
                "Le document contient des maquettes fils de fer. "
                "Les descriptions de champs, boutons et workflows visuels "
                "constituent des exigences implicites."
            )

        if "schéma" in self.raw_description.lower() or "diagramme" in self.raw_description.lower():
            parts.append(
                "Le document contient des schémas techniques. "
                "Les relations entre composants et les flux représentés "
                "constituent des exigences d'architecture."
            )

        return "\n".join(parts) if parts else ""

    def build_is_requirement_hint(self) -> str:
        """
        Hint pour le champ is_real_requirement dans le prompt BABOK.
        """
        hints = [
            "is_real_requirement = false si le texte est : légende de figure, "
            "header/footer, note administrative, mention de confidentialité, "
            "référence bibliographique, titre de section seul."
        ]
        if self.document_type == "RFP":
            hints.append(
                "is_real_requirement = true si le texte exprime une obligation "
                "fonctionnelle, une contrainte technique ou une règle métier."
            )
        elif self.document_type == "CONTRACT":
            hints.append(
                "is_real_requirement = true si le texte exprime une obligation "
                "contractuelle, une clause ou une condition de service."
            )
        else:
            hints.append(
                "is_real_requirement = true si le texte exprime une obligation, "
                "une contrainte ou une règle claire."
            )
        return " ".join(hints)

    # ------------------------------------------------------------------ #
    #  Détection par règles                                                #
    # ------------------------------------------------------------------ #

    def _detect_from_text(self, text: str):
        """Détection heuristique à partir de la description utilisateur."""
        lower = text.lower()

        # Type de document
        if any(w in lower for w in ["rfp", "appel d'offres", "appel d offres"]):
            self.document_type = "RFP"
        elif any(w in lower for w in ["cctp", "cahier des clauses techniques", "cahier des charges"]):
            self.document_type = "CCTP"
        elif any(w in lower for w in ["contrat", "contract", "sla", "accord"]):
            self.document_type = "CONTRACT"
        elif any(w in lower for w in ["spécification", "specification", "spec ", "urd", "srd"]):
            self.document_type = "SPEC"
        elif any(w in lower for w in ["note technique", "technical note", "architecture"]):
            self.document_type = "TECHNICAL_NOTE"

        # Domaine
        if any(w in lower for w in ["application", "logiciel", "software", "web", "api", "base de données"]):
            self.domain = "IT"
        elif any(w in lower for w in ["infrastructure", "réseau", "serveur", "cloud", "hébergement"]):
            self.domain = "INFRASTRUCTURE"
        elif any(w in lower for w in ["métier", "business", "processus", "workflow"]):
            self.domain = "METIER"

        # Langue
        if any(w in lower for w in ["english", "requirement", "shall", "must"]):
            self.language = "en"
        elif any(w in lower for w in ["exigence", "doit", "devra"]):
            self.language = "fr"

        # Détection automatique du pattern d'identifiants
        # Cherche des patterns du type "BN-XXX", "REQ-XXX", "F-XXX", etc.
        id_hint = re.search(r'\b([A-Z]{1,6}[-_]\d{2,4})\b', text)
        if id_hint:
            prefix = re.match(r'([A-Z]{1,6})', id_hint.group(1)).group(1)
            sep = '-' if '-' in id_hint.group(1) else '_'
            digits = len(re.search(r'\d+', id_hint.group(1)).group(0))
            self.requirement_id_pattern = rf"{prefix}{re.escape(sep)}\d{{{digits}}}"
            self.requirement_id_example = id_hint.group(1)
        elif any(w in lower for w in ["bn-", "bn "]):
            self.requirement_id_pattern = r"BN-\d{3}(?:\\[0-9_]*)?"
            self.requirement_id_example = "BN-039"
        elif any(w in lower for w in ["req-", "req "]):
            self.requirement_id_pattern = r"REQ-\d+"
            self.requirement_id_example = "REQ-001"

        # Types de contenu
        if any(w in lower for w in ["maquette", "fil de fer", "wireframe", "mockup"]):
            self.content_types.append("maquettes fils de fer")
        if any(w in lower for w in ["schéma", "schema", "diagramme", "diagram"]):
            self.content_types.append("schémas")
        if any(w in lower for w in ["tableau", "table", "matrice", "matrix"]):
            self.content_types.append("tableaux")
        if any(w in lower for w in ["exigence normée", "exigences normées", "bn-", "req-"]):
            self.content_types.append("exigences normées")

    def _build_llm_hint(self):
        """Construit le hint court pour les prompts LLM."""
        parts = []
        if self.document_type != "UNKNOWN":
            parts.append(self.document_type)
        if self.domain != "UNKNOWN":
            parts.append(f"domaine {self.domain}")
        if self.content_types:
            parts.append(f"contenant {', '.join(self.content_types)}")
        if self.requirement_id_example:
            parts.append(f"avec identifiants type '{self.requirement_id_example}'")
        self.llm_context_hint = " — ".join(parts) if parts else self.raw_description[:120]
