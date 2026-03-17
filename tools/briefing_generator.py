import os
from datetime import datetime
from pathlib import Path
from langchain_groq import ChatGroq
from langchain.prompts import ChatPromptTemplate
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

    # Prepara i dati per il prompt
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

    # Salva il briefing su file
    output_dir = Path("./briefings")
    output_dir.mkdir(exist_ok=True)
    filename = output_dir / f"briefing_{state.get('date', datetime.now().strftime('%Y-%m-%d'))}.md"
    filename.write_text(briefing, encoding="utf-8")

    print(f"  ✓ Briefing saved: {filename}")

    return {"final_briefing": briefing}