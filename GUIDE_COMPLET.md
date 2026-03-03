# 📖 Manuel de l'Usine : Exploiter les Livrables

Ce guide explique comment utiliser les fichiers générés à la fin du cycle de vie des exigences.

---

## 🏗️ L'arborescence des Sorties (Outputs)

```text
data/
├── technical_baseline_final.md  <-- POUR LES HUMAINS (Lire & Valider)
├── Matrice_Conformite_RFP.xlsx  <-- MATRICE DE CONFORMITÉ (Format Client)
├── technical_baseline_alm.json  <-- POUR LES MACHINES (Importer & Tracer)
└── fsm_registry.json            <-- REGISTRE INTERMÉDIAIRE (Audit des agents)
```

---

## 🚀 Le Workflow Industriel (3 Étapes)

### 1. Ingestion (Phase 1)
Préparez la matière première.
```bash
python extract/main.py --input data/input/mon_rfp.pdf
```
### 2. Moissonnage (Phase 2)
Lancez l'usine de traitement complète. `requirement_harvester.py` scanne **l'intégralité** de la base immuable de manière asynchrone (parallèle).

```bash
python extract/requirement_harvester.py
```

**🔧 Optimisation (Tuning) :**
Si vous avez un GPU avec peu de VRAM (ex: 4 Go), vous pouvez ajuster les performances dans `requirement_harvester.py` :
- `MAX_CONCURRENT_REQUESTS` : Nombre de fragments traités en même temps (Défaut : 2).
- `num_ctx` (dans `micro_agents.py`) : Taille de la mémoire réservée pour chaque fragment (Défaut : 1024).

---

### 3. Certification (Phase 3)
Générez les livrables finaux (Markdown, JSON et Excel).
```bash
# Générer le rapport Markdown et JSON
python extract/phase3/composer.py

# Générer la matrice de conformité Excel
python extract/phase3/excel_generator.py
```

---

## 📄 1. Le Rapport Markdown (`technical_baseline_final.md`)

**À quoi ça sert ?**
C'est votre document officiel de revue. Il résume tout le travail des agents :
- **Priorités MoSCoW** : Voyez tout de suite ce qui est "Must have".
- **Catalogue Atomique** : Chaque phrase est présentée sous sa forme normalisée (Sujet/Action/Objet).
- **Auditabilité** : Vous voyez le chemin parcouru par chaque exigence (RAW ➔ AUDITED).

**Conseil :** Imprimez-le en PDF pour le joindre à votre proposition commerciale comme annexe technique certifiée.

---

## 💾 2. L'Artefact JSON (`technical_baseline_alm.json`)

**À quoi ça sert ?**
C'est le fichier qui permet de connecter Augmented BID IA au reste de votre chaîne de production logicielle.
- **ALM Integration** : Vous pouvez utiliser ce fichier pour créer automatiquement des tickets Jira ou alimenter un outil comme Confluence.
- **Sceau d'Immuabilité** : Le `project_uid` présent à l'intérieur garantit que ce fichier n'a pas été modifié "à la main" après sa génération par l'IA.

---

## 📊 3. La Matrice de Conformité Excel (`Matrice_Conformite_RFP.xlsx`)

**À quoi ça sert ?**
C'est le document de travail pour votre réponse commerciale.
- **Tri MoSCoW** : Les exigences sont réparties dans des onglets (MUST, SHOULD, COULD).
- **Anti-Bruit** : Les scories du document (sommaires, etc.) sont isolées dans un onglet dédié pour audit.
- **Prêt pour le Chiffrage** : Vous pouvez ajouter vos propres colonnes (Estimation, Responsable) directement dans ce fichier.

---

## 🚀 Le mot de la fin

Votre usine est maintenant un système complet. Elle ne se contente pas d'analyser, elle **produit** des artefacts de niveau industriel. Bonne analyse !
