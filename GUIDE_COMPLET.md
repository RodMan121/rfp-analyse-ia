# 📖 Guide complet du fonctionnement — rfp-analyse-ia

> Un outil IA pour analyser automatiquement les appels d'offres (RFP/CCTP). Ce guide explique comment chaque pièce du puzzle fonctionne.

---

## 🗺️ Vue d'ensemble — L'Intelligence Granulaire

Le projet est divisé en scripts spécialisés :

### 📥 1. Ingestion (`main.py`)
- Découpe le PDF (IBM Docling).
- Stocke les fragments dans une bibliothèque (ChromaDB + BM25).
- **Analogie** : Le Facteur qui trie le courrier.

### 🔬 2. Audit Granulaire (`granular_audit.py`)
- Fait passer chaque exigence par les **3 Micro-Agents**.
- Identifie les "loups" (ambiguïtés).
- Suggère des complétudes basées sur l'ISO 25010.
- **Analogie** : Le Labo d'analyse qui cherche les bactéries dans un échantillon.

### ✅ 3. Gap Analysis (`compliance.py`)
- Compare les exigences client avec votre catalogue de services.
- Génère la matrice GTM finale.
- **Analogie** : Le Juge qui compare le besoin et l'offre.

### 🤖 4. Agent Expert (`rfp_agent.py`)
- Répond à vos questions en utilisant tout le contexte (Texte + Vision).
- Se souvient des échanges passés (Mémoire courte).
- **Analogie** : Le Consultant Senior à qui vous pouvez tout demander.

---

## 🛠️ Configuration Stratégique (`.env`)

```bash
# Modèles LLM
OLLAMA_TEXT_MODEL=qwen2.5:7b
OLLAMA_VISION_MODEL=llama3.2-vision

# Parallélisme Ollama (Vitesse d'audit)
OLLAMA_NUM_PARALLEL=1
```

---

## 🚀 Flux de Travail Conseillé

1.  **Ingérer** le document : `python main.py --input doc.pdf`
2.  **Lancer l'audit granulaire** : `python granular_audit.py`
    - *Vérifiez les ambiguïtés dans `granular_audit_report.md`.*
3.  **Lancer l'audit de conformité** : `python compliance.py`
    - *Obtenez votre matrice de conformité dans `gap_analysis_report.md`.*
4.  **Affiner** avec l'agent expert pour les points de détail.
