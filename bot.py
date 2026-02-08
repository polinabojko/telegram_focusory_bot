import telebot
from telebot.types import ReplyKeyboardMarkup
import json
import os
import threading
from datetime import date, datetime, timedelta

# ------------------ ТОКЕН ------------------
os.getenv("TOKEN")
bot = telebot.TeleBot(TOKEN)
DATA_FILE = "data.json"

# ------------------ ДАННЫЕ ------------------
user_language = {}
daily_affirmation_index = {}
last_affirmation_date = {}
user_moods = {}
pomodoro_sessions = {}  # chat_id: {"timer": threading.Timer, "minutes": int, "on_break": bool}
pomodoro_stats = {}
tasks = {}

# ------------------ ЗАГРУЗКА/СОХРАНЕНИЕ ------------------
def load_data():
    global user_language, daily_affirmation_index, last_affirmation_date, user_moods, pomodoro_stats, tasks
    if not os.path.exists(DATA_FILE):
        return
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)
    user_language = data.get("user_language", {})
    daily_affirmation_index = data.get("daily_affirmation_index", {})
    last_affirmation_date = data.get("last_affirmation_date", {})
    user_moods = data.get("user_moods", {})
    pomodoro_stats = data.get("pomodoro_stats", {})
    tasks = data.get("tasks", {})

def save_data():
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump({
            "user_language": user_language,
            "daily_affirmation_index": daily_affirmation_index,
            "last_affirmation_date": last_affirmation_date,
            "user_moods": user_moods,
            "pomodoro_stats": pomodoro_stats,
            "tasks": tasks
        }, f, ensure_ascii=False, indent=2)

load_data()

# ------------------ ТЕКСТЫ ------------------
texts = {
    "ru": {
        "choose_lang": "👋 Выберите язык:",
        "welcome": "🤍 Я помогу вам планировать день, сосредотачиваться и заботиться о себе.",
        "already_affirmed": "🌿 Вы уже получили сегодняшнюю аффирмацию.",
        "mood_saved": "💛 Настроение сохранено.",
        "no_mood": "Пока нет данных о настроении.",
        "mood_prompt": "☁️ Как вы себя чувствуете сегодня?",
        "focus_start": "⏳ Фокус начался — {minutes} минут",
        "focus_done": "✅ Фокус завершён!",
        "focus_stop": "⛔ Фокус остановлен",
        "break_start": "🌿 Перерыв — {minutes} минут",
        "new_or_menu": "Выберите действие:",
        "new_focus": "🔁 Начать новый фокус",
        "exit": "🚪 Выйти из Pomodoro",
        "skip_break": "⏭️ Пропустить перерыв",
        "task_added": "📝 Задача добавлена!",
        "choose_task_view": "📅 Выберите период для просмотра задач:",
        "task_done": "✅ Задача отмечена как выполненная.",
        "no_tasks": "Пока нет задач."
    },
    "en": {
        "choose_lang": "👋 Please choose your language:",
        "welcome": "🤍 I help you plan, focus, and take care of yourself.",
        "already_affirmed": "🌿 You already received today’s affirmation.",
        "mood_saved": "💛 Mood saved.",
        "no_mood": "No mood data yet.",
        "mood_prompt": "☁️ How are you feeling today?",
        "focus_start": "⏳ Focus started — {minutes} minutes",
        "focus_done": "✅ Focus complete!",
        "focus_stop": "⛔ Focus stopped",
        "break_start": "🌿 Break — {minutes} minutes",
        "new_or_menu": "Choose an action:",
        "new_focus": "🔁 New focus",
        "exit": "🚪 Exit Pomodoro",
        "skip_break": "⏭️ Skip break",
        "task_added": "📝 Task added!",
        "choose_task_view": "📅 Choose period to view tasks:",
        "task_done": "✅ Task marked done.",
        "no_tasks": "No tasks yet."
    }
}

# ------------------ АФФИРМАЦИИ ------------------
affirmations = {
    "ru": [
        "Позвольте себе двигаться в собственном ритме.", "Каждый шаг имеет значение.",
        "Сегодня можно уделить время только себе.", "Маленький прогресс — тоже прогресс.",
        "Ваш день может быть спокойным и продуктивным.", "Вы заслуживаете отдыха.",
        "Примите свои эмоции такими, какие они есть.", "Фокус на одном деле эффективнее.",
        "Вы делаете больше, чем думаете.", "Делайте шаг за шагом.",
        "Вы способны справиться с этим.", "Сегодня вы сильнее, чем вчера.",
        "Вы можете изменить свой день.", "Ничто не идеально — и это нормально.",
        "Слушайте себя и свои потребности.", "Сделайте паузу, когда нужно.",
        "Вы умеете концентрироваться.", "Маленькая победа — это тоже победа.",
        "Вы достойны заботы о себе.", "Сегодня вы можете всё, что запланировали.",
        "Ваш темп уникален.", "Сохраняйте спокойствие и ясность.",
        "Вы управляете своим временем.", "Прогресс важнее идеала.",
        "Ваши усилия имеют значение.", "Сосредоточьтесь на настоящем.",
        "Вы выбираете свой путь.", "Не спешите, делайте обдуманно.",
        "Каждое действие важно.", "Сегодня вы заботитесь о себе."
    ],
    "en": [
        "Allow yourself to move at your own pace.", "Every step matters.",
        "Take time today just for yourself.", "Small progress is still progress.",
        "Your day can be calm and productive.", "You deserve rest.",
        "Accept your emotions as they are.", "Focus on one task is more effective.",
        "You are accomplishing more than you think.", "Take it step by step.",
        "You can handle this.", "Today you are stronger than yesterday.",
        "You can change your day.", "Nothing is perfect — and that’s okay.",
        "Listen to yourself and your needs.", "Take a pause when needed.",
        "You are capable of concentration.", "Small wins are still wins.",
        "You deserve self-care.", "Today you can do everything planned.",
        "Your pace is unique.", "Maintain calm and clarity.",
        "You control your time.", "Progress matters more than perfection.",
        "Your efforts matter.", "Focus on the present.", "You choose your path.",
        "Take your time, act thoughtfully.", "Every action matters.",
        "Today you take care of yourself."
    ]
}

# ------------------ КНОПКИ ------------------
def language_keyboard():
    kb = ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add("🇷🇺 Русский", "🇬🇧 English")
    return kb

def main_keyboard(lang):
    kb = ReplyKeyboardMarkup(resize_keyboard=True)
    if lang == "ru":
        kb.add("🌸 Аффирмация дня", "🍵 Фокус")
        kb.add("☁️ Настроение", "✨ Инсайты")
        kb.add("📝 Планирование")
    else:
        kb.add("🌸 Daily affirmation", "🍵 Focus")
        kb.add("☁️ Mood", "✨ Insights")
        kb.add("📝 Planning")
    return kb

def mood_keyboard(lang):
    kb = ReplyKeyboardMarkup(resize_keyboard=True)
    if lang == "ru":
        kb.add("😄 Отлично", "🙂 Хорошо", "😐 Нормально", "🙁 Плохо", "😣 Очень плохо")
    else:
        kb.add("😄 Excellent", "🙂 Good", "😐 Neutral", "🙁 Bad", "😣 Very bad")
    return kb

def pomodoro_keyboard(lang):
    kb = ReplyKeyboardMarkup(resize_keyboard=True)
    if lang == "ru":
        kb.add("🍵 15 мин", "🍵 25 мин", "🍵 50 мин")
        kb.add("⛔ Завершить")
    else:
        kb.add("🍵 15 min", "🍵 25 min", "🍵 50 min")
        kb.add("⛔ Stop")
    return kb

def get_lang(chat_id):
    return user_language.get(str(chat_id), "en")

def today_str():
    return date.today().isoformat()

# ------------------ ОБРАБОТЧИК /start ------------------
@bot.message_handler(commands=['start'])
def start(message):
    bot.send_message(message.chat.id, texts["en"]["choose_lang"], reply_markup=language_keyboard())

@bot.message_handler(func=lambda m: m.text in ["🇷🇺 Русский", "🇬🇧 English"])
def set_language(message):
    cid = str(message.chat.id)
    lang = "ru" if "Русский" in message.text else "en"
    user_language[cid] = lang
    save_data()
    bot.send_message(message.chat.id, texts[lang]["welcome"], reply_markup=main_keyboard(lang))

# ------------------ ЗАПУСК ------------------
print("Bot is running...")
bot.infinity_polling(timeout=60, long_polling_timeout=60)
