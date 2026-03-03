# 🔰 Guide Débutant : Augmented BID IA (V2.2)

Si vous n'êtes pas un expert en IA, ce guide est fait pour vous. Voici comment votre machine "lit" et "comprend" vos appels d'offres (RFP) avec une précision professionnelle.

---

## 1. Pourquoi est-ce plus intelligent qu'une recherche Google ?
Normalement, pour trouver une info, vous faites `Ctrl+F`. Mais `Ctrl+F` ne cherche que les mots exacts. 
Notre outil utilise une **Recherche Hybride** :
1.  **Le Cerveau (Vecteurs)** : Il comprend le sens. Si vous cherchez "Argent", il trouve "Budget".
2.  **La Loupe (Mots-clés)** : Il trouve les références exactes comme "Article 12.3" ou "ISO 27001".
L'algorithme **RRF** mélange les deux pour vous donner la réponse parfaite.

---

## 2. Le Super-Pouvoir de l'Audit 🛡️
L'outil ne se contente pas de répondre, il **compare**.
- Vous lui donnez l'Appel d'Offres du client.
- Vous lui donnez votre catalogue de services.
- Il rédige pour vous une **Matrice de Conformité** avec des ✅, ⚠️ et ❌.

---

## 3. Comment l'utiliser très simplement ? ✨

### Étape A : Apprendre les documents à l'IA
Posez vos fichiers PDF dans le dossier `data/input/` puis lancez :
`python extract/main.py --input data/input/votre_document.pdf`

### Étape B : Poser une question (Méthode Facile)
Au lieu de taper dans le terminal :
1.  Ouvrez le fichier **`data/prompt.md`**.
2.  Écrivez votre question à l'intérieur (ex: "Quels sont les délais de livraison ?").
3.  Lancez juste : `python extract/rfp_agent.py`.
L'IA lira votre fichier et affichera sa réponse.

---

## 4. Est-ce que je peux lui faire confiance ? 📋
Oui, car l'outil génère un **Rapport de Confiance** (`data/confidence_report.md`).
Il vous dira honnêtement : "Sur cette partie, je suis sûr à 90%" ou "Ici, le texte était illisible, j'ai besoin de vous".

---

🔒 **Zéro Cloud** : Vos documents restent sur votre ordinateur. Rien ne part sur Internet (sauf si vous utilisez explicitement le moteur Gemini optionnel).
