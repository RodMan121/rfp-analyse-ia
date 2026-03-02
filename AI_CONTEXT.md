# 🤖 Contexte pour l'IA (Instructions de Développement)

Ce fichier est destiné aux agents IA (Cursor, Windsurf, Gemini) travaillant sur ce projet.

## 🏗️ Principes Architecturaux
- **Local-First** : Priorité absolue aux modèles tournant sur Ollama ou localement (Docling, FlashRank).
- **Hierarchical RAG** : Ne jamais traiter les fragments comme des blocs isolés. Toujours maintenir le lien avec les `breadcrumbs` (fil d'ariane).
- **Reranking System** : La recherche vectorielle seule n'est pas suffisante. Toujours passer par `LocalReranker` avant la génération.

## 🛠️ Stack Technique
- **LLM Raisonnement** : `qwen2.5:7b` (ou supérieur).
- **Vision** : `llama3.2-vision`.
- **Parsing** : `Docling` (IBM).
- **Vector DB** : `ChromaDB`.

## 🎯 Pistes d'Optimisation (Backlog IA)
1.  **Cache Vision** : Implémenter un système de cache pour ne pas ré-analyser une image de page si elle n'a pas changé.
2.  **Hybrid Search** : Combiner la recherche vectorielle avec une recherche par mots-clés classique (BM25) pour les termes techniques métier.
3.  **Agents Multi-Documents** : Étendre la recherche à plusieurs fichiers PDF simultanément avec filtrage par source.
4.  **Extraction de Tableaux** : Optimiser le rendu des tableaux Docling pour qu'ils soient plus lisibles par Qwen (format Markdown strict).

## ⚠️ Vigilance Technique
- **NumPy** : Attention, ChromaDB nécessite `numpy < 2.0.0`.
- **Mémoire** : Llama 3.2 Vision est gourmand en VRAM. Surveiller les appels Ollama.
