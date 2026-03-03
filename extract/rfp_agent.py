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

# Chargement de la configuration (chemin relatif au fichier)
env_path = Path(__file__).parent / ".env"
load_dotenv(env_path)
console = Console()

class RFPAgent:
    """
    Agent Expert en analyse de documents RFP.
    Supporte le texte, la vision, la mémoire et le streaming.
    """

    def __init__(self, db_path: str = "data/chroma_db_hierarchical"):
        self.store = VectorStore(db_path=db_path)
        self.reranker = LocalReranker()
        
        self.text_model = "qwen2.5:7b"
        self.vision_model = "llama3.2-vision" 
        self.image_dir = Path("data/output_images")
        self.history = []
        self.last_mode = "TEXT" # Pour suivi interne
        
        logger.info(f"🚀 Agent Expert prêt (Modèle: {self.text_model})")

    def _route_request(self, question: str) -> str:
        """Détermine si la requête nécessite de la vision ou du texte."""
        router_prompt = f"Réponds UNIQUEMENT par 'VISION' si la question demande d'analyser une image/schéma, sinon 'TEXT'.\n\nQUESTION : {question}\nMODE :"
        try:
            response = ollama.generate(model=self.text_model, prompt=router_prompt, options={"num_predict": 5})
            mode = response['response'].strip().upper()
            return "VISION" if "VISION" in mode else "TEXT"
        except Exception as e:
            logger.warning(f"⚠️ Échec routage LLM ({e}), repli sur mots-clés.")
            keywords = ["schéma", "visuel", "maquette", "écran", "interface", "figure", "dessin", "image", "plan"]
            return "VISION" if any(kw in question.lower() for kw in keywords) else "TEXT"

    def ask(self, question: str, stream: bool = True) -> str:
        """Point d'entrée principal avec gestion du streaming."""
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
            self.history = [{"role": "system", "content": f"Résumé: {response['response']}"}, *self.history[-2:]]
        except: self.history = self.history[-4:]

    def _ask_text(self, question: str, stream: bool = True) -> str:
        """Pipeline RAG textuel avec limite de contexte et streaming."""
        initial_results = self.store.search_hybrid(query=question, n_results=20)
        if not initial_results: return "⚠️ Aucun fragment trouvé."
        
        best_results = self.reranker.rerank(query=question, documents=initial_results, top_n=5)
        
        # 1. Construction du contexte avec limite de taille
        MAX_CONTEXT_CHARS = 8000
        context_parts = []
        for r in best_results:
            source_info = f"SOURCE: {r['metadata']['breadcrumbs']} (Page {r['metadata']['page']})"
            context_parts.append(f"--- {source_info} ---\n{r['text']}")
        
        context = "\n\n".join(context_parts)
        if len(context) > MAX_CONTEXT_CHARS:
            context = context[:MAX_CONTEXT_CHARS] + "\n\n[... contexte tronqué pour stabilité ...]"
        
        history_str = "\n".join([f"{m['role'].upper()}: {m['content']}" for m in self.history])
        
        prompt = f"""Tu es un analyste senior. Réponds selon les règles :
1. Basse-toi UNIQUEMENT sur le CONTEXTE ci-dessous.
2. Cite TOUJOURS la section et la page.
3. Si absent, dis "Information non présente".

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
                    token = chunk['response']
                    full_response += token
                    live.update(Markdown(full_response))
            return full_response
        else:
            response = ollama.generate(model=self.text_model, prompt=prompt)
            return response['response']

    def _ask_vision(self, question: str) -> str:
        """Analyse visuelle multi-modale."""
        results = self.store.search_hybrid(query=question, n_results=3)
        if not results: return "⚠️ Impossible d'identifier la page."
        
        page_no = results[0]['metadata']['page']
        source_stem = Path(results[0]['metadata']['source']).stem
        image_path = self.image_dir / f"{source_stem}_page_{page_no}.png"
        
        if not image_path.exists():
            return f"⚠️ Capture visuelle introuvable (P.{page_no})."

        prompt = f"Analyse cette image technique pour répondre à : {question}. Sois précis."
        response = ollama.generate(model=self.vision_model, prompt=prompt, images=[str(image_path)])
        return f"**(Analyse Visuelle - Page {page_no})**\n\n{response['response']}"

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

    agent = RFPAgent()
    # ask() gère déjà l'affichage streaming si stream=True
    answer = agent.ask(question_text, stream=True)
    
    # Affichage final dans un panel
    title = "🖼️ VISION" if agent.last_mode == "VISION" else "📝 TEXTE"
    console.print(Panel(Markdown(answer), title=title, border_style="cyan"))
