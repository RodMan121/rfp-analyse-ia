# 🤖 Contexte pour l'IA (Instructions de Développement V3.0)

Ce fichier définit les règles d'or pour tout futur développement sur ce projet.

## 🏗️ Architecture FSM-Driven (Strict)
Ce projet n'est pas un système RAG classique, c'est une **Machine à État Finis (FSM)**.
- Le cycle de vie d'une exigence est unidirectionnel : `RAW` ➔ `CLASSIFIED` ➔ `NORMALIZED` ➔ `CLEAN` ➔ `AUDITED` ➔ `BASELINE`.
- **Règle de Sûreté :** Ne jamais forcer la transition vers `CLEAN` si l'ambiguïté est > 0. Le blocage est une *feature*, pas un bug.

## ⚙️ Méthodologie "Dissocier, Traiter, Associer"
- **Dissocier (Phase 1)** : Ancrage MD5 strict obligatoire. Ne jamais muter un fragment brut une fois stocké en base.
- **Traiter (Phase 2)** : Utilisation exclusive du pattern **Micro-Agents** via héritage de la classe de base `FSMAgent`. Chaque agent fait *une* seule chose.
- **Associer (Phase 3)** : Le rendu final (Technical Baseline) doit être sérialisable (JSON/Markdown) et prêt pour une injection dans un outil ALM.

## 🛠️ Stack & Standards Techniques
- **Architecture Asynchrone** : Utilisation systématique de `asyncio` pour les entrées/sorties LLM. Toutes les méthodes `trigger` des agents et les appels LLM doivent être asynchrones (`async`/`await`).
- **LLM Hybride & Multi-Cloud** : Support natif d'**Ollama**, **Gemini** et **OpenRouter**. Centralisation obligatoire via `_call_llm()` asynchrone avec gestion de retry robuste.
- **Gestion des Ressources** : Utilisation de `Semaphore` pour limiter la concurrence LLM. Bridage du contexte (`num_ctx`) pour l'optimisation VRAM locale.
- **Data Protection** : Interdiction formelle de muter les dictionnaires source lors du chargement (ex: pas de `pop()` sur les données de registre). Travailler systématiquement sur des copies.
- **Data Integrity** : `dataclasses` obligatoires pour la manipulation de données.
- **JSON Handling** : Toujours utiliser `_clean_json_response()` pour parser les retours LLM (qui contiennent souvent du Markdown indésirable).
- **PEP8 & Ruff** : Adhérence stricte aux standards PEP8 via `Ruff`. Formatage automatique et linting obligatoires avant chaque commit.
- **Typage** : Utilisation intensive du typage statique (`mypy`) avec Python 3.12+.
- **Logging** : Logging unifié via `loguru` et `utils/factory_log.py` pour la traçabilité industrielle.
- **Requirement Harvester** : Point d'entrée industriel (`extract/requirement_harvester.py`) pour le scan complet et la mise en file d'attente FSM.
