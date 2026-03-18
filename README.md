# 🌱 EcoWatch Agent

Weekly environmental intelligence — receive every Monday a newsletter on climate change, environmental policy, and scientific research.

## Stack
- **LangGraph** — agent orchestration
- **Groq** — free LLM (LLaMA 3.3)
- **Tavily** — real-time news search
- **ChromaDB** — scientific papers database
- **GitHub Actions** — automatic scheduler

## Setup

### 1. Clone the repo
```bash
git clone https://github.com/marcoBorto2921/ecowatch-agent.git
cd ecowatch-agent
```

### 2. Create the virtual environment
```bash
python -m venv .venv
.venv\Scripts\activate        # Windows
source .venv/bin/activate     # Mac/Linux
pip install -r requirements.txt
```

### 3. Configure API keys
```bash
cp .env.example .env
# Fill in your keys
```

Required API keys:
- **Groq**: [console.groq.com](https://console.groq.com) — free
- **Tavily**: [tavily.com](https://tavily.com) — free (1000 req/month)
- **Gmail App Password**: [myaccount.google.com/apppasswords](https://myaccount.google.com/apppasswords)

### 4. Add scientific papers
```bash
# Edit data/papers.json with your papers
python add_papers.py
```

## Usage

### Daily briefing (manual)
```bash
python main.py
```

### Weekly digest (manual)
```bash
python scheduler.py
```

### Weekly digest (automatic)
The GitHub Action sends the newsletter every **Monday at 8:00 UTC (9:00 Italian time)** automatically.

To run it manually: GitHub → Actions → EcoWatch Weekly Digest → Run workflow.

## Project Structure
```
ecowatch-agent/
├── agents/
│   ├── state.py               # LangGraph state
│   └── graph.py               # Agent graph
├── tools/
│   ├── news_search.py         # News search (Tavily)
│   ├── bias_analyzer.py       # Bias analysis (Groq)
│   ├── paper_retriever.py     # Paper retrieval (ChromaDB)
│   ├── briefing_generator.py  # Briefing generation
│   ├── weekly_digest.py       # Weekly newsletter
│   └── email_sender.py        # Email sending (Gmail)
├── data/
│   └── papers.json            # Scientific papers
├── .github/
│   └── workflows/
│       └── weekly_digest.yml  # GitHub Actions scheduler
├── .env.example
└── main.py
```
```
