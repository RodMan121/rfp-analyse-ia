# 🏭 Augmented BID IA — Phase 1 : Ingestion & Analyse RFP

Solution locale de parsing et d'analyse d'appels d'offres (RFP/CCTP) utilisant une architecture **Local-First** pour minimiser les coûts API et garantir la confidentialité des données.

## 🚀 Architecture Optimisée
Le pipeline suit une stratégie de traitement hybride :
1.  **Parsing Local (Docling)** : Extraction de la structure, des tableaux et du texte sans frais API.
2.  **Snapshot Visuel** : Capture haute résolution de chaque page pour l'analyse des maquettes et fils de fer.
3.  **Vectorisation Locale (ChromaDB)** : Indexation sémantique via `sentence-transformers` (modèle multilingue).
4.  **Analyse Cognitive (RAG)** :
    *   **🏠 Mode Local (Ollama)** : Utilisation de modèles comme `qwen2.5:7b` ou `llama3.2` pour une analyse gratuite et privée.
    *   **☁️ Mode Cloud (Gemini)** : Utilisation de `gemini-2.0-flash` pour des analyses complexes on-demand.

## 🛠️ Installation

1.  **Prérequis** : Python 3.10+, Ollama (pour le mode local).
2.  **Installation des dépendances** :
    ```bash
    python -m venv venv
    source venv/bin/activate
    pip install -r extract/requirements.txt
    python -m spacy download fr_core_news_md
    ```

## 📋 Utilisation

### 📥 Ingestion des documents
Placez vos PDF dans `data/input/` et lancez l'ingestion :
```bash
./venv/bin/python extract/main.py --input data/input/votre_document.pdf
```
Cela génère :
*   `data/output_markdown/` : Le document complet structuré.
*   `data/output_images/` : Captures PNG de chaque page (maquettes).
*   `data/chroma_db/` : La base vectorielle interrogeable.

### 🧠 Interrogation de l'Agent (RAG)
Posez des questions à vos documents via Ollama (Local) :
```bash
./venv/bin/python extract/rfp_agent.py "Quels sont les objectifs du projet ?" --backend ollama --model qwen2.5:7b
```

## 🔒 Sécurité & Confidentialité
*   **Données** : Les fichiers PDF et les bases de données vectorielles restent locaux (configurés dans `.gitignore`).
*   **Modèles** : Le parsing et le raisonnement peuvent être effectués à 100% hors-ligne.
