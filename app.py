import os, requests
from flask import Flask, request
from openai import OpenAI

app = Flask(__name__)

BOT_TOKEN = os.environ.get("BOT_TOKEN", "")
WEBHOOK_SECRET = os.environ.get("WEBHOOK_SECRET", "devsecret")
TG_API = f"https://api.telegram.org/bot{BOT_TOKEN}"

# --- клавиатура и кнопки ---
BUTTONS = {
    "📊 Исследование": "research",
    "✍️ Контент": "content",
    "🎨 Дизайн": "design",
    "📈 Маркетинг": "marketing",
    "📁 Менеджмент": "management",
    "❓ Другие вопросы": "misc",
}

def build_keyboard(cols=2):
    keys = list(BUTTONS.keys())
    rows = [[{"text": t} for t in keys[i:i+cols]] for i in range(0, len(keys), cols)]
    return {"keyboard": rows, "resize_keyboard": True}

MAIN_KB = build_keyboard()

# --- состояние чатов (какой режим выбран) ---
CHAT_STATE = {}

# --- OpenAI клиент (если ключ не задан, будет None) ---
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "")
oai = OpenAI(api_key=OPENAI_API_KEY) if OPENAI_API_KEY else None

def ai_generate(mode_title: str, task: str) -> str:
    """
    Возвращает осмысленный ответ.
    Если ключ OpenAI не задан — отдаём шаблон.
    """
    if not oai:
        templates = {
            "✍️ Контент": f"Черновик поста по теме «{task}»:\n— Зацепка (1–2 фразы)\n— 3 тезиса/факта\n— Призыв к действию.",
            "🎨 Дизайн": f"Бриф по задаче «{task}»:\nЦель, стиль (минимализм/неон), референсы (3 ссылки), форматы (обложка/логотип/сторис).",
            "📈 Маркетинг": f"Мини-план по «{task}»:\nЦА, оффер, каналы (IG/TG/Reels), бюджет, KPI на 2 недели.",
            "📊 Исследование": f"Скелет ресёрча «{task}»:\nГипотезы, 5 источников, 10 вопросов, критерии выводов.",
            "📁 Менеджмент": f"Чек-лист:\n— Результат: {task}\n— Дедлайн, ответственный\n— Критерии готовности\n— Риски/план B.",
            "❓ Другие вопросы": f"Короткий ответ по «{task}»:\nСформулируй, какой результат нужен — предложу шаги.",
        }
        return templates.get(mode_title, f"Черновик по запросу: {task}")

    system = f"Ты помощник. Отвечай кратко и по делу, на русском. Режим: {mode_title}."
    prompt = f"Задача: {task}\nСделай полезный структурированный ответ (списком/короткими абзацами)."
    try:
        resp = oai.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": prompt},
            ],
            temperature=0.7,
            max_tokens=500,
        )
        return resp.choices[0].message.content.strip()
    except Exception as e:
        return f"Не удалось сгенерировать текст ({e}). Черновик по «{task}»."

# --- помощник отправки сообщений ---
def send_message(chat_id, text):
    requests.post(f"{TG_API}/sendMessage",
                  json={"chat_id": chat_id, "text": text, "reply_markup": MAIN_KB})

# --- маршруты ---
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

    # Команда старт
    if text.lower() in ("/start", "start"):
        CHAT_STATE[chat_id] = None
        send_message(chat_id, "Привет! Выбери режим на клавиатуре ниже 👇")
        return "ok"

    # Нажатие на кнопку (точное совпадение с названием)
    if text in BUTTONS:
        CHAT_STATE[chat_id] = text  # сохраняем титул кнопки (для красивого ответа)
        send_message(chat_id, f"Режим установлен: {BUTTONS[text]}. Опиши коротко задачу.")
        return "ok"

    # Пришёл текст после выбора режима — генерируем ответ
    if chat_id in CHAT_STATE and CHAT_STATE[chat_id]:
        mode_title = CHAT_STATE[chat_id]
        result = ai_generate(mode_title, text)
        send_message(chat_id, result)
        return "ok"

    # Фоллбэк
    send_message(chat_id, "Не поняла. Нажми кнопку режима ниже или напиши /start.")
    return "ok"

# Временный хелпер: можно дернуть для установки вебхука
@app.get("/set_webhook")
def set_webhook():
    url = request.args.get("url")
    if not (url and BOT_TOKEN):
        return "need ?url=https://your-host"
    r = requests.get(f"{TG_API}/setWebhook",
                     params={"url": f"{url}/webhook/{WEBHOOK_SECRET}"})
    return r.json()

