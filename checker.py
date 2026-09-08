#!/usr/bin/env python3
"""
MarketWatch checker.
Legge data/searches.json, controlla Vinted e Subito per nuove inserzioni,
manda notifica Telegram per ogni annuncio nuovo, aggiorna data/seen.json.
"""

import json
import os
import sys
import time
import requests

DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
SEARCHES_FILE = os.path.join(DATA_DIR, "searches.json")
SEEN_FILE = os.path.join(DATA_DIR, "seen.json")

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")

HEADERS_BROWSER = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/124.0 Safari/537.36",
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "it-IT,it;q=0.9",
}


def load_json(path, default):
    if not os.path.exists(path):
        return default
    with open(path, "r", encoding="utf-8") as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            return default


def save_json(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def send_telegram(text, url=None):
    if not TELEGRAM_TOKEN or not TELEGRAM_CHAT_ID:
        print("Telegram non configurato, salto invio:", text)
        return
    api = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": text,
        "disable_web_page_preview": False,
    }
    try:
        r = requests.post(api, data=payload, timeout=15)
        if r.status_code != 200:
            print("Errore invio Telegram:", r.status_code, r.text)
    except Exception as e:
        print("Eccezione invio Telegram:", e)


# ---------------- VINTED ----------------

def vinted_search(keyword, max_price=None):
    """
    Usa la tecnica 'session pre-warm': prima visita la homepage per ottenere
    i cookie di sessione (bypassa parzialmente la protezione anti-bot),
    poi interroga l'API catalogo pubblica.
    """
    session = requests.Session()
    session.headers.update(HEADERS_BROWSER)

    try:
        session.get("https://www.vinted.it/", timeout=15)
    except Exception as e:
        print("Errore pre-warm Vinted:", e)
        return []

    params = {
        "search_text": keyword,
        "order": "newest_first",
        "per_page": 20,
    }
    if max_price:
        params["price_to"] = max_price

    try:
        r = session.get(
            "https://www.vinted.it/api/v2/catalog/items",
            params=params,
            timeout=15,
        )
        if r.status_code != 200:
            print(f"Vinted risposta {r.status_code} per '{keyword}': {r.text[:200]}")
            return []
        data = r.json()
    except Exception as e:
        print("Errore richiesta Vinted:", e)
        return []

    results = []
    for item in data.get("items", []):
        results.append({
            "id": f"vinted-{item.get('id')}",
            "title": item.get("title"),
            "price": (item.get("price") or {}).get("amount"),
            "url": item.get("url"),
        })
    return results


# ---------------- SUBITO ----------------

def subito_search(keyword, max_price=None, city=None):
    """
    Tenta l'API interna usata dal sito (hades.subito.it).
    NB: Subito blocca spesso gli IP dei server cloud: se questa funzione
    smette di restituire risultati, è previsto — usa gli avvisi nativi
    di Subito come alternativa.
    """
    params = {
        "q": keyword,
        "shp": "false",
        "t": "s",
    }
    if max_price:
        params["ps"] = max_price
    if city:
        params["c"] = city

    try:
        r = requests.get(
            "https://hades.subito.it/v1/search/items",
            params=params,
            headers=HEADERS_BROWSER,
            timeout=15,
        )
        if r.status_code != 200:
            print(f"Subito risposta {r.status_code} per '{keyword}': {r.text[:200]}")
            return []
        data = r.json()
    except Exception as e:
        print("Errore richiesta Subito (probabile blocco anti-bot):", e)
        return []

    results = []
    for item in data.get("ads", []):
        results.append({
            "id": f"subito-{item.get('urn', item.get('item_id', item.get('id')))}",
            "title": item.get("subject"),
            "price": (item.get("features", {}).get("/price", {}) or {}).get("values", [{}])[0].get("key"),
            "url": item.get("urls", {}).get("default"),
        })
    return results


# ---------------- MAIN ----------------

def main():
    searches = load_json(SEARCHES_FILE, [])
    seen = load_json(SEEN_FILE, {})

    if not searches:
        print("Nessuna ricerca configurata.")
        return

    new_notifications = 0

    for s in searches:
        keyword = s["keyword"]
        platform = s["platform"]
        max_price = s.get("maxPrice")
        city = s.get("city")
        search_key = s.get("id", keyword)

        print(f"Controllo: [{platform}] '{keyword}'...")

        if platform == "vinted":
            items = vinted_search(keyword, max_price)
        elif platform == "subito":
            items = subito_search(keyword, max_price, city)
        else:
            continue

        seen_ids = set(seen.get(search_key, []))
        fresh_ids = list(seen_ids)

        for item in items:
            if item["id"] in seen_ids:
                continue
            price_txt = f" - €{item['price']}" if item.get("price") else ""
            msg = f"🔔 Nuovo annuncio ({platform})\n{item['title']}{price_txt}\n{item['url']}"
            send_telegram(msg)
            new_notifications += 1
            fresh_ids.append(item["id"])
            time.sleep(1)  # non spammare l'API Telegram

        # tieni solo gli ultimi 300 id visti per ricerca, per non far crescere il file all'infinito
        seen[search_key] = fresh_ids[-300:]

    save_json(SEEN_FILE, seen)
    print(f"Fatto. Notifiche inviate: {new_notifications}")


if __name__ == "__main__":
    main()
