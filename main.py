import feedparser
import requests
import os
import time

# CONFIGURACION
TOKEN = os.environ['TELEGRAM_TOKEN']
CHAT_ID = os.environ['TELEGRAM_CHAT_ID']
# Busqueda: Chacarita + palabras clave - retweets (Codificado para URL)
QUERY = "Chacarita%20(refuerzo%20OR%20firma%20OR%20incorpora%20OR%20interesa)%20-filter%3Aretweets"

# Lista de espejos de Nitter (si uno falla, prueba el otro)
NITTER_INSTANCES = [
    "https://nitter.net",
    "https://nitter.cz",
    "https://nitter.privacydev.net",
    "https://nitter.projectsegfau.lt"
]

def enviar_telegram(texto):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    requests.post(url, data={"chat_id": CHAT_ID, "text": texto, "parse_mode": "Markdown"})

def leer_ultimo_id():
    if os.path.exists("last_id.txt"):
        with open("last_id.txt", "r") as f:
            return f.read().strip()
    return None

def guardar_ultimo_id(id_tweet):
    with open("last_id.txt", "w") as f:
        f.write(id_tweet)

def main():
    ultimo_visto = leer_ultimo_id()
    print(f"👀 Último tweet visto: {ultimo_visto}")

    feed = None
    # Intentamos con cada servidor hasta que uno ande
    for instance in NITTER_INSTANCES:
        try:
            url_feed = f"{instance}/search/rss?f=tweets&q={QUERY}"
            print(f"Intentando conectar con {instance}...")
            feed = feedparser.parse(url_feed)
            if feed.entries:
                break # Si encontramos tweets, salimos del bucle
        except:
            continue
    
    if not feed or not feed.entries:
        print("⚠️ No se pudo conectar a ningún servidor o no hay tweets.")
        return

    # Recorremos los tweets del más viejo al más nuevo
    nuevos_tweets = []
    for entry in reversed(feed.entries):
        # El ID en RSS suele ser la URL
        tweet_id = entry.link
        
        # Si es un tweet nuevo (y no es el mismo que el último guardado)
        if tweet_id != ultimo_visto:
            # Chequeo simple para no mandar 20 tweets la primera vez
            if ultimo_visto is not None: 
                msg = f"🔴 *NOVEDAD CHACA*\n\n{entry.title}\n\n🔗 {entry.link}"
                enviar_telegram(msg)
                time.sleep(1) # Espera 1 seg para no saturar
            
            # Actualizamos el último visto al actual
            ultimo_visto = tweet_id
            guardar_ultimo_id(tweet_id)

if __name__ == "__main__":
    main()
