import requests
import time
from datetime import datetime
import pytz

# Scegli il fuso europeo (es. Roma, Berlino, Parigi)
EUROPE_TZ = pytz.timezone("Europe/Rome")

def wait_until_2am():
    while True:
        now = datetime.now(EUROPE_TZ)
        if now.hour == 2:
            return
        print(f"[{now.strftime('%H:%M:%S')}] Aspetto le 2:00...")
        time.sleep(60)

def run_daily_reset():
    try:
        print("✅ Avvio reset giornaliero...")
        response = requests.get("http://127.0.0.1:5000/run_daily_reset")
        if response.status_code == 200:
            print("🎉 Reset completato con successo.")
        else:
            print("⚠️ Errore nel reset.")
    except Exception as e:
        print("Errore nella richiesta:", e)

if __name__ == "__main__":
    wait_until_2am()
    run_daily_reset()
