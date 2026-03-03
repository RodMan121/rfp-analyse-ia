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
    """

    def __init__(self, db_path: str = "data/chroma_db_hierarchical"):
        """Initialise les moteurs de recherche, de reranking et les modèles Ollama."""
        self.store = VectorStore(db_path=db_path)
        self.reranker = LocalReranker()
        
        # Configuration des modèles spécialisés (Ollama)
        self.text_model = "qwen2.5:7b"
        self.vision_model = "llama3.2-vision" 
        self.image_dir = Path("data/output_images")
        
        # MÉMOIRE : Liste de dictionnaires {role: str, content: str}
        self.history = []
        
        logger.info(f"🚀 Agent Expert prêt (Texte: {self.text_model} | Vision: {self.vision_model})")

    def _route_request(self, question: str) -> str:
        """
        Routage intelligent via LLM (plus précis que les mots-clés).
        """
        router_prompt = f"""Analyse la question utilisateur. Réponds UNIQUEMENT par 'VISION' si la question demande explicitement d'analyser un schéma, une image, un diagramme, un tableau complexe ou un aspect visuel de la page. Sinon, réponds 'TEXT'.

QUESTION : {question}
MODE :"""
        try:
            response = ollama.generate(model=self.text_model, prompt=router_prompt, options={"num_predict": 5})
            mode = response['response'].strip().upper()
            return "VISION" if "VISION" in mode else "TEXT"
        except Exception as e:
            logger.warning(f"⚠️ Échec du routage LLM ({e}), repli sur mots-clés.")
            keywords = ["schéma", "visuel", "maquette", "écran", "interface", "figure", "dessin", "image", "plan"]
            return "VISION" if any(kw in question.lower() for kw in keywords) else "TEXT"

    def ask(self, question: str) -> str:
        """Point d'entrée principal avec mémoire résumée."""
        # 1. Gestion de la mémoire (Résumé si trop long)
        if len(self.history) > 8:
            self._summarize_history()

        mode = self._route_request(question)
        
        if mode == "VISION":
            answer = self._ask_vision(question)
        else:
            answer = self._ask_text(question)
            
        self.history.append({"role": "user", "content": question})
        self.history.append({"role": "assistant", "content": answer})
        
        return answer

    def _summarize_history(self):
        """Résume les échanges passés pour libérer du contexte."""
        logger.info("🧠 Résumé de l'historique de conversation...")
        history_text = "\n".join([f"{m['role']}: {m['content']}" for m in self.history[:-2]])
        prompt = f"Résume cette conversation technique en 3 phrases clés pour conserver le contexte :\n\n{history_text}"
        try:
            response = ollama.generate(model=self.text_model, prompt=prompt)
            self.history = [
                {"role": "system", "content": f"Résumé des échanges précédents : {response['response']}"},
                *self.history[-2:]
            ]
        except Exception as e:
            logger.warning(f"⚠️ Échec du résumé : {e}")
            self.history = self.history[-4:]

    def _ask_text(self, question: str) -> str:
        """Pipeline de raisonnement textuel avec recherche hybride et mémoire."""
        logger.info(f"📝 Intention : Texte | Modèle : {self.text_model}")
        
        # 1. Retrieval (Recherche Hybride : Vecteurs + BM25)
        initial_results = self.store.search_hybrid(query=question, n_results=20)
        if not initial_results: return "⚠️ Aucun fragment trouvé."
        
        # 2. Reranking
        best_results = self.reranker.rerank(query=question, documents=initial_results, top_n=5)
        
        # 3. Context Building
        context_parts = []
        for r in best_results:
            source_info = f"SOURCE: {r['metadata']['breadcrumbs']} (Page {r['metadata']['page']})"
            context_parts.append(f"--- {source_info} ---\n{r['text']}")
        
        context = "\n\n".join(context_parts)
        
        # 4. Prompting Senior (avec Historique)
        history_str = "\n".join([f"{m['role'].upper()}: {m['content']}" for m in self.history])
        
        prompt = f"""Tu es un expert senior en analyse d'Appels d'Offres. Ta mission est de fournir une réponse technique, précise et exhaustive.

### RÈGLES D'ANALYSE :
1. Basse-toi UNIQUEMENT sur le CONTEXTE fourni.
2. CITE TOUJOURS la section et la page.
3. [IMPORTANT] LECTURE DES TABLEAUX : Si tu vois un bloc [DÉBUT TABLEAU]...[FIN TABLEAU], lis-le colonne par colonne. Ne confonds pas les lignes. Si une cellule est vide, ignore-la.
4. FORMAT : Utilise du Markdown pour ta réponse. Si la question porte sur des chiffres ou des délais, présente tes conclusions sous forme de tableau si cela améliore la clarté.

### HISTORIQUE :
{history_str}

### CONTEXTE DU DOCUMENT :
{context}

### QUESTION :
{question}

RÉPONSE (Analyste Senior) :"""
        
        response = ollama.generate(model=self.text_model, prompt=prompt)
        return response['response']

    def _ask_vision(self, question: str) -> str:
        """Pipeline vision multi-candidats avec recherche hybride."""
        logger.info(f"🖼️ Intention : Vision | Modèle : {self.vision_model}")
        
        # Recherche hybride pour trouver la page (plus précis sur les noms de schémas)
        results = self.store.search_hybrid(query=question, n_results=3)
        if not results: return "⚠️ Impossible d'identifier la page visuelle."
        
        # On essaie d'abord le meilleur résultat
        page_no = results[0]['metadata']['page']
        source_stem = Path(results[0]['metadata']['source']).stem
        image_path = self.image_dir / f"{source_stem}_page_{page_no}.png"
        
        if not image_path.exists():
            # Essayer de trouver n'importe quel PNG de ce document si le nom exact échoue
            possible_images = list(self.image_dir.glob(f"{source_stem}_page_*.png"))
            if possible_images:
                image_path = sorted(possible_images, key=lambda x: abs(int(x.stem.split('_')[-1]) - page_no))[0]
            else:
                return f"⚠️ Capture visuelle introuvable pour la page {page_no} (Doc: {source_stem})."

        logger.info(f"🧠 Analyse visuelle de l'image : {image_path.name}")
        prompt = f"Réponds à cette question d'analyse technique en examinant l'image : {question}. Sois précis sur les éléments graphiques."
        
        response = ollama.generate(model=self.vision_model, prompt=prompt, images=[str(image_path)])
        return f"**(Analyse Visuelle - Page {page_no})**\n\n{response['response']}"



if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Agent RFP Expert Multimodal")
    parser.add_argument("question", nargs="?", help="Question directe (optionnel si --file est utilisé)")
    parser.add_argument("--file", default="data/prompt.md", help="Chemin vers un fichier Markdown contenant votre prompt")
    args = parser.parse_args()
    
    # 1. Détermination de la source de la question
    question_text = ""
    if args.question:
        question_text = args.question
    else:
        prompt_path = Path(args.file)
        if prompt_path.exists():
            logger.info(f"📄 Lecture du prompt depuis : {args.file}")
            with open(prompt_path, "r", encoding="utf-8") as f:
                question_text = f.read().strip()
        else:
            console.print(f"[bold red]Erreur :[/bold red] Aucune question fournie et le fichier '{args.file}' est introuvable.")
            sys.exit(1)

    if not question_text:
        console.print("[bold yellow]Attention :[/bold yellow] Le prompt est vide.")
        sys.exit(0)

    agent = RFPAgent()
    
    # Logic de routage et exécution
    mode = agent._route_request(question_text)
    title = "🖼️ ANALYSE VISUELLE" if mode == "VISION" else "📝 ANALYSE TEXTUELLE"
    model_used = agent.vision_model if mode == "VISION" else agent.text_model
    
    try:
        answer = agent.ask(question_text)
        console.print(Panel(Markdown(answer), title=title, border_style="cyan", subtitle=f"Modèle: {model_used}"))
    except Exception as e:
        logger.error(f"Erreur lors du traitement : {e}")
        console.print(f"[bold red]Erreur critique :[/bold red] {e}")
