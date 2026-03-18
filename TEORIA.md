# 📚 Teoria — Come funziona EcoWatch Agent

Questa guida spiega i concetti teorici dietro EcoWatch Agent.
Ogni concetto è collegato a come viene usato nel progetto.

---

## 1. Cos'è un Agente AI

Un programma normale esegue istruzioni fisse:
```
input → elaborazione → output
```

Un agente AI invece:
```
input → ragiona → decide cosa fare → agisce → osserva il risultato → ragiona di nuovo
```

La differenza chiave è l'**autonomia** — l'agente decide da solo
quali azioni eseguire per raggiungere un obiettivo.

### I componenti di un agente

**Cervello (LLM)** — il modello linguistico che ragiona e decide.
In EcoWatch usiamo LLaMA 3.3 via Groq.

**Strumenti (Tools)** — azioni che l'agente può eseguire.
In EcoWatch i tools sono:
- Tavily → cerca notizie su internet
- ChromaDB → cerca paper scientifici
- Gmail → invia email

**Memoria** — informazioni che l'agente ricorda durante l'esecuzione.
In EcoWatch lo State di LangGraph è la memoria condivisa tra i nodi.

**Orchestratore** — decide l'ordine delle azioni.
In EcoWatch è LangGraph.

### EcoWatch è un agente "pipeline"

Esistono diversi tipi di agenti:

| Tipo | Come funziona |
|---|---|
| **Pipeline** | Esegue passi in sequenza fissa |
| **ReAct** | Ragiona e decide il passo successivo dinamicamente |
| **Multi-agent** | Più agenti collaborano tra loro |

EcoWatch è una pipeline — i passi sono sempre gli stessi:
cerca → analizza → recupera → genera. È il tipo più semplice
e affidabile per task ripetitivi come un briefing quotidiano.

---

## 2. LangGraph — Grafi, Nodi e State

### Il problema che risolve

Senza LangGraph, scriveresti:
```python
articoli = cerca_notizie()
analisi = analizza_bias(articoli)
paper = recupera_paper(analisi)
briefing = genera_briefing(paper)
```

Funziona, ma non scala. Non gestisce errori, non permette
logica condizionale, non è modulare.

### Il grafo

LangGraph tratta l'agente come un **grafo orientato**:
```
[search_news] → [analyze_bias] → [retrieve_papers] → [generate_briefing]
```

Ogni blocco è un **nodo**. Le frecce sono **edge** (connessioni).
Il grafo sa in che ordine eseguirli.

### Lo State

Lo State è un dizionario Python condiviso tra tutti i nodi.
È la "memoria di lavoro" dell'agente — ogni nodo legge da qui
e scrive qui.
```python
class EcoWatchState(TypedDict):
    articles: List[NewsArticle]      # scritto da search_news
    bias_analyses: List[dict]        # scritto da analyze_bias
    scientific_papers: List[dict]    # scritto da retrieve_papers
    final_briefing: str              # scritto da generate_briefing
```

### I Nodi

Ogni nodo è una funzione Python normale:
```python
def search_news(state: EcoWatchState) -> dict:
    # 1. Legge dallo state
    queries = state.get("search_queries")
    
    # 2. Fa qualcosa
    articles = tavily.search(queries)
    
    # 3. Restituisce aggiornamenti allo state
    return {"articles": articles}
```

I nodi non si chiamano direttamente — comunicano solo
attraverso lo State. Questo li rende indipendenti e modulari.

### Annotated — la magia dell'accumulo
```python
articles: Annotated[List[NewsArticle], operator.add]
```

Senza `Annotated` → ogni nodo sovrascrive il valore precedente.
Con `Annotated[List, operator.add]` → i valori si accumulano.

Esempio:
```
Nodo 1 → {"articles": [art1, art2]}
Nodo 2 → {"articles": [art3]}
Risultato → {"articles": [art1, art2, art3]}  ✅
```

---

## 3. Database Vettoriali ed Embedding

### Il problema

Un database SQL cerca per corrispondenza esatta:
```sql
SELECT * FROM papers WHERE title LIKE '%clima%'
```

Non trova "riscaldamento globale" se cerchi "temperatura oceani"
— le parole sono diverse anche se il significato è simile.

### La soluzione — Embedding

Un **embedding** è la rappresentazione numerica del significato
di un testo. Ogni testo viene convertito in un vettore —
una lista di numeri che rappresenta la sua posizione in uno
"spazio semantico".
```
"riscaldamento globale" → [0.23, 0.87, 0.12, 0.95, ...]
"temperatura oceani"   → [0.21, 0.85, 0.15, 0.91, ...]
"ricetta pasta"        → [0.91, 0.02, 0.76, 0.11, ...]
```

Testi con significato simile hanno vettori **vicini** nello spazio.
Testi con significato diverso hanno vettori **lontani**.

### ChromaDB

ChromaDB è un database che:
1. Riceve un testo
2. Lo converte in embedding automaticamente
3. Lo salva con i suoi metadati
4. Quando cerchi, converte la query in embedding
5. Trova i documenti con embedding più vicini

In EcoWatch usiamo ChromaDB per trovare i paper scientifici
più rilevanti per ogni notizia analizzata.
```python
# ChromaDB trova i paper semanticamente vicini alla notizia
results = collection.query(
    query_texts=["ondate di calore in Europa"],
    n_results=3
)
# Trova: paper su heat stress, mortalità estiva, clima mediterraneo
# Anche se non contengono esattamente quelle parole
```

### Il modello di embedding

In EcoWatch usiamo `all-MiniLM-L6-v2` — un modello leggero
(~80MB) che ChromaDB scarica automaticamente al primo avvio.
Converte testi in vettori da 384 dimensioni.

---

## 4. RAG — Retrieval Augmented Generation

### Il problema degli LLM

Gli LLM hanno una **knowledge cutoff** — sanno solo quello
che era nel loro training data fino a una certa data.
Non conoscono paper scientifici specifici, notizie recenti,
o documenti privati.

### La soluzione — RAG

RAG combina due sistemi:
```
[Database documenti] + [LLM] = risposte basate su fonti reali
```

Il flusso RAG:
```
1. Query → "Cosa dice la scienza sulle ondate di calore?"
2. Retrieve → ChromaDB trova i 3 paper più rilevanti
3. Augment → i paper vengono aggiunti al prompt dell'LLM
4. Generate → l'LLM risponde basandosi sui paper reali
```

### RAG in EcoWatch
```python
# 1. RETRIEVE — trova paper rilevanti per la notizia
results = collection.query(
    query_texts=[article["title"] + article["content"]],
    n_results=3
)

# 2. AUGMENT — aggiungi i paper al prompt
prompt = f"""
Analizza questa notizia:
{article["content"]}

Paper scientifici rilevanti:
{results}  ← i paper reali dal database

Genera il briefing basandoti su queste fonti.
"""

# 3. GENERATE — l'LLM risponde con fonti reali
response = llm.invoke(prompt)
```

Senza RAG, l'LLM genererebbe un briefing basato solo
sul suo training generico. Con RAG, il briefing è
**ancorato a paper scientifici specifici** che hai scelto tu.

### Perché RAG è potente

| Senza RAG | Con RAG |
|---|---|
| Risposte generiche | Risposte basate su fonti specifiche |
| Knowledge cutoff | Sempre aggiornato |
| Può allucinare | Ancorato a documenti reali |
| Non personalizzabile | Il database è tuo |

---

## Architettura completa di EcoWatch
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
                    GitHub Actions (ogni lunedì)
```

---

*EcoWatch Agent — costruito con LangGraph + Groq + ChromaDB + Tavily*