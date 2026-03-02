import os
import argparse
import ollama
from dotenv import load_dotenv
from google import genai
from phase1.vectorstore import VectorStore
from loguru import logger
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel

load_dotenv("extract/.env")
console = Console()

class RFPAgent:
    """Agent d'analyse cognitive supportant Gemini (Cloud) et Ollama (Local)."""

    def __init__(self, db_path: str = "data/chroma_db", backend: str = "ollama", model: str = "qwen2.5:7b"):
        self.store = VectorStore(db_path=db_path)
        self.backend = backend.lower()
        self.model = model
        
        if self.backend == "gemini":
            # Si on force Gemini, on s'assure d'avoir un modèle flash
            if "gemini" not in self.model:
                self.model = "gemini-2.0-flash"
            self.client = genai.Client(api_key=os.getenv("GOOGLE_API_KEY"))
            logger.info(f"🧠 Agent RFP initialisé sur Gemini (Modèle: {self.model})")
        else:
            logger.info(f"🏠 Agent RFP initialisé sur Ollama Local (Modèle: {self.model})")

    def ask(self, question: str, n_fragments: int = 10) -> str:
        """Répond à une question en utilisant le contexte extrait (RAG)."""
        
        # 1. Recherche RAG
        results = self.store.search(query=question, n_results=n_fragments)
        if not results:
            return "⚠️ Aucun fragment pertinent trouvé dans la base."

        context = "\n\n".join([f"--- SOURCE: {r['metadata']['source']} ---\n{r['text']}" for r in results])
        
        # 2. Construction du prompt
        prompt = f"""
        Tu es un expert en analyse d'appels d'offres (RFP/CCTP). 
        Utilise EXCLUSIVEMENT le contexte ci-dessous pour répondre à la question. 
        Si la réponse n'est pas dans le contexte, dis-le clairement.

        ### CONTEXTE :
        {context}

        ### QUESTION :
        {question}

        ### RÉPONSE (en Français) :
        """

        # 3. Appel au Backend choisi
        try:
            if self.backend == "gemini":
                logger.info(f"☁️ Appel Gemini ({self.model})...")
                response = self.client.models.generate_content(model=self.model, contents=[prompt])
                return response.text
            else:
                logger.info(f"🏠 Appel Ollama Local ({self.model})...")
                response = ollama.generate(model=self.model, prompt=prompt)
                return response['response']
        except Exception as e:
            logger.error(f"❌ Erreur lors de l'appel au LLM : {e}")
            return f"❌ Erreur : {e}"

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Agent RFP — Analyse cognitive Multi-Backend")
    parser.add_argument("question", help="La question à poser")
    parser.add_argument("--backend", default="ollama", choices=["gemini", "ollama"], help="Moteur d'IA")
    parser.add_argument("--model", default="qwen2.5:7b", help="Modèle à utiliser")
    parser.add_argument("--db", default="data/chroma_db", help="Chemin vers la base ChromaDB")
    
    args = parser.parse_args()
    
    agent = RFPAgent(db_path=args.db, backend=args.backend, model=args.model)
    answer = agent.ask(args.question)
    
    console.print(Panel(Markdown(answer), title=f"🤖 [{args.backend}] Analyse : {args.question}", border_style="green"))
