# 📖 Manuel de l'Usine : Exploiter les Livrables

Ce guide explique comment utiliser les fichiers générés à la fin du cycle de vie des exigences.

---

## 🏗️ L'arborescence des Sorties (Outputs)

```text
data/
├── technical_baseline_final.md  <-- POUR LES HUMAINS (Lire & Valider)
└── technical_baseline_alm.json  <-- POUR LES MACHINES (Importer & Tracer)
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
