# 📖 Manuel Opérationnel : Piloter l'Usine à RFP

Ce guide est votre manuel de pilotage. Il vous explique comment transformer un PDF commercial brut en une Technical Baseline rigoureuse, en maîtrisant les flux de données.

---

## 🗺️ Cartographie des Flux (Input / Output)

L'usine est organisée de manière stricte. Vous ne modifiez jamais les fichiers de sortie à la main.

### 📥 Entrées (Vos leviers d'action)
| Élément | Chemin | Rôle |
|---|---|---|
| **Documents Sources** | `data/input/*.pdf` | Vos RFP, CCTP, ou vos Catalogues de Services. |
| **Configuration** | `.env` | Paramétrage des modèles (Ollama/Gemini) et des workers de calcul. |
| *(Optionnel)* | `data/prompt.md` | Si vous souhaitez utiliser l'Agent QA en mode investigation ad-hoc. |

### 📤 Sorties (Générées par la Machine)
| Élément | Chemin | Rôle |
|---|---|---|
| **Base Vectorielle** | `data/chroma_db_hierarchical/` | La "Single Source of Truth" (SSOT). Contient les vecteurs et l'index BM25. |
| **Cache & Images** | `data/output_*/` | Accélérateurs de performance et preuves visuelles pour le multimodalisme. |
| **Audit Technique** | `data/granular_audit_report.md` | Liste des ambiguïtés (loups) bloquées par la machine d'état (FSM). |
| **Baseline Métier** | `data/gap_analysis_report.md` | Matrice de décision finale (MoSCoW, Conformité, TOGAF). |

---

## 🚀 Le Workflow Industriel (Le 1-2-3)

### Phase 1 : Dissocier (`main.py`)
*Le but : Garantir l'immuabilité.*

```bash
# Indexer le document cible (ex: le cahier des charges client)
python extract/main.py --input data/input/cahier_charges.pdf

# (Optionnel) Indexer votre référentiel pour la Gap Analysis
python extract/main.py --input data/input/mon_catalogue.pdf --collection service_catalog
```
**Ce qui se passe :** Le PDF est détruit en fragments. Chaque fragment reçoit un ID MD5 unique. Il est désormais "ancré" et impossible à falsifier.

---

### Phase 2 : Traiter (`granular_audit.py`)
*Le but : Activer la Machine à État (FSM).*

```bash
python extract/granular_audit.py --cat TECHNIQUE
```
**Ce qui se passe :** 
1. L'agent **BABOK** réécrit l'exigence (Sujet + Action).
2. L'agent **Radar à Loups** calcule l'ambiguïté. Si > 0, l'exigence est bloquée (`STALLED`).
3. L'agent **ISO 25010** génère des "Gap Tickets" pour les fonctions oubliées (ex: Sécurité).

➡️ **Votre Action :** Ouvrez `granular_audit_report.md`. Regardez les exigences bloquées. Clarifiez-les avec votre client.

---

### Phase 3 : Associer (`phase3/composer.py`)
*Le but : Générer la Technical Baseline finale.*

```bash
python extract/phase3/composer.py
```
**Ce qui se passe :**
Seules les exigences ayant passé avec succès les tests de la Phase 2 (`AUDITED`) sont utilisées. La machine génère une matrice MoSCoW, analyse le cycle de vie du système, et évalue le risque global via la méthode Reverse TOGAF.

➡️ **Votre Action :** Ouvrez `gap_analysis_report.md`. C'est votre feuille de route technique validée.

---

## 🕵️ En cas de blocage : L'Agent d'Investigation

L'outil `rfp_agent.py` n'est plus votre outil principal. C'est votre **Consultant de Secours**. 
Si l'audit Phase 2 bloque sur un paragraphe complexe, utilisez-le pour dialoguer avec la base de données de la Phase 1 :

```bash
python extract/rfp_agent.py "Explique les contraintes réseau de la page 45"
```
*(Vous pouvez aussi écrire une question longue dans `data/prompt.md` et lancer le script sans argument).*
