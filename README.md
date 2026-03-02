# 🏭 Augmented BID IA — Phase 1 : Ingestion & Analyse RFP (Version Expert)

Solution locale de parsing et d'analyse d'appels d'offres (RFP/CCTP) utilisant une architecture **Multimodale Local-First**.

## 🚀 Fonctionnalités Avancées
- **Parsing Hiérarchique (Docling)** : Découpage intelligent préservant la structure du document (breadcrumbs, sections).
- **Reranker Local (Secret Weapon)** : Utilisation de `FlashRank` pour une précision de recherche supérieure au RAG classique.
- **Routage Intelligent (Ollama)** :
    - **📝 Raisonnement Texte** : Propulsé par `qwen2.5:7b` pour les analyses juridiques et techniques.
    - **🖼️ Vision Cognitive** : Bascule automatique vers `llama3.2-vision` pour l'analyse des schémas et maquettes.
- **Zéro Cloud** : Indexation et raisonnement 100% locaux (Confidentialité totale).

## 🛠️ Installation

1.  **Prérequis** : Python 3.10+, Ollama.
2.  **Modèles Ollama requis** :
    ```bash
    ollama pull qwen2.5:7b
    ollama pull llama3.2-vision
    ```
3.  **Dépendances** :
    ```bash
    pip install -r extract/requirements.txt
    ```

## 📋 Utilisation

### 📥 Ingestion Hiérarchique
```bash
./venv/bin/python extract/main.py --input data/input/votre_document.pdf
```

### 🧠 Agent Expert (Texte & Vision)
L'agent détecte automatiquement si vous parlez d'un schéma :
```bash
# Analyse textuelle
./venv/bin/python extract/rfp_agent.py "Quelles sont les pénalités de retard ?"

# Analyse visuelle
./venv/bin/python extract/rfp_agent.py "Décris-moi le schéma technique de la page 15"
```

## 🔒 Sécurité
Les données sensibles (.env, data/, bases vectorielles) sont exclues du dépôt via `.gitignore`.
