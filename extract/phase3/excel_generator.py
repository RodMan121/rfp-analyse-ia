import json
import pandas as pd
from pathlib import Path
from loguru import logger

# Configuration des chemins
REGISTRY_PATH = Path("data/fsm_registry.json")
OUTPUT_EXCEL = Path("data/Matrice_Conformite_RFP.xlsx")

class ExcelGenerator:
    """Générateur de matrice de conformité Excel avec filtrage anti-bruit et MoSCoW."""

    def __init__(self, registry_path: Path):
        self.registry_path = registry_path
        self.requirements = []
        self.must = []
        self.should = []
        self.could = []
        self.other = []
        self.rejected_noise = []

    def load_and_filter(self):
        """Charge le registre FSM et sépare le bon grain de l'ivraie."""
        if not self.registry_path.exists():
            logger.error(f"❌ Fichier {self.registry_path} introuvable.")
            return

        with open(self.registry_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        noise_keywords = [
            "TABLE OF", "END OF DOCUMENT", "SECTION: Racine", 
            "APPENDIX", "aucune exigence explicite", "Table "
        ]

        for entry in data:
            # 1. Nettoyage et Filtrage (Anti-Bruit)
            sujet = str(entry.get("subject", "")).lower()
            action = str(entry.get("action", "")).lower()
            source = str(entry.get("source_quote", "")).upper()

            is_null = any(val in [sujet, action] for val in ["null", "none", "aucun", ""])
            has_noise_kw = any(kw.upper() in source for kw in noise_keywords)

            if is_null or has_noise_kw:
                self.rejected_noise.append(self._format_entry(entry))
                continue

            # 2. Catégorisation MoSCoW
            formatted = self._format_entry(entry)
            action_full = (action + " " + source.lower())
            
            if any(w in action_full for w in ["must", "shall", "doit", "required", "obligatoire"]):
                self.must.append(formatted)
            elif any(w in action_full for w in ["should", "devrait", "recommended", "recommandé"]):
                self.should.append(formatted)
            elif any(w in action_full for w in ["can", "could", "may", "peut", "might"]):
                self.could.append(formatted)
            else:
                self.other.append(formatted)

    def _format_entry(self, entry: dict) -> dict:
        """Prépare une entrée pour le DataFrame pandas."""
        meta = entry.get("metadata", {})
        return {
            "ID Officiel": meta.get("official_id", "N/A"),
            "Sujet": entry.get("subject", ""),
            "Action": entry.get("action", ""),
            "Objet": entry.get("target_object", ""),
            "Citation Source": entry.get("source_quote", ""),
            "Page": meta.get("page", "?"),
            "Ambiguïté (0-100)": entry.get("ambiguity_score", 0),
            "Texte Original": entry.get("original_text", "") # Gardé pour l'onglet rejet
        }

    def generate(self):
        """Produit le fichier Excel multi-onglets."""
        logger.info("📊 Préparation de l'export Excel...")

        # Préparation des DataFrames
        df_must = pd.DataFrame(self.must).drop(columns=["Texte Original"], errors='ignore')
        df_should = pd.DataFrame(self.should).drop(columns=["Texte Original"], errors='ignore')
        df_could = pd.DataFrame(self.could).drop(columns=["Texte Original"], errors='ignore')
        df_rejected = pd.DataFrame(self.rejected_noise)

        # Synthèse
        summary_data = {
            "Catégorie": ["MUST", "SHOULD", "COULD", "AUTRES / WON'T", "REJETÉS (BRUIT)"],
            "Nombre": [len(self.must), len(self.should), len(self.could), len(self.other), len(self.rejected_noise)]
        }
        df_summary = pd.DataFrame(summary_data)

        with pd.ExcelWriter(OUTPUT_EXCEL, engine="openpyxl") as writer:
            df_summary.to_excel(writer, sheet_name="Synthèse", index=False)
            df_must.to_excel(writer, sheet_name="MUST", index=False)
            df_should.to_excel(writer, sheet_name="SHOULD", index=False)
            df_could.to_excel(writer, sheet_name="COULD", index=False)
            df_rejected.to_excel(writer, sheet_name="Rejetés (Bruit)", index=False)

            # Formatage via openpyxl
            workbook = writer.book
            for sheet_name in ["MUST", "SHOULD", "COULD", "Rejetés (Bruit)"]:
                worksheet = workbook[sheet_name]
                # Figer la ligne 1
                worksheet.freeze_panes = "A2"
                
                # Ajustement des largeurs (basique)
                for i, col in enumerate(worksheet.columns):
                    max_length = 0
                    column = col[0].column_letter
                    for cell in col:
                        try:
                            if len(str(cell.value)) > max_length:
                                max_length = len(str(cell.value))
                        except: pass
                    
                    # Limites raisonnables
                    adjusted_width = min(max_length + 2, 60)
                    if sheet_name != "Rejetés (Bruit)" and i == 4: # Citation Source
                        adjusted_width = 80
                    worksheet.column_dimensions[column].width = adjusted_width
                    
                    # Wrap text pour les longues colonnes
                    if adjusted_width >= 40:
                        from openpyxl.styles import Alignment
                        for cell in col:
                            cell.alignment = Alignment(wrap_text=True, vertical='top')

        logger.success(f"✅ Excel généré avec succès : {OUTPUT_EXCEL}")
        logger.info(f"📈 MUST: {len(self.must)} | SHOULD: {len(self.should)} | COULD: {len(self.could)} | Rejetés: {len(self.rejected_noise)}")

if __name__ == "__main__":
    generator = ExcelGenerator(REGISTRY_PATH)
    generator.load_and_filter()
    generator.generate()
