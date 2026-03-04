# 🤖 Contexte pour l'IA (Instructions de Développement V3.0)

Ce fichier définit les règles d'or pour tout futur développement sur ce projet.

## 🏗️ Architecture FSM-Driven (Strict)
Ce projet n'est pas un système RAG classique, c'est une **Machine à État Finis (FSM)**.
- Le cycle de vie d'une exigence est unidirectionnel : `RAW` ➔ `CLASSIFIED` ➔ `NORMALIZED` ➔ `CLEAN` ➔ `AUDITED` ➔ `BASELINE`.
- **Règle de Sûreté :** Ne jamais forcer la transition vers `CLEAN` si l'ambiguïté est > 0. Le blocage est une *feature*, pas un bug.

## ⚙️ Méthodologie "Dissocier, Traiter, Associer"
- **Dissocier (Phase 1)** : Ancrage MD5 strict obligatoire. Filtrage du bruit structurel (regex) et adaptation thématique via `DocumentContext` dès l'ingestion.
- **Traiter (Phase 2)** : Utilisation exclusive du pattern **Micro-Agents**. L'agent BABOK doit utiliser `DocumentContext` pour adapter ses regex d'ID et ses prompts.
- **Associer (Phase 3)** : Dédoublonnage sémantique obligatoire avant certification. Seules les exigences `CLEAN`, `AUDITED` ou `NORMALIZED` avec identifiant officiel sont éligibles à la baseline.
- **Livrables Finaux** : Génération systématique de la **Technical Baseline** (Markdown/JSON) et de la **Matrice de Conformité Excel** (`excel_generator.py`).
- **Interface Interactive** : Utilisation de `rfp_agent.py` (RAG) pour l'exploration conversationnelle et multimodale du document.

## 🛠️ Stack & Standards Techniques
- **Pipeline Multimodal** : Les images extraites du PDF sont stockées dans `data/output_images/`. Le `FSMAgent` doit supporter le passage d'un `image_path` à `_call_llm()`.
- **Modèles Vision** : Utiliser en priorité `google/gemini-2.0-flash-001` ou `llama3.2-vision` pour les fragments de type `IMAGE`.
- **Architecture Asynchrone** : Utilisation systématique de `asyncio`.
- **Gestion des Ressources** : Utilisation de `Semaphore` pour limiter la concurrence LLM. Bridage du contexte (`num_ctx`) pour l'optimisation VRAM locale.
- **Data Protection** : Interdiction formelle de muter les dictionnaires source lors du chargement (ex: pas de `pop()` sur les données de registre). Travailler systématiquement sur des copies.
- **Data Integrity** : `dataclasses` obligatoires pour la manipulation de données.
- **JSON Handling** : Toujours utiliser `_clean_json_response()` pour parser les retours LLM (qui contiennent souvent du Markdown indésirable).
- **PEP8 & Ruff** : Adhérence stricte aux standards PEP8 via `Ruff`. Formatage automatique et linting obligatoires avant chaque commit.
- **Typage** : Utilisation intensive du typage statique (`mypy`) avec Python 3.12+.
- **Logging** : Logging unifié via `loguru` et `utils/factory_log.py` pour la traçabilité industrielle.
- **Requirement Harvester** : Point d'entrée industriel (`extract/requirement_harvester.py`) pour le scan complet et la mise en file d'attente FSM.
