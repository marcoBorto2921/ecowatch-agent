import os
from typing import List
from tavily import TavilyClient
from agents.state import EcoWatchState, NewsArticle

QUERIES_DEFAULT = [
    # International
    "climate change news today",
    "COP30 climate agreement 2025",
    "renewable energy policy 2025",
    # Italia
    "cambiamento climatico italia oggi",
    "politica ambientale governo italiano",
]

def search_news(state: EcoWatchState) -> dict:
    print("\n🔍 Searching for news...")

    client = TavilyClient(api_key=os.getenv("TAVILY_API_KEY"))
    queries = state.get("search_queries") or QUERIES_DEFAULT

    articles: List[NewsArticle] = []

    for query in queries:
        print(f"  → {query}")

        risultati = client.search(
            query=query,
            max_results=2,
        )

        for r in risultati["results"]:
            article: NewsArticle = {
                "title": r["title"],
                "url": r["url"],
                "content": r["content"],
                "source": r["url"].split("/")[2],
            }
            articles.append(article)

    print(f"  ✓ Found {len(articles)} articles")

    return {"articles": articles}