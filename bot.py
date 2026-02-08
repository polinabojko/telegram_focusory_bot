import telebot
from telebot.types import ReplyKeyboardMarkup
import json
import os
import threading
from datetime import date

TOKEN = os.getenv("TOKEN") or "PASTE_TOKEN_HERE"
bot = telebot.TeleBot(TOKEN)

DATA_FILE = "data.json"

# ===== DATA =====
user_language = {}
last_affirmation_date = {}
affirmation_index = {}
user_moods = {}
pomodoro_stats = {}
pomodoro_timers = {}

# ===== LOAD / SAVE =====
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

def today():
    return date.today().isoformat()

def get_lang(chat_id):
    return user_language.get(str(chat_id), "en")

# ===== TEXTS =====
texts = {
    "ru": {
        "choose_lang": "👋 Выбери язык",
        "welcome": "🤍 Я помогу тебе фокусироваться, замечать своё состояние и быть к себе бережнее.",
        "affirmed": "🌿 Ты уже получил(а) аффирмацию сегодня.",
        "mood_ask": "Какое у тебя сегодня настроение?",
        "mood_saved": "💛 Спасибо, я сохранила твоё состояние.",
        "no_mood": "Пока нет данных о настроении.",
        "choose_focus": "🍅 Выбери время фокуса:",
        "focus_started": "🍅 Фокус начался на {m} минут.",
        "focus_done": "✅ Фокус завершён. Сделай паузу 🌿",
        "focus_stop": "⏸ Фокус остановлен. Что дальше?",
        "end_focus": "🛑 Завершить",
        "resume_focus": "▶️ Продолжить"
    },
    "en": {
        "choose_lang": "👋 Choose your language",
        "welcome": "🤍 I help you focus, reflect on your state, and treat yourself with care.",
        "affirmed": "🌿 You already received today’s affirmation.",
        "mood_ask": "How are you feeling today?",
        "mood_saved": "💛 Thank you, I saved your mood.",
        "no_mood": "No mood data yet.",
        "choose_focus": "🍅 Choose focus time:",
        "focus_started": "🍅 Focus started for {m} minutes.",
        "focus_done": "✅ Focus finished. Take a short break 🌿",
        "focus_stop": "⏸ Focus paused. What would you like to do?",
        "end_focus": "🛑 End",
        "resume_focus": "▶️ Resume"
    }
}

# ===== AFFIRMATIONS (GENDER-NEUTRAL) =====
affirmations = {
    "ru": [
        "Ты не обязан быть продуктивным, чтобы быть ценным.",
        "Твоя ценность не измеряется результатами.",
        "Ты можешь двигаться медленно и всё равно идти вперёд.",
        "Даже маленькие шаги имеют значение.",
        "Ты имеешь право на паузу.",
        "Ты справляешься лучше, чем тебе кажется.",
        "Не всё нужно решать сегодня.",
        "Ты можешь выбирать мягкость.",
        "Ошибки — часть роста.",
        "Ты уже достаточно."
    ] * 3,
    "en": [
        "You don’t have to be productive to be worthy.",
        "Your value is not defined by results.",
        "You can move slowly and still move forward.",
        "Small steps still matter.",
        "You are allowed to rest.",
        "You’re handling more than you realize.",
        "Not everything needs to be solved today.",
        "You can choose gentleness.",
        "Mistakes are part of growth.",
        "You are already enough."
    ] * 3
}

# ===== KEYBOARDS =====
def language_keyboard():
    kb = ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add("🇷🇺 Русский", "🇬🇧 English")
    return kb

def main_keyboard(lang):
    kb = ReplyKeyboardMarkup(resize_keyboard=True)
    if lang == "ru":
        kb.add("🌅 Аффирмация дня", "💭 Настроение")
        kb.add("🍅 Фокус", "📊 Статистика")
    else:
        kb.add("🌅 Daily affirmation", "💭 Mood")
        kb.add("🍅 Pomodoro", "📊 Stats")
    return kb

def mood_keyboard():
    kb = ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add("😊 Хорошо", "🙂 Нормально", "😐 Спокойно")
    kb.add("😔 Тяжело", "😣 Очень тяжело")
    return kb

def pomodoro_keyboard(lang):
    kb = ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add("🍅 15", "🍅 25", "🍅 50")
    kb.add(texts[lang]["end_focus"])
    return kb

def pause_keyboard(lang):
    kb = ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add(texts[lang]["resume_focus"], texts[lang]["end_focus"])
    return kb

# ===== HANDLERS =====
@bot.message_handler(commands=["start"])
def start(message):
    bot.send_message(message.chat.id, texts["en"]["choose_lang"], reply_markup=language_keyboard())

@bot.message_handler(func=lambda m: m.text in ["🇷🇺 Русский", "🇬🇧 English"])
def set_lang(message):
    chat_id = str(message.chat.id)
    lang = "ru" if "Русский" in message.text else "en"
    user_language[chat_id] = lang
    save_data()
    bot.send_message(message.chat.id, texts[lang]["welcome"], reply_markup=main_keyboard(lang))

# ===== AFFIRMATION =====
@bot.message_handler(func=lambda m: m.text in ["🌅 Аффирмация дня", "🌅 Daily affirmation"])
def affirmation(message):
    cid = str(message.chat.id)
    lang = get_lang(cid)

    if last_affirmation_date.get(cid) == today():
        bot.send_message(message.chat.id, texts[lang]["affirmed"])
        return

    idx = affirmation_index.get(cid, 0)
    text = affirmations[lang][idx % len(affirmations[lang])]

    affirmation_index[cid] = idx + 1
    last_affirmation_date[cid] = today()
    save_data()

    bot.send_message(message.chat.id, "🌿 " + text)

# ===== MOOD =====
@bot.message_handler(func=lambda m: m.text in ["💭 Настроение", "💭 Mood"])
def mood(message):
    bot.send_message(
        message.chat.id,
        texts[get_lang(message.chat.id)]["mood_ask"],
        reply_markup=mood_keyboard()
    )

@bot.message_handler(func=lambda m: any(x in m.text for x in ["😊", "🙂", "😐", "😔", "😣"]))
def save_mood(message):
    cid = str(message.chat.id)
    user_moods.setdefault(cid, {})[today()] = message.text
    save_data()
    bot.send_message(message.chat.id, texts[get_lang(cid)]["mood_saved"], reply_markup=main_keyboard(get_lang(cid)))

# ===== POMODORO =====
def pomodoro_done(cid):
    lang = get_lang(cid)
    pomodoro_stats.setdefault(cid, {})
    pomodoro_stats[cid][today()] = pomodoro_stats[cid].get(today(), 0) + 1
    save_data()
    bot.send_message(int(cid), texts[lang]["focus_done"])
    pomodoro_timers.pop(cid, None)

@bot.message_handler(func=lambda m: m.text in ["🍅 Фокус", "🍅 Pomodoro"])
def pomodoro_menu(message):
    lang = get_lang(message.chat.id)
    bot.send_message(message.chat.id, texts[lang]["choose_focus"], reply_markup=pomodoro_keyboard(lang))

@bot.message_handler(func=lambda m: m.text.startswith("🍅 "))
def start_focus(message):
    cid = str(message.chat.id)
    lang = get_lang(cid)
    minutes = int(message.text.split()[1])

    timer = threading.Timer(minutes * 60, pomodoro_done, args=[cid])
    pomodoro_timers[cid] = timer
    timer.start()

    bot.send_message(message.chat.id, texts[lang]["focus_started"].format(m=minutes))

@bot.message_handler(func=lambda m: m.text in ["🛑 Завершить", "🛑 End"])
def stop_focus(message):
    cid = str(message.chat.id)
    lang = get_lang(cid)
    timer = pomodoro_timers.pop(cid, None)
    if timer:
        timer.cancel()
    bot.send_message(message.chat.id, texts[lang]["focus_stop"], reply_markup=pause_keyboard(lang))

# ===== RUN =====
print("Bot running")
bot.infinity_polling()
