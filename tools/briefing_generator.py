import os
from datetime import datetime
from pathlib import Path
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from agents.state import EcoWatchState

PROMPT = ChatPromptTemplate.from_messages([
    ("system", """You are the editor of EcoWatch, a daily environmental intelligence service.
Your job is to produce a clear, evidence-based daily briefing in Italian.
Style: precise, critical, action-oriented.

Structure your briefing exactly like this:

## 🌍 Executive Summary
(3-4 sentences on today's environmental situation)

## 📰 Top Stories
(for each article: headline, summary, credibility note)

## 🔬 Scientific Context
(connect the news to the scientific papers provided)

## ⚠️ Red Flags
(highlight low credibility sources or misinformation)

## 💡 Key Takeaways
(what does this mean for citizens and policy makers)"""),
    ("human", """Today is {date}.

ARTICLES ANALYZED:
{articles}

BIAS ANALYSES:
{analyses}

SCIENTIFIC PAPERS:
{papers}

Generate the daily briefing in Italian:""")
])


def generate_briefing(state: EcoWatchState) -> dict:
    print("\n✍️  Generating daily briefing...")

    llm = ChatGroq(
        model="llama-3.3-70b-versatile",
        temperature=0.3,
        api_key=os.getenv("GROQ_API_KEY"),
    )

    articles_text = "\n".join([
        f"- {a['title']} ({a['source']})"
        for a in state.get("articles", [])
    ])

    analyses_text = "\n".join([
        f"- {a['article_title']}: credibility {a['credibility_score']}/10, bias: {a['bias_type']}"
        for a in state.get("bias_analyses", [])
    ])

    papers_text = "\n".join([
        f"- {p['title']} ({p['year']}) — relevance: {p['relevance']}"
        for p in state.get("scientific_papers", [])
    ])

    chain = PROMPT | llm

    response = chain.invoke({
        "date": state.get("date", datetime.now().strftime("%Y-%m-%d")),
        "articles": articles_text,
        "analyses": analyses_text,
        "papers": papers_text,
    })

    briefing = response.content
    date = state.get("date", datetime.now().strftime("%Y-%m-%d"))

    # Salva .md
    output_dir = Path("./briefings")
    output_dir.mkdir(exist_ok=True)
    md_file = output_dir / f"briefing_{date}.md"
    md_file.write_text(briefing, encoding="utf-8")
    print(f"  ✓ Markdown saved: {md_file}")

    # Salva HTML
    html = _generate_html(briefing, date, state)
    html_file = output_dir / f"briefing_{date}.html"
    html_file.write_text(html, encoding="utf-8")
    print(f"  ✓ HTML saved: {html_file}")

    return {"final_briefing": briefing}


def _generate_html(briefing: str, date: str, state: EcoWatchState) -> str:
    """Converte il briefing in una newsletter HTML professionale."""

    # Converti il markdown in HTML semplice
    html_content = ""
    for line in briefing.split("\n"):
        if line.startswith("## "):
            title = line.replace("## ", "")
            html_content += f'<h2 class="section-title">{title}</h2>\n'
        elif line.startswith("### "):
            title = line.replace("### ", "")
            html_content += f'<h3>{title}</h3>\n'
        elif line.startswith("- "):
            html_content += f'<li>{line[2:]}</li>\n'
        elif line.startswith("**") and line.endswith("**"):
            html_content += f'<strong>{line[2:-2]}</strong>\n'
        elif line.strip() == "":
            html_content += "<br>\n"
        else:
            html_content += f'<p>{line}</p>\n'

    # Statistiche
    n_articles = len(state.get("articles", []))
    analyses = state.get("bias_analyses", [])
    avg_credibility = round(
        sum(a.get("credibility_score", 5) for a in analyses) / len(analyses), 1
    ) if analyses else 0

    # Badge credibilità media
    if avg_credibility >= 7:
        badge_color = "#2d6a4f"
        badge_label = "Alta"
    elif avg_credibility >= 4:
        badge_color = "#e9c46a"
        badge_label = "Media"
    else:
        badge_color = "#e63946"
        badge_label = "Bassa"

    return f"""<!DOCTYPE html>
<html lang="it">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>EcoWatch Briefing — {date}</title>
  <style>
    * {{ margin: 0; padding: 0; box-sizing: border-box; }}
    body {{ background: #f4f4f4; font-family: Georgia, serif; color: #333; }}

    .email-wrapper {{ max-width: 680px; margin: 40px auto; background: white; border-radius: 8px; overflow: hidden; box-shadow: 0 2px 20px rgba(0,0,0,0.1); }}

    /* Header */
    .header {{ background: #1b4332; padding: 40px 48px; text-align: center; }}
    .header .logo {{ font-size: 36px; }}
    .header h1 {{ color: #d8f3dc; font-size: 22px; font-weight: normal; letter-spacing: 3px; text-transform: uppercase; margin-top: 8px; }}
    .header .date {{ color: #95d5b2; font-size: 14px; margin-top: 8px; }}

    /* Stats bar */
    .stats-bar {{ background: #2d6a4f; padding: 16px 48px; display: flex; gap: 32px; }}
    .stat {{ color: white; font-size: 13px; font-family: Arial, sans-serif; }}
    .stat span {{ font-size: 20px; font-weight: bold; display: block; }}

    /* Badge credibilità */
    .badge {{ background: {badge_color}; color: white; padding: 4px 12px; border-radius: 20px; font-size: 12px; font-family: Arial, sans-serif; display: inline-block; margin-left: 8px; }}

    /* Contenuto */
    .content {{ padding: 48px; }}
    .section-title {{ color: #1b4332; font-size: 20px; border-bottom: 2px solid #d8f3dc; padding-bottom: 8px; margin: 32px 0 16px; }}
    .section-title:first-child {{ margin-top: 0; }}
    p {{ line-height: 1.8; margin-bottom: 12px; font-size: 16px; }}
    li {{ line-height: 1.8; margin-bottom: 8px; margin-left: 20px; font-size: 15px; }}
    h3 {{ color: #40916c; margin: 16px 0 8px; font-size: 17px; }}

    /* Footer */
    .footer {{ background: #f8f9fa; border-top: 1px solid #e9ecef; padding: 24px 48px; text-align: center; }}
    .footer p {{ color: #868e96; font-size: 13px; font-family: Arial, sans-serif; line-height: 1.6; }}
  </style>
</head>
<body>
  <div class="email-wrapper">

    <div class="header">
      <div class="logo">🌱</div>
      <h1>EcoWatch Daily</h1>
      <div class="date">{datetime.strptime(date, "%Y-%m-%d").strftime("%A %d %B %Y")}</div>
    </div>

    <div class="stats-bar">
      <div class="stat">
        <span>{n_articles}</span>
        Articoli analizzati
      </div>
      <div class="stat">
        <span>{avg_credibility}/10</span>
        Credibilità media
      </div>
      <div class="stat">
        <span>{len(state.get("scientific_papers", []))}</span>
        Paper scientifici
      </div>
      <div class="stat">
        Affidabilità fonti
        <span><span class="badge">{badge_label}</span></span>
      </div>
    </div>

    <div class="content">
      {html_content}
    </div>

    <div class="footer">
      <p>🌱 <strong>EcoWatch Agent</strong> — Intelligence ambientale quotidiana<br>
      Generato automaticamente con LangGraph + Groq + ChromaDB + Tavily<br>
      {date}</p>
    </div>

  </div>
</body>
</html>"""