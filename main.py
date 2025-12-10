import os
import time
import requests
import feedparser
import re
from duckduckgo_search import DDGS

# --- CONFIGURACIÓN ---
TOKEN = os.environ['TELEGRAM_TOKEN']
CHAT_ID = os.environ['TELEGRAM_CHAT_ID']

# Palabras clave para DuckDuckGo (Buscamos de varias formas)
QUERIES_DDG = [
    "site:twitter.com Chacarita",
    "site:x.com Chacarita",
    "Chacarita twitter"
]

# Búsqueda para Google News
QUERY_GOOGLE = "Chacarita"

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
    # Intenta sacar el ID numérico del tweet
    match = re.search(r'/status/(\d+)', url)
    return match.group(1) if match else url

# --- ESTRATEGIA 1: DUCKDUCKGO (Modo Ametralladora) ---
def buscar_ddg_intensivo(vistos):
    print("--- 1. Probando DuckDuckGo (Búsqueda Intensiva) ---")
    try:
        ddgs = DDGS()
        
        # Probamos con cada una de las frases de búsqueda
        for query in QUERIES_DDG:
            print(f"🔎 Buscando: {query}...")
            # Usamos timelimit='d' (día) para asegurar resultados
            results = ddgs.text(query, region='ar-es', timelimit='d', max_results=10)
            
            if not results:
                print("   ↳ Nada por acá.")
                continue

            for r in results:
                link = r.get('href', '')
                titulo = r.get('title', 'Tweet')
                
                # Filtramos: Solo nos sirven links de Twitter/X
                if "twitter.com" in link or "x.com" in link:
                    tid = extraer_id(link)
                    
                    if tid not in vistos:
                        print(f"✅ Nuevo Tweet encontrado: {link}")
                        msg = f"🐦 *TWEET ENCONTRADO*\n\n📝 {titulo}\n\n🔗 {link}"
                        enviar_telegram(msg)
                        guardar_historial(tid)
                        vistos.add(tid)
                        time.sleep(2)

            time.sleep(1) # Respiro entre búsquedas

    except Exception as e:
        print(f"⚠️ Error en DuckDuckGo: {e}")

# --- ESTRATEGIA 2: GOOGLE NEWS (El Tanque) ---
def buscar_google(vistos):
    print("--- 2. Probando Google News ---")
    try:
        url = f"https://news.google.com/rss/search?q={QUERY_GOOGLE}+when:1d&hl=es-419&gl=AR&ceid=AR:es-419"
        feed = feedparser.parse(url)
        
        for entry in reversed(feed.entries):
            link = entry.link
            if link not in vistos:
                print(f"✅ Noticia Google: {entry.title}")
                msg = f"📰 *GOOGLE NEWS*\n\n{entry.title}\n\n🔗 {link}"
                enviar_telegram(msg)
                guardar_historial(link)
                vistos.add(link)
                time.sleep(1)
    except Exception as e:
        print(f"⚠️ Google Falló: {e}")

def main():
    vistos = leer_historial()
    buscar_ddg_intensivo(vistos)
    buscar_google(vistos)

if __name__ == "__main__":
    main()
