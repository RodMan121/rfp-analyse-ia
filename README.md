# 🏭 Augmented BID IA — Usine à RFP (FSM-Driven)

**Transformer les Appels d'Offres flous en Technical Baselines immuables. Une approche déterministe basée sur une Machine à État (FSM) pour une auditabilité totale.**

---

## 🗺️ La Méthodologie : Cycle de Vie de l'Exigence

Chaque information extraite suit un parcours strict validé par nos micro-agents. Si une exigence est floue, elle est **bloquée** tant qu'elle n'est pas clarifiée.

### Phase 1 : Ingestion (RAW ➔ CLASSIFIED)
- **Dissocier :** Extraction chirurgicale via Docling.
- **Ancrer :** Attribution d'un UID déterministe (Hash MD5).

### Phase 2 : Traitement (NORMALIZED ➔ CLEAN ➔ AUDITED)
- **Normaliser (Agent BABOK) :** Structure Sujet-Action-Objet.
- **Nettoyer (Agent Radar) :** Bloque la transition vers `CLEAN` si un "loup" sémantique est détecté.
- **Auditer (Agent Complétude) :** Inférence ISO 25010 pour détecter les manques.

### Phase 3 : Synthèse (➔ BASELINE)
- **Baseline Technique :** Réassemblage des exigences validées en une vision cible immuable (ALM Ready).
- **Reverse TOGAF :** Scoring d'intégrité système (1 à 5).

---

## 🚀 Guide d'Utilisation Rapide

### 1. Lancer l'Usine (Ingestion)
```bash
./venv/bin/python extract/main.py --input data/input/rfp.pdf
```

### 2. Audit de la Machine à État (FSM)
Vérifiez quelles exigences sont passées et lesquelles sont bloquées.
```bash
./venv/bin/python extract/granular_audit.py
```

### 3. Générer la Baseline
```bash
./venv/bin/python extract/phase3/composer.py
```

---

🔒 **Auditabilité Totale** : Chaque exigence porte son historique de transition `state_history`.
*(Détails techniques dans [ARCHITECTURE.md](ARCHITECTURE.md))*
