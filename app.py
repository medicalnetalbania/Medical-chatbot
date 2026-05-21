import os
from flask import Flask, request, jsonify
import anthropic
import requests

app = Flask(__name__)

URUN_KATALOGU = """
ÜRÜN LİSTESİ VE FİYATLARI:
- Latex Eldiven (Pudrasız): 100'lük paket, 700 Lek. Renkler: Beyaz, Mavi. Beden: S, M, L, XL
- Nitrile Eldiven: 100'lük paket. Pembe: 890 Lek, Siyah: 840 Lek, Mavi: 740 Lek. Beden: S, M, L, XL
- Cerrahi Maske (3 Katlı): 50'lik kutu, 640 Lek. Renkler: Beyaz, Mavi, Pembe, Siyah
- Galoş: 500'lük paket 1400 Lek, 1000'lik paket 2400 Lek. Renk: Mavi
- Muayene Örtüsü: 50 metrelik rulo, 1400 Lek. Renkler: Beyaz, Pembe, Mavi
- Bone: 250'lik paket, 1500 Lek. Renkler: Beyaz, Mavi

SET ÖNERİLERİ:
- Pembe Set: Pembe Nitrile Eldiven + Pembe Maske + Pembe Muayene Örtüsü
- Mavi Set: Mavi Nitrile Eldiven + Mavi Maske + Galoş + Mavi Bone
- Temel Set: Latex Eldiven + Beyaz Maske + Galoş
"""

SISTEM_PROMPTU = """Sen Medicalnet Albania'nın Instagram DM satış asistanısın.
Görevin müşteri sorularını yanıtlamak ve ek ürün önererek satışı artırmak.

""" + URUN_KATALOGU + """

KURALLARIN:
1. Her zaman Arnavutça yanıt ver
2. Samimi ve yardımsever ol
3. Müşteri bir ürün sorduğunda mutlaka ilgili ek ürün öner
4. Sipariş almak istediğinde: isim, telefon ve adres iste
5. Sipariş tamamlanınca özet ver
6.Fiyat sorulursa ürün kataloğundaki fiyatı direkt söyle
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
        yanit = claude_yanit_al(mesaj, konusmalar[gonderici_id])
        konusmalar[gonderici_id].append({"role": "user", "content": mesaj})
        konusmalar[gonderici_id].append({"role": "assistant", "content": yanit})
        instagram_mesaj_gonder(gonderici_id, yanit)
    except Exception as e:
        print(f"Hata: {e}")
    return jsonify({"status": "ok"})
