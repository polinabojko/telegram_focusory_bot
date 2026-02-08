import telebot
from telebot.types import ReplyKeyboardMarkup
import json
import os
import threading
from datetime import date

# ================== CONFIG ==================
TOKEN = os.getenv("TOKEN") or "PASTE_YOUR_TOKEN_HERE"
bot = telebot.TeleBot(TOKEN)

DATA_FILE = "data.json"

# ================== DATA ==================
user_language = {}
last_affirmation_date = {}
affirmation_index = {}
user_moods = {}
pomodoro_stats = {}
pomodoro_timers = {}

# ================== LOAD / SAVE ==================
def load_data():
    global user_language, last_affirmation_date, affirmation_index, user_moods, pomodoro_stats
    if not os.path.exists(DATA_FILE):
        return
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)
    user_language = data.get("user_language", {})
    last_affirmation_date = data.get("last_affirmation_date", {})
    affirmation_index = data.get("affirmation_index", {})
    user_moods = data.get("user_moods", {})
    pomodoro_stats = data.get("pomodoro_stats", {})

def save_data():
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump({
            "user_language": user_language,
            "last_affirmation_date": last_affirmation_date,
            "affirmation_index": affirmation_index,
            "user_moods": user_moods,
            "pomodoro_stats": pomodoro_stats
        }, f, ensure_ascii=False, indent=2)

load_data()

# ================== HELPERS ==================
def today():
    return date.today().isoformat()

def get_lang(chat_id):
    return user_language.get(str(chat_id), "en")

# ================== TEXTS ==================
texts = {
    "ru": {
        "choose_lang": "👋 Выбери язык",
        "welcome": "🤍 Я помогу тебе планировать день, заботиться о себе и сохранять фокус.",
        "already_affirmed": "🌿 Ты уже получил(а) аффирмацию сегодня.",
        "mood_saved": "💛 Я сохранила твоё настроение.",
        "no_mood": "Пока нет данных о настроении.",
        "choose_pomo": "🍅 Выбери время фокуса:",
        "pomo_done": "✅ Фокус завершён! Сделай паузу 🌿",
        "pomo_stop": "🛑 Pomodoro остановлен."
    },
    "en": {
        "choose_lang": "👋 Choose your language",
        "welcome": "🤍 I help you plan, focus and take care of yourself.",
        "already_affirmed": "🌿 You already got today’s affirmation.",
        "mood_saved": "💛 Mood saved.",
        "no_mood": "No mood data yet.",
        "choose_pomo": "🍅 Choose focus time:",
        "pomo_done": "✅ Pomodoro done! Take a short break 🌿",
        "pomo_stop": "🛑 Pomodoro stopped."
    }
}

# ================== AFFIRMATIONS (30+) ==================
affirmations = {
    "ru": [
        "✨ Сегодня я выбираю спокойствие.",
        "🌱 Я двигаюсь в своём темпе.",
        "💛 Мне можно быть неидеальной.",
        "🌸 Маленькие шаги важны.",
        "☀️ Я заслуживаю доброго дня.",
        "🌿 Я дышу глубоко и спокойно.",
        "💫 Я справляюсь.",
        "🤍 Я забочусь о себе.",
        "🌈 У меня достаточно сил.",
        "🕊 Я выбираю мягкость.",
        "🔥 Я могу начать заново.",
        "🌙 Я в безопасности.",
        "💪 Я сильнее, чем думаю.",
        "🍃 Я отпускаю лишнее.",
        "🌼 Я делаю лучшее, что могу.",
        "🌊 Я позволяю себе отдых.",
        "🌻 Я ценю себя.",
        "🧘 Я здесь и сейчас.",
        "🌟 Я достойна хорошего.",
        "🫶 Я не одна.",
        "🌸 Я доверяю процессу.",
        "✨ Я позволяю себе радость.",
        "🌿 Я принимаю себя.",
        "💛 Мне можно ошибаться.",
        "☀️ Я выбираю свет.",
        "🌈 Всё приходит вовремя.",
        "🕊 Я в гармонии.",
        "🔥 Я двигаюсь вперёд.",
        "🌱 Я расту.",
        "🤍 Я достаточно."
    ],
    "en": [
        "✨ Today I choose calm.",
        "🌱 I move at my own pace.",
        "💛 It’s okay to be imperfect.",
        "🌸 Small steps matter.",
        "☀️ I deserve a good day.",
        "🌿 I breathe deeply.",
        "💫 I can handle this.",
        "🤍 I take care of myself.",
        "🌈 I have enough strength.",
        "🕊 I choose gentleness.",
        "🔥 I can start again.",
        "🌙 I am safe.",
        "💪 I am stronger than I think.",
        "🍃 I let go.",
        "🌼 I do my best.",
        "🌊 I allow myself to rest.",
        "🌻 I value myself.",
        "🧘 I am present.",
        "🌟 I deserve good things.",
        "🫶 I am not alone.",
        "🌸 I trust the process.",
        "✨ I allow joy.",
        "🌿 I accept myself.",
        "💛 Mistakes are allowed.",
        "☀️ I choose light.",
        "🌈 Things come in time.",
        "🕊 I am in balance.",
        "🔥 I move forward.",
        "🌱 I grow.",
        "🤍 I am enough."
    ]
}

# ================== KEYBOARDS ==================
def language_keyboard():
    kb = ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add("🇷🇺 Русский", "🇬🇧 English")
    return kb

def main_keyboard(lang):
    kb = ReplyKeyboardMarkup(resize_keyboard=True)
    if lang == "ru":
        kb.add("🌅 Утро", "💭 Настроение")
        kb.add("🍅 Фокус", "📊 Статистика")
    else:
        kb.add("🌅 Morning", "💭 Mood")
        kb.add("🍅 Pomodoro", "📊 Stats")
    return kb

def pomodoro_keyboard():
    kb = ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add("🍅 15", "🍅 25", "🍅 50")
    kb.add("🛑 Stop")
    return kb

# ================== HANDLERS ==================
@bot.message_handler(commands=["start"])
def start(message):
    bot.send_message(message.chat.id, texts["en"]["choose_lang"], reply_markup=language_keyboard())

@bot.message_handler(func=lambda m: m.text in ["🇷🇺 Русский", "🇬🇧 English"])
def set_language(message):
    chat_id = str(message.chat.id)
    lang = "ru" if "Русский" in message.text else "en"
    user_language[chat_id] = lang
    save_data()

    bot.send_message(
        message.chat.id,
        texts[lang]["welcome"],
        reply_markup=main_keyboard(lang)
    )

# ================== MORNING ==================
@bot.message_handler(func=lambda m: m.text in ["🌅 Утро", "🌅 Morning"])
def morning(message):
    chat_id = str(message.chat.id)
    lang = get_lang(chat_id)
    if last_affirmation_date.get(chat_id) == today():
        bot.send_message(message.chat.id, texts[lang]["already_affirmed"])
        return

    idx = affirmation_index.get(chat_id, 0)
    phrase = affirmations[lang][idx % len(affirmations[lang])]

    affirmation_index[chat_id] = idx + 1
    last_affirmation_date[chat_id] = today()
    save_data()

    bot.send_message(message.chat.id, "🌅 " + phrase)

# ================== MOOD ==================
@bot.message_handler(func=lambda m: m.text in ["💭 Настроение", "💭 Mood"])
def mood(message):
    bot.send_message(message.chat.id, "😊 🙂 😐 😔 😣")

@bot.message_handler(func=lambda m: m.text in ["😊", "🙂", "😐", "😔", "😣"])
def save_mood(message):
    chat_id = str(message.chat.id)
    user_moods.setdefault(chat_id, {})[today()] = message.text
    save_data()
    bot.send_message(message.chat.id, texts[get_lang(chat_id)]["mood_saved"])

# ================== STATS ==================
@bot.message_handler(func=lambda m: m.text in ["📊 Статистика", "📊 Stats"])
def stats(message):
    chat_id = str(message.chat.id)
    lang = get_lang(chat_id)
    moods = user_moods.get(chat_id, {})

    if not moods:
        bot.send_message(message.chat.id, texts[lang]["no_mood"])
        return

    summary = {}
    for m in moods.values():
        summary[m] = summary.get(m, 0) + 1

    text = "📊\n"
    for k, v in summary.items():
        text += f"{k} — {v}\n"

    bot.send_message(message.chat.id, text)

# ================== POMODORO ==================
def pomodoro_done(chat_id):
    lang = get_lang(chat_id)
    pomodoro_stats.setdefault(chat_id, {})
    pomodoro_stats[chat_id][today()] = pomodoro_stats[chat_id].get(today(), 0) + 1
    save_data()

    bot.send_message(int(chat_id), texts[lang]["pomo_done"])
    pomodoro_timers.pop(chat_id, None)

@bot.message_handler(func=lambda m: m.text in ["🍅 Фокус", "🍅 Pomodoro"])
def pomodoro_menu(message):
    bot.send_message(message.chat.id, texts[get_lang(message.chat.id)]["choose_pomo"], reply_markup=pomodoro_keyboard())

@bot.message_handler(func=lambda m: m.text.startswith("🍅 "))
def start_pomodoro(message):
    chat_id = str(message.chat.id)
    minutes = int(message.text.split()[1])

    if chat_id in pomodoro_timers:
        return

    timer = threading.Timer(minutes * 60, pomodoro_done, args=[chat_id])
    pomodoro_timers[chat_id] = timer
    timer.start()

@bot.message_handler(func=lambda m: m.text == "🛑 Stop")
def stop_pomodoro(message):
    chat_id = str(message.chat.id)
    timer = pomodoro_timers.pop(chat_id, None)
    if timer:
        timer.cancel()
    bot.send_message(message.chat.id, texts[get_lang(chat_id)]["pomo_stop"])

# ================== RUN ==================
print("Bot is running...")
bot.infinity_polling()
