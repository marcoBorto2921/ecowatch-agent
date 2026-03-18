# Theory — How EcoWatch Agent Works

This guide explains the theoretical concepts behind EcoWatch Agent.
Each concept is connected to how it is used in the project.

---

## 1. What is an AI Agent

A normal program executes fixed instructions:
```
input → processing → output
```

An AI agent instead:
```
input → reasons → decides what to do → acts → observes the result → reasons again
```

The key difference is **autonomy** — the agent decides on its own
which actions to take to reach a goal.

### Agent components

**Brain (LLM)** — the language model that reasons and decides.
EcoWatch uses LLaMA 3.3 via Groq.

**Tools** — actions the agent can execute.
EcoWatch tools are:
- Tavily → searches for news on the internet
- ChromaDB → searches scientific papers
- Gmail → sends emails

**Memory** — information the agent remembers during execution.
In EcoWatch, the LangGraph State is the shared memory between nodes.

**Orchestrator** — decides the order of actions.
In EcoWatch, this is LangGraph.

### EcoWatch is a "pipeline" agent

There are different types of agents:

| Type | How it works |
|---|---|
| **Pipeline** | Executes steps in a fixed sequence |
| **ReAct** | Reasons and dynamically decides the next step |
| **Multi-agent** | Multiple agents collaborate |

EcoWatch is a pipeline — the steps are always the same:
search → analyze → retrieve → generate. It is the simplest
and most reliable type for repetitive tasks like a daily briefing.

---

## 2. LangGraph — Graphs, Nodes and State

### The problem it solves

Without LangGraph, you would write:
```python
articles = search_news()
analysis = analyze_bias(articles)
papers = retrieve_papers(analysis)
briefing = generate_briefing(papers)
```

It works, but doesn't scale. It doesn't handle errors, doesn't allow
conditional logic, and is not modular.

### The graph

LangGraph treats the agent as a **directed graph**:
```
[search_news] → [analyze_bias] → [retrieve_papers] → [generate_briefing]
```

Each block is a **node**. The arrows are **edges** (connections).
The graph knows the order in which to execute them.

### The State

The State is a Python dictionary shared between all nodes.
It is the agent's "working memory" — each node reads from here
and writes here.
```python
class EcoWatchState(TypedDict):
    articles: List[NewsArticle]      # written by search_news
    bias_analyses: List[dict]        # written by analyze_bias
    scientific_papers: List[dict]    # written by retrieve_papers
    final_briefing: str              # written by generate_briefing
```

### Nodes

Each node is a normal Python function:
```python
def search_news(state: EcoWatchState) -> dict:
    # 1. Reads from state
    queries = state.get("search_queries")
    
    # 2. Does something
    articles = tavily.search(queries)
    
    # 3. Returns updates to state
    return {"articles": articles}
```

Nodes don't call each other directly — they communicate only
through the State. This makes them independent and modular.

### Annotated — the accumulation magic
```python
articles: Annotated[List[NewsArticle], operator.add]
```

Without `Annotated` → each node overwrites the previous value.
With `Annotated[List, operator.add]` → values accumulate.

Example:
```
Node 1 → {"articles": [art1, art2]}
Node 2 → {"articles": [art3]}
Result → {"articles": [art1, art2, art3]}  ✅
```

---

## 3. Vector Databases and Embeddings

### The problem

A SQL database searches by exact match:
```sql
SELECT * FROM papers WHERE title LIKE '%climate%'
```

It won't find "global warming" if you search "ocean temperature"
— the words are different even if the meaning is similar.

### The solution — Embeddings

An **embedding** is the numerical representation of the meaning
of a text. Each text is converted into a vector —
a list of numbers representing its position in a
"semantic space".
```
"global warming"    → [0.23, 0.87, 0.12, 0.95, ...]
"ocean temperature" → [0.21, 0.85, 0.15, 0.91, ...]
"pasta recipe"      → [0.91, 0.02, 0.76, 0.11, ...]
```

Texts with similar meaning have **close** vectors in space.
Texts with different meaning have **distant** vectors.

### ChromaDB

ChromaDB is a database that:
1. Receives a text
2. Converts it into an embedding automatically
3. Saves it with its metadata
4. When you search, converts the query into an embedding
5. Finds the documents with the closest embeddings

In EcoWatch we use ChromaDB to find the most relevant scientific
papers for each news article analyzed.
```python
# ChromaDB finds papers semantically close to the news
results = collection.query(
    query_texts=["heatwaves in Europe"],
    n_results=3
)
# Finds: papers on heat stress, summer mortality, Mediterranean climate
# Even if they don't contain exactly those words
```

### The embedding model

EcoWatch uses `all-MiniLM-L6-v2` — a lightweight model
(~80MB) that ChromaDB downloads automatically on first run.
It converts texts into vectors with 384 dimensions.

---

## 4. RAG — Retrieval Augmented Generation

### The LLM problem

LLMs have a **knowledge cutoff** — they only know what
was in their training data up to a certain date.
They don't know specific scientific papers, recent news,
or private documents.

### The solution — RAG

RAG combines two systems:
```
[Document database] + [LLM] = answers based on real sources
```

The RAG flow:
```
1. Query → "What does science say about heatwaves?"
2. Retrieve → ChromaDB finds the 3 most relevant papers
3. Augment → the papers are added to the LLM prompt
4. Generate → the LLM answers based on real papers
```

### RAG in EcoWatch
```python
# 1. RETRIEVE — find relevant papers for the news
results = collection.query(
    query_texts=[article["title"] + article["content"]],
    n_results=3
)

# 2. AUGMENT — add the papers to the prompt
prompt = f"""
Analyze this news article:
{article["content"]}

Relevant scientific papers:
{results}  ← real papers from the database

Generate the briefing based on these sources.
"""

# 3. GENERATE — the LLM answers with real sources
response = llm.invoke(prompt)
```

Without RAG, the LLM would generate a briefing based only
on its generic training. With RAG, the briefing is
**anchored to specific scientific papers** that you chose.

### Why RAG is powerful

| Without RAG | With RAG |
|---|---|
| Generic answers | Answers based on specific sources |
| Knowledge cutoff | Always up to date |
| Can hallucinate | Anchored to real documents |
| Not customizable | The database is yours |

---

## Complete EcoWatch Architecture
```
                    ┌─────────────────────────────────┐
                    │         LangGraph Graph          │
                    │                                  │
  [Tavily API] ──→  │  search_news                     │
                    │       ↓                          │
  [Groq LLM]  ──→  │  analyze_bias                    │
                    │       ↓                          │
  [ChromaDB]  ──→  │  retrieve_papers   ← RAG         │
                    │       ↓                          │
  [Groq LLM]  ──→  │  generate_briefing               │
                    │       ↓                          │
                    │  [briefing.html + email]         │
                    └─────────────────────────────────┘
                              ↑
                    GitHub Actions (every Monday)
```

---

*EcoWatch Agent — built with LangGraph + Groq + ChromaDB + Tavily*
