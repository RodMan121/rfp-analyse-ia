import os
import sys
import ollama
import json
from pathlib import Path
from loguru import logger
from typing import List, Dict, Optional
from dataclasses import dataclass, asdict, field
from dotenv import load_dotenv

# Fix pour les imports et configuration
env_path = Path(__file__).parent.parent / ".env"
load_dotenv(env_path)
sys.path.append(str(Path(__file__).parent.parent))

@dataclass
class GranularRequirement:
    """Modèle de données pour une exigence analysée chirurgicalement."""
    original_text: str
    subject: str = ""
    action: str = ""
    target_object: str = ""
    constraint: str = ""
    condition: str = ""
    ambiguity_score: int = 0
    fuzzy_terms: List[str] = field(default_factory=list)
    status: str = "VALIDATED"
    missing_implications: List[str] = field(default_factory=list)
    gap_tickets: List[str] = field(default_factory=list)

class GranularAnalysisEngine:
    """
    Moteur déterministe transformant le langage naturel en spécifications techniques.
    """

    def __init__(self, model: Optional[str] = None):
        self.model = model or os.getenv("OLLAMA_TEXT_MODEL", "qwen2.5:7b")
        logger.info(f"⚙️ Moteur Granulaire prêt (Modèle: {self.model})")

    def process_requirement(self, raw_text: str) -> GranularRequirement:
        """Pipeline de traitement par micro-agents."""
        req = GranularRequirement(original_text=raw_text)
        
        # 1. Normalisation BABOK
        req = self._agent_babok(req)
        
        # 2. Radar à Loups
        req = self._agent_radar_loups(req)
        
        # 3. Complétude ISO 25010
        req = self._agent_completude(req)
        
        return req

    def _clean_json_response(self, raw_resp: str) -> str:
        """Nettoie les éventuelles balises Markdown pour extraire le JSON pur."""
        clean = raw_resp.strip()
        if "```json" in clean:
            clean = clean.split("```json")[1].split("```")[0]
        elif "```" in clean:
            clean = clean.split("```")[1].split("```")[0]
        return clean.strip()

    def _agent_babok(self, req: GranularRequirement) -> GranularRequirement:
        """Agent Traducteur : Structure Sujet + Action + Objet + Contrainte."""
        prompt = f"""Tu es l'Agent Traducteur BABOK. 
Transforme l'exigence suivante en structure déterministe.

STRUCTURE CIBLE :
- Sujet : L'acteur (Le Système, L'Utilisateur, etc.)
- Action : Le verbe d'action précis
- Objet : Ce sur quoi porte l'action
- Contrainte : Limite technique/temporelle
- Condition : Déclencheur

EXIGENCE : "{req.original_text}"

Réponds UNIQUEMENT en JSON :
{{
  "condition": "...", "sujet": "...", "action": "...", "objet": "...", "contrainte": "..."
}}"""
        try:
            resp = ollama.generate(model=self.model, prompt=prompt)
            clean_resp = self._clean_json_response(resp.get('response', '{}'))
            data = json.loads(clean_resp)
            req.condition = data.get('condition', '')
            req.subject = data.get('sujet', '')
            req.action = data.get('action', '')
            req.target_object = data.get('objet', '')
            req.constraint = data.get('contrainte', '')
        except Exception as e:
            logger.warning(f"⚠️ Erreur Agent BABOK : {e}")
        return req

    def _agent_radar_loups(self, req: GranularRequirement) -> GranularRequirement:
        """Agent de Désambiguïsation : Traque du flou artistique."""
        prompt = f"""Tu es l'Agent Radar à Loups. 
Détecte les termes flous (ex: ergonomique, rapide, moderne, simple, efficace).

EXIGENCE : "{req.original_text}"

Réponds UNIQUEMENT en JSON :
{{
  "ambiguity_score": 0-100,
  "fuzzy_terms": ["terme1", "..."],
  "status": "VALIDATED ou PENDING_CLARIFICATION"
}}"""
        try:
            resp = ollama.generate(model=self.model, prompt=prompt)
            clean_resp = self._clean_json_response(resp.get('response', '{}'))
            data = json.loads(clean_resp)
            req.ambiguity_score = data.get('ambiguity_score', 0)
            req.fuzzy_terms = data.get('fuzzy_terms', [])
            req.status = data.get('status', 'VALIDATED')
        except Exception as e:
            logger.warning(f"⚠️ Erreur Agent Loups : {e}")
        return req

    def _agent_completude(self, req: GranularRequirement) -> GranularRequirement:
        """Agent ISO 25010 : Inférence de fonctionnalités manquantes."""
        prompt = f"""Tu es l'Agent de Complétude ISO 25010. 
Identifie les fonctions implicites manquantes (Sécurité, Archivage, etc.).

EXIGENCE : "{req.original_text}"

Réponds UNIQUEMENT en JSON :
{{
  "missing_implications": ["manque 1", "..."],
  "gap_tickets": ["Titre du ticket d'écart"]
}}"""
        try:
            resp = ollama.generate(model=self.model, prompt=prompt)
            clean_resp = self._clean_json_response(resp.get('response', '{}'))
            data = json.loads(clean_resp)
            req.missing_implications = data.get('missing_implications', [])
            req.gap_tickets = data.get('gap_tickets', [])
        except Exception as e:
            logger.warning(f"⚠️ Erreur Agent ISO : {e}")
        return req

if __name__ == "__main__":
    engine = GranularAnalysisEngine()
    test_req = "L'application doit être très rapide et permettre le stockage des documents personnels."
    logger.info(f"🧪 Test démonstration : {test_req}")
    result = engine.process_requirement(test_req)
    print(json.dumps(asdict(result), indent=2, ensure_ascii=False))
