import os
import time
import requests
import feedparser
import re
from duckduckgo_search import DDGS

# --- CONFIGURACIÓN ---
TOKEN = os.environ['TELEGRAM_TOKEN']
CHAT_ID = os.environ['TELEGRAM_CHAT_ID']

# Búsquedas
QUERY_NITTER = "Chacarita%20-filter%3Aretweets" # Formato URL para RSS
QUERY_DDG = "site:twitter.com Chacarita"         # Formato Buscador

# Servidores Nitter (Por si uno falla)
NITTER_INSTANCES = [
    "https://nitter.privacydev.net",
    "https://nitter.poast.org",
    "https://nitter.lucabased.xyz",
    "https://xcancel.com"
]

def enviar_telegram(texto):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    try:
        requests.post(url, data={"chat_id": CHAT_ID, "text": texto, "parse_mode": "Markdown"})
    except Exception as e:
        print(f"❌ Error enviando a Telegram: {e}")

# --- MEMORIA (Para no repetir) ---
def leer_historial():
    if os.path.exists("history_ids.txt"):
        with open("history_ids.txt", "r") as f:
            return set(f.read().splitlines())
    return set()

def guardar_historial(tweet_id):
    with open("history_ids.txt", "a") as f:
        f.write(f"{tweet_id}\n")

def extraer_id(url):
    # Busca el número largo en la URL (el ID del tweet)
    match = re.search(r'/status/(\d+)', url)
    return match.group(1) if match else None

# --- ESTRATEGIA 1: NITTER (RSS) ---
def buscar_nitter(vistos):
    print("--- 1. Probando vía Nitter ---")
    feed = None
    for instance in NITTER_INSTANCES:
        try:
            url = f"{instance}/search/rss?f=tweets&q={QUERY_NITTER}"
            print(f"Probando {instance}...")
            feed = feedparser.parse(url)
            if feed.entries:
                break
        except:
            continue
            
    if not feed or not feed.entries:
        print("⚠️ Nitter falló o no trajo nada.")
        return

    for entry in reversed(feed.entries):
        tid = extraer_id(entry.link)
        if tid and tid not in vistos:
            print(f"✅ Nuevo (Nitter): {tid}")
            msg = f"🔴 *ALERTA (Vía Nitter)*\n\n{entry.title}\n\n🔗 {entry.link}"
            enviar_telegram(msg)
            guardar_historial(tid)
            vistos.add(tid)
            time.sleep(1)

# --- ESTRATEGIA 2: DUCKDUCKGO ---
def buscar_ddg(vistos):
    print("--- 2. Probando vía DuckDuckGo ---")
    try:
        # Busca resultados de la última hora ('h')
        results = DDGS().text(QUERY_DDG, region='ar-es', timelimit='d', max_results=10)
        
        for r in results:
            link = r.get('href', '')
            tid = extraer_id(link)
            
            # Solo procesamos si es un link de twitter válido y tiene ID
            if tid and ("twitter.com" in link or "x.com" in link):
                if tid not in vistos:
                    print(f"✅ Nuevo (DDG): {tid}")
                    titulo = r.get('title', 'Tweet')
                    msg = f"🔵 *ALERTA (Vía Buscador)*\n\n📝 {titulo}\n\n🔗 {link}"
                    enviar_telegram(msg)
                    guardar_historial(tid)
                    vistos.add(tid)
                    time.sleep(2)
    except Exception as e:
        print(f"⚠️ Error en DuckDuckGo: {e}")

# --- MAESTRO DE ORQUESTA ---
def main():
    vistos = leer_historial()
    
    # Ejecuta las dos estrategias
    buscar_nitter(vistos)
    buscar_ddg(vistos)

if __name__ == "__main__":
    main()
