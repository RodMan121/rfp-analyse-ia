# 🏭 Augmented BID IA — Moteur de Conformité & Analyse RFP

Un système d'analyse d'Appels d'Offres (RFP) **100% local, multimodal** et orienté **"Gap Analysis"**. Ce projet transforme un document brut en une matrice d'exigences vérifiée par rapport à votre savoir-faire.

---

## 🌟 Pourquoi utiliser ce logiciel ?

| FONCTIONNALITÉ              |   BÉNÉFICE MÉTIER
|---------------------------|----------------------------------
| **Recherche Hybride (RRF)** | Trouve les concepts flous ET les articles de loi exacts.
| **Gap Analysis Automatique** | Détecte immédiatement vos écarts de conformité ✅/⚠️/❌.
| **Vision Cognitive**        | Analyse les schémas, maquettes et diagrammes d'architecture.
| **Audit de Confiance**      | L'IA s'auto-évalue pour garantir la fiabilité des données.
| **Zéro Cloud (Ollama)**     | Confidentialité totale : vos documents ne sortent pas de votre PC.

---

## 🚀 Guide d'Utilisation Rapide

### 1. Indexation (Apprentissage)
Apprenez à l'IA ce qu'elle doit analyser (le RFP) et ce que vous savez faire (votre catalogue).

```bash
# Indexer le cahier des charges client
./venv/bin/python extract/main.py --input data/input/mon_rfp.pdf

# Indexer votre référentiel technique (Catalogue)
./venv/bin/python extract/main.py --input data/input/notre_savoir_faire.pdf --collection service_catalog
```

### 2. Audit & Gap Analysis
Générez la matrice de conformité automatique et vérifiez la qualité.
```bash
# Vérifier si l'IA a bien "lu" le document (Rapport de Confiance)
./venv/bin/python extract/confidence_report.py --rfp "mon_rfp.pdf"

# Lancer la Gap Analysis (Matrice GTM)
./venv/bin/python extract/phase2/compliance.py
```

### 3. Dialogue Expert (Méthode Simple ✨)
Pour des questions complexes :
1.  Éditez le fichier **`data/prompt.md`**.
2.  Lancez l'agent sans argument : `./venv/bin/python extract/rfp_agent.py`

---

## 📂 Structure du Code

- `extract/phase1/` : **Le Bibliothécaire** (Parsing Docling/Gemini, Indexation RRF).
- `extract/phase2/` : **L'Expert Métier** (Compliance, Gap Analysis parallélisée).
- `data/` : **Le Coffre-fort** (Stockage local, Cache JSON, Images).

---

🔒 **Confidentialité** : Ce système tourne **100% en local**. Rien n'est envoyé sur internet.
*(Architecture détaillée dans [ARCHITECTURE.md](ARCHITECTURE.md))*
