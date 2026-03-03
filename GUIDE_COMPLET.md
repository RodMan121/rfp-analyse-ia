# 📖 Manuel de l'Usine : Exploiter les Livrables

Ce guide explique comment utiliser les fichiers générés à la fin du cycle de vie des exigences.

---

## 🏗️ L'arborescence des Sorties (Outputs)

```text
data/
├── technical_baseline_final.md  <-- POUR LES HUMAINS (Lire & Valider)
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
Lancez l'usine de traitement complète. Contrairement à `granular_audit.py` qui ne fait qu'un échantillon, `requirement_harvester.py` scanne **l'intégralité** de la base immuable pour en extraire chaque exigence potentielle.
```bash
python extract/requirement_harvester.py
```
*Vérifiez ensuite les logs dans la console pour voir le taux de réussite.*

### 3. Certification (Phase 3)
Générez les livrables finaux.
```bash
python extract/phase3/composer.py
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

## 🚀 Le mot de la fin

Votre usine est maintenant un système complet. Elle ne se contente pas d'analyser, elle **produit** des artefacts de niveau industriel. Bonne analyse !
