"""
document_context.py — Contexte documentaire générique
======================================================
Permet de décrire n'importe quel type de document en entrée
afin que tous les agents du pipeline s'y adaptent dynamiquement.

L'utilisateur écrit un fichier texte libre : data/document_context.md
Le pipeline le lit directement — pas de JSON, pas d'étape intermédiaire.

Usage :
    # Générer le template vide
    python main.py --init-context

    # Compléter data/document_context.md en texte libre, puis lancer
    python main.py --input mon_doc.pdf
"""

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional
from loguru import logger

# Fichier texte libre écrit par l'utilisateur — seule source de vérité
CONTEXT_MD_PATH = Path("data/document_context.md")


@dataclass
class DocumentContext:
    """
    Contexte sémantique d'un document analysé.
    Toutes les valeurs sont auto-déduites du fichier document_context.md.
    """

    # Texte brut lu dans le .md
    raw_description: str = ""

    # Type de document : RFP | CCTP | SPEC | CONTRACT | TECHNICAL_NOTE | UNKNOWN
    document_type: str = "UNKNOWN"

    # Domaine : IT | INFRASTRUCTURE | METIER | JURIDIQUE | UNKNOWN
    domain: str = "UNKNOWN"

    # Langue : fr | en | mixed
    language: str = "fr"

    # Regex des identifiants d'exigences (ex: r"BN-\d{3}" ou r"REQ-\d+")
    requirement_id_pattern: str = ""

    # Exemple d'identifiant pour les prompts (ex: "BN-039", "REQ-001")
    requirement_id_example: str = ""

    # Types de contenu détectés (ex: ["exigences normées", "schémas", "maquettes"])
    content_types: List[str] = field(default_factory=list)

    # Patterns de bruit supplémentaires spécifiques à ce document
    extra_noise_patterns: List[str] = field(default_factory=list)

    # Hint court injecté dans les prompts LLM (généré automatiquement)
    llm_context_hint: str = ""

    # ------------------------------------------------------------------ #
    #  Constructeurs                                                        #
    # ------------------------------------------------------------------ #

    @classmethod
    def from_file(cls, path: str = None) -> "DocumentContext":
        """
        Construit un DocumentContext depuis un fichier texte libre.
        Si path est None, utilise data/document_context.md par défaut.
        """
        target = Path(path) if path else CONTEXT_MD_PATH
        if not target.exists():
            logger.warning(f"⚠️ Fichier contexte introuvable : {target} — extraction générique.")
            return cls._generic()
        with open(target, "r", encoding="utf-8") as f:
            description = f.read().strip()
        if not description:
            logger.warning("⚠️ Fichier contexte vide — extraction générique.")
            return cls._generic()
        logger.info(f"📄 Contexte lu depuis : {target.name} ({len(description)} chars)")
        ctx = cls(raw_description=description)
        ctx._detect_from_text(description)
        ctx._build_llm_hint()
        return ctx

    @classmethod
    def load_or_generic(cls) -> "DocumentContext":
        """
        Lit data/document_context.md s'il existe,
        sinon retourne un contexte générique neutre.
        """
        if CONTEXT_MD_PATH.exists():
            return cls.from_file()
        logger.warning("⚠️ Aucun fichier data/document_context.md — extraction générique.")
        return cls._generic()

    @classmethod
    def _generic(cls) -> "DocumentContext":
        return cls(
            raw_description="Document générique sans contexte spécifié.",
            document_type="UNKNOWN",
            domain="UNKNOWN",
            language="fr",
            llm_context_hint="Document dont le type est inconnu. Extraire toute obligation fonctionnelle."
        )

    @classmethod
    def create_template(cls, path: str = None):
        """
        Génère un fichier data/document_context.md vide à compléter.
        """
        target = Path(path) if path else CONTEXT_MD_PATH
        target.parent.mkdir(parents=True, exist_ok=True)
        if target.exists():
            logger.warning(f"⚠️ Fichier déjà existant : {target} — non écrasé.")
            return
        template = """\
# Contexte du document à analyser

## Nature du document
<!-- Ex: RFP, Cahier des charges, Spécification technique, Contrat SLA... -->


## Organisation concernée
<!-- Ex: L'ESSP (European Satellite Services Provider), ANSP certifié EASA -->


## Sujet principal
<!-- Décrivez en quelques phrases ce que le document couvre -->


## Identifiants d'exigences
<!-- Format utilisé dans le document pour numéroter les exigences -->
<!-- Ex: BN-XXX (ex: BN-039), REQ-XXX, ou "aucun identifiant normalisé" -->


## Types de contenu présents
<!-- Listez ce que contient le document -->
<!-- Ex: exigences normées, schémas, maquettes fils de fer, tableaux, workflows -->


## Fonctionnalités clés décrites
<!-- Listez les grandes fonctionnalités ou modules décrits dans le document -->


## Contraintes techniques
<!-- Ex: hébergement on-premise Ubuntu, Active Directory, politique mots de passe -->


## Notes complémentaires
<!-- Tout autre élément utile pour guider l'extraction des exigences -->
"""
        with open(target, "w", encoding="utf-8") as f:
            f.write(template)
        logger.success(f"✅ Template créé : {target}")

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
        """Bloc de contexte injecté dans le prompt BABOK, adapté au type de document."""
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
        Version v14 : liste noire explicite + règle de domaine.
        """
        # --- Règle négative : liste noire explicite ---
        false_cases = (
            "is_real_requirement = false dans TOUS ces cas :\n"
            "  - Titre de section ou sous-section seul (ex: '3.3 BOARDS DASHBOARD', 'D4 : Analysis')\n"
            "  - Entrée de table des matières (ex: 'TABLE OF CONTENT', 'TABLE OF TABLES')\n"
            "  - Label de champ seul sans verbe d'obligation (ex: 'Recom sol family', 'Sub ref status')\n"
            "  - Légende de figure ou de tableau (ex: 'Table 5: Compliance level')\n"
            "  - Référence bibliographique ou documentaire\n"
            "  - En-tête ou pied de page (numéro de page, confidentialité, 'Iss. 01-00')\n"
            "  - Note administrative ou organisationnelle sans obligation\n"
            "  - Fragment hors domaine du document (ex: satellite, énergie solaire si le document "
            "    parle d'un outil logiciel)\n"
            "  - Texte qui ne contient aucun des mots : must, shall, should, doit, devra, "
            "    il faut, nécessite, requis, obligatoire, interdit, autorisé\n"
        )

        # --- Règle positive : selon le type de document ---
        if self.document_type == "RFP":
            true_case = (
                "is_real_requirement = true UNIQUEMENT si le texte exprime une obligation "
                "fonctionnelle, une contrainte technique ou une règle métier "
                "pour l'outil logiciel décrit dans ce RFP. "
                "En cas de doute, mettre false."
            )
        elif self.document_type == "CONTRACT":
            true_case = (
                "is_real_requirement = true UNIQUEMENT si le texte exprime une obligation "
                "contractuelle, une clause ou une condition de service. "
                "En cas de doute, mettre false."
            )
        else:
            true_case = (
                "is_real_requirement = true UNIQUEMENT si le texte contient une obligation "
                "claire avec un verbe normatif. En cas de doute, mettre false."
            )

        # --- Règle de domaine : si un contexte est défini ---
        domain_rule = ""
        if self.llm_context_hint and self.document_type != "UNKNOWN":
            domain_rule = (
                f"\nContexte de référence : {self.llm_context_hint}\n"
                "Si le texte ne concerne pas ce domaine (ex: exigence de satellite dans un RFP "
                "d'outil logiciel), mettre is_real_requirement = false."
            )

        return f"{false_cases}\n{true_case}{domain_rule}"

    # ------------------------------------------------------------------ #
    #  Détection par règles                                                #
    # ------------------------------------------------------------------ #

    def _detect_from_text(self, text: str):
        """Détection heuristique à partir du contenu du fichier .md."""
        lower = text.lower()

        # Type de document
        if any(w in lower for w in ["rfp", "appel d'offres", "appel d offres", "request for proposal"]):
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
        if any(w in lower for w in ["workflow", "flux de travail", "cycle de vie"]):
            self.content_types.append("workflows")

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
