# 🏗️ Architecture Déterministe : FSM-Driven Engine

Ce document décrit l'organisation de l'Usine à RFP basée sur une Machine à État Finis (FSM).

---

## 📊 1. Cycle de Vie de l'Exigence

Chaque fragment d'information est un objet `FSMRequirement` qui transite entre les états suivants :

| État | Agent Responsable | Condition de Sortie |
|---|---|---|
| **RAW** | `DoclingDecomposer` | Extraction réussie |
| **CLASSIFIED** | `SemanticRouter` | Contexte métier affecté |
| **NORMALIZED** | `BABOKAgent` | Structure Sujet-Action-Objet validée |
| **CLEAN** | `WolfRadarAgent` | **Score d'ambiguïté = 0** |
| **AUDITED** | `CompletenessAgent` | Inférence ISO 25010 effectuée |
| **BASELINE** | `ArchitectureComposer` | Intégration dans le rendu final |

---

## 🔬 2. Logique de Blocage (Désambiguïsation)

L'agent **Radar à Loups** agit comme un gardien de transition. 
- Si l'IA détecte un adjectif qualitatif non mesurable (*rapide, ergonomique, moderne*), elle refuse la transition vers l'état `CLEAN`.
- L'exigence est marquée comme `STALLED`. Elle nécessite une intervention humaine ou une clarification client pour reprendre son cycle.

---

## 🎨 3. Synthèse & Baseline Technique

La Phase 3 réassemble uniquement les exigences ayant atteint l'état **AUDITED**.
- **Technical Baseline :** Un document JSON/Markdown immuable, prêt à être injecté dans un outil d'ALM (Jira, Doors, etc.).
- **Reverse TOGAF :** Un score d'intégrité (1 à 5) est calculé pour évaluer la cohérence de la Baseline sur les domaines Métier, Données, Application et Technologie.

---

## 🛠️ Stack Technique
- **Pipeline Orchestrator :** `FSMPipeline` (Python).
- **LLM :** Ollama (Qwen 2.5).
- **Standards :** BABOK, ISO 25010, TOGAF.
- **Trace :** Historique d'état immuable par objet.
