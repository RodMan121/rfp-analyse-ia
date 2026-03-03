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
- **LLM Local** : Modèles Ollama (`qwen2.5:7b`).
- **Data Integrity** : `dataclasses` obligatoires pour la manipulation de données. Mutation en place interdite (travailler sur des copies).
- **JSON Handling** : Toujours utiliser `_clean_json_response()` pour parser les retours LLM (qui contiennent souvent du Markdown indésirable).
- **PEP8** : Respect strict, aucun point-virgule. Logging via `loguru`.
