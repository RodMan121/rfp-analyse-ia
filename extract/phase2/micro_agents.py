import os
import sys
import ollama
import json
from pathlib import Path
from loguru import logger
from typing import List, Dict
from dataclasses import dataclass, asdict

# Fix pour les imports
sys.path.append(str(Path(__file__).parent.parent))

@dataclass
class GranularRequirement:
    original_text: str
    subject: str = ""
    action: str = ""
    target_object: str = ""
    constraint: str = ""
    condition: str = ""
    ambiguity_score: int = 0  # 0 = Clair, 100 = Loup total
    fuzzy_terms: List[str] = None
    status: str = "VALIDATED"  # VALIDATED | PENDING_CLARIFICATION
    missing_implications: List[str] = None
    gap_tickets: List[str] = None

class GranularAnalysisEngine:
    """
    Chaîne de montage de micro-agents pour l'analyse déterministe.
    """

    def __init__(self, model: str = None):
        self.model = model or os.getenv("OLLAMA_TEXT_MODEL", "qwen2.5:7b")
        logger.info(f"⚙️ Moteur Granulaire prêt (Modèle: {self.model})")

    def process_requirement(self, raw_text: str) -> GranularRequirement:
        """Fait passer une exigence brute par les 3 agents."""
        req = GranularRequirement(original_text=raw_text, fuzzy_terms=[], missing_implications=[], gap_tickets=[])
        
        # 1. Agent Traducteur BABOK
        req = self._agent_babok(req)
        
        # 2. Agent Radar à Loups
        req = self._agent_radar_loups(req)
        
        # 3. Agent de Complétude (ISO 25010)
        req = self._agent_completude(req)
        
        return req

    def _agent_babok(self, req: GranularRequirement) -> GranularRequirement:
        """Normalisation atomique de l'exigence (Version stricte)."""
        prompt = f"""Tu es l'Agent Traducteur BABOK. Ta mission est la RIGUEUR technique.
Transforme l'exigence en une structure déterministe. 

STRUCTURE CIBLE :
- Sujet : L'entité qui agit (ex: Le Système, L'Utilisateur, La Base de données).
- Action : Le verbe d'action précis (ex: Sauvegarder, Afficher, Vérifier).
- Objet : Ce sur quoi porte l'action.
- Contrainte : Limite technique ou temporelle.
- Condition : Événement déclencheur.

EXEMPLE :
"L'accès doit être sécurisé" -> Sujet: "Le Système", Action: "Authentifier", Objet: "L'Utilisateur", Contrainte: "via protocole MFA".

EXIGENCE À TRAITER : "{req.original_text}"

Réponds UNIQUEMENT en JSON :
{{
  "condition": "...",
  "sujet": "...",
  "action": "...",
  "objet": "...",
  "contrainte": "..."
}}"""
        try:
            resp = ollama.generate(model=self.model, prompt=prompt, format="json")
            data = json.loads(resp.get('response', '{}'))
            req.condition = data.get('condition', '')
            req.subject = data.get('sujet', '')
            req.action = data.get('action', '')
            req.target_object = data.get('objet', '')
            req.constraint = data.get('contrainte', '')
        except: pass
        return req

    def _agent_radar_loups(self, req: GranularRequirement) -> GranularRequirement:
        """Désambiguïsation et traque des termes flous."""
        prompt = f"""Tu es l'Agent Radar à Loups. 
Traque les termes flous (ex: ergonomique, rapide, moderne, simple, efficace, etc.).

EXIGENCE : "{req.original_text}"

Réponds UNIQUEMENT en JSON :
{{
  "ambiguity_score": 0-100,
  "fuzzy_terms": ["terme1", "terme2"],
  "status": "VALIDATED ou PENDING_CLARIFICATION"
}}"""
        try:
            resp = ollama.generate(model=self.model, prompt=prompt, format="json")
            data = json.loads(resp.get('response', '{}'))
            req.ambiguity_score = data.get('ambiguity_score', 0)
            req.fuzzy_terms = data.get('fuzzy_terms', [])
            req.status = data.get('status', 'VALIDATED')
        except: pass
        return req

    def _agent_completude(self, req: GranularRequirement) -> GranularRequirement:
        """Inférence ISO 25010 pour détecter les exigences implicites manquantes."""
        prompt = f"""Tu es l'Agent de Complétude (ISO 25010). 
Identifie les fonctions manquantes induites par cette exigence (ex: Sécurité, Archivage, Suppression, Performance).

EXIGENCE : "{req.original_text}"

Réponds UNIQUEMENT en JSON :
{{
  "missing_implications": ["ce qui manque"],
  "gap_tickets": ["Titre du ticket d'écart à générer"]
}}"""
        try:
            resp = ollama.generate(model=self.model, prompt=prompt, format="json")
            data = json.loads(resp.get('response', '{}'))
            req.missing_implications = data.get('missing_implications', [])
            req.gap_tickets = data.get('gap_tickets', [])
        except: pass
        return req

if __name__ == "__main__":
    engine = GranularAnalysisEngine()
    test_req = "L'application doit être très rapide et permettre le stockage des documents personnels."
    
    logger.info(f"🧪 TEST DÉMONSTRATION — CHAÎNE DE MONTAGE")
    logger.info(f"Phrase source : '{test_req}'")
    
    result = engine.process_requirement(test_req)
    
    import json
    print("\n" + "="*50)
    print("🎯 RÉSULTAT DE L'ANALYSE GRANULAIRE")
    print("="*50)
    print(json.dumps(asdict(result), indent=2, ensure_ascii=False))
    print("="*50)
