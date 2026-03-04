# 🔰 Guide Débutant : Bienvenue à l'Usine (v13)

Ce guide utilise la métaphore de l'usine pour vous expliquer comment l'IA transforme un PDF complexe en une liste d'exigences claires.

---

## 🏭 Le Concept : Votre Document sur un Tapis Roulant

Imaginez que votre document PDF est une grosse pièce brute. Pour la traiter, nous allons la faire passer par **trois ateliers**.

### 🛠️ Atelier 0 : Le Brief du Chef (Initialisation)
Avant de démarrer, vous devez dire aux robots ce qu'ils vont traiter.
1.  Lancez `python extract/main.py --init-context`.
2.  Ouvrez `data/document_context.md` et écrivez simplement : *"C'est un RFP pour une application, les exigences sont de type BN-XXX et il y a des maquettes."*
3.  **C'est tout !** Vos robots sont maintenant briefés.

### ✂️ Atelier 1 : La Découpe (Phase 1)
Vous donnez votre PDF. Les machines le découpent en centaines de petits paragraphes atomiques.
*   **Magie de la Vision** : Si une image est un schéma technique, le robot la prend en photo pour l'analyser plus tard.
*   **Résultat** : Une base de données de fragments "bruts" (`data/chroma_db_hierarchical`).

### 🤖 Atelier 2 : Le Tapis des Experts (Phase 2)
C'est ici que le travail intelligent se fait. Chaque paragraphe défile sur un tapis roulant devant des robots experts :
1.  **Le Robot Vision** : Traduit les schémas en texte.
2.  **Le Robot BABOK** : Réécrit la phrase pour qu'elle soit claire (Sujet, Verbe, Complément).
3.  **Le Radar à Ambiguïté** : Si la phrase est floue (ex: *"le système doit être rapide"*), il allume un feu rouge 🚩. L'exigence est bloquée.

### 📦 Atelier 3 : L'Emballage (Phase 3)
On récupère uniquement les exigences qui ont reçu un feu vert. On les assemble dans de beaux rapports :
*   **Le Catalogue (Markdown)** pour votre lecture.
*   **La Matrice (Excel)** pour votre chiffrage.
*   **Le Fichier ALM (JSON)** pour vos outils de gestion (Jira).

---

## 🚀 Vos 4 Commandes "Coup de Poing"

| Étape | Commande à taper | Résultat attendu |
| :--- | :--- | :--- |
| **0** | `python extract/main.py --init-context` | Crée le fichier de description. |
| **1** | `python extract/main.py --input mon_rfp.pdf` | Découpe le PDF en fragments. |
| **2** | `python extract/requirement_harvester.py` | Fait travailler les robots experts. |
| **3** | `python extract/phase3/composer.py` | Génère les rapports finaux. |
| **4** | `python extract/phase3/excel_generator.py` | Produit la matrice Excel. |

---

## 🕵️ Envie de discuter avec le document ?
Si vous voulez poser une question précise sur un point de détail :
`python extract/rfp_agent.py "Quels sont les délais de livraison ?"`

🔒 **Confidentialité** : Tout se passe dans **votre ordinateur**. Rien n'est envoyé sur le cloud si vous utilisez Ollama.
