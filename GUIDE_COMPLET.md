# 📖 Manuel de l'Usine : Code et Données

Ce guide détaille le rôle de chaque dossier et script pour vous aider à naviguer dans le projet.

---

## 🧠 1. Le Moteur (`extract/`)

C'est ici que réside toute l'intelligence. Le code est organisé selon les phases de notre méthodologie.

- **`phase1/` (Dissocier)** : 
    - `local_parser.py` : Le service qui découpe le PDF.
    - `vectorstore.py` : La gestion du cerveau (similarités et mots-clés).
    - `reranker.py` : Le filtre de précision.
- **`phase2/` (Traiter)** :
    - `micro_agents.py` : La chaîne de montage (BABOK, Loup, ISO).
    - `compliance.py` : Le moteur de comparaison métier.
- **`phase3/` (Associer)** :
    - `composer.py` : Le script qui crée la Technical Baseline et le Reverse TOGAF.
- **Scripts Racines** :
    - `main.py` : Le chef d'orchestre pour l'ingestion.
    - `rfp_agent.py` : L'interface interactive (votre consultant IA).
    - `granular_audit.py` : Le bouton magique pour traquer les "loups".

---

## 🗄️ 2. Le Coffre-fort (`data/`)

Ce dossier est votre espace de travail local. Il est vital de comprendre que ces fichiers sont **générés pour vous**.

- **`input/`** : Votre bibliothèque de départ. Rien ne se passe si ce dossier est vide.
- **`output_images/`** : Le stock de "photos" du document. Si vous les supprimez, l'agent ne pourra plus analyser les schémas.
- **`output_json/`** : Votre accélérateur de vitesse. Il contient les documents déjà "mâchés" par l'IA.
- **`chroma_db_hierarchical/`** : La base de données finale. C'est ici que l'IA va "piocher" ses réponses.

---

## ⚙️ 3. L'Environnement (`venv/` & `.env`)

- **`venv/`** : Contient toutes les bibliothèques (Docling, Ollama, ChromaDB). Ne modifiez jamais ce dossier manuellement.
- **`.env`** : Votre panneau de contrôle. C'est ici que vous dites à l'IA quel modèle utiliser (ex: Qwen 2.5) et où sont vos dossiers.

---

🔒 **Auditabilité** : Grâce à cette structure claire, vous pouvez tracer une réponse de l'agent (Phase 3) jusqu'à son fragment d'origine (Phase 1) et voir par quel état FSM elle est passée.
