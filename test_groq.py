from dotenv import load_dotenv # for reading .env file
from langchain_groq import ChatGroq
import os

# Carica le variabili dal file .env
load_dotenv()

# Crea il client Groq
llm = ChatGroq(
    model="llama-3.3-70b-versatile",
    api_key=os.getenv("GROQ_API_KEY"),
)

# Prima chiamata
risposta = llm.invoke("Ciao! In una frase, cos'è il cambiamento climatico?")

print(risposta.content)