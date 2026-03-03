# 📓 Journal de Bord : Augmented BID IA

## ✅ Étapes franchies (Fait !)

### Phase 1 : Ingestion & Décomposition (Dissocier)
- [x] Découpage structurel des PDF (IBM Docling).
- [x] Ancrage déterministe avec ID MD5 unique par fragment.
- [x] Recherche Hybride RRF (ChromaDB + BM25).

### Phase 2 : Analyse Granulaire & FSM (Traiter)
- [x] Refonte en architecture Micro-Services autonomes.
- [x] Implémentation du cycle de vie FSM (`RAW` ➔ `CLEAN`).
- [x] **Agent BABOK** : Normalisation "Sujet-Action-Objet".
- [x] **Agent Radar** : Fonction de blocage (score d'ambiguïté).
- [x] **Agent ISO 25010** : Inférence de complétude.

### Phase 3 : Synthèse & Baseline (Associer)
- [x] Constructeur Matrice MoSCoW.
- [x] Génération de matrice de Transitions d'États.
- [x] Moteur Reverse TOGAF avec scoring d'intégrité (1 à 5).
- [x] Output "ALM Ready" (Technical Baseline Immuable).

## 🚀 Prochaines étapes (Backlog)
- [ ] Connecteur d'export vers ALM (Jira / Confluence / DOORS).
- [ ] Interface Web Dashboard (Streamlit).
- [ ] Validation humaine dans la FSM (Interface pour débloquer les états `STALLED`).

---
*Dernière mise à jour : 3 mars 2026*
