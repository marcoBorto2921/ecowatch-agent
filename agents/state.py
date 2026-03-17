#Typedict dizinario python con tipi dichiarati (dizionari che in piu ti danno errori se metti cose sbagliate dentro)
# Annotated serve per sommare i risultati degli articoli e non salvare solo l'ultimo
from typing import TypedDict, Annotated, List, Optional
import operator

class NewsArticle(TypedDict): #ogni articolo deve aere questi campi
    title: str
    url: str
    content: str
    source: str

class EcoWatchState(TypedDict):
    # Input
    search_queries: List[str]
    
    # Nodo 1 — cerca notizie
    articles: Annotated[List[NewsArticle], operator.add]  #operator add fa appen
    
    # Nodo 2 — analisi bias
    bias_analyses: Annotated[List[dict], operator.add]
    
    # Nodo 3 — paper scientifici
    scientific_papers: Annotated[List[dict], operator.add]
    
    # Nodo 4 — briefing finale
    final_briefing: str
    
    # Metadata
    date: str
    errors: Annotated[List[str], operator.add]