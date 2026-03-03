# 📖 Manuel de l'Usine : Le Workflow Automatisé

Ce guide explique comment piloter l'usine sans avoir à poser de questions manuelles.

---

## 🏗️ L'arborescence simplifiée

```text
data/
├── input/                  <-- VOTRE SEULE ENTRÉE
├── output_images/          <-- Dossier technique (Vision)
├── output_json/            <-- Dossier technique (Vitesse)
├── chroma_db_hierarchical/ <-- Dossier technique (Cerveau)
├── gap_analysis_report.md  <-- VOTRE LIVRABLE MÉTIER
└── granular_audit_report.md <-- VOTRE LIVRABLE TECHNIQUE
```

---

## ⚙️ Pourquoi n'y a-t-il plus de fichier "prompt" ?

Dans les versions précédentes, vous deviez écrire vos questions dans un fichier. Désormais, l'IA sait ce qu'elle doit chercher grâce aux **Micro-Agents** :

1.  **L'IA BABOK** sait qu'elle doit structurer chaque phrase.
2.  **L'IA Radar** sait qu'elle doit traquer les mots flous.
3.  **L'IA ISO** sait qu'elle doit vérifier la sécurité et la maintenance.

**Le travail manuel est remplacé par un processus industriel.**

---

## 🛠️ Utilisation de l'Agent d'Investigation

Si un rapport vous indique une anomalie, vous pouvez toujours "discuter" avec le document pour comprendre le problème :

```bash
# Exemple d'investigation ad-hoc
./venv/bin/python extract/rfp_agent.py "Explique-moi les détails de l'exigence sur le chiffrement page 12"
```

L'agent n'est plus votre outil principal, c'est votre **expert de secours** pour les cas difficiles.
