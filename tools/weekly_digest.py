import os
import json
from datetime import datetime
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from tavily import TavilyClient
import chromadb

load_dotenv()

QUERIES = [
    "climate change news this week",
    "environmental news today",
    "EU environmental policy this week",
    "italy environmental policy news",
    "climate science research 2026",
]

PROMPT = ChatPromptTemplate.from_messages([
    ("system", """You are the editor of EcoWatch Weekly, a professional environmental newsletter.
Produce a weekly digest in English, clear and evidence-based.

Structure exactly like this:

## 🌍 Week in Review
(3-4 sentences on the main themes of the week)

## 🌐 Europe & World
(top 3 most important international and European news with summary and source)

## 🇮🇹 Italy
(environmental and policy updates from Italy)

## 🔬 From Science
(relevant papers and research this week)

## 💡 Watch This Space
(emerging topics to follow next week)

Style: authoritative, precise, accessible."""),
    ("human", """Week of {date}.

ARTICLES COLLECTED:
{articles}

SCIENTIFIC PAPERS IN DATABASE:
{papers}

Generate the weekly digest in English:""")
])

RANKING_PROMPT = ChatPromptTemplate.from_messages([
    ("system", """You are an expert environmental editor.
Analyze these articles and return ONLY valid JSON, no additional text.

JSON structure:
[
  {{
    "index": 0,
    "importance": 9,
    "comment": "Brief comment in English, max 20 words"
  }}
]

Importance criteria (1-10):
- Global or European impact → high score
- Authoritative source (UN, IPCC, governments) → high score
- Recent and relevant news → high score
- Low quality source or generic news → low score"""),
    ("human", """Rank these articles by importance:

{articles}

Return ONLY the JSON, no text before or after:""")
])


def generate_weekly_digest() -> str:
    print("\n╔══════════════════════════════════════╗")
    print("║     🌱 EcoWatch Weekly Digest        ║")
    print("╚══════════════════════════════════════╝")

    print("\n🔍 Searching for news...")
    articles = _search_news()
    print(f"  ✓ Found {len(articles)} articles")

    print("\n📊 Ranking articles by importance...")
    ranked_articles = _rank_articles(articles)
    print(f"  ✓ Ranked {len(ranked_articles)} articles")

    print("\n📚 Retrieving scientific papers...")
    papers = _get_papers()
    print(f"  ✓ {len(papers)} papers in database")

    print("\n✍️  Generating digest...")
    content = _generate_content(articles, papers)

    html = _generate_html(content, ranked_articles)

    from tools.email_sender import send_email
    date = datetime.now().strftime("%d %B %Y")
    send_email(
        subject=f"🌱 EcoWatch Weekly — {date}",
        html_content=html
    )

    return content


PAYWALL_DOMAINS = [
    "ft.com",
    "bloomberg.com",
    "wsj.com",
    "economist.com",
    "thetimes.co.uk",
    "telegraph.co.uk",
    "technologyreview.com",
    "hbr.org",
    "nature.com",
    "science.org",
]

def _search_news() -> list:
    client = TavilyClient(api_key=os.getenv("TAVILY_API_KEY"))
    articles = []
    seen_urls = set()

    for query in QUERIES:
        try:
            results = client.search(query=query, max_results=3, days=7)
            for r in results.get("results", []):
                domain = r["url"].split("/")[2].replace("www.", "")
                
                # Salta paywall
                if any(pw in domain for pw in PAYWALL_DOMAINS):
                    print(f"  ⚠ Skipping paywall: {domain}")
                    continue
                
                if r["url"] not in seen_urls:
                    seen_urls.add(r["url"])
                    articles.append({
                        "title": r["title"],
                        "url": r["url"],
                        "content": r["content"][:500],
                        "source": domain,
                    })
        except Exception as e:
            print(f"  ✗ Error query '{query}': {e}")

    return articles

def _rank_articles(articles: list) -> list:
    llm = ChatGroq(
        model="llama-3.3-70b-versatile",
        temperature=0.1,
        api_key=os.getenv("GROQ_API_KEY"),
    )

    articles_text = "\n".join([
        f"[{i}] {a['title']} ({a['source']}): {a['content'][:150]}"
        for i, a in enumerate(articles)
    ])

    try:
        chain = RANKING_PROMPT | llm
        response = chain.invoke({"articles": articles_text})

        text = response.content.strip()
        if "```json" in text:
            text = text.split("```json")[1].split("```")[0].strip()
        elif "```" in text:
            text = text.split("```")[1].split("```")[0].strip()

        rankings = json.loads(text)

        ranked = []
        for r in rankings:
            idx = r.get("index", 0)
            if idx < len(articles):
                article = articles[idx].copy()
                article["importance"] = r.get("importance", 5)
                article["comment"] = r.get("comment", "")
                ranked.append(article)

        ranked.sort(key=lambda x: x["importance"], reverse=True)
        return ranked[:10]

    except Exception as e:
        print(f"  ✗ Ranking error: {e}")
        return articles[:10]


def _get_papers() -> list:
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
    llm = ChatGroq(
        model="llama-3.3-70b-versatile",
        temperature=0.3,
        api_key=os.getenv("GROQ_API_KEY"),
    )

    articles_text = "\n".join([
        f"- {a['title']} ({a['source']}): {a['content'][:200]}"
        for a in articles
    ])

    papers_text = "\n".join([f"- {p}" for p in papers]) or "No papers available."

    chain = PROMPT | llm
    response = chain.invoke({
        "date": datetime.now().strftime("%d %B %Y"),
        "articles": articles_text,
        "papers": papers_text,
    })

    return response.content


def _generate_html(content: str, ranked_articles: list) -> str:
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

    # Badge colore per importanza
    def importance_color(score):
        if score >= 8:
            return "#2d6a4f"
        elif score >= 6:
            return "#e9a010"
        else:
            return "#adb5bd"

    # Top 10 articoli con badge e commento
    articles_html = ""
    for i, a in enumerate(ranked_articles, 1):
        score = a.get("importance", 5)
        comment = a.get("comment", "")
        color = importance_color(score)

        articles_html += f"""
        <div style="border-left:3px solid {color}; padding:12px 16px; margin-bottom:16px; background:#f8f9fa; border-radius:0 6px 6px 0;">
          <div style="display:flex; align-items:center; gap:10px; margin-bottom:6px;">
            <span style="background:{color}; color:white; font-size:11px; font-family:Arial; padding:2px 8px; border-radius:10px; font-weight:bold;">#{i} — {score}/10</span>
            <a href="{a['url']}" style="color:#1b4332; font-size:14px; font-family:Arial; font-weight:bold; text-decoration:none;">{a['title']}</a>
          </div>
          <div style="font-size:12px; color:#868e96; font-family:Arial; margin-bottom:4px;">{a['source']}</div>
          <div style="font-size:13px; color:#495057; font-family:Arial; font-style:italic;">{comment}</div>
        </div>
        """

    return f"""<!DOCTYPE html>
<html lang="en">
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
    .stats-bar {{ background: #2d6a4f; padding: 20px 48px; display: flex; justify-content: space-between; }}    .stat span {{ font-size: 20px; font-weight: bold; display: block; }}
    .content {{ padding: 48px; }}
    .section-title {{ color: #1b4332; font-size: 20px; border-bottom: 2px solid #d8f3dc; padding-bottom: 8px; margin: 32px 0 16px; }}
    .section-title:first-child {{ margin-top: 0; }}
    p {{ line-height: 1.8; margin-bottom: 12px; font-size: 16px; }}
    li {{ line-height: 1.8; margin-bottom: 8px; margin-left: 20px; font-size: 15px; }}
    .footer {{ background: #f8f9fa; border-top: 1px solid #e9ecef; padding: 24px 48px; text-align: center; }}
    .footer p {{ color: #868e96; font-size: 13px; font-family: Arial, sans-serif; line-height: 1.6; }}
  </style>
</head>
<body>
  <div class="wrapper">
    <div class="header">
      <div class="logo">🌱</div>
      <h1>EcoWatch Weekly</h1>
      <div class="subtitle">Environmental Intelligence</div>
      <div class="date">{date}</div>
    </div>

    <div class="stats-bar" style="justify-content: space-around;">
      <div class="stat" style="text-align: center;"><span>{len(ranked_articles)}</span>Articles analyzed</div>
      <div class="stat" style="text-align: center;"><span>3</span>Thematic sections</div>
      <div class="stat" style="text-align: center;"><span>1</span>Time per week</div>
    </div>

    <div class="content">
      {html_content}

      <h2 class="section-title">📎 Top Articles This Week</h2>
      <p style="font-size:13px; color:#868e96; font-family:Arial; margin-bottom:20px;">
        Ranked by importance — click the title to read the full article
      </p>
      {articles_html}
    </div>

    <div class="footer">
      <p>🌱 <strong>EcoWatch Weekly</strong> — Environmental Intelligence<br>
      Powered by LangGraph + Groq + ChromaDB + Tavily<br>
      {date}</p>
    </div>
  </div>
</body>
</html>"""