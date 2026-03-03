# 📖 Guide complet du fonctionnement — rfp-analyse-ia

> Un outil IA pour analyser automatiquement les appels d'offres (RFP/CCTP). Ce guide explique comment chaque pièce du puzzle fonctionne.

---

## 🗺️ Vue d'ensemble — Comment ça s'articule ?

Le projet fonctionne en **deux grandes phases** :

1. **Ingestion** — on prépare le document une seule fois (l'apprentissage).
2. **Question/Réponse** — on interroge autant de fois qu'on veut.

```text
📄 Votre PDF
     │
     ▼
✂️  Découpe en fragments     (local_parser.py)
     │
     ▼
📦  Fragments + catégories
     │
     ├──────────────────────┐
     ▼                      ▼
🧠  ChromaDB (vecteurs)   🔤 BM25 (mots-clés)
     │                      │
     └──────────┬───────────┘
                ▼
           🎯  Reranker — Top 5        (reranker.py)
                ▼
❓  Question  ──► 🤖  LLM Ollama       (rfp_agent.py)
                ▼
           💬  Réponse citant les sources
```

---

## 📥 Étape 1 — Ingestion (`main.py`)

### C'est quoi ?
Le point d'entrée du programme. Son seul rôle : recevoir un PDF en argument et lancer le pipeline de traitement.

### 📬 Analogie
> Imaginez un **facteur**. Il reçoit un colis (le PDF), vérifie l'adresse (le chemin en argument), puis le confie à l'atelier de découpe. Il ne lit pas le contenu lui-même — il **orchestre**.

### Ce que fait `main.py` en 3 lignes de logique
```python
parser = DoclingParser()                        # Crée la machine à découper
fragments = parser.parse_to_fragments(fichier)  # Découpe le PDF en morceaux
store.add_fragments_batch(fragments)            # Stocke tout dans la base
```

### ⚙️ Le paramètre `--collection`
Vous pouvez avoir plusieurs bases séparées :
- `rfp_hierarchical` → pour les appels d'offres reçus.
- `service_catalog` → pour vos propres offres de services (votre savoir-faire).

C'est la même base de données physique, mais comme des **tiroirs différents**.

---

## ✂️ Étape 2 — Découpe (`local_parser.py`)

### C'est quoi ?
Ce fichier transforme un PDF brut en centaines de petits morceaux de texte intelligemment découpés. C'est lui qui fait le plus gros du travail de compréhension structurelle.

### 📖 Analogie
> Imaginez que vous devez résumer un livre de 200 pages. Vous ne le lisez pas d'un bloc — vous découpez d'abord par chapitres, puis paragraphes, en notant pour chaque extrait : *« chapitre 3 > section 2, page 47 »*. C'est exactement ce que fait ce fichier.

### Les 4 choses qu'il fait pour chaque PDF

**1 — 💾 Cache**
Si le PDF a déjà été traité, il recharge les résultats sauvegardés (plus rapide). Si le PDF a été **modifié depuis**, il recommence automatiquement l'analyse.

**2 — 📝 Extraction**
Il parcourt chaque élément du document : titres, paragraphes, tableaux. Il retient « où on est » dans la hiérarchie pour donner du contexte à l'IA.

**3 — 🏷️ Catégorisation automatique**
Pour chaque fragment, il détecte le thème en cherchant des mots-clés (TECHNIQUE, FINANCIER, JURIDIQUE, etc.).

**4 — ✂️ Découpe adaptative**
Les très longs paragraphes sont découpés en morceaux de **1 500 caractères max**, avec un **chevauchement de 200 caractères** pour ne pas couper une idée en plein milieu d'une phrase.

---

## 🗄️ Étape 3 — Indexation (`vectorstore.py`)

### C'est quoi ?
Une fois les fragments créés, il faut les stocker de façon à pouvoir les retrouver. Ce fichier gère **deux moteurs de recherche en parallèle**.

### 📚 Analogie : deux façons de trouver un livre
> - Chercher par **SENS** (*« je veux un livre sur la tristesse »*) → c'est **ChromaDB** (Vecteurs).
> - Chercher par **MOT EXACT** (*« je veux le livre avec le mot mélancolie »*) → c'est **BM25** (Mots-clés).

### 🔀 RRF — Reciprocal Rank Fusion
L'algorithme **RRF** fusionne les résultats : un fragment bien classé dans les **deux** moteurs remonte en tête. C'est la garantie d'une précision maximale.

### 🔑 IDs déterministes (hash MD5)
Chaque fragment a un identifiant unique calculé selon son contenu. Si vous réingérez le même document, il n'y a **jamais de doublons**.

---

## 🎯 Étape 4 — Reclassement (`reranker.py`)

### C'est quoi ?
La recherche remonte **20 candidats**. Le reranker en sélectionne les **5 meilleurs** avec une technique plus précise : le **Cross-Encoder**.

### 🕵️ Analogie : le recrutement
> **Phase 1** : on passe 1 000 CV en revue rapidement → 20 sont retenus.
> **Phase 2** (Reranker) : on fait passer un **entretien approfondi** aux 20 → on garde les 5 meilleurs.

---

## 🤖 Étape 5 — Agent Q&A (`rfp_agent.py`)

### C'est quoi ?
L'interface principale. L'utilisateur pose une question, l'agent trouve les fragments et génère une réponse avec un LLM local (Ollama).

### 🧠 La mémoire de conversation
L'historique est conservé. Au-delà de **8 messages**, l'IA en fait un **résumé** pour libérer de la place tout en gardant le fil de la discussion.

### 👁️ Mode Vision
Si la question porte sur un schéma, l'agent retrouve la page correspondante et utilise le modèle **Llama 3.2 Vision** pour "regarder" l'image PNG.

---

## ✅ Bonus — Audit de conformité (`compliance.py`)

### C'est quoi ?
Ce module automatise la **Gap Analysis**. Il liste les exigences du client et vérifie dans votre catalogue si vous savez y répondre.

### 📊 Résultat de l'audit
Il génère un tableau avec des statuts clairs :
| Statut | Confiance | Priorité | Exigence | Justification |
|---|---|---|---|---|
| ✅ | 92% | 🔴 | Certification ISO 27001 | Certifiés depuis 2022 |
| ❌ | 15% | 🔴 | Support 24/7 | Non couvert actuellement |

---

## 🚀 Commandes essentielles à retenir

```bash
# 1. Apprendre un document
python main.py --input document.pdf

# 2. Poser une question
python rfp_agent.py "Quels sont les SLA ?"

# 3. Lancer l'audit de conformité
python phase2/compliance.py
```
