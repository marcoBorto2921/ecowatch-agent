import chromadb

print("1. importazione ok")
# ── 1. CREA IL DATABASE ───────────────────────────────
# PersistentClient salva i dati su disco (nella cartella ./database)
client = chromadb.PersistentClient(path="./database")
print("2. client creato")
# Una "collection" è come una tabella in un database normale
collection = client.get_or_create_collection(name="paper_scientifici")
print("3. collection creata")
# ── 2. AGGIUNGI DOCUMENTI ─────────────────────────────
collection.upsert(
    ids=["paper1", "paper2", "paper3"],
    documents=[
        "Il riscaldamento globale sta causando lo scioglimento dei ghiacciai artici",
        "Le energie rinnovabili come il solare stanno riducendo le emissioni di CO2",
        "La deforestazione in Amazzonia accelera il cambiamento climatico",
    ]
)

print("✓ 3 paper aggiunti al database")

# ── 3. CERCA PER SIGNIFICATO ──────────────────────────
risultati = collection.query(
    query_texts=["temperatura oceani e ghiaccio"],
    n_results=2,
)

print("\nRicerca: 'temperatura oceani e ghiaccio'")
print("Risultati più simili:\n")

for doc, dist in zip(risultati["documents"][0], risultati["distances"][0]):
    similarita = round(1 - dist, 2)
    print(f"  Similarità: {similarita} → {doc}")