# 🏭 Augmented BID IA — Usine à RFP (FSM-Driven)

**Transformer les Appels d'Offres flous en Technical Baselines immuables. Une approche déterministe basée sur une Machine à État (FSM) pour une auditabilité totale.**

---

## 🗺️ Cartographie des Flux

### 📥 Entrées (Inputs)
- **`data/input/`** : Vos documents sources (RFP, CCTP, Catalogues). C'est l'unique matière première.

### 📤 Sorties (Outputs)
- **`data/granular_audit_report.md`** : Liste les ambiguïtés et les manques du client (Phase 2).
- **`data/gap_analysis_report.md`** : Matrice GTM montrant votre conformité (Phase 3).
- **`data/output_images/`** : Preuves visuelles utilisées par l'IA Vision pour l'audit.

---

## 🚀 Guide d'Utilisation Automatisé

1.  **Dissocier (Phase 1)** : Apprenez le document à l'IA.
    ```bash
    ./venv/bin/python extract/main.py --input data/input/mon_rfp.pdf
    ```
2.  **Traiter (Phase 2 ✨)** : Lancez l'audit automatique via les Micro-Agents (BABOK, Loup, ISO).
    ```bash
    ./venv/bin/python extract/granular_audit.py
    ```
3.  **Associer (Phase 3)** : Générez la Technical Baseline et le Reverse TOGAF.
    ```bash
    ./venv/bin/python extract/phase3/composer.py
    ```

---

💡 **Besoin d'investigation ?** Utilisez l'agent interactif pour poser des questions spécifiques sur un point bloqué : `./venv/bin/python extract/rfp_agent.py "Pourquoi l'exigence X est bloquée ?"`

---

🔒 **Confidentialité** : Système 100% local. Vos documents ne quittent jamais votre machine.
*(Détails techniques dans [ARCHITECTURE.md](ARCHITECTURE.md))*
