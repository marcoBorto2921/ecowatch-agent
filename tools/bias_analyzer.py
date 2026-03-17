import os
import json
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from agents.state import EcoWatchState

PROMPT = ChatPromptTemplate.from_messages([
    ("system", """You are a media analyst specialized in environmental journalism.
Analyze news articles for:
1. Editorial bias (political, ideological, commercial)
2. Source credibility
3. Misinformation signals

Always respond in valid JSON with this exact structure:
{{
  "credibility_score": <number 0-10>,
  "bias_type": "<neutral|eco-alarmist|climate-denialist|pro-industry|political>",
  "bias_intensity": "<low|medium|high>",
  "key_claims": ["<claim 1>", "<claim 2>"],
  "red_flags": ["<flag 1>"],
  "reasoning": "<brief explanation in English, max 100 words>"
}}"""),
    ("human", """Analyze this article:

TITLE: {title}
SOURCE: {source}
CONTENT: {content}

Provide the JSON analysis:""")
])


def analyze_bias(state: EcoWatchState) -> dict:
    print("\n🔬 Analyzing bias and credibility...")

    llm = ChatGroq(
        model="llama-3.3-70b-versatile",
        temperature=0.1,
        api_key=os.getenv("GROQ_API_KEY"),
    )

    chain = PROMPT | llm
    articles = state.get("articles", [])
    analyses = []

    for i, article in enumerate(articles, 1):
        print(f"  → [{i}/{len(articles)}] {article['title'][:60]}...")

        try:
            response = chain.invoke({
                "title": article["title"],
                "source": article["source"],
                "content": article["content"][:2000],
            })

            # Pulisci il JSON dalla risposta
            text = response.content.strip()
            if "```json" in text:
                text = text.split("```json")[1].split("```")[0].strip()
            elif "```" in text:
                text = text.split("```")[1].split("```")[0].strip()

            data = json.loads(text)
            data["article_title"] = article["title"]
            analyses.append(data)

            score = data["credibility_score"]
            bias = data["bias_type"]
            print(f"     ✓ Credibility: {score}/10 | Bias: {bias}")

        except Exception as e:
            print(f"     ✗ Error: {e}")

    return {"bias_analyses": analyses}