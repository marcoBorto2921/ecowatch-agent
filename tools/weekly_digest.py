import os
from datetime import datetime, timedelta
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from tavily import TavilyClient
import chromadb

load_dotenv()

QUERIES = [
    # Clima e ambiente
    "climate change news this week",
    "environmental news today",
    # Politica ambientale
    "EU environmental policy this week",
    "italy environmental policy news",
    # Scientifica
    "climate science research 2026",
]

PROMPT = ChatPromptTemplate.from_messages([
    ("system", """Sei il redattore di EcoWatch Weekly, una newsletter ambientale professionale.
Produci una digest settimanale in italiano, chiara e basata su evidenze.

Struttura esattamente così:

## 🌍 La Settimana in Sintesi
(3-4 frasi sui temi principali della settimana)

## 📰 Notizie Clima e Ambiente
(le 3 notizie più importanti con riassunto e fonte)

## 🏛️ Politica Ambientale
(aggiornamenti su EU e Italia)

## 🔬 Dalla Scienza
(paper e ricerche rilevanti della settimana)

## 💡 Da Tenere d'Occhio
(temi emergenti per la prossima settimana)

Stile: autorevole, preciso, accessibile."""),
    ("human", """Settimana del {date}.

NOTIZIE RACCOLTE:
{articles}

PAPER SCIENTIFICI NEL DATABASE:
{papers}

Genera la digest settimanale in italiano:""")
])


def generate_weekly_digest() -> str:
    """Genera la digest settimanale e la invia via email."""
    print("\n╔══════════════════════════════════════╗")
    print("║     🌱 EcoWatch Weekly Digest        ║")
    print("╚══════════════════════════════════════╝")

    # 1. Cerca notizie
    print("\n🔍 Cerco notizie della settimana...")
    articles = _search_news()
    print(f"  ✓ Trovati {len(articles)} articoli")

    # 2. Recupera paper dal database
    print("\n📚 Recupero paper scientifici...")
    papers = _get_papers()
    print(f"  ✓ {len(papers)} paper nel database")

    # 3. Genera il contenuto
    print("\n✍️  Genero la digest...")
    content = _generate_content(articles, papers)

    # 4. Genera HTML
    html = _generate_html(content, articles)

    # 5. Invia email
    from tools.email_sender import send_email
    date = datetime.now().strftime("%d %B %Y")
    send_email(
        subject=f"🌱 EcoWatch Weekly — {date}",
        html_content=html
    )

    return content


def _search_news() -> list:
    """Cerca notizie della settimana con Tavily."""
    client = TavilyClient(api_key=os.getenv("TAVILY_API_KEY"))
    articles = []
    seen_urls = set()

    for query in QUERIES:
        try:
            results = client.search(query=query, max_results=2)
            for r in results.get("results", []):
                if r["url"] not in seen_urls:
                    seen_urls.add(r["url"])
                    articles.append({
                        "title": r["title"],
                        "url": r["url"],
                        "content": r["content"][:500],
                        "source": r["url"].split("/")[2],
                    })
        except Exception as e:
            print(f"  ✗ Errore query '{query}': {e}")

    return articles


def _get_papers() -> list:
    """Recupera i paper dal database ChromaDB."""
    try:
        client = chromadb.PersistentClient(path="./database")
        collection = client.get_or_create_collection(name="scientific_papers")
        
        if collection.count() == 0:
            return []

        results = collection.get(limit=10, include=["metadatas"])
        return [
            f"{m.get('title', '')} ({m.get('year', '')}) — {m.get('authors', '')}"
            for m in results["metadatas"]
        ]
    except Exception:
        return []


def _generate_content(articles: list, papers: list) -> str:
    """Genera il testo della digest con Groq."""
    llm = ChatGroq(
        model="llama-3.3-70b-versatile",
        temperature=0.3,
        api_key=os.getenv("GROQ_API_KEY"),
    )

    articles_text = "\n".join([
        f"- {a['title']} ({a['source']}): {a['content'][:200]}"
        for a in articles
    ])

    papers_text = "\n".join([f"- {p}" for p in papers]) or "Nessun paper disponibile."

    chain = PROMPT | llm
    response = chain.invoke({
        "date": datetime.now().strftime("%d %B %Y"),
        "articles": articles_text,
        "papers": papers_text,
    })

    return response.content


def _generate_html(content: str, articles: list) -> str:
    """Genera l'HTML della newsletter settimanale."""
    date = datetime.now().strftime("%d %B %Y")

    # Converti markdown in HTML
    html_content = ""
    for line in content.split("\n"):
        if line.startswith("## "):
            html_content += f'<h2 class="section-title">{line[3:]}</h2>\n'
        elif line.startswith("- "):
            html_content += f'<li>{line[2:]}</li>\n'
        elif line.strip() == "":
            html_content += "<br>\n"
        else:
            html_content += f'<p>{line}</p>\n'

    # Lista fonti
    sources_html = "\n".join([
        f'<li><a href="{a["url"]}" style="color:#40916c;">{a["title"]}</a> — {a["source"]}</li>'
        for a in articles[:5]
    ])

    return f"""<!DOCTYPE html>
<html lang="it">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>EcoWatch Weekly — {date}</title>
  <style>
    * {{ margin: 0; padding: 0; box-sizing: border-box; }}
    body {{ background: #f4f4f4; font-family: Georgia, serif; color: #333; }}
    .wrapper {{ max-width: 680px; margin: 40px auto; background: white; border-radius: 8px; overflow: hidden; box-shadow: 0 2px 20px rgba(0,0,0,0.1); }}
    .header {{ background: #1b4332; padding: 40px 48px; text-align: center; }}
    .header .logo {{ font-size: 36px; }}
    .header h1 {{ color: #d8f3dc; font-size: 22px; font-weight: normal; letter-spacing: 3px; text-transform: uppercase; margin-top: 8px; }}
    .header .subtitle {{ color: #95d5b2; font-size: 14px; margin-top: 4px; }}
    .header .date {{ color: #74c69d; font-size: 13px; margin-top: 8px; }}
    .stats-bar {{ background: #2d6a4f; padding: 16px 48px; display: flex; gap: 32px; }}
    .stat {{ color: white; font-size: 13px; font-family: Arial, sans-serif; }}
    .stat span {{ font-size: 20px; font-weight: bold; display: block; }}
    .content {{ padding: 48px; }}
    .section-title {{ color: #1b4332; font-size: 20px; border-bottom: 2px solid #d8f3dc; padding-bottom: 8px; margin: 32px 0 16px; }}
    .section-title:first-child {{ margin-top: 0; }}
    p {{ line-height: 1.8; margin-bottom: 12px; font-size: 16px; }}
    li {{ line-height: 1.8; margin-bottom: 8px; margin-left: 20px; font-size: 15px; }}
    .sources {{ background: #f8f9fa; border-radius: 8px; padding: 24px; margin-top: 32px; }}
    .sources h3 {{ color: #1b4332; margin-bottom: 12px; font-size: 16px; }}
    .footer {{ background: #f8f9fa; border-top: 1px solid #e9ecef; padding: 24px 48px; text-align: center; }}
    .footer p {{ color: #868e96; font-size: 13px; font-family: Arial, sans-serif; line-height: 1.6; }}
  </style>
</head>
<body>
  <div class="wrapper">
    <div class="header">
      <div class="logo">🌱</div>
      <h1>EcoWatch Weekly</h1>
      <div class="subtitle">Intelligence Ambientale</div>
      <div class="date">{date}</div>
    </div>

    <div class="stats-bar">
      <div class="stat">
        <span>{len(articles)}</span>
        Fonti analizzate
      </div>
      <div class="stat">
        <span>3</span>
        Sezioni tematiche
      </div>
      <div class="stat">
        <span>1</span>
        Volta a settimana
      </div>
    </div>

    <div class="content">
      {html_content}

      <div class="sources">
        <h3>📎 Fonti principali</h3>
        <ul>{sources_html}</ul>
      </div>
    </div>

    <div class="footer">
      <p>🌱 <strong>EcoWatch Weekly</strong> — Intelligence ambientale settimanale<br>
      Generato con LangGraph + Groq + ChromaDB + Tavily<br>
      {date}</p>
    </div>
  </div>
</body>
</html>"""