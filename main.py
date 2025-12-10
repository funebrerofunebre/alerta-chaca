import os
import time
import requests
import feedparser
import re
from bs4 import BeautifulSoup

# --- CONFIGURACIÓN ---
TOKEN = os.environ['TELEGRAM_TOKEN']
CHAT_ID = os.environ['TELEGRAM_CHAT_ID']
QUERY_TWITTER = "Chacarita"
QUERY_GOOGLE = "Chacarita"

# Headers para "disfrazarnos" de navegador real
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

def extraer_id(url):
    match = re.search(r'/status/(\d+)', url)
    return match.group(1) if match else url

# --- ESTRATEGIA 1: BING SEARCH (Disfrazado) ---
def buscar_bing(vistos):
    print("--- 1. Probando Bing Search (Modo Camaleón) ---")
    try:
        # Buscamos en Bing: site:twitter.com Chacarita
        # &filters=ex1%3a%22ez1%22 fuerza resultados de las últimas 24hs
        url = f"https://www.bing.com/search?q=site%3Atwitter.com+{QUERY_TWITTER}&filters=ex1%3a%22ez1%22"
        
        response = requests.get(url, headers=HEADERS, timeout=10)
        
        if response.status_code != 200:
            print(f"⚠️ Bing nos rechazó con código: {response.status_code}")
            return

        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Buscamos todos los links de la página
        links = soup.find_all('a', href=True)
        encontrados = 0
        
        for link in links:
            href = link['href']
            # Filtramos solo los que son tweets reales
            if "twitter.com" in href and "/status/" in href:
                tid = extraer_id(href)
                
                if tid not in vistos:
                    titulo = link.get_text()[:100] # Primeros 100 caracteres del titulo
                    print(f"✅ Tweet en Bing: {href}")
                    msg = f"🔍 *TWEET (Vía Bing)*\n\n📝 {titulo}...\n\n🔗 {href}"
                    enviar_telegram(msg)
                    guardar_historial(tid)
                    vistos.add(tid)
                    encontrados += 1
                    time.sleep(2)
        
        if encontrados == 0:
            print("   ↳ Bing conectó, pero no vio tweets nuevos.")

    except Exception as e:
        print(f"❌ Error en Bing: {e}")

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
    buscar_bing(vistos)
    buscar_google(vistos)

if __name__ == "__main__":
    main()
