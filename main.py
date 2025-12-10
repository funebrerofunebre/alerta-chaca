import os
import time
import requests
import feedparser
import re
from bs4 import BeautifulSoup

# --- CONFIGURACIÓN ---
TOKEN = os.environ['TELEGRAM_TOKEN']
CHAT_ID = os.environ['TELEGRAM_CHAT_ID']

# Búsqueda amplia (No solo Twitter)
QUERY_GENERAL = "Chacarita" 

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
}

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

# --- 1. BING WEB (Búsqueda General) ---
def buscar_bing(vistos):
    print("--- 1. Probando Bing Web ---")
    try:
        # Buscamos noticias recientes en la web general
        # q=Chacarita + filtro de ultimas 24hs
        url = f"https://www.bing.com/search?q={QUERY_GENERAL}&filters=ex1%3a%22ez1%22"
        
        response = requests.get(url, headers=HEADERS, timeout=10)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Buscamos resultados de búsqueda (clase 'b_algo' es comun en Bing)
        resultados = soup.find_all('li', class_='b_algo')
        
        if not resultados:
            print("   ↳ Bing conectó pero no trajo resultados frescos.")
        
        for res in resultados:
            link_tag = res.find('a', href=True)
            if link_tag:
                link = link_tag['href']
                titulo = link_tag.get_text()
                
                if link not in vistos:
                    print(f"✅ Novedad Bing: {titulo}")
                    msg = f"🔍 *WEB (Bing)*\n\n📝 {titulo}\n\n🔗 {link}"
                    enviar_telegram(msg)
                    guardar_historial(link)
                    vistos.add(link)
                    time.sleep(2)

    except Exception as e:
        print(f"❌ Error en Bing: {e}")

# --- 2. GOOGLE NEWS (El Tanque) ---
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
    buscar_bing(vistos)
    buscar_google(vistos)

if __name__ == "__main__":
    main()
