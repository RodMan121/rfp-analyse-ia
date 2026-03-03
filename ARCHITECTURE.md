# 🏗️ Architecture Technique : Le Déterminisme au service du Bid

Ce document détaille la logique de traitement en deux phases : Dissociation et Traitement Granulaire.

---

## 🏭 Phase 1 : Ingestion & Décomposition (Dissocier)

L'objectif est d'isoler l'information pour éliminer le "bruit" contextuel tout en garantissant une traçabilité parfaite.

### 1. Parser Document (Objets JSON)
- **Action :** Extraction de la structure (titres, tableaux, annexes).
- **Format :** Chaque élément est transformé en un objet JSON contenant sa position hiérarchique (breadcrumbs) et sa page.
- **Résultat :** Une unité d'information "atomique".

### 2. Routeur / Classifier
- **Action :** Affectation d'un contexte métier (Sécurité, Performance, Fonctionnel).
- **Utilité :** Permet aux micro-agents de la Phase 2 d'appliquer des règles de complétude spécifiques au domaine.

### 3. Base Vectorielle & Immuabilité
- **Concept :** Gère l'**immuabilité**. 
- **Ancrage :** Une fois un fragment stocké, son ID (Hash MD5) le lie définitivement à sa position source. Cela interdit toute dérive sémantique lors des phases de génération suivantes.

---

## 🔬 Phase 2 : Analyse Granulaire (Traiter - Les Micro-Agents)

Cette phase est le cœur du déterminisme. Elle utilise trois agents spécialisés travaillant en chaîne de montage.

### 1. Agent Traducteur BABOK (Normalisation Atomique)
Il transforme le langage naturel souvent passif en exigences structurées.
- **Formule :** $\text{Condition} + \text{Sujet} + \text{Action} + \text{Objet} + \text{Contrainte}$.
- **Exemple :** 
    - *Entrée :* "L'accès doit être sécurisé."
    - *Sortie :* "Le Système [Sujet] DOIT authentifier [Action] l'Utilisateur [Objet] via un protocole MFA [Contrainte]."

### 2. Agent Radar à Loups (Désambiguïsation)
Il agit comme une fonction de hachage de la qualité sémantique.
- **Action :** Traque les "loups" (termes flous : *ergonomique, rapide, moderne*).
- **Statut :** Tant que le score d'ambiguïté n'est pas nul, l'exigence est bloquée dans l'état `PENDING_CLARIFICATION`.

### 3. Agent de Complétude (Inférence & ISO 25010)
Utilisant la norme ISO 25010, il identifie les **exigences implicites**. 
- **Action :** S'il détecte une fonction de "Stockage de données", il vérifie la présence de transitions d'états pour la "Suppression" ou le "Chiffrement". 
- **Sortie :** En cas d'absence, il génère automatiquement un **Gap Ticket**.

---

## 🛠️ Stack Technologique
- **Intelligence :** Ollama (Qwen 2.5 / Llama 3.2 Vision).
- **Indexation :** Hybrid Search (ChromaDB + BM25) avec Fusion RRF.
- **Standards :** BABOK, ISO 25010.
