# 🏭 Augmented BID IA — Moteur de Conformité & Analyse RFP

Un système d'analyse d'Appels d'Offres (RFP) **100% local, multimodal** et orienté **"Gap Analysis"**. Ce projet transforme un document brut en une matrice d'exigences vérifiée par rapport à votre savoir-faire.

---

## 🌟 Pourquoi utiliser ce logiciel ?

| RAG CLASSIQUE              |   AUGMENTED BID IA
|---------------------------|----------------------------------
| "Cherche dans le texte"    |   "Cherche (Vecteurs) + Vérifie (BM25)"
| "Donne une réponse"        |   "Vérifie la Conformité ✅/⚠️/❌"
| "Texte uniquement"         |   "Analyse aussi les Schémas & Photos"
| "Amnésique"                |   "Mémoire de conversation résumée"

---

## 🚀 Guide d'Utilisation Rapide

### 1. Indexation (Une seule fois)
Apprenez à l'IA ce qu'elle doit analyser (le RFP) et ce que vous savez faire (votre catalogue).

```bash
# Indexer le cahier des charges client
./venv/bin/python extract/main.py --input data/input/mon_rfp.pdf

# Indexer votre référentiel technique (Catalogue)
./venv/bin/python extract/main.py --input data/input/notre_savoir_faire.pdf --collection service_catalog
```

### 2. Analyse Métier (Gap Analysis)
Générez la matrice de conformité automatique entre le client et vous.
```bash
./venv/bin/python extract/phase2/compliance.py
```
➡️ Rapport disponible dans : `data/gap_analysis_report.md`

### 3. Dialogue Expert (Méthode Simple ✨)
C'est la méthode recommandée pour travailler. Plus besoin de taper de longues commandes :
1.  Éditez le fichier **`data/prompt.md`** (mettez-y votre question complexe).
2.  Lancez l'agent sans argument :
```bash
./venv/bin/python extract/rfp_agent.py
```
L'IA lira le fichier Markdown et affichera la réponse formatée dans votre terminal.

---

## 📊 Structure Didactique du Code

- `extract/phase1/` : **Le Bibliothécaire** (Parsing, Chunking, Indexation).
- `extract/phase2/` : **L'Expert Métier** (Compliance, Gap Analysis).
- `data/` : **Le Coffre-fort** (Vos documents confidentiels restent ici).

🔒 **Sécurité** : 100% Local. Aucune donnée n'est envoyée sur internet.
*(Architecture détaillée dans [ARCHITECTURE.md](ARCHITECTURE.md))*
