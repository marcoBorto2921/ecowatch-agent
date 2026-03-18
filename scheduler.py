import schedule
import time
from dotenv import load_dotenv
from tools.weekly_digest import generate_weekly_digest

load_dotenv()

def job():
    print("\n⏰ Avvio weekly digest automatica...")
    try:
        generate_weekly_digest()
    except Exception as e:
        print(f"❌ Errore: {e}")

# Esegui ogni lunedì alle 8:00
schedule.every().monday.at("08:00").do(job)

print("⏰ Scheduler attivo — digest ogni lunedì alle 08:00")
print("   Premi Ctrl+C per fermare\n")

# Esegui subito la prima volta per testare
print("🔄 Prima esecuzione immediata per test...")
job()

# Poi continua ad aspettare
while True:
    try:
        schedule.run_pending()
        time.sleep(60)
    except KeyboardInterrupt:
        print("\n⏹ Scheduler fermato.")
        break