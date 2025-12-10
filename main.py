import os
import time
import requests
import feedparser
import re
from ntscraper import Nitter

# --- CONFIGURACIÓN ---
TOKEN = os.environ['TELEGRAM_TOKEN']
CHAT_ID = os.environ['TELEGRAM_CHAT_ID']

# Búsquedas
QUERY_TWITTER = "Chacarita"  # Busca la palabra exacta en Twitter
QUERY_GOOGLE = "Chacarita"   # Busca en Google News

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

# --- ESTRATEGIA 1: NTSCRAPER (El que busca tweets de verdad) ---
def buscar_twitter_real(vistos):
    print("--- 1. Probando Nitter Automático (ntscraper) ---")
    try:
        # Iniciamos el scraper para que busque un servidor potable
        scraper = Nitter(log_level=1, skip_instance_check=False)
        
        # Buscamos los últimos tweets
        print(f"🔎 Buscando '{QUERY_TWITTER}' en Twitter...")
        resultados = scraper.get_tweets(QUERY_TWITTER, mode='term', number=15)
        
        tweets = resultados.get('tweets', [])
        
        if not tweets:
            print("⚠️ No se encontraron tweets (o bloquearon la instancia).")
            return

        # Recorremos del más viejo al más nuevo
        for tweet in reversed(tweets):
            link = tweet['link']
            tid = extraer_id(link)
            
            if tid not in vistos:
                usuario = tweet['user']['username']
                texto = tweet['text']
                fecha = tweet['date']
                
                print(f"✅ Nuevo Tweet: {usuario}")
                msg = f"🐦 *TWEET CHACA*\n\n👤 *{usuario}*: {texto}\n\n📅 {fecha}\n🔗 {link}"
                enviar_telegram(msg)
                guardar_historial(tid)
                vistos.add(tid)
                time.sleep(1) # Respeto para Telegram

    except Exception as e:
        print(f"❌ Error en ntscraper: {e}")

# --- ESTRATEGIA 2: GOOGLE NEWS (El respaldo) ---
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
    # Ejecutamos las dos estrategias
    buscar_twitter_real(vistos)
    buscar_google(vistos)

if __name__ == "__main__":
    main()
