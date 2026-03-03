# 🏭 Augmented BID IA — L'Usine à Appels d'Offres (FSM-Driven)

> 💡 **Bienvenue.** Si vous découvrez ce projet, commencez par notre [📖 Guide complet du fonctionnement](GUIDE_COMPLET.md) ou notre [🔰 Guide Débutant](GUIDE_DEBUTANT.md).

**Augmented BID IA n'est pas un énième chatbot.** C'est un moteur d'ingénierie déterministe qui transforme le "bruit" des documents commerciaux (RFP, CCTP) en une Technical Baseline immuable, prête pour vos équipes de réalisation. 100% local, confidentiel et auditable.

---

## 🗺️ La Méthodologie : L'Usine en 3 Phases

Notre philosophie repose sur le refus de l'approximation. Nous utilisons une approche **"Dissocier, Traiter, Associer"** pilotée par une Machine à État (FSM).

```text
[ 📄 PDF Client ]
       │
       ▼
 ┌─────────────┐
 │  PHASE 1    │ ✂️ DISSOCIER : Le document est découpé en fragments JSON
 │  Ingestion  │    Ancrage MD5 → Zéro hallucination possible.
 └─────────────┘
       │
       ▼
 ┌─────────────┐
 │  PHASE 2    │ 🔬 TRAITER : Les Micro-Agents analysent chaque fragment.
 │  Audit FSM  │    (BABOK normalise, Radar traque les loups, ISO complète)
 └─────────────┘
       │
       ▼
 ┌─────────────┐
 │  PHASE 3    │ 🧩 ASSOCIER : La vision cible est générée.
 │  Synthèse   │    (Matrice MoSCoW, Gap Analysis, Reverse TOGAF)
 └─────────────┘
       │
       ▼
[ 📊 Rapports Métier & Technique ]
```

---

## 🌟 Pourquoi ce système est supérieur au RAG Classique ?

| RAG CLASSIQUE (L'Artisanat) | AUGMENTED BID IA (L'Usine) |
| :--- | :--- |
| **Génératif** : L'IA "résume" le document avec le risque d'inventer ou d'oublier. | **Déterministe** : Chaque fragment est tracé par un ID MD5. La source est prouvable. |
| **Passif** : Vous devez poser les bonnes questions dans un "prompt". | **Proactif** : Les Micro-Agents scannent tout et vous alertent des manques (ISO 25010). |
| **Crédule** : Accepte les termes flous du client ("Le système doit être rapide"). | **Intransigeant** : Le "Radar à Loups" bloque les exigences non mesurables. |
| **Texte uniquement** : Ignore les schémas techniques. | **Multimodal** : Analyse l'architecture visuelle via Llama 3.2 Vision. |

---

## 🚀 Guide d'Utilisation (Workflow Automatisé)

Plus besoin de prompter manuellement, l'usine travaille pour vous en 3 commandes :

### Étape 1 : Ingestion (Apprentissage)
Chargez le document client dans la base vectorielle.
```bash
./venv/bin/python extract/main.py --input data/input/mon_rfp.pdf
```
*(Optionnel : Chargez votre catalogue avec `--collection service_catalog` pour la Gap Analysis)*

### Étape 2 : Audit Granulaire (Les Micro-Agents)
Traquez les ambiguïtés et forcez la normalisation technique.
```bash
./venv/bin/python extract/granular_audit.py
```
➡️ **Livrable** : `data/granular_audit_report.md` (Vos alertes techniques)

### Étape 3 : Synthèse & Baseline (Reverse TOGAF)
Générez la matrice de conformité métier et l'évaluation des risques.
```bash
./venv/bin/python extract/phase3/composer.py
```
➡️ **Livrable** : `data/gap_analysis_report.md` (Votre matrice de décision)

---

### 🕵️ Outil d'Investigation (En cas de besoin)
Si un rapport remonte un blocage sévère, utilisez l'Agent QA interactif pour investiguer la source :
```bash
./venv/bin/python extract/rfp_agent.py "Explique-moi les détails de la page 42 sur la sécurité."
```

---

🔒 **Confidentialité Totale** : Ce système tourne **100% en local** via Ollama. Vos documents ne quittent jamais votre environnement.
*(Détails techniques pour les ingénieurs dans [ARCHITECTURE.md](ARCHITECTURE.md))*
