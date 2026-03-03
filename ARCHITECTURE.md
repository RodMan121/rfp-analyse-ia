# 🏗️ Sous le capot : L'Architecture du Système

Ce document explique comment les composants du projet collaborent pour produire une analyse de haute qualité.

---

## 📊 Le Voyage de la Donnée

Voici le chemin parcouru par votre PDF (diagramme simplifié) :

```text
📄 PDF BRUT
    |
    ▼
[⚙️ PARSER DOCLING] -> Découpe proprement (Sections, Tableaux)
    |
    ▼
[📦 TAGGING SÉMANTIQUE] -> Classe par métier (FINANCE, TECH, SÉCURITÉ)
    |
    ▼
[🗄️ DOUBLE INDEXATION]
    ├─► ChromaDB (Vecteurs pour le sens)
    └─► BM25 (Index textuel pour les mots exacts)
    |
    ▼
[🤖 AGENT IA] -> Fusionne les résultats (RRF) et répond (Streaming)
```

---

## 🧠 Les 3 Secrets de la Précision

### 1. La Fusion RRF (Reciprocal Rank Fusion)
C'est notre "juge de paix". Elle prend les 20 meilleurs résultats des vecteurs et les 20 meilleurs de l'index BM25. Elle ne garde que ceux qui sont bien classés dans les deux listes. 
*   **Résultat** : Une précision chirurgicale sur les termes techniques.

### 2. Le Reranking (FlashRank)
Avant de donner les textes à l'IA, un mini-cerveau ultra-rapide les relit pour s'assurer que le contenu répond **réellement** à la question. Il trie les documents du plus pertinent au moins pertinent.

### 3. La Vision Cognitive
Si vous demandez d'analyser un schéma, l'agent bascule automatiquement sur le modèle **Llama 3.2 Vision**. Il récupère l'image de la page correspondante et la "regarde" pour vous.

---

## 🛠️ Stack Technique
- **LLM Local** : Ollama (Qwen 2.5 / Llama 3.2 Vision).
- **Base Vectorielle** : ChromaDB (avec IDs MD5 déterministes).
- **Parsing** : IBM Docling (Extraction hiérarchique).
- **Reranker** : FlashRank.
- **Robustesse** : Tenacity (pour les retries API Gemini).

---

🔒 **Sécurité & Robustesse** : Le système utilise un cache de fragments (`.fragments.json`) qui ne se recharge que si le PDF source a été modifié.
