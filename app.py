import os
from flask import Flask, request, jsonify
import anthropic
import requests

app = Flask(__name__)

URUN_KATALOGU = """
ÜRÜN LİSTESİ:
- Latex Eldiven (Pudrasız): Paket başına 100 adet. Renkler: Beyaz, Mavi. Beden: S, M, L, XL
- Nitrile Eldiven: Paket başına 100 adet. Renkler: Mavi, Siyah, Pembe. Beden: S, M, L, XL
- Cerrahi Maske (3 Katlı): Kutu başına 50 adet. Renkler: Beyaz, Mavi, Pembe, Siyah
- Galoş: Paket başına 100 adet. Renk: Mavi
- Muayene Örtüsü: Rulo başına 50 metre. Renkler: Beyaz, Pembe, Mavi
- Bone: Paket başına 100 adet. Renk: Beyaz, Mavi

SET ÖNERİLERİ:
- Pembe Set: Pembe eldiven + Pembe maske + Pembe muayene örtüsü
- Mavi Set: Mavi eldiven + Mavi maske + Mavi galoş + Mavi bone
- Temel Set: Beyaz eldiven + Beyaz maske + Galoş
"""

SISTEM_PROMPTU = """Sen Medikal Almanya'nın Instagram DM satış asistanısın.
Görevin müşteri sorularını yanıtlamak ve ek ürün önererek satışı artırmak.

""" + URUN_KATALOGU + """

KURALLARIN:
1. Her zaman Türkçe yanıt ver
2. Samimi ve yardımsever ol
3. Müşteri bir ürün sorduğunda mutlaka ilgili ek ürün öner
4. Sipariş almak istediğinde: isim, telefon ve adres iste
5. Sipariş tamamlanınca özet ver
6. Fiyat sorulursa "size özel fiyat için DM'den devam edelim" de
7. Kısa ve net yanıtlar ver
"""

konusmalar = {}

def claude_yanit_al(musteri_mesaji, konusma_gecmisi):
    client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))
    mesajlar = konusma_gecmisi + [{"role": "user", "content": musteri_mesaji}]
    response = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=500,
        system=SISTEM_PROMPTU,
        messages=mesajlar
    )
    return response.content[0].text

def instagram_mesaj_gonder(alici_id, mesaj):
    url = "https://graph.facebook.com/v18.0/me/messages"
    params = {"access_token": os.environ.get("INSTAGRAM_TOKEN")}
    data = {
        "recipient": {"id": alici_id},
        "message": {"text": mesaj}
    }
    requests.post(url, params=params, json=data)

@app.route("/webhook", methods=["GET"])
def webhook_dogrula():
    verify_token = os.environ.get("VERIFY_TOKEN", "medicalnetalbania2025")
    token = request.args.get("hub.verify_token")
    challenge = request.args.get("hub.challenge")
    mode = request.args.get("hub.mode")
    if mode == "subscribe" and token == verify_token:
        return challenge, 200
    return "Forbidden", 403

@app.route("/webhook", methods=["POST"])
def webhook_al():
    data = request.json
    try:
        entry = data["entry"][0]
        messaging = entry["messaging"][0]
        gonderici_id = messaging["sender"]["id"]
        mesaj = messaging["message"]["text"]
        if gonderici_id not in konusmalar:
            konusmalar[gonderici_id] = []
        yanit = claude_yanit_al(mesaj, konusmalar[gonderici
