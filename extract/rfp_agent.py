import os
import argparse
import ollama
from pathlib import Path
from dotenv import load_dotenv
from google import genai
from phase1.vectorstore import VectorStore
from phase1.reranker import LocalReranker
from loguru import logger
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel

# Chargement de la configuration environnement (API Keys)
load_dotenv("extract/.env")
console = Console()

class RFPAgent:
    """
    Agent Expert en analyse de documents RFP (Request For Proposal).
    
    Cet agent implémente un pipeline RAG avancé avec :
    1. Routage Intentionnel (Texte vs Vision)
    2. Recherche Sémantique (ChromaDB)
    3. Reranking de haute précision (FlashRank)
    4. Génération spécialisée (Qwen pour le texte, Llama3.2-Vision pour les images)
    """

    def __init__(self, db_path: str = "data/chroma_db_hierarchical"):
        """Initialise les moteurs de recherche, de reranking et les modèles Ollama."""
        self.store = VectorStore(db_path=db_path)
        self.reranker = LocalReranker()
        
        # Configuration des modèles spécialisés (Ollama)
        self.text_model = "qwen2.5:7b"
        self.vision_model = "llama3.2-vision" 
        self.image_dir = Path("data/output_images")
        
        logger.info(f"🚀 Agent Expert prêt (Texte: {self.text_model} | Vision: {self.vision_model})")

    def _is_vision_request(self, question: str) -> bool:
        """
        Analyse sémantique simple pour router vers le modèle Vision.
        
        Args:
            question: La requête utilisateur.
        Returns:
            bool: True si la question porte sur un aspect visuel.
        """
        keywords = ["schéma", "visuel", "maquette", "écran", "interface", "figure", "dessin", "image", "plan"]
        return any(kw in question.lower() for kw in keywords)

    def ask(self, question: str) -> str:
        """
        Point d'entrée principal pour interroger le document.
        
        Args:
            question: La question posée par l'expert métier.
        Returns:
            str: La réponse synthétisée par l'IA la plus adaptée.
        """
        if self._is_vision_request(question):
            return self._ask_vision(question)
        else:
            return self._ask_text(question)

    def _ask_text(self, question: str) -> str:
        """
        Pipeline de raisonnement textuel (RAG + Reranking).
        
        Processus :
        1. Recherche de 20 candidats dans ChromaDB (Embedding distance).
        2. Reranking pour sélectionner les 5 fragments les plus pertinents.
        3. Synthèse par Qwen 2.5 en respectant strictement le contexte.
        """
        logger.info(f"📝 Intention : Texte | Modèle : {self.text_model}")
        
        # 1. Retrieval
        initial_results = self.store.search(query=question, n_results=20)
        if not initial_results: return "⚠️ Aucun fragment trouvé dans la base de connaissances."
        
        # 2. Reranking
        best_results = self.reranker.rerank(query=question, documents=initial_results, top_n=5)
        
        # 3. Augmentation (Context Building)
        context_parts = []
        for r in best_results:
            source_info = f"SOURCE: {r['metadata']['source']} | PAGE: {r['metadata']['page']}\nSECTION: {r['metadata']['breadcrumbs']}"
            context_parts.append(f"--- {source_info} ---\n{r['text']}")
        
        context = "\n\n".join(context_parts)
        
        prompt = f"""Tu es un analyste senior en appels d'offres. Réponds à la question suivante en te basant UNIQUEMENT sur le contexte fourni. 
Si l'information n'est pas présente, dis-le. Cite toujours la section ou la page.

CONTEXTE :
{context}

QUESTION : {question}

RÉPONSE (en Français, professionnelle) :"""
        
        # 4. Generation
        response = ollama.generate(model=self.text_model, prompt=prompt)
        return response['response']

    def _ask_vision(self, question: str) -> str:
        """
        Pipeline d'analyse visuelle (Multimodal RAG).
        
        Processus :
        1. Recherche de la page contenant les mots-clés de la question.
        2. Chargement du snapshot PNG haute résolution correspondant.
        3. Analyse directe de l'image par Llama 3.2 Vision.
        """
        logger.info(f"🖼️ Intention : Vision | Modèle : {self.vision_model}")
        
        # 1. Identification de la page cible via les métadonnées thématiques
        results = self.store.search(query=question, n_results=3)
        page_no = results[0]['metadata']['page'] if results else 1
        
        image_path = self.image_dir / f"RFP_page_{page_no}.png"
        
        if not image_path.exists():
            return f"⚠️ La page {page_no} semble pertinente mais la capture visuelle est introuvable."

        logger.info(f"🧠 Analyse visuelle de la page {page_no}...")
        
        prompt = f"Analyse cette capture d'écran pour répondre à la question suivante : {question}. Décris les éléments visuels, les boutons, les champs ou les flux techniques visibles."
        
        # 2. Inférence Multimodale
        response = ollama.generate(
            model=self.vision_model,
            prompt=prompt,
            images=[str(image_path)]
        )
        return f"**(Analyse Multimodale - Page {page_no})**\n\n{response['response']}"

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Agent RFP Expert Multimodal")
    parser.add_argument("question", help="Question à poser au document")
    args = parser.parse_args()
    
    agent = RFPAgent()
    answer = agent.ask(args.question)
    
    # Affichage riche
    title = "🖼️ ANALYSE VISUELLE" if agent._is_vision_request(args.question) else "📝 ANALYSE TEXTUELLE"
    console.print(Panel(Markdown(answer), title=title, border_style="cyan", subtitle=f"Modèle: {agent.text_model if not agent._is_vision_request(args.question) else agent.vision_model}"))
