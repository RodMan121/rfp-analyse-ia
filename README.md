# 🏭 Augmented BID IA — Usine à RFP (FSM-Driven)

**Transformer les Appels d'Offres flous en Technical Baselines immuables. Une approche déterministe basée sur une Machine à État (FSM) pour une auditabilité totale.**

---

## 📂 Arborescence du Projet

Voici l'organisation de votre usine IA :

```text
.
├── 📂 extract/              # 🧠 LE MOTEUR (Code Source)
│   ├── phase1/              # Dissociation : Ingestion & Indexation
│   ├── phase2/              # Traitement : Micro-Agents & FSM
│   ├── phase3/              # Association : Synthèse & Baseline
│   ├── main.py              # Point d'entrée de l'usine
│   ├── rfp_agent.py         # L'Agent expert (Q&A)
│   ├── granular_audit.py    # Script d'audit stratégique
│   └── split_pdf.py         # Utilitaire pour les gros documents
│
├── 📂 data/                 # 🗄️ LE COFFRE-FORT (Données Locales)
│   ├── input/               # Vos PDF originaux (RFP, catalogues)
│   ├── output_images/       # Captures PNG des pages (Preuves Vision)
│   ├── output_json/         # Cache technique des fragments
│   ├── chroma_db_hierarchical/ # Base de données vectorielle immuable
│   ├── prompt.md            # Votre fichier de questions complexes
│   ├── gap_analysis_report.md  # Rapport final de conformité
│   └── granular_audit_report.md # Rapport final technique (loups)
│
├── 📂 venv/                 # ⚙️ L'ENVIRONNEMENT (Python)
├── ARCHITECTURE.md          # Guide technique profond
├── GUIDE_COMPLET.md         # Manuel opérationnel des flux
└── README.md                # Cette présentation
```

---

## 🗺️ Cartographie des Flux

### 📥 Entrées (Inputs)
- **`data/input/`** : Déposez ici vos PDF.
- **`data/prompt.md`** : Écrivez vos questions ici.

### 📤 Sorties (Outputs)
- **`data/granular_audit_report.md`** : Liste les ambiguïtés et les manques du client.
- **`data/gap_analysis_report.md`** : Matrice GTM montrant votre conformité.
- **`data/output_images/`** : Preuves visuelles utilisées par l'IA Vision.

---

## 🚀 Guide d'Utilisation Rapide

1.  **Dissocier** : `python extract/main.py --input data/input/mon_rfp.pdf`
2.  **Traiter** : `python extract/granular_audit.py`
3.  **Associer** : `python extract/phase3/composer.py`

---

🔒 **Confidentialité** : Le dossier `data/` est exclu de Git via `.gitignore`. Vos documents confidentiels restent chez vous.
*(Détails techniques dans [ARCHITECTURE.md](ARCHITECTURE.md))*
