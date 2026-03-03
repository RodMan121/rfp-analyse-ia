# 🏗️ Architecture Déterministe : FSM-Driven Engine

Ce document décrit l'organisation de l'Usine à RFP basée sur une Machine à État Finis.

---

## 📊 1. Modèle Conceptuel (L'Usine en 3 Phases)

```mermaid
graph TD
    subgraph "PHASE 1 : Dissocier"
        A[📄 Document Brut] -->|Docling| B(🧩 Fragments Atomiques)
        B -->|Hash MD5| C[(🗄️ Base Immuable)]
    end
    
    subgraph "PHASE 2 : Traiter (FSM)"
        C -->|Requirement Harvester| D[Industrial Scanning]
        D -->|Unified LLM Call| LLM{Ollama OR Gemini}
        LLM -->|Agent BABOK| E{NORMALIZED}
        E -->|Agent Radar| F{CLEAN}
        F -->|Agent ISO| G{AUDITED}
        F -.->|Score > 0| H[🚩 STALLED]
    end
    
    subgraph "PHASE 3 : Associer"
        G -->|Certification| I{BASELINE}
        I --> J[📄 Rendu Markdown]
        I --> K[💾 Rendu JSON ALM]
    end
```

---

## 🎨 2. Certification & Produits de Sortie (Output Node)

La Phase 3 génère deux artefacts certifiés dès que l'état **BASELINE** est atteint :

### A. Le Livrable Humain (`technical_baseline_final.md`)
Un document structuré pour les décideurs et les architectes. Il contient la matrice MoSCoW, le score d'intégrité Reverse TOGAF et le catalogue complet des exigences validées.

### B. Le Livrable Machine (`technical_baseline_alm.json`)
Un fichier structuré avec tous les attributs techniques (UID, Sujet, Action, Objet, Contrainte). Ce fichier est conçu pour être importé par script dans des outils de gestion des exigences (ALM).

---

## 🛠️ 3. Intégrité, Sûreté & Observabilité

- **Project UID :** Le sceau d'immuabilité (ALM-XXXX) est un hash calculé sur l'intégralité des exigences certifiées. Toute modification ultérieure briserait cette signature.
- **Fail-Safe :** Une exigence ne peut atteindre l'état BASELINE si son score d'ambiguïté en Phase 2 n'est pas strictement égal à zéro.
- **Observabilité :** Le système intègre un `factory_logger` (Phase 2 & 3) qui trace chaque événement industriel (début de scan, certification, erreurs de pipeline) pour une maintenance préventive facilitée.
