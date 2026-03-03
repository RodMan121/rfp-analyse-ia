import os
import sys
import argparse
import ollama
import json
from pathlib import Path
from dotenv import load_dotenv
from phase1.vectorstore import VectorStore
from phase1.reranker import LocalReranker
from loguru import logger
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.live import Live

# Configuration robuste
env_path = Path(__file__).parent / ".env"
load_dotenv(env_path)
console = Console()

class RFPAgent:
    """
    Agent Expert en analyse de documents RFP.
    Supporte le texte, la vision (non-streamée), la mémoire et le streaming textuel.
    """

    def __init__(self, db_path: str = "data/chroma_db_hierarchical"):
        self.store = VectorStore(db_path=db_path)
        self.reranker = LocalReranker()
        
        # Modèles pilotés par variables d'environnement
        self.text_model = os.getenv("OLLAMA_TEXT_MODEL", "qwen2.5:7b")
        self.vision_model = os.getenv("OLLAMA_VISION_MODEL", "llama3.2-vision")
        
        self.image_dir = Path("data/output_images")
        self.history = []
        self.last_mode = "TEXT"
        
        logger.info(f"🚀 Agent Expert prêt (Modèle: {self.text_model})")

    def _route_request(self, question: str) -> str:
        """Détermine l'intention (Texte vs Vision)."""
        router_prompt = f"Réponds UNIQUEMENT par 'VISION' si la question demande d'analyser une image/schéma, sinon 'TEXT'.\n\nQUESTION : {question}\nMODE :"
        try:
            response = ollama.generate(model=self.text_model, prompt=router_prompt, options={"num_predict": 5})
            mode = response.get('response', 'TEXT').strip().upper()
            return "VISION" if "VISION" in mode else "TEXT"
        except Exception as e:
            logger.warning(f"⚠️ Échec routage LLM ({e}), repli sur mots-clés.")
            keywords = ["schéma", "visuel", "maquette", "écran", "interface", "figure", "dessin", "image", "plan"]
            return "VISION" if any(kw in question.lower() for kw in keywords) else "TEXT"

    def ask(self, question: str, stream: bool = True) -> str:
        """Point d'entrée principal."""
        self.last_mode = self._route_request(question)
        
        if len(self.history) > 8:
            self._summarize_history()

        if self.last_mode == "VISION":
            answer = self._ask_vision(question)
        else:
            answer = self._ask_text(question, stream=stream)
            
        self.history.append({"role": "user", "content": question})
        self.history.append({"role": "assistant", "content": answer})
        return answer

    def _summarize_history(self):
        """Résume l'historique pour libérer du contexte."""
        history_text = "\n".join([f"{m['role']}: {m['content']}" for m in self.history[:-2]])
        prompt = f"Résume cette conversation technique en 3 phrases :\n\n{history_text}"
        try:
            response = ollama.generate(model=self.text_model, prompt=prompt)
            self.history = [{"role": "system", "content": f"Résumé: {response.get('response', '')}"}, *self.history[-2:]]
        except Exception:
            # Correction audit : replacement du bare except par Exception
            self.history = self.history[-4:]

    def _ask_text(self, question: str, stream: bool = True) -> str:
        """Pipeline RAG textuel avec streaming."""
        initial_results = self.store.search_hybrid(query=question, n_results=20)
        if not initial_results: return "⚠️ Aucun fragment trouvé."
        
        best_results = self.reranker.rerank(query=question, documents=initial_results, top_n=5)
        
        MAX_CONTEXT_CHARS = 8000
        context_parts = []
        for r in best_results:
            source_info = f"SOURCE: {r['metadata']['breadcrumbs']} (P.{r['metadata']['page']})"
            context_parts.append(f"--- {source_info} ---\n{r['text']}")
        
        context = "\n\n".join(context_parts)
        if len(context) > MAX_CONTEXT_CHARS:
            context = context[:MAX_CONTEXT_CHARS] + "\n\n[... contexte tronqué ...]"
        
        history_str = "\n".join([f"{m['role'].upper()}: {m['content']}" for m in self.history])
        
        prompt = f"""Tu es analyste senior. Réponds en te basant sur le CONTEXTE.
CITE la section/page. Si absent, dis "Information non présente".

### HISTORIQUE :
{history_str}

### CONTEXTE :
{context}

### QUESTION :
{question}

RÉPONSE :"""
        
        full_response = ""
        if stream:
            response_gen = ollama.generate(model=self.text_model, prompt=prompt, stream=True)
            with Live(Markdown(""), refresh_per_second=10, console=console) as live:
                for chunk in response_gen:
                    token = chunk.get('response', '')
                    full_response += token
                    live.update(Markdown(full_response))
            return full_response
        else:
            response = ollama.generate(model=self.text_model, prompt=prompt)
            return response.get('response', '')

    def _ask_vision(self, question: str) -> str:
        """Analyse visuelle (non-streamée par limitation modèle vision)."""
        results = self.store.search_hybrid(query=question, n_results=3)
        if not results: return "⚠️ Impossible d'identifier la page."
        
        page_no = results[0]['metadata']['page']
        source_stem = Path(results[0]['metadata']['source']).stem
        image_path = self.image_dir / f"{source_stem}_page_{page_no}.png"
        
        if not image_path.exists():
            return f"⚠️ Capture visuelle introuvable (P.{page_no})."

        prompt = f"Analyse cette image technique pour répondre à : {question}."
        response = ollama.generate(model=self.vision_model, prompt=prompt, images=[str(image_path)])
        return f"**(Analyse Visuelle - Page {page_no})**\n\n{response.get('response', '')}"

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Agent RFP Expert")
    parser.add_argument("question", nargs="?", help="Question directe")
    parser.add_argument("--file", default="data/prompt.md", help="Fichier de prompt")
    args = parser.parse_args()
    
    question_text = ""
    if args.question:
        question_text = args.question
    else:
        p = Path(args.file)
        if p.exists():
            with open(p, "r", encoding="utf-8") as f: question_text = f.read().strip()
        else:
            console.print(f"[red]Erreur : Fichier '{args.file}' introuvable.[/red]")
            sys.exit(1)

    if not question_text: sys.exit(0)

    try:
        agent = RFPAgent()
        answer = agent.ask(question_text, stream=True)
        title = "🖼️ VISION" if agent.last_mode == "VISION" else "📝 TEXTE"
        console.print(Panel(Markdown(answer), title=title, border_style="cyan"))
    except Exception as e:
        logger.error(f"Erreur critique agent : {e}")
        console.print(f"[bold red]Erreur :[/bold red] {e}")
