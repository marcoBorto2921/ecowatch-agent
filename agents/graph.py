from datetime import datetime
from dotenv import load_dotenv
from langgraph.graph import StateGraph, END

from agents.state import EcoWatchState
from tools.news_search import search_news
from tools.bias_analyzer import analyze_bias
from tools.paper_retriever import retrieve_papers
from tools.briefing_generator import generate_briefing

load_dotenv()


def build_graph():
    graph = StateGraph(EcoWatchState)

    # ── Aggiungi i nodi ──────────────────────────────
    graph.add_node("search_news", search_news)
    graph.add_node("analyze_bias", analyze_bias)
    graph.add_node("retrieve_papers", retrieve_papers)
    graph.add_node("generate_briefing", generate_briefing)

    # ── Collega i nodi in sequenza ───────────────────
    graph.set_entry_point("search_news")
    graph.add_edge("search_news", "analyze_bias")
    graph.add_edge("analyze_bias", "retrieve_papers")
    graph.add_edge("retrieve_papers", "generate_briefing")
    graph.add_edge("generate_briefing", END)

    return graph.compile()


def run():
    print("\n╔══════════════════════════════════════╗")
    print("║       🌱 EcoWatch Agent              ║")
    print("╚══════════════════════════════════════╝")
    print(f"  {datetime.now().strftime('%A %d %B %Y — %H:%M')}\n")

    app = build_graph()

    initial_state: EcoWatchState = {
        "search_queries": [],
        "articles": [],
        "bias_analyses": [],
        "scientific_papers": [],
        "final_briefing": "",
        "date": datetime.now().strftime("%Y-%m-%d"),
        "errors": [],
    }

    result = app.invoke(initial_state)

    print("\n" + "═" * 40)
    print(result["final_briefing"])
    print("═" * 40)

    return result