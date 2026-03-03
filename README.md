# 🏭 Augmented BID IA — Usine à RFP (FSM-Driven)

**Transformer les Appels d'Offres flous en Technical Baselines certifiées. Une approche déterministe basée sur une Machine à État (FSM) pour une auditabilité totale.**

---

## 🗺️ Cartographie des Flux

### 📥 Entrées (Matière Première)
- **`data/input/*.pdf`** : Vos documents sources (RFP, CCTP, catalogues).

### 📤 Sorties (Produits Certifiés)
Le système génère une **Technical Baseline** bi-format à la fin du processus :
1.  **`technical_baseline_final.md`** : Le livrable humain. Un catalogue élégant avec priorités MoSCoW et traçabilité FSM.
2.  **`technical_baseline_alm.json`** : Le livrable machine. Prêt pour l'import dans vos outils ALM (Jira, DOORS).
3.  **`granular_audit_report.md`** : Le rapport de "loups" sémantiques identifiés en Phase 2.

---

## 🚀 Guide d'Utilisation Automatisé (1-2-3)

1.  **Dissocier (Phase 1)** : Ingestion et ancrage immuable.
    ```bash
    ./venv/bin/python extract/main.py --input data/input/mon_rfp.pdf
    ```
2.  **Traiter (Phase 2 ✨)** : Moissonnage industriel par les Micro-Agents.
    ```bash
    # Utiliser le moissonneur pour un scan complet du document
    ./venv/bin/python extract/requirement_harvester.py
    ```
3.  **Associer (Phase 3 📦)** : Certification de la Baseline technique.
    ```bash
    ./venv/bin/python extract/phase3/composer.py
    ```

---

## 🛡️ Standards de Qualité & Ingénierie
Le code est audité et maintenu selon des standards rigoureux :
- **Haute Performance (Async)** : Architecture asynchrone complète via `asyncio`. Traitement parallèle des exigences avec gestion de concurrence.
- **Optimisation GPU (VRAM)** : Pilotage intelligent du contexte (`num_ctx`) et limitation de concurrence pour tourner sur des configurations modestes (4 Go VRAM).
- **Multi-Cloud & Local** : Support natif d'**Ollama** (Local), de l'**API Gemini** (Google) et d'**OpenRouter** (Cloud). Bascule intelligente selon les clés configurées.
- **Typage** : Vérification statique par `Mypy` (Python 3.12+).
- **Auditabilité** : Chaque exigence porte son `project_uid` unique et son historique de transition.

*(Détails techniques dans [ARCHITECTURE.md](ARCHITECTURE.md))*
