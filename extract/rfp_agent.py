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

load_dotenv("extract/.env")
console = Console()

class RFPAgent:
    """Agent RFP Spécialisé : Routeur Texte (Qwen) vs Vision (Llava)."""

    def __init__(self, db_path: str = "data/chroma_db_hierarchical"):
        self.store = VectorStore(db_path=db_path)
        self.reranker = LocalReranker()
        # Modèles spécialisés
        self.text_model = "qwen2.5:7b"
        self.vision_model = "llama3.2-vision" 
        self.image_dir = Path("data/output_images")
        
        logger.info(f"🚀 Agent Expert prêt (Texte: {self.text_model} | Vision: {self.vision_model})")

    def _is_vision_request(self, question: str) -> bool:
        """Détecte si la question demande une analyse visuelle."""
        keywords = ["schéma", "visuel", "maquette", "écran", "interface", "figure", "dessin", "image", "plan"]
        return any(kw in question.lower() for kw in keywords)

    def ask(self, question: str) -> str:
        """Route la question vers le bon modèle."""
        
        if self._is_vision_request(question):
            return self._ask_vision(question)
        else:
            return self._ask_text(question)

    def _ask_text(self, question: str) -> str:
        """Analyse textuelle via RAG + Qwen."""
        logger.info(f"📝 Intention : Texte | Modèle : {self.text_model}")
        
        # 1. RAG
        initial_results = self.store.search(query=question, n_results=20)
        if not initial_results: return "⚠️ Aucun fragment trouvé."
        
        # 2. Reranking
        best_results = self.reranker.rerank(query=question, documents=initial_results, top_n=5)
        
        # 3. Prompt
        context = "\n\n".join([f"--- SOURCE: {r['metadata']['source']} | PAGE: {r['metadata']['page']}\nSECTION: {r['metadata']['breadcrumbs']}\n{r['text']}" for r in best_results])
        
        prompt = f"Tu es un expert RFP. Réponds à la question en utilisant ce contexte :\n\n{context}\n\nQUESTION : {question}"
        
        response = ollama.generate(model=self.text_model, prompt=prompt)
        return response['response']

    def _ask_vision(self, question: str) -> str:
        """Analyse visuelle via Llava."""
        logger.info(f"🖼️ Intention : Vision | Modèle : {self.vision_model}")
        
        # 1. On cherche la page la plus pertinente (RAG sur les descriptions ou titres)
        results = self.store.search(query=question, n_results=3)
        page_no = results[0]['metadata']['page'] if results else 1
        
        # 2. On récupère l'image correspondante
        # Convention : RFP_page_X.png
        image_path = self.image_dir / f"RFP_page_{page_no}.png"
        
        if not image_path.exists():
            return f"⚠️ Je pense que la réponse est page {page_no}, mais je ne trouve pas la capture {image_path.name}."

        logger.info(f"🧠 Analyse de l'image : {image_path.name}")
        
        prompt = f"Analyse cette image pour répondre à la question suivante : {question}. Sois précis sur les éléments visuels."
        
        response = ollama.generate(
            model=self.vision_model,
            prompt=prompt,
            images=[str(image_path)]
        )
        return f"**(Analyse de la Page {page_no})**\n\n{response['response']}"

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Agent RFP Spécialisé (Routeur)")
    parser.add_argument("question", help="La question à poser")
    args = parser.parse_args()
    
    agent = RFPAgent()
    answer = agent.ask(args.question)
    
    # Affichage adapté selon le mode
    title = "🖼️ Analyse Visuelle" if agent._is_vision_request(args.question) else "📝 Analyse Textuelle"
    console.print(Panel(Markdown(answer), title=title, border_style="cyan"))
