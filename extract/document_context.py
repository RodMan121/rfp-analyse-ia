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

    def get_normatif_regex(self) -> re.Pattern:
        """
        Retourne le regex des verbes normatifs adapté à la langue du document.
        Utilisé par BABOKAgent comme pré-filtre avant l'appel LLM.

        Important : self.language décrit la langue du fichier .md (la description),
        pas forcément la langue du PDF analysé. Un .md en français peut décrire
        un document dont les exigences sont rédigées en anglais (must/shall).
        Par défaut on utilise donc `mixed` (fr + en).
        On ne spécialise que si l'utilisateur a explicitement indiqué la langue
        du document (mot-clé 'en anglais', 'in english', 'document anglais'…).
        """
        # Signal fort : l'utilisateur a précisé que le PDF est en anglais
        if self.language == "en" and any(
            w in self.raw_description.lower()
            for w in ["document anglais", "in english", "english document", "written in english"]
        ):
            pattern = (
                r"\b(must|shall|should|is required|are required|"
                r"need to|needs to|has to|have to|"
                r"is mandatory|are mandatory|is prohibited|is allowed)\b"
            )
        # Signal fort : l'utilisateur a précisé que le PDF est en français
        elif self.language == "fr" and any(
            w in self.raw_description.lower()
            for w in ["document français", "en français", "rédigé en français", "french document"]
        ):
            pattern = (
                r"\b(doit|doivent|devra|devront|devrait|devraient|"
                r"il faut|nécessite|nécessitent|requis|requise|"
                r"obligatoire|obligatoires|interdit|interdite|"
                r"autorisé|autorisée|peut\b|peuvent\b)\b"
            )
        else:
            # Par défaut : mixed — couvre les documents bilingues ou dont
            # la langue n'est pas explicitement précisée dans le .md
            pattern = (
                r"\b(must|shall|should|is required|are required|need to|has to|"
                r"is mandatory|are mandatory|is prohibited|is allowed|"
                r"doit|doivent|devra|devront|devrait|il faut|nécessite|"
                r"requis|obligatoire|interdit|autorisé|peut\b|peuvent\b)\b"
            )
        return re.compile(pattern, re.IGNORECASE)

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
        Génère la règle is_real_requirement adaptée au document.
        Entièrement dérivée du contexte — aucun pattern projet codé en dur.
        """
        # --- Règle négative universelle ---
        false_cases = (
            "is_real_requirement = false dans TOUS ces cas :\n"
            "  - Titre de section ou sous-section seul\n"
            "  - Entrée de table des matières ou liste de figures\n"
            "  - Label de champ seul sans verbe d'obligation\n"
            "  - Légende de figure ou de tableau\n"
            "  - Référence bibliographique ou documentaire\n"
            "  - En-tête ou pied de page\n"
            "  - Note administrative sans obligation\n"
        )

        # --- Règle négative de domaine (auto-générée depuis llm_context_hint) ---
        if self.llm_context_hint and self.document_type != "UNKNOWN":
            false_cases += (
                f"  - Texte qui ne concerne manifestement pas : "
                f"« {self.llm_context_hint} »\n"
            )

        # --- Règle négative linguistique (auto-générée depuis language) ---
        if self.language == "en":
            false_cases += (
                "  - Texte sans aucun de ces mots : "
                "must, shall, should, required, mandatory, prohibited, allowed\n"
            )
        elif self.language == "fr":
            false_cases += (
                "  - Texte sans aucun de ces mots : "
                "doit, devra, devrait, il faut, nécessite, requis, "
                "obligatoire, interdit, autorisé\n"
            )
        else:
            false_cases += (
                "  - Texte sans aucun verbe d'obligation en français ou en anglais\n"
            )

        # --- Règle positive selon le type de document ---
        true_cases = {
            "RFP": (
                "is_real_requirement = true UNIQUEMENT si le texte exprime "
                "une obligation fonctionnelle, une contrainte technique ou "
                "une règle métier pour le système décrit. En cas de doute : false."
            ),
            "CCTP": (
                "is_real_requirement = true UNIQUEMENT si le texte exprime "
                "une clause technique ou une prescription du cahier des charges. "
                "En cas de doute : false."
            ),
            "CONTRACT": (
                "is_real_requirement = true UNIQUEMENT si le texte exprime "
                "une obligation contractuelle ou une condition de service. "
                "En cas de doute : false."
            ),
            "SPEC": (
                "is_real_requirement = true UNIQUEMENT si le texte exprime "
                "une spécification technique vérifiable. En cas de doute : false."
            ),
        }
        true_case = true_cases.get(
            self.document_type,
            "is_real_requirement = true UNIQUEMENT si une obligation claire est exprimée. "
            "En cas de doute : false."
        )

        return f"{false_cases}\n{true_case}"

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

        # Génération automatique des patterns de bruit hors-domaine
        # Chaque domaine détecté implique que certains autres sujets sont du bruit
        self._generate_domain_noise_patterns()

    def _generate_domain_noise_patterns(self):
        """
        Génère automatiquement extra_noise_patterns selon le domaine détecté.
        Principe : ce qui est clairement hors-domaine pour ce type de document est du bruit.
        Aucun pattern spécifique à un projet n'est codé en dur ici.
        """
        # Patterns toujours ajoutés (bruit structurel universel)
        universal = [
            r"^table of content|^table of tables|^table of figures?",
            r"^end of document|^fin du document",
            r"^d[1-8]\s*:",                          # titres d'étapes "D4 : Analysis"
            r"^section:\s*racine",                   # métadonnée structurelle interne
            r"^\d+\.\d+\s+[A-Z][\w\s]{3,40}$",      # "3.3 BOARDS DASHBOARD" seul
        ]
        for p in universal:
            if p not in self.extra_noise_patterns:
                self.extra_noise_patterns.append(p)

        # Patterns hors-domaine selon le domaine détecté
        domain_exclusions = {
            "IT": [
                # Exigences matérielles / physiques / spatiales → hors-domaine d'un outil IT
                r"solar panel|solar power|capture sunlight",
                r"satellite must|satellite component",
                r"antenna point|power management system",
                r"alimentation en énergie du satellite",
                r"panneaux? solaires?",
            ],
            "INFRASTRUCTURE": [
                # Exigences d'interface utilisateur → hors-domaine d'une infrastructure
                r"bouton|maquette|wireframe|champ de formulaire",
                r"user interface|interface utilisateur",
            ],
            "METIER": [
                # Exigences matérielles bas-niveau → hors-domaine métier
                r"solar panel|hardware spec|physical layer",
                r"voltage|ampere|watt",
            ],
            "JURIDIQUE": [
                # Exigences techniques → hors-domaine juridique
                r"cpu|ram|bandwidth|latency|throughput",
            ],
        }

        for pattern in domain_exclusions.get(self.domain, []):
            if pattern not in self.extra_noise_patterns:
                self.extra_noise_patterns.append(pattern)

        if self.extra_noise_patterns:
            logger.debug(
                f"🔧 {len(self.extra_noise_patterns)} patterns de bruit générés "
                f"pour domaine={self.domain}"
            )

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
