# 🤖 Contexte pour l'IA (Instructions de Développement V2.1)

Ce fichier est destiné aux agents IA (Cursor, Windsurf, Gemini) travaillant sur ce projet.

## 🏗️ Principes Architecturaux
- **Hybrid Search RRF** : Toujours utiliser la fusion Vecteurs + BM25 pour la précision.
- **Micro-Agents Determinism** : Pour l'analyse stratégique, utiliser la chaîne de montage : `BABOK -> WOLF -> ISO`.
- **Local-First** : Priorité absolue aux modèles Ollama locaux.

## 🛠️ Stack Technique & Micro-Agents
- **Agent BABOK** : Normalisation atomique (`extract/phase2/micro_agents.py`).
- **Agent Radar à Loups** : Calcul de l'ambiguïté.
- **Agent de Complétude** : Inférence ISO 25010.
- **Orchestration** : `extract/granular_audit.py`.

## ⚠️ Vigilance Code
- **JSON Formatting** : Les Micro-Agents attendent des réponses JSON strictes.
- **Race Conditions** : La Gap Analysis est parallélisée, attention aux accès concurrents sur les ressources partagées (bien que ChromaDB gère cela).
- **PEP8** : Pas de points-virgules, typage statique obligatoire.
