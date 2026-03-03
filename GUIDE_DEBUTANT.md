# 🔰 Guide Débutant : L'Usine à Appels d'Offres

Bienvenue ! Ce guide explique comment l'IA ne se contente plus de lire vos documents, mais les traite comme dans une véritable usine.

---

## 🏭 Le Concept : L'Usine en 3 Ateliers

Oubliez le concept du "Chatbot" (type ChatGPT) à qui vous posez des questions. Ici, nous avons construit une **Chaîne de Montage**.

### 1. Atelier de Découpage (La Dissociation)
Vous donnez un gros document PDF à l'usine. Les machines le découpent en centaines de petits paragraphes.
*   **Le truc malin :** Chaque paragraphe reçoit un "Code Barre" unique (un hash MD5). Impossible pour l'IA d'inventer une phrase qui n'existe pas, car on garde toujours la trace de son code barre.

### 2. Atelier de Traitement (Les Micro-Agents)
Chaque paragraphe passe ensuite sur un tapis roulant où trois "Robots Experts" l'analysent :
*   **Le Robot BABOK** : Il réécrit les phrases floues du client en vraies spécifications techniques.
*   **Le Radar à Loups** : Il cherche les mots dangereux (*"rapide", "efficace"*). S'il en trouve un, il met un feu rouge 🛑 (l'exigence est bloquée).
*   **Le Robot ISO** : Il vérifie ce que le client a oublié de dire (ex: "Vous parlez de paiement, mais pas de sécurité !").

### 3. Atelier d'Assemblage (La Synthèse)
L'usine récupère uniquement les paragraphes qui ont reçu un "Feu Vert" au deuxième atelier. Elle les assemble pour créer votre livrable final : une **Baseline Technique** propre, chiffrable et sans risque.

---

## 🚦 Comment utiliser l'usine ?

Vous êtes le chef d'atelier. Voici vos 3 commandes :

1.  **Démarrer les machines (Ingestion)** :
    Vous mettez le PDF dans `data/input/` et vous lancez :
    `python extract/main.py --input data/input/mon_document.pdf`

2.  **Lancer le tapis roulant (Audit Granulaire)** :
    Vous dites aux robots d'inspecter les pièces :
    `python extract/granular_audit.py`
    *(Vous lisez ensuite le rapport pour voir quelles pièces ont eu un feu rouge).*

3.  **Emballer le produit final (Synthèse)** :
    Vous générez le tableau Excel / Markdown :
    `python extract/phase3/composer.py`

---

## 🕵️ Et si je veux juste discuter avec mon document ?
Si vous avez besoin de comprendre pourquoi un point est bloqué, vous pouvez toujours utiliser le vieux système de "Chatbot" pour enquêter :
`python extract/rfp_agent.py "Pourquoi ce point est bloqué ?"`

---

🔒 **Votre Sécurité** : Cette usine est construite **dans votre ordinateur**. Aucune donnée confidentielle ne sort par les tuyaux d'internet.
