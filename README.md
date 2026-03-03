# 🏭 Augmented BID IA — Votre Assistant Privé pour Appels d'Offres

**Imaginez un expert qui lit 500 pages de documents techniques en 2 minutes, repère toutes les obligations cachées, et vérifie si votre entreprise sait y répondre. Le tout, sans jamais envoyer vos données confidentielles sur Internet.**

C'est exactement ce que fait **Augmented BID IA**.

---

## 🌟 Pourquoi ce projet est-il "Magique" ?

Si vous utilisez ChatGPT, vous envoyez vos documents chez OpenAI. Ici, le "cerveau" de l'IA est **dans votre ordinateur**.

| Ce que vous avez aujourd'hui | Ce que l'outil vous apporte |
|:---:|:---:|
| "Ctrl+F" pour chercher des mots exacts | Une recherche par **idées** (ex: cherche "Argent" -> trouve "Budget") |
| Des heures à lister les exigences | Une **Matrice de Conformité** générée en un clic |
| Le risque de fuite de données | Une **confidentialité totale** (100% local) |
| L'oubli des schémas techniques | Une IA qui **"regarde"** vos images et schémas |

---

## 🚀 Guide de démarrage (Le 1-2-3 facile)

### Étape 1 : Apprendre le document à l'IA
Mettez votre PDF dans le dossier `data/input/` et lancez cette commande :
```bash
./venv/bin/python extract/main.py --input data/input/votre_document.pdf
```
*L'IA découpe le document en milliers de fiches intelligentes et les range dans sa bibliothèque.*

### Étape 2 : Vérifier la qualité
L'IA a-t-elle bien "lu" ? Demandez-lui son rapport d'auto-critique :
```bash
./venv/bin/python extract/confidence_report.py --rfp "votre_document.pdf"
```
*Consultez `data/confidence_report.md` : l'IA vous avoue ce qu'elle n'a pas bien compris.*

### Étape 3 : Poser vos questions (La Méthode Facile ✨)
1. Ouvrez le fichier **`data/prompt.md`** avec un bloc-notes.
2. Écrivez votre question (ex: "Fais-moi un résumé des pénalités de retard").
3. Lancez : `./venv/bin/python extract/rfp_agent.py`
*La réponse s'affiche en direct, comme si l'IA vous parlait.*

---

## 📂 Où sont mes fichiers ?

- `extract/` : Le moteur (les câbles et les engrenages).
- `data/input/` : Déposez vos PDF ici.
- `data/gap_analysis_report.md` : Votre tableau de conformité final.

---

🔒 **Confidentialité** : Ce système est un coffre-fort. Rien ne sort de votre PC.
*(Pour les techniciens, les détails sont dans [ARCHITECTURE.md](ARCHITECTURE.md))*
