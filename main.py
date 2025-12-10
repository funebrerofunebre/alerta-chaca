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
QUERY_NITTER = "Chacarita%20-filter%3Aretweets"
QUERY_DDG = "site:twitter.com Chacarita"
# Google: Busca noticias de Chacarita de las últimas 24hs
QUERY_GOOGLE = "Chacarita" 

# Servidores Nitter
NITTER_INSTANCES = [
    "https://nitter.net",
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

def leer_historial():
    if os.path.exists("history_ids.txt"):
        with open("history_ids.txt", "r") as f:
            return set(f.read().splitlines())
    return set()

def guardar_historial(dato):
    with open("history_ids.txt", "a") as f:
        f.write(f"{dato}\n")

def extraer_id(url):
    match = re.search(r'/status/(\d+)', url)
    return match.group(1) if match else url 

# --- 1. NITTER ---
def buscar_nitter(vistos):
    print("--- 1. Probando Nitter ---")
    feed = None
    for instance in NITTER_INSTANCES:
        try:
            url = f"{instance}/search/rss?f=tweets&q={QUERY_NITTER}"
            feed = feedparser.parse(url)
            if feed.entries:
                print(f"✅ Conectado a {instance}")
                break
        except:
            continue
            
    if feed and feed.entries:
        for entry in reversed(feed.entries):
            tid = extraer_id(entry.link)
            if tid not in vistos:
                msg = f"🔴 *TWITTER (Nitter)*\n\n{entry.title}\n\n🔗 {entry.link}"
                enviar_telegram(msg)
                guardar_historial(tid)
                vistos.add(tid)
                time.sleep(1)

# --- 2. DUCKDUCKGO ---
def buscar_ddg(vistos):
    print("--- 2. Probando DuckDuckGo ---")
    try:
        results = DDGS().text(QUERY_DDG, region='ar-es', timelimit='d', max_results=10)
        for r in results:
            link = r.get('href', '')
            tid = extraer_id(link)
            if "twitter.com" in link or "x.com" in link:
                if tid not in vistos:
                    msg = f"🔵 *TWITTER (Buscador)*\n\n📝 {r.get('title', 'Tweet')}\n\n🔗 {link}"
                    enviar_telegram(msg)
                    guardar_historial(tid)
                    vistos.add(tid)
                    time.sleep(2)
    except Exception as e:
        print(f"⚠️ DDG Falló: {e}")

# --- 3. GOOGLE NEWS ---
def buscar_google(vistos):
    print("--- 3. Probando Google News ---")
    try:
        # Busca noticias de Chacarita en Argentina
        url = f"https://news.google.com/rss/search?q={QUERY_GOOGLE}+when:1d&hl=es-419&gl=AR&ceid=AR:es-419"
        feed = feedparser.parse(url)
        
        for entry in reversed(feed.entries):
            link = entry.link
            if link not in vistos:
                print(f"✅ Noticia Google: {entry.title}")
                msg = f"📰 *NOTICIA (Google)*\n\n{entry.title}\n\n🔗 {link}"
                enviar_telegram(msg)
                guardar_historial(link)
                vistos.add(link)
                time.sleep(1)
    except Exception as e:
        print(f"⚠️ Google Falló: {e}")

def main():
    vistos = leer_historial()
    buscar_nitter(vistos)
    buscar_ddg(vistos)
    buscar_google(vistos)

if __name__ == "__main__":
    main()
