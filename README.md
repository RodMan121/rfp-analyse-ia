# 🏭 Augmented BID IA — Votre Expert en Appels d'Offres

> 💡 **Nouveau sur le projet ?** Lisez notre [📖 Guide complet du fonctionnement](GUIDE_COMPLET.md) pour tout comprendre en 5 minutes.

**L'IA qui transforme vos documents flous en spécifications d'ingénieur. 100% local, confidentiel et multimodal.**

---

## 🌟 La Puissance des Micro-Agents

Contrairement à une IA classique, notre système utilise une "chaîne de montage" d'experts :

```text
CLIENT : "Le logiciel doit être moderne et rapide."
   │
   ▼
[AGENTS D'ANALYSE]
   │
   ├─ 📖 BABOK : Traduit en "Le Système doit répondre en < 2s"
   ├─ 🐺 LOUPS : Alerte sur le mot flou "moderne"
   └─ 🛡️ ISO   : Suggère d'ajouter une clause de maintenance
   │
   ▼
VOUS : Une réponse précise, chiffrable et sans risque.
```

---

## 🚀 Guide d'Utilisation Rapide

### 1. Ingestion (Apprentissage)
```bash
./venv/bin/python extract/main.py --input data/input/votre_rfp.pdf
```

### 2. Audit Granulaire (Stratégique ✨)
Traquez les ambiguïtés et les manques techniques.
```bash
./venv/bin/python extract/granular_audit.py
```
➡️ Consultez `data/granular_audit_report.md`

### 3. Gap Analysis (Métier)
Vérifiez votre conformité par rapport à votre catalogue.
```bash
./venv/bin/python extract/phase2/compliance.py
```

---

🔒 **Confidentialité** : Ce système tourne **100% en local**. Rien n'est envoyé sur internet.
*(Détails techniques dans [ARCHITECTURE.md](ARCHITECTURE.md))*
