# 🌱 EcoWatch Agent

Intelligence ambientale settimanale — ricevi ogni lunedì una newsletter su clima, politica ambientale e ricerca scientifica.

## Stack
- **LangGraph** — orchestrazione agente
- **Groq** — LLM gratuito (LLaMA 3.3)
- **Tavily** — ricerca notizie in tempo reale
- **ChromaDB** — database paper scientifici
- **GitHub Actions** — scheduler automatico

## Setup

### 1. Clona il repo
```bash
git clone https://github.com/tuonome/ecowatch-agent.git
cd ecowatch-agent
```

### 2. Crea il virtual environment
```bash
python -m venv .venv
.venv\Scripts\activate        # Windows
source .venv/bin/activate     # Mac/Linux
pip install -r requirements.txt
```

### 3. Configura le API keys
```bash
cp .env.example .env
# Modifica .env con le tue chiavi
```

API keys necessarie:
- **Groq**: [console.groq.com](https://console.groq.com) — gratuito
- **Tavily**: [tavily.com](https://tavily.com) — gratuito (1000 req/mese)
- **Gmail App Password**: [myaccount.google.com/apppasswords](https://myaccount.google.com/apppasswords)

### 4. Aggiungi paper scientifici
```bash
# Modifica data/papers.json con i tuoi paper
python add_papers.py
```

## Utilizzo

### Briefing giornaliero (manuale)
```bash
python main.py
```

### Weekly digest (manuale)
```bash
python scheduler.py
```

### Weekly digest (automatica)
La GitHub Action invia la newsletter ogni **lunedì alle 9:00** (ora italiana) automaticamente.

Per eseguirla manualmente: GitHub → Actions → EcoWatch Weekly Digest → Run workflow.

## Struttura
```
ecowatch-agent/
├── agents/
│   ├── state.py          # Stato LangGraph
│   └── graph.py          # Grafo agente
├── tools/
│   ├── news_search.py    # Ricerca notizie (Tavily)
│   ├── bias_analyzer.py  # Analisi bias (Groq)
│   ├── paper_retriever.py # Database paper (ChromaDB)
│   ├── briefing_generator.py # Genera briefing
│   ├── weekly_digest.py  # Newsletter settimanale
│   └── email_sender.py   # Invio email (Gmail)
├── data/
│   └── papers.json       # Paper scientifici
├── .github/
│   └── workflows/
│       └── weekly_digest.yml # GitHub Actions
├── .env.example
└── main.py
```