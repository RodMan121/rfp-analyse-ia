# 📖 Guide de l'Usine à RFP : Logique FSM

Ce guide explique comment piloter le cycle de vie des exigences dans le système.

---

## 🏭 Le Concept : Une Usine à État

Dans ce projet, une exigence n'est pas juste un texte, c'est une entité qui "grandit" à travers des états.

### 🧩 1. États Initiaux (Phase 1)
- **RAW** : Le texte vient d'être extrait du PDF.
- **CLASSIFIED** : On sait si c'est du technique, du prix ou de la sécurité.

### ⚙️ 2. Traitement Déterministe (Phase 2)
- **NORMALIZED** : L'IA a réécrit la phrase en Sujet-Action-Objet.
- **CLEAN** : L'IA confirme qu'il n'y a plus aucun mot flou (Score = 0). **Attention :** Si le client a écrit "très rapide", l'exigence reste bloquée ici.
- **AUDITED** : On a vérifié ce qui manquait (ISO 25010).

### 📦 3. Rendu Final (Phase 3)
- **BASELINE** : L'exigence est intégrée dans le catalogue final du projet.

---

## 🚦 Comment débloquer une exigence ?

Si vous voyez une exigence bloquée à l'état `NORMALIZED` (Ambiguïté > 0) :
1.  Consultez le `fuzzy_terms` dans le rapport granulaire.
2.  Clarifiez le point avec votre client.
3.  Une fois le texte précis injecté, l'IA validera le passage à l'état `CLEAN`.

---

## 🚀 Commandes de Contrôle

| Action | Commande | État Cible |
|---|---|---|
| **Démarrage** | `python main.py` | RAW ➔ CLASSIFIED |
| **Audit FSM** | `python granular_audit.py` | ➔ AUDITED |
| **Génération** | `python phase3/composer.py` | ➔ BASELINE |
