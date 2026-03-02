# 🏗️ Architecture Technique : Augmented BID IA (V2)

## 📊 Nouveau Flux de Précision (Phase 2)

### 1. Moteur de Recherche Hybride (Double Indexation)
Le système utilise désormais un couplage **Vecteurs + BM25**.
- **Vecteurs (SentenceTransformers)** : Capte l'intention et le sens global (ex: 'cybersécurité' -> 'protection des données').
- **BM25 (Textuel)** : Identifie les références exactes (ex: 'Article 4.2', 'ISO 27001').
- **Fusion** : L'agent récupère les 20 meilleurs candidats des deux mondes avant le reranking.

### 2. Tagging Sémantique (Classifier)
Lors de l'ingestion, chaque fragment est étiqueté (`ADMIN`, `TECHNIQUE`, `FINANCIER`, etc.).
- **Pourquoi ?** Cela permet à l'IA d'analyser les exigences par domaine métier et de filtrer le bruit.

### 3. Matrice de Conformité & Gap Analysis (GTM)
Le moteur d'audit (Phase 2) suit ce processus :
1. **Extraction (RFP)** : Identification des obligations du client.
2. **Retrieval (Catalogue)** : Recherche automatique dans votre référentiel de savoir-faire (`service_catalog`).
3. **Inférence de Conformité** : L'IA compare l'exigence client et votre preuve de savoir-faire pour déterminer le statut (`CONFORME`, `PARTIEL`, `NON_CONFORME`).

### 4. Agent Expert avec Mémoire
L'agent RFP n'est plus sans mémoire. Il conserve les 6 derniers échanges pour permettre un dialogue fluide (ex: questions de suivi).

---

## 🛠️ Stack Technique Mise à jour
- **BM25 Engine** : `rank_bm25` (Algorithme de ranking textuel).
- **Routage** : LLM-Based Routing (Qwen 2.5 décide si c'est de la vision ou du texte).
- **Audit Engine** : JSON Extraction (Ollama Qwen 2.5).
