import os, requests
from flask import Flask, request

app = Flask(__name__)

BOT_TOKEN = os.environ.get("BOT_TOKEN", "")          # зададим на Render
WEBHOOK_SECRET = os.environ.get("WEBHOOK_SECRET", "devsecret")  # секрет пути вебхука

TG_API = f"https://api.telegram.org/bot{BOT_TOKEN}"

@app.get("/")
def index():
    return "ok"

@app.post(f"/webhook/{WEBHOOK_SECRET}")
def tg_webhook():
    update = request.get_json(silent=True) or {}
    msg = update.get("message") or update.get("edited_message")
    if not msg:
        return "ok"
    chat_id = msg["chat"]["id"]
    text = msg.get("text") or ""
    # простой ответ-эхо
    requests.post(f"{TG_API}/sendMessage", json={"chat_id": chat_id, "text": f"Ты написала: {text}"})
    return "ok"

@app.get("/set_webhook")
def set_webhook():
    """Временный хелпер: дернем после деплоя. Пример:
       https://ТВОЙ-URL-на-Render/set_webhook?url=https://ТВОЙ-URL-на-Render
    """
    url = request.args.get("url")
    if not (url and BOT_TOKEN):
        return "need ?url=https://your-host"
    r = requests.get(f"{TG_API}/setWebhook",
                     params={"url": f"{url}/webhook/{WEBHOOK_SECRET}"})
    return r.json()

