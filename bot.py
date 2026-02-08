import telebot 
from telebot.types import ReplyKeyboardMarkup 
import random 
import json 
import os 
import threading 
from datetime import date, datetime

TOKEN = os.getenv("TOKEN")
bot = telebot.TeleBot(TOKEN)
DATA_FILE = "data.json"


user_language = {} 
daily_affirmation_index = {} 
last_affirmation_date = {} 
user_moods = {} 
pomodoro_timers = {} 
pomodoro_stats = {}


def load_data(): 
    global user_language, daily_affirmation_index, last_affirmation_date, user_moods, pomodoro_stats 
    if not os.path.exists(DATA_FILE): 
        return 
    with open(DATA_FILE, "r", encoding="utf-8") as f: 
            data = json.load(f) 
    user_language = data.get("user_language", {}) 
    daily_affirmation_index = data.get("daily_affirmation_index", {}) 
    last_affirmation_date = data.get("last_affirmation_date", {}) 
    user_moods = data.get("user_moods", {}) 
    pomodoro_stats = data.get("pomodoro_stats", {})

def save_data():
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump({
            "user_language": user_language, 
            "daily_affirmation_index": daily_affirmation_index, 
            "last_affirmation_date": last_affirmation_date, 
            "user_moods": user_moods, 
            "pomodoro_stats": pomodoro_stats 
        }, f, ensure_ascii=False, indent=2)

load_data()


texts = {
    "ru": { "choose_lang": "👋 Выбери язык:", 
           "welcome": "🤍 Я помогу тебе планировать день, фокусироваться и заботиться о себе.", 
           "already_affirmed": "🌿 Ты уже получил(а) сегодняшнюю аффирмацию.", 
           "mood_saved": "💛 Настроение сохранено.", "no_mood": "Пока нет данных о настроении." 
          },
    "en": {
        "choose_lang": "👋 Please choose your language:",
        "welcome": "🤍 I help you plan, focus, and take care of yourself.",
        "already_affirmed": "🌿 You already received today’s affirmation.",
        "mood_saved": "💛 Mood saved.", "no_mood": "No mood data yet." 
    } 
}

affirmations = {
    "ru": [
        "✨ Сегодня я выбираю спокойствие и ясность.", 
        "🌱 Я двигаюсь вперёд в своём темпе.", 
        "💛 Мне можно быть неидеальным(ой).", 
        "🌸 Маленькие шаги тоже важны.", 
        "☀️ Этот день может быть добрым ко мне." 
    ], 
    "en": [
        "✨ Today I choose calm and clarity.",
        "🌱 I move forward at my own pace.",
        "💛 It’s okay to be imperfect.",
        "🌸 Small steps still matter.",
        "☀️ This day can be kind to me." 
    ] 
}


def language_keyboard():
    kb = ReplyKeyboardMarkup(resize_keyboard=True) 
    kb.add("🇷🇺 Русский", "🇬🇧 English") 
    return kb

def main_keyboard():
    kb = ReplyKeyboardMarkup(resize_keyboard=True) 
    kb.add("🌅 Morning", "📅 Plan") 
    kb.add("💭 Mood", "🍅 Pomodoro") 
    kb.add("📊 Stats") 
    return kb

def pomodoro_keyboard():
    kb = ReplyKeyboardMarkup(resize_keyboard=True) 
    kb.add("🍅 15 min", "🍅 25 min", "🍅 50 min") 
    kb.add("🛑 Stop") 
    return kb


def get_lang(chat_id):
    return user_language.get(str(chat_id), "en")

def today_str():
    return date.today().isoformat()


@bot.message_handler(commands=['start']) 
def start(message):
    bot.send_message( message.chat.id, texts["en"]["choose_lang"], 
                     reply_markup=language_keyboard() )

@bot.message_handler(func=lambda m: m.text in ["🇷🇺 Русский", "🇬🇧 English"]) 
def set_language(message):
    cid = str(message.chat.id)

    if "Русский" in message.text:
        lang = "ru"
    else:
        lang = "en"

    user_language[cid] = lang
    save_data()

bot.send_message(
    elseat.id,
    texts[lang]["welcome"],
    reply_markup=main_keyboard()
)


@bot.message_handler(commands=['morning'])
def morning(message):
    chat_id = str(message.chat.id) 
    lang = get_lang(chat_id) 
    today = today_str()
    if last_affirmation_date.get(chat_id) == today:
    bot.send_message(message.chat.id, texts[lang]["already_affirmed"])
        return

idx = daily_affirmation_index.get(chat_id, 0)
phrase = affirmations[lang][idx % len(affirmations[lang])]

daily_affirmation_index[chat_id] = idx + 1
last_affirmation_date[chat_id] = today
save_data()

bot.send_message(message.chat.id, "🌅 " + phrase)


@bot.message_handler(commands=['mood'])
def mood(message):
    bot.send_message( message.chat.id, "😊 🙂 😐 😔 😣" )

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


@bot.message_handler(commands=['stats']) 
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

if lang == "en": 
    text = "📊 Mood stats:\n"
else: 
    text = "📊 Статистика настроения:\n"
for k, v in summary.items():
    text += f"{k} — {v}\n"

today_pomo = pomodoro_stats.get(chat_id, {}).get(today_str(), 0)
text += f"\n🍅 Pomodoro today: {today_pomo}"

bot.send_message(message.chat.id, text)


@bot.message_handler(commands=['pomodoro']) 
def pomodoro_menu(message):
    bot.send_message( message.chat.id, "🍅 Choose focus time:", reply_markup=pomodoro_keyboard() )

def start_pomodoro(chat_id, minutes): lang = get_lang(chat_id)

if lang == "en":
    text = f"🍅 Focus started — {minutes} minutes."
else:
    text = f"🍅 Фокус начался — {minutes} минут."

bot.send_message(
    int(chat_id),
    text
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

if lang == "en":
    text = "✅ Pomodoro done! Take a short break 🌿"
else:
    text = "✅ Фокус завершен! Сделай перерыв 🌿"

bot.send_message(
    int(chat_id),
    text
)

pomodoro_timers.pop(chat_id, None)

@bot.message_handler(func=lambda m: m.text in ["🍅 15 min", "🍅 25 min", "🍅 50 min"]) 
def handle_pomodoro_choice(message):
    chat_id = str(message.chat.id)

if chat_id in pomodoro_timers:
    return

minutes = int(message.text.split()[1])
start_pomodoro(chat_id, minutes)

@bot.message_handler(func=lambda m: m.text == "🛑 Stop") 
def stop_pomodoro(message):
    chat_id = str(message.chat.id) 
    timer = pomodoro_timers.pop(chat_id, None) 
    if timer: timer.cancel()

if get_lang(chat_id) == "en":
    text = "🛑 Pomodoro stopped."
else:
    text = "🛑 Pomodoro остановлен."

bot.send_message(
    message.chat.id,
    text
)

print("Bot is running...") 
bot.infinity_polling()
