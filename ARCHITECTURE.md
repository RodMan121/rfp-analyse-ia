# 🏗️ Architecture Technique : Augmented BID IA (V2.2)

Ce document détaille le fonctionnement interne du moteur.

---

## 📊 1. Pipeline d'Extraction Multimodal

Le système supporte deux moteurs d'extraction :
1.  **IBM Docling (Local)** : Parsing structurel hiérarchique, idéal pour la confidentialité totale.
2.  **Gemini 2.0 Flash (Cloud)** : Extraction avancée de schémas PlantUML, diagrammes d'architecture et relations logiques (nécessite une `GOOGLE_API_KEY`).

---

## 🧠 2. Recherche Hybride & Fusion RRF

Pour une précision chirurgicale, nous fusionnons deux index :
-   **Index Vectoriel (ChromaDB)** : Capture le contexte sémantique (Embeddings multilingual).
-   **Index Textuel (BM25)** : Capture les termes exacts (Articles, Normes, IDs).

### Formule RRF (Reciprocal Rank Fusion)
Nous utilisons l'algorithme standard avec une constante `k=60` :
`Score(d) = Σ (1 / (k + Rang(d, moteur)))`
Cela garantit que les documents bien classés dans les *deux* moteurs remontent en priorité.

---

## 🛡️ 3. Audit & Robustesse

### IDs Déterministes
Pour éviter les doublons lors de ré-indexations, chaque fragment possède un ID généré par un **Hash MD5** du contenu (`source + page + texte`).

### Cache de Fragments
Le fichier `.fragments.json` stocke le résultat du parsing. Le système vérifie la date de modification (`st_mtime`) du PDF source : si le PDF est plus récent que le cache, le parsing est relancé automatiquement.

### Gap Analysis Parallélisée
L'analyse de conformité utilise un `ThreadPoolExecutor`. Le nombre de threads est piloté par `OLLAMA_NUM_PARALLEL` pour s'adapter à la configuration de votre serveur Ollama.

---

## 🛠️ Stack Technique
- **LLM** : Ollama (Qwen 2.5)
- **Vision** : Llama 3.2 Vision
- **Vector Store** : ChromaDB
- **Reranker** : FlashRank
- **Retry Logic** : Tenacity (Exponentiel)
