import telebot
from telebot import types
import os
import json
import threading
from datetime import datetime, date, timedelta

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
        json.dump(DB, f, ensure_ascii=False, indent=2)

DB = load_data()

def user(cid):
    if cid not in DB:
        DB[cid] = {
            "state": None,
            "notes": [],
            "tasks": [],
            "moods": {},
            "focus": {"sessions": 0, "minutes": 0}
        }
    return DB[cid]

# ---------------- UI ----------------

def main_menu():
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add("📅 План", "🍅 Фокус")
    kb.add("📝 Заметки", "😊 Настроение")
    kb.add("📊 Статистика")
    return kb

# ---------------- START ----------------

@bot.message_handler(commands=["start"])
def start(message):
    bot.send_message(
        message.chat.id,
        "Focusory — управление фокусом и задачами.",
        reply_markup=main_menu()
    )

# =========================
# 😊 MOOD
# =========================

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

# =========================
# 📝 NOTES (CATEGORIES)
# =========================

@bot.message_handler(func=lambda m: m.text == "📝 Заметки")
def notes_menu(message):
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add("➕ Добавить", "📂 Категории")
    kb.add("⬅️ Назад")
    bot.send_message(message.chat.id, "Заметки:", reply_markup=kb)

@bot.message_handler(func=lambda m: m.text == "➕ Добавить")
def add_note_start(message):
    cid = str(message.chat.id)
    user(cid)["state"] = "note_category"
    save_data()
    bot.send_message(message.chat.id, "Введите категорию заметки:")

@bot.message_handler(func=lambda m: user(str(m.chat.id))["state"] == "note_category")
def note_category(message):
    cid = str(message.chat.id)
    user(cid)["tmp_cat"] = message.text
    user(cid)["state"] = "note_text"
    save_data()
    bot.send_message(message.chat.id, "Введите текст заметки:")

@bot.message_handler(func=lambda m: user(str(m.chat.id))["state"] == "note_text")
def note_text(message):
    cid = str(message.chat.id)
    user(cid)["notes"].append({
        "category": user(cid)["tmp_cat"],
        "title": message.text[:30],
        "text": message.text
    })
    user(cid)["state"] = None
    save_data()
    bot.send_message(message.chat.id, "Заметка сохранена.", reply_markup=main_menu())

@bot.message_handler(func=lambda m: m.text == "📂 Категории")
def show_categories(message):
    cid = str(message.chat.id)
    cats = sorted(set(n["category"] for n in user(cid)["notes"]))
    if not cats:
        bot.send_message(message.chat.id, "Нет заметок.", reply_markup=main_menu())
        return
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    for c in cats:
        kb.add(c)
    kb.add("⬅️ Назад")
    bot.send_message(message.chat.id, "Выбери категорию:", reply_markup=kb)

@bot.message_handler(func=lambda m: m.text not in main_menu().keyboard and m.text != "⬅️ Назад")
def category_notes(message):
    cid = str(message.chat.id)
    notes = [n for n in user(cid)["notes"] if n["category"] == message.text]
    if not notes:
        return
    user(cid)["state"] = "view_note"
    user(cid)["current_notes"] = notes
    save_data()
    text = "Заметки:\n" + "\n".join(n["title"] for n in notes)
    bot.send_message(message.chat.id, text + "\n\nНапиши название заметки:")

@bot.message_handler(func=lambda m: user(str(m.chat.id))["state"] == "view_note")
def view_note(message):
    cid = str(message.chat.id)
    for n in user(cid)["current_notes"]:
        if n["title"] == message.text:
            kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
            kb.add("🗑 Удалить", "⬅️ Назад")
            user(cid)["current_view"] = n
            save_data()
            bot.send_message(message.chat.id, n["text"], reply_markup=kb)
            return

@bot.message_handler(func=lambda m: m.text == "🗑 Удалить")
def delete_note(message):
    cid = str(message.chat.id)
    user(cid)["notes"].remove(user(cid)["current_view"])
    user(cid)["state"] = None
    save_data()
    bot.send_message(message.chat.id, "Заметка удалена.", reply_markup=main_menu())

# =========================
# 🍅 POMODORO
# =========================

timers = {}

@bot.message_handler(func=lambda m: m.text == "🍅 Фокус")
def focus_menu(message):
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add("25 минут", "50 минут")
    kb.add("⬅️ Назад")
    bot.send_message(message.chat.id, "Выбери время фокуса:", reply_markup=kb)

@bot.message_handler(func=lambda m: m.text in ["25 минут","50 минут"])
def start_focus(message):
    cid = str(message.chat.id)
    minutes = int(message.text.split()[0])
    bot.send_message(message.chat.id, f"Фокус начался на {minutes} минут.")
    timer = threading.Timer(minutes*60, finish_focus, args=[cid, minutes])
    timers[cid] = timer
    timer.start()

def finish_focus(cid, minutes):
    user(cid)["focus"]["sessions"] += 1
    user(cid)["focus"]["minutes"] += minutes
    save_data()
    bot.send_message(cid, "Фокус завершён. Сделай перерыв.", reply_markup=main_menu())

# =========================
# 📊 STATS
# =========================

@bot.message_handler(func=lambda m: m.text == "📊 Статистика")
def stats(message):
    cid = str(message.chat.id)
    moods = {}
    for m in user(cid)["moods"].values():
        moods[m] = moods.get(m, 0) + 1
    mood_text = "\n".join(f"{k} — {v}" for k,v in moods.items()) or "Нет данных"

    focus = user(cid)["focus"]
    text = (
        "📊 Статистика\n\n"
        f"😊 Настроение:\n{mood_text}\n\n"
        f"🍅 Фокус:\n"
        f"Сессий: {focus['sessions']}\n"
        f"Минут: {focus['minutes']}"
    )
    bot.send_message(message.chat.id, text, reply_markup=main_menu())

# ---------------- RUN ----------------

print("Bot is running")
bot.infinity_polling()
