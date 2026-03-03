# 🤖 Contexte pour l'IA (Instructions de Développement V2.2)

Ce fichier est destiné aux agents IA (Cursor, Windsurf, Gemini) travaillant sur ce projet.

## 🏗️ Principes Architecturaux
- **Hybrid-First** : La recherche doit toujours combiner Vecteurs (ChromaDB) et Mots-clés (BM25) via l'algorithme **RRF (Reciprocal Rank Fusion)**.
- **Robustesse ID** : Les IDs de fragments dans ChromaDB sont des hash MD5 (`hashlib.md5`) basés sur le contenu pour éviter les collisions lors d'ingestions multiples.
- **Cache de Fragments** : Utiliser `.fragments.json` avec validation par date de modification (`st_mtime`) pour éviter le re-parsing inutile.
- **Parallélisme** : La Gap Analysis supporte le multi-threading via `OLLAMA_NUM_PARALLEL`.

## 🛠️ Stack Technique & Modèles
- **Extraction Locale** : IBM Docling (Parsing hiérarchique).
- **Extraction Multimodale** : Gemini 2.0 Flash (avec logique de `tenacity.retry`).
- **LLM Raisonnement** : Ollama `qwen2.5:7b`.
- **Vision Cognitive** : Ollama `llama3.2-vision`.
- **Reranking** : FlashRank (`ms-marco-MiniLM-L-12-v2`).

## 🎯 Backlog d'Optimisation
1.  **Parallélisation Gemini** : Permettre le parsing de plusieurs documents simultanément.
2.  **Streaming Vision** : Explorer les capacités de streaming pour les modèles multimodaux Ollama.
3.  **Filtrage par Hash** : Implémenter une vérification de contenu identique avant indexation pour économiser de l'espace.

## ⚠️ Vigilance Code
- **Type Safety** : Toujours utiliser les Type Hints Python.
- **Exceptions** : Jamais de `bare except:`. Utiliser `except Exception:` ou des exceptions ciblées.
- **PEP8** : Pas de points-virgules `;`. Une instruction par ligne.
