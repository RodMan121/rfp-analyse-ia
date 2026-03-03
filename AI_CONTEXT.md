# 🤖 Contexte pour l'IA (Instructions de Développement V2.1)

Ce fichier définit les règles d'or pour le développement futur du projet.

## 🏗️ Principes de Développement
- **Chain of Thought (CoT)** : Les analyses métier doivent passer par une chaîne de micro-agents (`BABOK -> WOLF -> ISO`).
- **Déterminisme** : Transformer le langage naturel flou en structures Sujet/Action/Objet.
- **Local-First** : Priorité absolue aux modèles Ollama (Qwen 2.5).

## 🔬 Les 3 Micro-Agents (Phase 2.1)
1.  **Agent BABOK** : Normalisation structurelle (Sujet, Action, Objet, Contrainte).
2.  **Agent Radar à Loups** : Calcul du score d'ambiguïté (0-100) et détection des termes qualitatifs.
3.  **Agent ISO 25010** : Inférence sur les fonctionnalités implicites manquantes (Sécurité, Archivabilité, etc.).

## ⚠️ Standards Techniques
- **JSON Robustness** : Utiliser `_clean_json_response` pour extraire les données des réponses LLM.
- **Type Safety** : Utiliser `dataclasses` et Type Hints Python.
- **Robustness** : Jamais de `bare except:`. Logging systématique avec `loguru`.
- **PEP8** : Une instruction par ligne, pas de `;`.
