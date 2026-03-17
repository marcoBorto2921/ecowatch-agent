from typing import TypedDict
from langgraph.graph import StateGraph, END
from dotenv import load_dotenv

load_dotenv()

# ── 1. STATE ──────────────────────────────────────────
# Il dizionario condiviso tra tutti i nodi
class State(TypedDict):
    domanda: str
    risposta: str

# ── 2. NODI ───────────────────────────────────────────
# Ogni nodo riceve lo state e restituisce un aggiornamento

def nodo_domanda(state: State) -> dict:
    print(">> Nodo 1: ricevo la domanda")
    print("   Domanda:", state["domanda"])
    return {}  # non modifica nulla, passa avanti

def nodo_risposta(state: State) -> dict:
    print(">> Nodo 2: genero la risposta")
    risposta = f"Hai chiesto: '{state['domanda']}' — risposta elaborata!"
    return {"risposta": risposta}  # aggiorna lo state

# ── 3. GRAFO ──────────────────────────────────────────
grafo = StateGraph(State)

# Aggiungi i nodi
grafo.add_node("nodo_domanda", nodo_domanda)
grafo.add_node("nodo_risposta", nodo_risposta)

# Collega i nodi
grafo.set_entry_point("nodo_domanda")
grafo.add_edge("nodo_domanda", "nodo_risposta")
grafo.add_edge("nodo_risposta", END)

# Compila il grafo
app = grafo.compile()

# ── 4. ESEGUI ─────────────────────────────────────────
risultato = app.invoke({"domanda": "cos'è il clima?", "risposta": ""})

print("\n>> State finale:")
print("   Domanda:", risultato["domanda"])
print("   Risposta:", risultato["risposta"])