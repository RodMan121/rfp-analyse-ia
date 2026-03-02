# 📓 Journal du Projet & État d'Avancement

## ✅ Ce qui a été fait (Phase 1)
- [x] **Ingestion Hiérarchique** : Docling extrait les sections et le fil d'ariane.
- [x] **Capture Visuelle** : Snapshot automatique de chaque page en PNG.
- [x] **Vectorisation** : Stockage dans ChromaDB avec métadonnées complètes.
- [x] **Reranking** : Intégration de FlashRank pour la précision.
- [x] **Routage Vision** : Agent capable de basculer vers Llama 3.2 Vision.
- [x] **Documentation Pro** : Guide débutant, Architecture et Guide IA.

## 📍 État Actuel (Session du 02/03/2026)
- **Base de données** : `data/chroma_db_hierarchical` contient le document `RFP.pdf`.
- **Modèle de Vision** : Configuré sur `llama3.2-vision`.
- **Dernier test** : L'agent répond correctement sur les objectifs du projet via Ollama.

## 🚀 Prochaines Étapes suggérées
1.  **Interface Web** : Créer un petit micro-service FastAPI avec une interface Streamlit pour poser des questions via un navigateur.
2.  **Analyse de Conformité** : Créer un agent qui compare point par page le RFP avec une réponse type (Phase 2).
3.  **Export Excel** : Générer automatiquement un tableau de synthèse des exigences à partir des fragments extraits.
