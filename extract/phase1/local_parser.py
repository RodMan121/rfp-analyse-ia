import os
import pathlib
import re
from dataclasses import dataclass
from loguru import logger
from docling.document_converter import DocumentConverter

@dataclass
class LocalRawFragment:
    """
    Structure de données pour un fragment de document enrichi.
    
    Attributes:
        text (str): Le contenu textuel ou Markdown du fragment.
        section (str): Le titre de la section la plus proche.
        breadcrumbs (str): Fil d'ariane complet (ex: Introduction > Sécurité).
        page (int): Numéro de la page d'origine (1-indexed).
        fragment_type (str): Type de contenu ('text' ou 'table').
        source_file (str): Nom du fichier source.
    """
    text: str
    section: str = "Général"
    breadcrumbs: str = ""
    page: int = 0
    fragment_type: str = "texte"
    source_file: str = ""

class DoclingParser:
    """
    Parser local haute performance basé sur IBM Docling.
    
    Ce parser transforme des documents complexes (PDF, DOCX) en une structure 
    hiérarchique. Contrairement à un découpage par nombre de caractères, 
    il respecte la sémantique du document en identifiant les titres et les tableaux.
    """

    def __init__(self):
        """Initialise le convertisseur Docling avec les modèles par défaut."""
        logger.info("🤖 Initialisation du Parser Hiérarchique (Propriétés Natives)...")
        self.converter = DocumentConverter()

    def parse_to_fragments(self, filepath: str | pathlib.Path) -> list[LocalRawFragment]:
        """
        Analyse un document et le découpe en fragments intelligents.
        
        Algorithme :
        1. Conversion du document en objet DoclingDocument.
        2. Itération sur chaque élément structurel (Titre, Paragraphe, Tableau).
        3. Maintien d'une pile (stack) de titres pour générer le fil d'ariane.
        4. Attribution du numéro de page via les métadonnées de provenance.
        
        Args:
            filepath: Chemin vers le fichier à analyser.
            
        Returns:
            list[LocalRawFragment]: Liste des fragments enrichis de métadonnées.
        """
        logger.info(f"📄 Analyse structurelle de : {filepath}")
        result = self.converter.convert(filepath)
        doc = result.document
        source_name = pathlib.Path(filepath).name
        
        fragments = []
        title_stack = [] 

        for item, level in doc.iterate_items():
            label = item.label.lower()
            
            # Extraction sécurisée du texte selon le type d'item
            try:
                item_text = ""
                if hasattr(item, "text"):
                    item_text = item.text
                else:
                    item_text = item.export_to_markdown() if hasattr(item, "export_to_markdown") else ""
                
                item_text = item_text.strip()
                if not item_text: continue
            except Exception as e:
                logger.debug(f"Saut d'un élément non extractible : {e}")
                continue

            # Gestion de la hiérarchie des titres (H1, H2, H3...)
            # Permet à l'IA de savoir dans quel contexte se trouve un paragraphe
            if "heading" in label or "title" in label or "header" in label:
                depth = level if level is not None else 0
                title_stack = title_stack[:depth] # On remonte au niveau parent
                title_stack.append(item_text)     # On ajoute le titre actuel
                continue

            # Filtrage du bruit (fragments trop courts sans valeur sémantique)
            if len(item_text) < 30: continue

            # Construction des métadonnées contextuelles
            breadcrumbs = " > ".join(title_stack) if title_stack else "Racine"
            current_section = title_stack[-1] if title_stack else "Général"
            
            # Récupération de la page physique dans le PDF
            page_no = 0
            if item.prov and len(item.prov) > 0:
                page_no = item.prov[0].page_no + 1

            fragments.append(LocalRawFragment(
                text=item_text,
                section=current_section,
                breadcrumbs=breadcrumbs,
                page=page_no,
                source_file=source_name,
                fragment_type="table" if "table" in label else "text"
            ))

        logger.success(f"✅ {len(fragments)} fragments hiérarchiques extraits.")
        return fragments
