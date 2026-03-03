# 📖 Manuel Opérationnel — Méthodologie Augmented BID

Ce guide explique comment appliquer la logique "Dissocier & Traiter" avec les outils du projet.

---

## 🏭 Phase 1 : Dissocier (Ingestion)

L'ingestion n'est pas qu'une simple lecture, c'est une **décomposition chirurgicale**.

### 📥 `main.py` & `local_parser.py`
Ces scripts extraient les "objets" du PDF. Chaque objet JSON est scellé par un ID MD5 unique.
- **Règle d'Immuabilité :** Une fois indexé, un fragment ne change plus. Il est ancré à sa page et sa section. Cela garantit que l'IA ne pourra jamais "inventer" une source qui n'existe pas.

### 🏷️ Le Classifier
Il affecte un contexte métier (TECHNIQUE, JURIDIQUE, etc.). Ce contexte est crucial pour la Phase 2 car il définit les règles de complétude à appliquer.

---

## 🔬 Phase 2 : Traiter (Micro-Agents)

Le traitement granulaire élimine l'incertitude humaine.

### 🤖 `micro_agents.py` (La Chaîne de Montage)
Chaque exigence détectée passe par trois stations de travail :

1.  **Station BABOK :** On réécrit l'exigence. Fini le "Il faudrait que...". On veut : `Sujet` + `Action` + `Objet`.
2.  **Station Radar à Loups :** On calcule le score d'ambiguïté. Si vous voyez un score élevé dans `granular_audit_report.md`, l'exigence est "bloquée". Vous devez demander des précisions au client.
3.  **Station ISO 25010 :** L'agent vérifie ce que le client a oublié.
    - *Exemple :* Le document parle de "données bancaires" mais pas de "chiffrement". L'agent génère un **Gap Ticket**.

---

## 🚀 Résumé des Commandes Stratégiques

| Action | Commande | Livrable |
|---|---|---|
| **Dissocier** | `python main.py --input doc.pdf` | Base Immuable |
| **Traiter** | `python granular_audit.py` | Rapport de Désambiguïsation |
| **Comparer** | `python compliance.py` | Matrice GTM Finale |
