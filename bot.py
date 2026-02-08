import telebot
from telebot.types import ReplyKeyboardMarkup
import json
import os
import threading
from datetime import date

TOKEN = os.getenv("TOKEN")
bot = telebot.TeleBot(TOKEN)

DATA_FILE = "data.json"

# ---------- DATA ----------
user_language = {}
user_moods = {}
pomodoro_stats = {}
pomodoro_timers = {}

# ---------- LOAD / SAVE ----------
def load_data():
    global user_language, user_moods, pomodoro_stats
    if not os.path.exists(DATA_FILE):
        return
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)
    user_language = data.get("user_language", {})
    user_moods = data.get("user_moods", {})
    pomodoro_stats = data.get("pomodoro_stats", {})

def save_data():
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump({
            "user_language": user_language,
            "user_moods": user_moods,
            "pomodoro_stats": pomodoro_stats
        }, f, ensure_ascii=False, indent=2)

load_data()

# ---------- TEXTS ----------
texts = {
    "ru": {
        "choose_lang": "👋 Выбери язык:",
        "welcome": "🤍 Я помогу тебе фокусироваться и заботиться о себе.",
        "mood_saved": "💛 Настроение сохранено.",
        "no_mood": "Пока нет данных о настроении.",
        "pomo_start": "🍅 Фокус начался — {m} минут.",
        "pomo_done": "✅ Фокус завершён! Сделай перерыв 🌿",
        "pomo_stop": "🛑 Помодоро остановлен."
    },
    "en": {
        "choose_lang": "👋 Please choose your language:",
        "welcome": "🤍 I help you focus and take care of yourself.",
        "mood_saved": "💛 Mood saved.",
        "no_mood": "No mood data yet.",
        "pomo_start": "🍅 Focus started — {m} minutes.",
        "pomo_done": "✅ Pomodoro done! Take a break 🌿",
        "pomo_stop": "🛑 Pomodoro stopped."
    }
}

# ---------- HELPERS ----------
def get_lang(chat_id):
    return user_language.get(str(chat_id), "en")

def today_str():
    return date.today().isoformat()

# ---------- KEYBOARDS ----------
def language_keyboard():
    kb = ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add("🇷🇺 Русский", "🇬🇧 English")
    return kb

def main_keyboard(lang):
    kb = ReplyKeyboardMarkup(resize_keyboard=True)
    if lang == "ru":
        kb.add("🌅 Утро", "💭 Настроение")
        kb.add("🍅 Помодоро", "📊 Статистика")
    else:
        kb.add("🌅 Morning", "💭 Mood")
        kb.add("🍅 Pomodoro", "📊 Stats")
    return kb

def pomodoro_keyboard(lang):
    kb = ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add("🍅 15", "🍅 25", "🍅 50")
    kb.add("🛑 Stop")
    return kb

# ---------- START ----------
@bot.message_handler(commands=["start"])
def start(message):
    bot.send_message(
        message.chat.id,
        texts["en"]["choose_lang"],
        reply_markup=language_keyboard()
    )

# ---------- LANGUAGE ----------
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

# ---------- MORNING ----------
@bot.message_handler(func=lambda m: m.text in ["🌅 Morning", "🌅 Утро"])
def morning(message):
    bot.send_message(message.chat.id, "☀️ Хорошего дня!" if get_lang(message.chat.id) == "ru" else "☀️ Have a good day!")

# ---------- MOOD ----------
@bot.message_handler(func=lambda m: m.text in ["💭 Mood", "💭 Настроение"])
def mood(message):
    bot.send_message(message.chat.id, "😊 🙂 😐 😔 😣")

@bot.message_handler(func=lambda m: m.text in ["😊", "🙂", "😐", "😔", "😣"])
def save_mood(message):
    chat_id = str(message.chat.id)
    today = today_str()
    user_moods.setdefault(chat_id, {})[today] = message.text
    save_data()

    bot.send_message(
        message.chat.id,
        texts[get_lang(chat_id)]["mood_saved"]
    )

# ---------- STATS ----------
@bot.message_handler(func=lambda m: m.text in ["📊 Stats", "📊 Статистика"])
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

    text = "📊 Статистика:\n" if lang == "ru" else "📊 Stats:\n"
    for k, v in summary.items():
        text += f"{k} — {v}\n"

    pomo = pomodoro_stats.get(chat_id, {}).get(today_str(), 0)
    text += f"\n🍅 Pomodoro today: {pomo}"

    bot.send_message(message.chat.id, text)

# ---------- POMODORO ----------
@bot.message_handler(func=lambda m: m.text in ["🍅 Pomodoro", "🍅 Помодоро"])
def pomodoro_menu(message):
    lang = get_lang(message.chat.id)
    bot.send_message(
        message.chat.id,
        "🍅 Choose time:" if lang == "en" else "🍅 Выбери время:",
        reply_markup=pomodoro_keyboard(lang)
    )

@bot.message_handler(func=lambda m: m.text in ["🍅 15", "🍅 25", "🍅 50"])
def start_pomodoro(message):
    chat_id = str(message.chat.id)
    if chat_id in pomodoro_timers:
        return

    minutes = int(message.text.split()[1])
    lang = get_lang(chat_id)

    bot.send_message(
        message.chat.id,
        texts[lang]["pomo_start"].format(m=minutes)
    )

    timer = threading.Timer(minutes * 60, pomodoro_finished, args=[chat_id])
    pomodoro_timers[chat_id] = timer
    timer.start()

def pomodoro_finished(chat_id):
    lang = get_lang(chat_id)
    today = today_str()

    pomodoro_stats.setdefault(chat_id, {})
    pomodoro_stats[chat_id][today] = pomodoro_stats[chat_id].get(today, 0) + 1
    save_data()

    bot.send_message(
        int(chat_id),
        texts[lang]["pomo_done"]
    )

    pomodoro_timers.pop(chat_id, None)

@bot.message_handler(func=lambda m: m.text == "🛑 Stop")
def stop_pomodoro(message):
    chat_id = str(message.chat.id)
    timer = pomodoro_timers.pop(chat_id, None)
    if timer:
        timer.cancel()

    bot.send_message(
        message.chat.id,
        texts[get_lang(chat_id)]["pomo_stop"]
    )

# ---------- RUN ----------
print("Bot is running...")
bot.infinity_polling()
