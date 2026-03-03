# 🏭 Augmented BID IA — Moteur de Conformité & Analyse RFP

Un système d'analyse d'Appels d'Offres (RFP) **100% local, multimodal** et orienté **"Gap Analysis"**. Ce projet transforme un document brut en une matrice d'exigences vérifiée par rapport à votre savoir-faire.

---

## 🌟 C'est quoi la différence avec un RAG classique ?

Contrairement à un simple agent conversationnel, **Augmented BID IA** est conçu pour les professionnels du "Bid Management" :

```text
RAG CLASSIQUE              |   AUGMENTED BID IA
---------------------------|----------------------------------
"Cherche dans le texte"    |   "Cherche (Vecteurs) + Vérifie (BM25)"
"Donne une réponse"        |   "Vérifie la Conformité ✅/⚠️/❌"
"Texte uniquement"         |   "Analyse aussi les Schémas & Photos"
"Amnésique"                |   "Mémoire de conversation résumée"
```

---

## 🚀 Guide d'Utilisation (Tutoriel)

### Étape 1 : Indexation des documents
Apprenez à l'IA ce qu'elle doit analyser (le RFP) et ce que vous savez faire (votre catalogue).

```bash
# 1. Indexer le cahier des charges du client
./venv/bin/python extract/main.py --input data/input/mon_rfp.pdf

# 2. Indexer vos plaquettes commerciales (Référentiel)
./venv/bin/python extract/main.py --input data/input/mon_catalogue.pdf --collection service_catalog
```

### Étape 2 : Analyse de Qualité & Gap Analysis
Vérifiez ce que l'IA a compris *avant* de lui faire confiance aveuglément.
```bash
# 3. Rapport d'Ingestion & Qualité (Points flous ?)
./venv/bin/python extract/confidence_report.py --rfp "mon_rfp.pdf"

# 4. Audit & Gap Analysis (Matrice de conformité GTM)
./venv/bin/python extract/phase2/compliance.py
```

### Étape 3 : Agent Expert (Dialogue libre)
Besoin d'un point de détail ? Interrogez l'agent directement :
```bash
./venv/bin/python extract/rfp_agent.py "Quels sont les pénalités de retard ?"
```

---

## 📊 Structure Didactique du Code

| Dossier | Rôle | Métaphore |
|---|---|---|
| `extract/phase1/` | Moteur d'ingestion | **Le Bibliothécaire** : Lit, classe et indexe. |
| `extract/phase2/` | Intelligence d'audit | **L'Expert Métier** : Analyse les écarts et rédige le rapport. |
| `data/` | Stockage local | **Le Coffre-fort** : Vos documents confidentiels ne sortent jamais d'ici. |

---

🔒 **Confidentialité** : Ce système tourne **100% en local**. Rien n'est envoyé sur internet.
*(Architecture détaillée disponible dans [ARCHITECTURE.md](ARCHITECTURE.md))*
