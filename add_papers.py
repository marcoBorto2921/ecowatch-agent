import json
import chromadb
from dotenv import load_dotenv

load_dotenv()

def load_papers():
    # Leggi il file JSON
    with open("data/papers.json", "r", encoding="utf-8") as f:
        papers = json.load(f)
    
    # Connettiti a ChromaDB
    client = chromadb.PersistentClient(path="./database")
    collection = client.get_or_create_collection(name="scientific_papers")
    
    # Carica i paper
    collection.upsert(
        ids=[p["id"] for p in papers],
        documents=[p["title"] + "\n\n" + p["abstract"] for p in papers],
        metadatas=[
            {
                "title": p["title"],
                "authors": p["authors"],
                "year": p["year"],
                "doi": p["doi"],
            }
            for p in papers
        ],
    )
    
    print(f"✅ Caricati {len(papers)} paper nel database")
    print(f"📚 Totale paper nel database: {collection.count()}")

if __name__ == "__main__":
    load_papers()