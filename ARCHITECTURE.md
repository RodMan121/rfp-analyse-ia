# 🏗️ Architecture Technique : Gestion des Flux et Cycle de Vie

Ce document détaille la transformation des fichiers d'entrée en produits de sortie immuables.

---

## 📥 Les Entrées (Single Source of Truth)

### 1. Dossier `data/input/`
Le système est conçu pour traiter des PDF complexes. 
- **Intégrité :** Le PDF d'origine n'est jamais modifié.
- **Multi-source :** Vous pouvez mélanger RFP client et catalogues internes en utilisant le paramètre `--collection`.

### 2. Fichier `data/prompt.md`
Utilisé par l'Agent QA (`rfp_agent.py`) pour des requêtes complexes.
- **Rôle :** Permet de structurer des prompts multi-lignes, incluant des exemples ou des contraintes de formatage pour l'IA.

---

## 📤 Les Sorties (Technical Artifacts)

### 1. Vision : `data/output_images/`
Lors de la Phase 1 (Dissocier), Docling extrait chaque page en PNG.
- **Utilité :** Ces images servent de "preuve visuelle" pour le modèle **Llama 3.2 Vision**. L'agent s'y réfère pour analyser les diagrammes ou les tableaux complexes.

### 2. Cache : `data/output_json/`
Contient les fichiers `.fragments.json`.
- **Rôle :** Stocke la décomposition structurelle (titres, paragraphes, métadonnées).
- **Vérification de fraîcheur :** Le système compare la date du PDF avec celle du JSON. Si le PDF change, le cache est invalidé.

### 3. Rapports Stratégiques (`.md`)
- **`granular_audit_report.md` :** Sortie de la Phase 2. Met en évidence les risques sémantiques (loups) et les suggestions ISO 25010.
- **`gap_analysis_report.md` :** Synthèse métier. Compare les exigences validées avec votre savoir-faire.

### 4. Database : `data/chroma_db_hierarchical/`
La base vectorielle ChromaDB.
- **ID MD5 :** Chaque fragment est scellé par un ID unique calculé sur son contenu.
- **États FSM :** La base stocke l'état courant de l'exigence (`RAW` ➔ `BASELINE`).

---

## 📊 Résumé de la Transformation

```text
[PDF Brut] ➔ [PNG + JSON Cache] ➔ [Vecteurs ChromaDB] ➔ [Rapports Markdown]
   (RAW)          (CLASSIFIED)         (NORMALIZED)          (BASELINE)
```
