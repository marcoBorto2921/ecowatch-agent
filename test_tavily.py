from dotenv import load_dotenv
from tavily import TavilyClient
import os

load_dotenv()

client = TavilyClient(api_key=os.getenv("TAVILY_API_KEY"))

risultati = client.search(
    query="cambiamento climatico notizie oggi",
    max_results=3,
)

for r in risultati["results"]:
    print("TITOLO:", r["title"])
    print("FONTE: ", r["url"])
    print("TESTO: ", r["content"][:200])  # primi 200 caratteri
    print("---")