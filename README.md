# 🏭 Augmented BID IA — Moteur de Conformité & Analyse RFP

Analysez vos appels d'offres localement, avec une précision chirurgicale (GTM & Gap Analysis).

## 🌟 Nouvelles Fonctionnalités (Phase 1 & 2)
Ce logiciel est passé d'un simple assistant RAG à un **système expert d'audit** :

- **🧠 Recherche Hybride (Vecteurs + BM25)** : Combine l'intelligence sémantique (sens) et la précision textuelle (mots-clés techniques, articles de loi).
- **🛡️ Gap Analysis Automatisée** : Compare les exigences du client (RFP) avec votre **Catalogue de Services** pour détecter les écarts de conformité.
- **🏷️ Tagging Sémantique** : Classification automatique des fragments (ADMIN, TECHNIQUE, JURIDIQUE, PLANNING, SÉCURITÉ).
- **📊 Parsing Tabulaire Haute-Fidélité** : Extraction des tableaux complexes en Markdown pour une analyse précise des prix et délais.
- **🤖 Agent Expert avec Mémoire** : Se souvient des échanges précédents pour des questions de suivi fluides.

---

## 🚀 Flux de Traitement (Pipeline)
1. **Ingestion (Docling)** : Parsing structurel + Capture PNG des schémas + Cache JSON.
2. **Double Indexation** : Stockage dans ChromaDB (Vecteurs) + BM25 (Textuel).
3. **Audit de Conformité** : Extraction des exigences et priorisation (HAUTE/MOYENNE).
4. **Gap Analysis** : Confrontation avec votre catalogue de savoir-faire.
5. **Rapport GTM** : Génération d'un tableau de synthèse Markdown (`data/gap_analysis_report.md`).

---

## 🛠️ Installation & Utilisation
### Prérequis
- Python 3.10+, Ollama.
- Modèles : `qwen2.5:7b` (Texte & Raisonnement), `llama3.2-vision` (Schémas).

### 1. Indexation
Indexer l'Appel d'Offres :
```bash
./venv/bin/python extract/main.py --input data/input/rfp.pdf --collection rfp_hierarchical
```
Indexer votre Catalogue de Services (Référentiel) :
```bash
./venv/bin/python extract/main.py --input data/input/catalogue.pdf --collection service_catalog
```

### 2. Audit & Gap Analysis (Nouveau !)
Générer la matrice de conformité et l'analyse d'écart :
```bash
./venv/bin/python extract/phase2/compliance.py
```

### 3. Agent Expert (Q&A)
Interroger le document (Texte ou Vision) :
```bash
./venv/bin/python extract/rfp_agent.py "Quelles sont les clauses de pénalités de retard ?"
```

---

## 📂 Structure du Projet
- `extract/phase1/` : Moteur d'ingestion (Parser, VectorStore, Reranker).
- `extract/phase2/` : Intelligence d'audit (Compliance, Gap Analysis).
- `data/` : Stockage local (Bases vectorielles, Images, Rapports).
- `ARCHITECTURE.md` : Détails profonds du fonctionnement hybride.

🔒 **Sécurité** : 100% Local. Aucune donnée n'est envoyée dans le cloud.
