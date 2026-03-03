# 📓 Journal du Projet & État d'Avancement

## ✅ Phase 1 : Ingestion & Analyse (TERMINÉE)
- [x] **Ingestion Hiérarchique** : Docling + Capture Visuelle.
- [x] **Double Indexation** : ChromaDB (Vecteurs) + BM25 (Mots-clés).
- [x] **Recherche Hybride** : Algorithme RRF (Reciprocal Rank Fusion).
- [x] **Cache de Fragments** : Chargement instantané via `.fragments.json`.
- [x] **IDs MD5** : Élimination des collisions d'indexation.

## ✅ Phase 2 : Audit & Conformité (TERMINÉE)
- [x] **Agent de Conformité** : Extraction automatique des exigences client.
- [x] **Gap Analysis** : Comparaison avec le catalogue de services.
- [x] **Rapport de Confiance** : Audit de la qualité d'ingestion (IA Self-Audit).
- [x] **Prompts Markdown** : Pilotage de l'agent via `data/prompt.md`.
- [x] **Parallélisation** : Gap Analysis multi-threadée.

## 🚀 Phase 3 : Interface & Accessibilité (EN COURS)
- [ ] **Interface Streamlit** : Rendre l'outil utilisable par des non-développeurs.
- [ ] **Dashboard de Conformité** : Vue d'ensemble graphique des ✅/⚠️/❌.
- [ ] **Export Excel Pro** : Génération de la matrice GTM au format .xlsx.
- [ ] **Multi-RFP Compare** : Comparer deux appels d'offres entre eux.

## 🛠️ Maintenance & Dette Technique
- [x] Migration PyPDF2 -> pypdf (v4).
- [x] Centralisation config modèles dans `.env`.
- [x] Logique de retry Gemini (Tenacity).
