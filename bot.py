import telebot
from telebot import types
import os, json, threading
from datetime import date, datetime, timedelta

TOKEN = os.getenv("TOKEN")
bot = telebot.TeleBot(TOKEN)

DATA_FILE = "data.json"

# ---------------- DATA ----------------

def load_data():
    if not os.path.exists(DATA_FILE):
        return {}
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_data():
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

data = load_data()

def user(cid):
    cid = str(cid)
    if cid not in data:
        data[cid] = {
            "state": None,
            "notes": [],
            "tasks": [],
            "moods": {},
            "focus": {"sessions": 0, "minutes": 0}
        }
    return data[cid]

# ---------------- UI ----------------

def main_menu():
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add("📅 План", "🍅 Фокус")
    kb.add("📝 Заметки", "😊 Настроение")
    kb.add("📊 Статистика")
    return kb

def back_menu():
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add("⬅️ Назад")
    return kb

# ---------------- START ----------------

@bot.message_handler(commands=["start"])
def start(message):
    user(message.chat.id)
    save_data()
    bot.send_message(
        message.chat.id,
        "Focusory — управление фокусом и задачами.",
        reply_markup=main_menu()
    )

# ---------------- BACK ----------------

@bot.message_handler(func=lambda m: m.text == "⬅️ Назад")
def back(message):
    user(message.chat.id)["state"] = None
    save_data()
    bot.send_message(message.chat.id, "Главное меню", reply_markup=main_menu())

# ---------------- MOOD ----------------

@bot.message_handler(func=lambda m: m.text == "😊 Настроение")
def mood_menu(message):
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add("😄", "🙂", "😐", "🙁", "😣")
    kb.add("⬅️ Назад")
    bot.send_message(message.chat.id, "Выбери настроение:", reply_markup=kb)

@bot.message_handler(func=lambda m: m.text in ["😄","🙂","😐","🙁","😣"])
def save_mood(message):
    cid = str(message.chat.id)
    today = date.today().isoformat()
    user(cid)["moods"][today] = message.text
    save_data()
    bot.send_message(message.chat.id, "Настроение сохранено.", reply_markup=main_menu())

# ---------------- NOTES ----------------

@bot.message_handler(func=lambda m: m.text == "📝 Заметки")
def notes_menu(message):
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add("➕ Добавить", "📂 По категории")
    kb.add("⬅️ Назад")
    bot.send_message(message.chat.id, "Заметки:", reply_markup=kb)

@bot.message_handler(func=lambda m: m.text == "➕ Добавить")
def note_add(message):
    cid = str(message.chat.id)
    user(cid)["state"] = "note_category"
    save_data()
    bot.send_message(message.chat.id, "Категория заметки:")

@bot.message_handler(func=lambda m: user(m.chat.id)["state"] == "note_category")
def note_cat(message):
    u = user(message.chat.id)
    u["tmp_cat"] = message.text
    u["state"] = "note_title"
    save_data()
    bot.send_message(message.chat.id, "Название заметки:")

@bot.message_handler(func=lambda m: user(m.chat.id)["state"] == "note_title")
def note_title(message):
    u = user(message.chat.id)
    u["tmp_title"] = message.text
    u["state"] = "note_text"
    save_data()
    bot.send_message(message.chat.id, "Текст заметки:")

@bot.message_handler(func=lambda m: user(m.chat.id)["state"] == "note_text")
def note_text(message):
    u = user(message.chat.id)
    u["notes"].append({
        "category": u["tmp_cat"],
        "title": u["tmp_title"],
        "text": message.text,
        "created": datetime.now().isoformat()
    })
    u["state"] = None
    save_data()
    bot.send_message(message.chat.id, "Заметка сохранена.", reply_markup=main_menu())

@bot.message_handler(func=lambda m: m.text == "📂 По категории")
def notes_by_cat(message):
    cats = sorted(set(n["category"] for n in user(message.chat.id)["notes"]))
    if not cats:
        bot.send_message(message.chat.id, "Нет заметок.", reply_markup=main_menu())
        return
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    for c in cats:
        kb.add(c)
    kb.add("⬅️ Назад")
    user(message.chat.id)["state"] = "notes_view"
    save_data()
    bot.send_message(message.chat.id, "Выбери категорию:", reply_markup=kb)

@bot.message_handler(func=lambda m: user(m.chat.id)["state"] == "notes_view")
def notes_list(message):
    u = user(message.chat.id)
    notes = [n for n in u["notes"] if n["category"] == message.text]
    text = "Заметки:\n\n" + "\n".join(f"• {n['title']}" for n in notes)
    u["state"] = None
    save_data()
    bot.send_message(message.chat.id, text, reply_markup=main_menu())

# ---------------- POMODORO ----------------

timers = {}

@bot.message_handler(func=lambda m: m.text == "🍅 Фокус")
def focus_menu(message):
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add("25", "50")
    kb.add("⬅️ Назад")
    bot.send_message(message.chat.id, "Минуты фокуса:", reply_markup=kb)

@bot.message_handler(func=lambda m: m.text in ["25","50"])
def start_focus(message):
    cid = str(message.chat.id)
    minutes = int(message.text)
    bot.send_message(message.chat.id, f"Фокус начался — {minutes} минут.", reply_markup=back_menu())
    timer = threading.Timer(minutes*60, finish_focus, args=[cid, minutes])
    timers[cid] = timer
    timer.start()

def finish_focus(cid, minutes):
    u = user(cid)
    u["focus"]["sessions"] += 1
    u["focus"]["minutes"] += minutes
    save_data()
    bot.send_message(int(cid), "Фокус завершён.", reply_markup=main_menu())

# ---------------- STATS ----------------

@bot.message_handler(func=lambda m: m.text == "📊 Статистика")
def stats(message):
    u = user(message.chat.id)
    mood_stats = {}
    for m in u["moods"].values():
        mood_stats[m] = mood_stats.get(m, 0) + 1

    text = (
        f"📊 Статистика\n\n"
        f"🍅 Фокус-сессий: {u['focus']['sessions']}\n"
        f"⏱ Минут фокуса: {u['focus']['minutes']}\n\n"
        "😊 Настроение:\n"
    )
    for k,v in mood_stats.items():
        text += f"{k} — {v}\n"

    bot.send_message(message.chat.id, text, reply_markup=main_menu())

# ---------------- RUN ----------------

print("Bot is running")
bot.infinity_polling()
