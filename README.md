# 🏭 Augmented BID IA — Moteur de Conformité & Analyse RFP

Un système d'analyse d'Appels d'Offres (RFP) 100% local, multimodal et orienté "Gap Analysis". Ce projet transforme un document brut en une matrice d'exigences vérifiée par rapport à votre savoir-faire.

---

## 🌟 Architecture & Fonctionnalités (Phase 1 & 2)
Ce logiciel ne se contente pas de faire du "RAG", c'est un véritable **système expert d'audit** :

### 1. Ingestion Robuste & Sémantique
- **Parsing Hiérarchique (Docling)** : Comprend la structure du document (Titres, Sous-titres).
- **Extraction Tabulaire** : Convertit les bordereaux de prix en Markdown strict.
- **Tagging Automatique** : Chaque texte est classé (ADMIN, TECHNIQUE, JURIDIQUE).
- **Cache JSON** : Les documents sont mis en cache pour un rechargement instantané.

### 2. Le Moteur Hybride (Précision)
- **Vecteurs (ChromaDB)** : Recherche par le sens (ex: "Cybersécurité").
- **Mots-clés (BM25)** : Recherche par mots exacts (ex: "Article 4.2", "ISO 27001").
- **Fusion RRF** : Les algorithmes combinent le meilleur des deux mondes.

### 3. Les 3 Agents Métier
- 🤖 **Agent QA (Avec Mémoire)** : Posez-lui des questions en direct, il se souvient des 6 derniers échanges et décide seul s'il doit "lire" ou "regarder" une page (Llama 3.2 Vision).
- 🛡️ **Agent de Conformité (Gap Analysis)** : Croise les exigences du client avec votre catalogue de services pour générer une Matrice de Conformité (GTM).
- 📋 **Auditeur de Confiance** : Un script qui note la qualité de l'ingestion de l'IA (Fiable, Douteux, Illisible) et vous remonte les questions bloquantes.

---

## 🛠️ Guide d'Utilisation (Tutoriel)

### Étape 0 : Prérequis
- Python 3.10+
- [Ollama](https://ollama.com/) avec les modèles : `qwen2.5:7b` et `llama3.2-vision`.

### Étape 1 : Indexation des documents
Apprenez à l'IA ce qu'elle doit analyser (le RFP) et ce que vous savez faire (votre catalogue).

```bash
# 1. Indexer l'Appel d'Offres du client
./venv/bin/python extract/main.py --input data/input/mon_rfp.pdf --collection rfp_hierarchical

# 2. Indexer votre référentiel technique (Catalogue, Ancienne offre)
./venv/bin/python extract/main.py --input data/input/mon_catalogue.pdf --collection service_catalog
```

### Étape 2 : Rapport de Confiance & Qualité
Vérifiez ce que l'IA a compris *avant* de lui faire confiance aveuglément.
```bash
./venv/bin/python extract/confidence_report.py --rfp "mon_rfp.pdf"
```
➡️ Consultez `data/confidence_report.md` pour voir si des schémas étaient illisibles.

### Étape 3 : Audit & Gap Analysis (GTM)
Générez automatiquement la matrice des exigences et l'analyse de vos écarts (ce que vous pouvez faire vs ce que le client demande).
```bash
./venv/bin/python extract/phase2/compliance.py
```
➡️ Consultez `data/gap_analysis_report.md` (Tableau Markdown ✅/⚠️/❌).

### Étape 4 : L'Agent Expert (Questions Libres)
Besoin d'un point de détail ? Interrogez l'agent directement :
```bash
./venv/bin/python extract/rfp_agent.py "Détaille les pénalités de retard"
# Ou pour une image :
./venv/bin/python extract/rfp_agent.py "Explique le schéma de l'architecture serveur"
```

---

## 📂 Structure du Code
- `extract/phase1/` : Le moteur bas niveau (Parser, Chunking, VectorStore RRF).
- `extract/phase2/` : L'intelligence métier (Compliance, Gap Analysis).
- `data/` : Espace de stockage (Ignoré par Git pour votre confidentialité).

🔒 **Confidentialité** : Ce système tourne **100% en local**. Rien n'est envoyé sur internet.
