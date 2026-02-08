import telebot
from telebot.types import ReplyKeyboardMarkup
import json
import os
import threading
from datetime import date, datetime, timedelta

# ------------------ ТОКЕН ------------------
TOKEN = os.getenv("TOKEN")  # токен берется из переменной окружения
bot = telebot.TeleBot(TOKEN)
DATA_FILE = "data.json"

# ------------------ ДАННЫЕ ------------------
user_language = {}
daily_affirmation_index = {}
last_affirmation_date = {}
user_moods = {}
pomodoro_sessions = {}  # chat_id: {"timer": threading.Timer, "minutes": int, "on_break": bool}
pomodoro_stats = {}
tasks = {}  # chat_id: list of tasks {"text": str, "date": "YYYY-MM-DD", "done": bool}

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

def pomodoro_choice_keyboard(lang):
    kb = ReplyKeyboardMarkup(resize_keyboard=True)
    if lang == "ru":
        kb.add(texts[lang]["new_focus"], texts[lang]["exit"], texts[lang]["skip_break"])
    else:
        kb.add(texts[lang]["new_focus"], texts[lang]["exit"], texts[lang]["skip_break"])
    return kb

def get_lang(chat_id):
    return user_language.get(str(chat_id), "en")

def today_str():
    return date.today().isoformat()

# ------------------ ОБРАБОТЧИКИ ------------------
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

# ------------------ Аффирмация дня ------------------
@bot.message_handler(func=lambda m: m.text in ["🌸 Аффирмация дня", "🌸 Daily affirmation"])
def daily_affirmation(message):
    chat_id = str(message.chat.id)
    lang = get_lang(chat_id)
    today = today_str()
    if last_affirmation_date.get(chat_id) == today:
        bot.send_message(chat_id, texts[lang]["already_affirmed"])
        return
    idx = daily_affirmation_index.get(chat_id, 0)
    phrase = affirmations[lang][idx % len(affirmations[lang])]
    daily_affirmation_index[chat_id] = idx + 1
    last_affirmation_date[chat_id] = today
    save_data()
    bot.send_message(chat_id, "🌸 " + phrase)

# ------------------ Настроение ------------------
@bot.message_handler(func=lambda m: m.text in ["☁️ Настроение", "☁️ Mood"])
def mood_prompt(message):
    chat_id = str(message.chat.id)
    lang = get_lang(chat_id)
    bot.send_message(chat_id, texts[lang]["mood_prompt"], reply_markup=mood_keyboard(lang))

@bot.message_handler(func=lambda m: m.text in ["😄 Отлично", "🙂 Хорошо", "😐 Нормально", "🙁 Плохо", "😣 Очень плохо",
                                               "😄 Excellent", "🙂 Good", "😐 Neutral", "🙁 Bad", "😣 Very bad"])
def save_mood(message):
    chat_id = str(message.chat.id)
    today = today_str()
    user_moods.setdefault(chat_id, {})[today] = message.text
    save_data()
    lang = get_lang(chat_id)
    bot.send_message(chat_id, texts[lang]["mood_saved"])

# ------------------ Pomodoro ------------------
def start_pomodoro(chat_id, minutes):
    lang = get_lang(chat_id)
    bot.send_message(chat_id, texts[lang]["focus_start"].format(minutes=minutes), reply_markup=pomodoro_keyboard(lang))
    timer = threading.Timer(minutes * 60, pomodoro_end, args=[chat_id])
    pomodoro_sessions[chat_id] = {"timer": timer, "minutes": minutes, "on_break": False}
    timer.start()

def pomodoro_end(chat_id):
    lang = get_lang(chat_id)
    session = pomodoro_sessions.get(chat_id)
    if not session:
        return
    today = today_str()
    pomodoro_stats.setdefault(chat_id, {})
    pomodoro_stats[chat_id][today] = pomodoro_stats[chat_id].get(today, 0) + 1
    save_data()

    if session["on_break"]:
        bot.send_message(chat_id, texts[lang]["break_start"].format(minutes=5) + "\n" + texts[lang]["new_or_menu"], reply_markup=pomodoro_choice_keyboard(lang))
        session["on_break"] = False
    else:
        bot.send_message(chat_id, texts[lang]["focus_done"], reply_markup=pomodoro_choice_keyboard(lang))
        session["on_break"] = True
        timer = threading.Timer(5*60, pomodoro_end, args=[chat_id])
        pomodoro_sessions[chat_id]["timer"] = timer
        timer.start()

@bot.message_handler(func=lambda m: m.text in ["🍵 15 мин","🍵 25 мин","🍵 50 мин","🍵 15 min","🍵 25 min","🍵 50 min"])
def handle_pomodoro_time(message):
    chat_id = str(message.chat.id)
    minutes = int(message.text.split()[1])
    start_pomodoro(chat_id, minutes)

@bot.message_handler(func=lambda m: m.text in ["🔁 Начать новый фокус","🚪 Выйти из Pomodoro","⏭️ Пропустить перерыв",
                                               "🔁 New focus","🚪 Exit Pomodoro","⏭️ Skip break"])
def handle_pomodoro_choice(message):
    chat_id = str(message.chat.id)
    lang = get_lang(chat_id)
    text = message.text

    if text in [texts[lang]["exit"]]:
        session = pomodoro_sessions.pop(chat_id, None)
        if session and session["timer"]:
            session["timer"].cancel()
        bot.send_message(chat_id, texts[lang]["focus_stop"], reply_markup=main_keyboard(lang))
    elif text in [texts[lang]["skip_break"]]:
        session = pomodoro_sessions.get(chat_id)
        if session and session["timer"]:
            session["timer"].cancel()
        bot.send_message(chat_id, texts[lang]["focus_done"], reply_markup=pomodoro_choice_keyboard(lang))
    elif text in [texts[lang]["new_focus"]]:
        bot.send_message(chat_id, "🍵 Выберите время фокуса:" if lang=="ru" else "🍵 Choose focus time:", reply_markup=pomodoro_keyboard(lang))
# ------------------ Планирование ------------------
def planning_keyboard(lang):
    kb = ReplyKeyboardMarkup(resize_keyboard=True)
    if lang == "ru":
        kb.add("➕ Добавить задачу", "📅 Показать задачи")
        kb.add("🔙 Главное меню")
    else:
        kb.add("➕ Add task", "📅 Show tasks")
        kb.add("🔙 Main menu")
    return kb

@bot.message_handler(func=lambda m: m.text in ["📝 Планирование", "📝 Planning"])
def planning_menu(message):
    chat_id = str(message.chat.id)
    lang = get_lang(chat_id)
    bot.send_message(chat_id, texts[lang]["choose_task_view"], reply_markup=planning_keyboard(lang))

# Добавление задачи
@bot.message_handler(func=lambda m: m.text in ["➕ Добавить задачу", "➕ Add task"])
def add_task_prompt(message):
    chat_id = str(message.chat.id)
    lang = get_lang(chat_id)
    msg = bot.send_message(chat_id, "Введите задачу в формате: Текст задачи | YYYY-MM-DD" if lang=="ru" else "Enter task as: Task text | YYYY-MM-DD")
    bot.register_next_step_handler(msg, save_task)

def save_task(message):
    chat_id = str(message.chat.id)
    lang = get_lang(chat_id)
    try:
        text, date_str = map(str.strip, message.text.split("|"))
        datetime.strptime(date_str, "%Y-%m-%d")  # проверка формата
        tasks.setdefault(chat_id, []).append({"text": text, "date": date_str, "done": False})
        save_data()
        bot.send_message(chat_id, texts[lang]["task_added"], reply_markup=planning_keyboard(lang))
    except:
        bot.send_message(chat_id, "Неверный формат. Используйте: Текст задачи | YYYY-MM-DD" if lang=="ru" else "Invalid format. Use: Task text | YYYY-MM-DD")
        planning_menu(message)

# Просмотр задач
@bot.message_handler(func=lambda m: m.text in ["📅 Показать задачи", "📅 Show tasks"])
def show_tasks_menu(message):
    chat_id = str(message.chat.id)
    lang = get_lang(chat_id)
    kb = ReplyKeyboardMarkup(resize_keyboard=True)
    if lang=="ru":
        kb.add("Сегодня", "Эта неделя", "Этот месяц", "🔙 Главное меню")
    else:
        kb.add("Today", "This week", "This month", "🔙 Main menu")
    bot.send_message(chat_id, "Выберите период для просмотра:" if lang=="ru" else "Choose period to view:", reply_markup=kb)

# Отображение задач по выбранному периоду
@bot.message_handler(func=lambda m: m.text in ["Сегодня","Эта неделя","Этот месяц","Today","This week","This month"])
def display_tasks(message):
    chat_id = str(message.chat.id)
    lang = get_lang(chat_id)
    period = message.text
    today = date.today()
    selected_tasks = []

    for t in tasks.get(chat_id, []):
        task_date = datetime.strptime(t["date"], "%Y-%m-%d").date()
        if period in ["Сегодня","Today"] and task_date == today:
            selected_tasks.append(t)
        elif period in ["Эта неделя","This week"]:
            start_week = today - timedelta(days=today.weekday())
            end_week = start_week + timedelta(days=6)
            if start_week <= task_date <= end_week:
                selected_tasks.append(t)
        elif period in ["Этот месяц","This month"]:
            if task_date.year == today.year and task_date.month == today.month:
                selected_tasks.append(t)

    if not selected_tasks:
        bot.send_message(chat_id, texts[lang]["no_tasks"], reply_markup=planning_keyboard(lang))
        return

    for idx, t in enumerate(selected_tasks, start=1):
        status = "✅" if t["done"] else "❌"
        bot.send_message(chat_id, f"{idx}. {status} {t['text']} ({t['date']})")
    
    msg = bot.send_message(chat_id, "Введите номер задачи, чтобы отметить её выполненной, или 🔙 для меню:" if lang=="ru" else "Enter task number to mark done or 🔙 to menu:")
    bot.register_next_step_handler(msg, mark_task_done, selected_tasks)

def mark_task_done(message, task_list):
    chat_id = str(message.chat.id)
    lang = get_lang(chat_id)
    if message.text == "🔙" or message.text == "🔙 Main menu":
        planning_menu(message)
        return
    try:
        idx = int(message.text) - 1
        task_list[idx]["done"] = True
        # Сохраняем изменения
        for t in tasks[chat_id]:
            if t["text"] == task_list[idx]["text"] and t["date"] == task_list[idx]["date"]:
                t["done"] = True
        save_data()
        bot.send_message(chat_id, texts[lang]["task_done"], reply_markup=planning_keyboard(lang))
    except:
        bot.send_message(chat_id, "Неверный номер задачи." if lang=="ru" else "Invalid task number.")
        planning_menu(message)

# ------------------ ЗАПУСК ------------------
print("Bot is running...")
bot.infinity_polling(timeout=60, long_polling_timeout=60)
