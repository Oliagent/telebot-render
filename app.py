import os, requests
from flask import Flask, request

app = Flask(__name__)

BOT_TOKEN = os.environ.get("BOT_TOKEN", "")      # зададим на Render
WEBHOOK_SECRET = os.environ.get("WEBHOOK_SECRET", "devsecret")
TG_API = f"https://api.telegram.org/bot{BOT_TOKEN}"

# --- кнопки и их ответы ---
BUTTONS = {
    "📊 Исследование": "Режим установлен: research. Опиши коротко задачу.",
    "✍️ Контент": "Режим установлен: content. Опиши коротко задачу.",
    "🎨 Дизайн": "Режим установлен: design. Опиши коротко задачу.",
    "📈 Маркетинг": "Режим установлен: marketing. Опиши коротко задачу.",
    "📁 Менеджмент": "Режим установлен: management. Опиши коротко задачу.",
    "❓ Другие вопросы": "Режим установлен: misc. Опиши коротко задачу."
}

def build_keyboard(cols=2):
    keys = list(BUTTONS.keys())
    rows = [ [{"text":t} for t in keys[i:i+cols]] for i in range(0, len(keys), cols) ]
    return {"keyboard": rows, "resize_keyboard": True}

MAIN_KB = build_keyboard()

# --- helpers ---
def send_message(chat_id, text):
    requests.post(f"{TG_API}/sendMessage",
        json={"chat_id": chat_id, "text": text, "reply_markup": MAIN_KB})

# --- routes ---
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

    # команды
    if text.lower() in ("/start", "start"):
        send_message(chat_id, "Привет! Выбери режим на клавиатуре ниже 👇")
    elif text in BUTTONS:
        send_message(chat_id, BUTTONS[text])
    else:
        send_message(chat_id, f"Поняла. Ты написала: {text}")

    return "ok"

@app.get("/set_webhook")
def set_webhook():
    url = request.args.get("url")
    if not (url and BOT_TOKEN):
        return "need ?url=https://your-host"
    r = requests.get(f"{TG_API}/setWebhook",
        params={"url": f"{url}/webhook/{WEBHOOK_SECRET}"})
    return r.json()

