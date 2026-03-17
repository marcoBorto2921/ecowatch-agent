import os
import chromadb
from agents.state import EcoWatchState

def get_collection():
    client = chromadb.PersistentClient(path="./database")
    collection = client.get_or_create_collection(name="scientific_papers")
    return collection


def retrieve_papers(state: EcoWatchState) -> dict:
    print("\n📚 Retrieving scientific papers...")

    collection = get_collection()
    articles = state.get("articles", [])
    all_papers = []

    if collection.count() == 0:
        print("  ⚠ Database empty — adding demo papers...")
        _add_demo_papers(collection)

    for i, article in enumerate(articles, 1):
        print(f"  → [{i}/{len(articles)}] {article['title'][:60]}...")

        results = collection.query(
            query_texts=[article["title"] + " " + article["content"][:300]],
            n_results=2,
        )

        for doc, meta, dist in zip(
            results["documents"][0],
            results["metadatas"][0],
            results["distances"][0],
        ):
            relevance = round(max(0, 1 - dist), 2)
            paper = {
                "title": meta.get("title", ""),
                "authors": meta.get("authors", ""),
                "year": meta.get("year", ""),
                "abstract": doc,
                "relevance": relevance,
                "related_to": article["title"],
            }
            all_papers.append(paper)
            print(f"     ✓ {paper['title'][:50]} (relevance: {relevance})")

    return {"scientific_papers": all_papers}


def _add_demo_papers(collection):
    """Aggiunge paper dimostrativi se il database è vuoto."""
    papers = [
        {
            "id": "ipcc-ar6-2021",
            "text": "Climate Change 2021: The Physical Science Basis. Human influence has warmed the atmosphere, ocean and land. Widespread and rapid changes in the atmosphere, ocean, cryosphere and biosphere have occurred.",
            "meta": {"title": "IPCC AR6 - Physical Science Basis", "authors": "IPCC Working Group I", "year": "2021"}
        },
        {
            "id": "renewable-energy-2023",
            "text": "Global renewable energy capacity reached record levels in 2023. Solar and wind power costs have fallen dramatically, making them the cheapest sources of electricity in history.",
            "meta": {"title": "Renewable Energy Global Status Report", "authors": "REN21", "year": "2023"}
        },
        {
            "id": "biodiversity-loss-2022",
            "text": "One million species face extinction due to human activities. Land use change, climate change, overexploitation and pollution are primary drivers of biodiversity loss worldwide.",
            "meta": {"title": "Global Biodiversity Assessment", "authors": "IPBES", "year": "2022"}
        },
        {
            "id": "extreme-weather-2023",
            "text": "Extreme weather events including heatwaves, droughts and floods are becoming more frequent and intense due to climate change. Mediterranean regions face increased drought risk.",
            "meta": {"title": "Extreme Weather Attribution Study", "authors": "Fischer & Knutti", "year": "2023"}
        },
    ]

    collection.upsert(
        ids=[p["id"] for p in papers],
        documents=[p["text"] for p in papers],
        metadatas=[p["meta"] for p in papers],
    )
    print(f"  ✓ Added {len(papers)} demo papers")