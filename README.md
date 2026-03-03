# 🏭 Augmented BID IA — Votre Expert en Appels d'Offres

> 💡 **Nouveau sur le projet ?** Lisez notre [📖 Guide complet du fonctionnement](GUIDE_COMPLET.md) pour tout comprendre en 5 minutes.

**Imaginez un expert qui lit 500 pages de documents techniques en 2 minutes, repère toutes les obligations cachées, traque les clauses ambiguës et vérifie si votre entreprise sait y répondre. Le tout, 100% localement.**

---

## 🌟 Pourquoi ce projet est-il unique ?

| RAG CLASSIQUE              |   AUGMENTED BID IA
|---------------------------|----------------------------------
| "Cherche dans le texte"    |   "Analyse (BABOK) + Vérifie (ISO 25010)"
| "Donne une réponse"        |   "Traque les pièges (Radar à Loups)"
| "Texte uniquement"         |   "Analyse aussi les Schémas & Photos"
| "Amnésique"                |   "Mémoire de conversation intelligente"

---

## 🚀 Guide d'Utilisation Rapide (Le 1-2-3-4)

### 1. Indexation (Apprentissage)
Apprenez à l'IA ce qu'elle doit analyser (le RFP) et ce que vous savez faire (votre catalogue).
```bash
./venv/bin/python extract/main.py --input data/input/mon_rfp.pdf
```

### 2. Audit Granulaire (Stratégique ✨)
Traquez les ambiguïtés et les manques techniques du client.
```bash
./venv/bin/python extract/granular_audit.py --cat TECHNIQUE
```
➡️ Rapport disponible dans : `data/granular_audit_report.md`

### 3. Analyse Métier (Gap Analysis)
Générez la matrice de conformité automatique entre le client et vous.
```bash
./venv/bin/python extract/phase2/compliance.py
```
➡️ Rapport disponible dans : `data/gap_analysis_report.md`

### 4. Dialogue Expert (Méthode Simple)
Posez vos questions complexes dans `data/prompt.md` et lancez l'agent :
```bash
./venv/bin/python extract/rfp_agent.py
```

---

🔒 **Confidentialité** : Ce système tourne **100% en local**. Rien n'est envoyé sur internet.
*(Architecture détaillée dans [ARCHITECTURE.md](ARCHITECTURE.md))*
