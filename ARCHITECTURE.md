# 🏗️ Architecture Technique : Augmented BID IA

Ce document décrit en profondeur les choix architecturaux et le flux de données de la Phase 1 (Ingestion & Analyse).

## 📊 Flux de Données (Data Pipeline)

### 1. Ingestion Sémantique (The Parser)
Contrairement aux solutions classiques qui découpent les documents par blocs de caractères (ex: 1000 chars), nous utilisons **IBM Docling**.
- **Avantage** : Il identifie les objets logiques (Titres, Tableaux, Listes).
- **Enrichissement** : Le script `local_parser.py` maintient une pile de titres pour générer un **fil d'ariane** (ex: *Maintenance > SLA > Pénalités*). Cela donne au LLM une conscience de la structure globale du document.

### 2. Double Indexation (The Vector Store)
Les fragments sont stockés dans **ChromaDB** avec un modèle d'embedding multilingue (`paraphrase-multilingual-MiniLM-L12-v2`).
- **Indexation augmentée** : Le titre de la section est injecté dans le texte indexé pour améliorer la recherche sémantique thématique.
- **Métadonnées** : La page et le fil d'ariane sont stockés pour permettre les citations de sources.

### 3. Recherche de Haute Précision (RAG + Reranking)
Le système utilise un pipeline en deux étapes pour la récupération :
1. **Retrieval (ChromaDB)** : Remonte 20 à 25 fragments thématiquement proches (rapide, mais peut inclure du bruit).
2. **Reranking (FlashRank)** : Un modèle **Cross-Encoder** (`ms-marco-MiniLM`) analyse la pertinence réelle entre la question et chaque fragment. Il ne sélectionne que les 5 meilleurs.
- **Résultat** : Réduction drastique des hallucinations et meilleure précision sur les chiffres (délais, montants).

### 4. Analyse Multimodale (The Router)
L'agent RFP agit comme un routeur intelligent :
- **Intention Texte** : Utilise `qwen2.5:7b` (Ollama) pour le raisonnement logique.
- **Intention Vision** : Si la question contient des mots-clés visuels (ex: 'schéma', 'maquette'), l'agent identifie la page cible et invoque `llama3.2-vision` en lui passant la capture PNG de la page.

## 🛠️ Stack Technologique
- **Parsing** : IBM Docling (Local)
- **OCR** : RapidOCR (Intégré à Docling)
- **Vector DB** : ChromaDB (Local)
- **Embedding** : Sentence-Transformers (Local)
- **Reranker** : FlashRank (Local)
- **LLMs** : Ollama (Local) - Qwen 2.5 & Llama 3.2 Vision

## 🔒 Confidentialité & Coûts
- **Coûts API** : 0€ (Tout est local).
- **Données** : Aucune donnée confidentielle (PDF ou base vectorielle) n'est envoyée dans le cloud.
