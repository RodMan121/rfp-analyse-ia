# 🔰 Guide Débutant : Comprendre Augmented BID IA

Si vous n'êtes pas un expert en IA, ce guide est fait pour vous. Voici comment votre machine "lit" et "comprend" vos appels d'offres (RFP).

## 1. Le Concept : Un "Cerveau Privé" pour vos documents
Imaginez que vous avez un document de 500 pages. Normalement, pour trouver une info, vous faites `Ctrl+F`. Mais `Ctrl+F` ne cherche que les mots exacts. 
Notre outil, lui, comprend le **sens**. Si vous cherchez "sécurité", il trouvera aussi les paragraphes qui parlent de "chiffrement" ou de "protection des données".

---

## 2. Les 4 étapes expliquées simplement

### 🧩 Étape 1 : Le Découpage Intelligent (Docling)
*   **Analogie** : Imaginez un livre que l'on découpe en petites fiches.
*   **Pourquoi c'est spécial ?** Au lieu de couper au milieu d'une phrase, l'outil reconnaît les titres ("Chapitre 1", "SLA") et les tableaux. Il crée des fiches intelligentes qui savent à quel chapitre elles appartiennent.

### 🗄️ Étape 2 : La Bibliothèque Magique (ChromaDB)
*   **Analogie** : On range ces fiches dans une bibliothèque où les livres sont classés par **idée** et non par ordre alphabétique.
*   **Le "GPS" du texte** : Chaque fiche reçoit une coordonnée géographique. Les idées proches (ex: "Argent" et "Budget") sont rangées sur la même étagère.

### 🎯 Étape 3 : Le Filtre de Haute Précision (Le Reranker)
*   **Analogie** : C'est un assistant qui passe après le bibliothécaire.
*   **Son rôle** : Si vous demandez "Quelles sont les pénalités ?", le bibliothécaire remonte 20 fiches qui parlent de pénalités. L'assistant (le Reranker) les lit toutes très vite et ne garde que les 5 fiches qui donnent **vraiment** la réponse.

### 🧠 Étape 4 : L'Expert qui vous répond (Ollama)
*   **Analogie** : C'est l'expert à qui on donne les 5 meilleures fiches et qui rédige une réponse claire pour vous.
*   **Local et Privé** : Tout se passe dans votre ordinateur. Aucune donnée ne sort chez Google ou OpenAI. C'est le mode "Ollama".

---

## 3. Le Super-Pouvoir : La Vision 🖼️
L'outil ne se contente pas de lire. Si vous lui posez une question sur un schéma ou une maquette, il va :
1.  Chercher la page du schéma.
2.  "Regarder" l'image avec un œil électronique (Llama 3.2 Vision).
3.  Vous décrire ce qu'il voit (ex: "Il y a un bouton Valider en bas à droite").

## 4. Comment l'utiliser en 2 commandes ?

1.  **Pour apprendre le document à l'IA** :
    `python extract/main.py --input mon_fichier.pdf`
2.  **Pour lui poser une question** :
    `python extract/rfp_agent.py "Ta question ici"`
