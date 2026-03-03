# 🏭 Augmented BID IA — Intelligence Déterministe pour Appels d'Offres

> 💡 **Nouveau sur le projet ?** Lisez notre [📖 Guide complet du fonctionnement](GUIDE_COMPLET.md) pour comprendre la méthodologie "Dissocier & Traiter".

**L'IA qui transforme le "bruit" des documents commerciaux en spécifications d'ingénieur rigoureuses. 100% local, confidentiel et déterministe.**

---

## 🗺️ La Méthodologie : Dissocier pour mieux Traiter

Contrairement aux IA classiques qui "résument" sans rigueur, ce système suit une chaîne de montage industrielle :

### Phase 1 : Ingestion & Décomposition (Dissocier)
L'objectif est d'isoler l'information pour éliminer le bruit tout en garantissant la traçabilité.
- **Parser Structurel :** Chaque titre, tableau ou annexe est extrait et transformé en un **objet JSON** autonome.
- **Routage Métier :** Chaque fragment est classifié par contexte (Sécurité, Performance, Fonctionnel).
- **Ancrage Immuable :** Une fois stocké en base vectorielle, le fragment est "scellé" à sa source. Aucune dérive sémantique n'est possible.

### Phase 2 : Analyse Granulaire (Traiter - Les Micro-Agents)
C'est le cœur du déterminisme. Trois micro-agents travaillent en chaîne de montage :
1.  **Agent BABOK (Normalisation)** : Traduit le langage naturel en structure atomique : `Condition + Sujet + Action + Objet + Contrainte`.
2.  **Agent Radar à Loups (Désambiguïsation)** : Traque les termes flous (*ergonomique, rapide, moderne*). Bloque l'exigence tant que l'ambiguïté n'est pas levée.
3.  **Agent de Complétude (ISO 25010)** : Identifie les exigences implicites manquantes (ex: stockage sans suppression) et génère des **Gap Tickets**.

---

## 🚀 Guide d'Utilisation

### 1. Dissocier (Ingestion)
Apprenez le document à l'IA.
```bash
./venv/bin/python extract/main.py --input data/input/mon_rfp.pdf
```

### 2. Traiter (Audit Granulaire ✨)
Activez la chaîne de montage des Micro-Agents.
```bash
./venv/bin/python extract/granular_audit.py
```
➡️ Rapport de désambiguïsation : `data/granular_audit_report.md`

### 3. Comparer (Gap Analysis)
Vérifiez la conformité par rapport à votre catalogue.
```bash
./venv/bin/python extract/phase2/compliance.py
```

---

🔒 **Confidentialité** : Système 100% local. Vos documents ne quittent jamais votre machine.
*(Détails techniques dans [ARCHITECTURE.md](ARCHITECTURE.md))*
