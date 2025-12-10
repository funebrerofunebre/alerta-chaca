import os
import time
import requests
import feedparser
import re
from duckduckgo_search import DDGS

# --- CONFIGURACIÓN ---
TOKEN = os.environ['TELEGRAM_TOKEN']
CHAT_ID = os.environ['TELEGRAM_CHAT_ID']
QUERY_TWITTER = "Chacarita"
QUERY_GOOGLE = "Chacarita"

# Lista de Puentes RSSHub (Si uno falla, probamos el siguiente)
RSSHUB_INSTANCES = [
    "https://rsshub.app",
    "https://rsshub.feeddd.org",
    "https://rsshub.lihaoyu.cn",
    "https://rss.shab.fun",
    "https://rsshub.blue"
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

# --- ESTRATEGIA 1: RSSHUB (El Puente) ---
def buscar_rsshub(vistos):
    print("--- 1. Probando Puentes RSSHub ---")
    feed = None
    
    # Probamos cada servidor de la lista
    for instance in RSSHUB_INSTANCES:
        try:
            # Ruta para buscar keyword en Twitter
            url = f"{instance}/twitter/keyword/{QUERY_TWITTER}"
            print(f"🔌 Probando conexión con {instance}...")
            
            # Timeout corto (5s) para no perder tiempo si está caído
            feed = feedparser.parse(url, agent="Mozilla/5.0")
            
            # Si el feed tiene entradas o un status 200, es que conectó
            if feed.entries:
                print(f"✅ ¡Conectado a {instance}!")
                break
            elif feed.status == 200 and not feed.entries:
                 print(f"⚠ Conectó a {instance} pero vino vacío (sin tweets nuevos).")
                 # Si conecta pero está vacío, cortamos acá para no seguir probando al pedo
                 return 
        except:
            continue
            
    if not feed or not feed.entries:
        print("❌ Todos los puentes RSSHub fallaron o están bloqueados.")
        return

    # Si llegamos acá, tenemos tweets
    for entry in feed.entries:
        link = entry.link
        if link not in vistos:
            print(f"🐦 Nuevo Tweet: {entry.title}")
            # Limpiamos un poco el título si viene sucio
            texto = entry.title.replace(" - Twitter Search / X", "")
            
            msg = f"🐦 *TWEET (Vía RSSHub)*\n\n📝 {texto}\n\n🔗 {link}"
            enviar_telegram(msg)
            guardar_historial(link)
            vistos.add(link)
            time.sleep(1)

# --- ESTRATEGIA 2: DUCKDUCKGO (Backup) ---
def buscar_ddg(vistos):
    print("--- 2. Probando DuckDuckGo (Backup) ---")
    try:
        # Le saqué el límite de tiempo estricto a ver si así muestra algo
        results = DDGS().text(f"site:twitter.com {QUERY_TWITTER}", region='ar-es', max_results=5)
        if not results:
            print("↳ Nada por acá.")
        
        for r in results:
            link = r.get('href', '')
            if "twitter.com" in link or "x.com" in link:
                if link not in vistos:
                    msg = f"🔍 *TWEET (Vía Buscador)*\n\n📝 {r.get('title', 'Tweet')}\n\n🔗 {link}"
                    enviar_telegram(msg)
                    guardar_historial(link)
                    vistos.add(link)
                    time.sleep(2)
    except Exception as e:
        print(f"⚠️ DDG Falló: {e}")

# --- ESTRATEGIA 3: GOOGLE NEWS (El Tanque) ---
def buscar_google(vistos):
    print("--- 3. Probando Google News ---")
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
    buscar_rsshub(vistos)
    buscar_ddg(vistos)
    buscar_google(vistos)

if __name__ == "__main__":
    main()
