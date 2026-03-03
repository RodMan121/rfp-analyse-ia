# 🏗️ Architecture Déterministe : FSM-Driven Engine

Ce document décrit l'organisation de l'Usine à RFP, construite sur une Machine à État Finis (FSM) pour garantir la sûreté de fonctionnement et l'auditabilité.

---

## 📊 1. Modèle Conceptuel (L'Usine en 3 Phases)

Le système est conçu pour transformer un document flou en une "Technical Baseline" exploitable. 

```mermaid
graph TD
    subgraph "PHASE 1 : Dissocier"
        A[📄 Document Brut] -->|Docling| B(🧩 Fragments Atomiques)
        B -->|Hash MD5| C[(🗄️ Base Immuable)]
    end
    
    subgraph "PHASE 2 : Traiter (FSM)"
        C -->|Agent BABOK| D{NORMALIZED}
        D -->|Agent Radar| E{CLEAN}
        E -->|Agent ISO| F{AUDITED}
        E -.->|Score > 0| G[🚩 STALLED]
    end
    
    subgraph "PHASE 3 : Associer"
        F -->|MoSCoW & TOGAF| H[📦 TECHNICAL BASELINE]
    end
    
    H --> I[node: ALM Ready Output]
```

---

## 🔬 2. Cycle de Vie de l'Exigence (FSM)

Chaque fragment d'information est un objet `FSMRequirement` qui transite entre des états stricts :

| État Cible | Agent Responsable | Condition de Transition |
|---|---|---|
| **RAW** | `DoclingDecomposer` | Extraction structurelle réussie. |
| **CLASSIFIED** | `SemanticRouter` | Contexte métier affecté (ex: Sécurité). |
| **NORMALIZED** | `BABOKAgent` | Validation du format `Sujet + Action + Objet`. |
| **CLEAN** | `WolfRadarAgent` | **Score d'ambiguïté = 0** (Aucun adjectif flou). |
| **AUDITED** | `CompletenessAgent` | Inférence ISO 25010 effectuée (Gap Tickets générés). |
| **BASELINE** | `ArchitectureComposer` | Intégration dans le rendu ALM final. |

### 🛑 Logique de Blocage (Fail-Safe)
Si l'agent Radar détecte un terme qualitatif non mesurable (*"ergonomique, rapide, moderne"*), il **refuse** la transition vers l'état `CLEAN`. L'exigence est marquée comme `STALLED` et exclue de la Baseline jusqu'à intervention humaine.

---

## 🎨 3. Synthèse & Baseline Technique (Output Node)

La Phase 3 réassemble uniquement les exigences ayant atteint l'état **AUDITED**.
- **Technical Baseline Immuable :** Un document JSON (`technical_baseline_alm.json`), scellé par un UID déterministe. Il est prêt à être injecté dans un outil d'ALM (Jira, DOORS).
- **Auditabilité :** Chaque exigence porte son `state_history`, prouvant son passage par tous les ateliers de validation.
- **Reverse TOGAF :** Un score d'intégrité (1 à 5) évalue la viabilité sur les domaines Business, Data, Application et Technologie.

---

## 🛠️ 4. Stack Technique & Immuabilité

- **Identifiants Déterministes** : Chaque fragment possède un ID `hashlib.md5(source + page + texte)`.
- **Dédoublonnage** : L'API ChromaDB utilise `.upsert()`. Une ré-ingestion du même PDF est idempotente.
- **Micro-Services** : Chaque Agent hérite d'une classe de base `FSMAgent`, permettant une composition de pipeline à la volée.
- **Orchestration LLM** : Ollama (`qwen2.5:7b`) avec `ThreadPoolExecutor` (pilotable via `OLLAMA_NUM_PARALLEL`).
