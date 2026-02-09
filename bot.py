import telebot
from telebot import types
import json
import os
import threading
import time
from datetime import datetime, timedelta

TOKEN = os.getenv("BOT_TOKEN")
bot = telebot.TeleBot(TOKEN)

DATA_FILE = "data.json"

# ---------- DATA ----------
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
    if cid not in data:
        data[cid] = {
            "tasks": [],
            "notes": [],
            "moods": {},
            "focus": {"sessions": 0, "minutes": 0},
            "state": None
        }
    return data[cid]

# ---------- UI ----------
def main_menu():
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add("🗓 Планирование", "🍅 Фокус")
    kb.add("😊 Настроение", "📝 Заметки")
    kb.add("📊 Статистика")
    return kb

# ---------- START ----------
@bot.message_handler(commands=["start"])
def start(message):
    bot.send_message(
        message.chat.id,
        "Focusory — управление фокусом и задачами.\n\nВыберите действие:",
        reply_markup=main_menu()
    )

# ---------- MOOD ----------
MOODS = ["😄", "🙂", "😐", "🙁", "😞"]

@bot.message_handler(func=lambda m: m.text == "😊 Настроение")
def mood_menu(message):
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add(*MOODS)
    kb.add("⬅️ Назад")
    bot.send_message(message.chat.id, "Какое у вас сегодня настроение?", reply_markup=kb)

@bot.message_handler(func=lambda m: m.text in MOODS)
def save_mood(message):
    cid = str(message.chat.id)
    today = datetime.now().strftime("%Y-%m-%d")
    user(cid)["moods"][today] = message.text
    save_data()
    bot.send_message(message.chat.id, "Записано.", reply_markup=main_menu())

# ---------- TASKS ----------
@bot.message_handler(func=lambda m: m.text == "🗓 Планирование")
def plan_menu(message):
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add("➕ Добавить задачу", "📋 Посмотреть задачи")
    kb.add("⬅️ Назад")
    bot.send_message(message.chat.id, "Планирование:", reply_markup=kb)

@bot.message_handler(func=lambda m: m.text == "➕ Добавить задачу")
def add_task(message):
    cid = str(message.chat.id)
    user(cid)["state"] = "add_task_text"
    save_data()
    bot.send_message(message.chat.id, "Введите текст задачи:")

@bot.message_handler(func=lambda m: user(str(m.chat.id)).get("state") == "add_task_text")
def add_task_text(message):
    cid = str(message.chat.id)
    user(cid)["new_task"] = message.text
    user(cid)["state"] = "add_task_date"
    save_data()

    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add("Сегодня", "Неделя", "Месяц", "Без даты")
    bot.send_message(message.chat.id, "Когда?", reply_markup=kb)

@bot.message_handler(func=lambda m: user(str(m.chat.id)).get("state") == "add_task_date")
def add_task_date(message):
    cid = str(message.chat.id)
    date = None
    now = datetime.now()

    if message.text == "Сегодня":
        date = now.strftime("%Y-%m-%d")
    elif message.text == "Неделя":
        date = (now + timedelta(days=7)).strftime("%Y-%m-%d")
    elif message.text == "Месяц":
        date = (now + timedelta(days=30)).strftime("%Y-%m-%d")

    user(cid)["tasks"].append({
        "text": user(cid)["new_task"],
        "date": date,
        "done": False
    })
    user(cid)["state"] = None
    save_data()

    bot.send_message(message.chat.id, "Задача добавлена.", reply_markup=main_menu())

# ---------- FOCUS ----------
focus_threads = {}

@bot.message_handler(func=lambda m: m.text == "🍅 Фокус")
def focus_menu(message):
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add("25 минут", "50 минут")
    kb.add("⬅️ Назад")
    bot.send_message(message.chat.id, "Выберите длительность фокуса:", reply_markup=kb)

def run_focus(cid, minutes):
    time.sleep(minutes * 60)
    data[cid]["focus"]["sessions"] += 1
    data[cid]["focus"]["minutes"] += minutes
    save_data()
    bot.send_message(int(cid), "Фокус завершён. Отличная работа.", reply_markup=main_menu())

@bot.message_handler(func=lambda m: m.text in ["25 минут", "50 минут"])
def start_focus(message):
    cid = str(message.chat.id)
    minutes = 25 if "25" in message.text else 50
    t = threading.Thread(target=run_focus, args=(cid, minutes))
    t.start()
    focus_threads[cid] = t
    bot.send_message(message.chat.id, f"Фокус начался на {minutes} минут.", reply_markup=main_menu())

# ---------- NOTES ----------
@bot.message_handler(func=lambda m: m.text == "📝 Заметки")
def notes_menu(message):
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add("➕ Добавить заметку", "📂 Посмотреть заметки")
    kb.add("⬅️ Назад")
    bot.send_message(message.chat.id, "Заметки:", reply_markup=kb)

@bot.message_handler(func=lambda m: m.text == "➕ Добавить заметку")
def add_note(message):
    cid = str(message.chat.id)
    user(cid)["state"] = "add_note"
    save_data()
    bot.send_message(message.chat.id, "Введите текст заметки:")

@bot.message_handler(func=lambda m: user(str(m.chat.id)).get("state") == "add_note")
def save_note(message):
    cid = str(message.chat.id)
    user(cid)["notes"].append({
        "text": message.text,
        "created": datetime.now().isoformat()
    })
    user(cid)["state"] = None
    save_data()
    bot.send_message(message.chat.id, "Заметка сохранена.", reply_markup=main_menu())

# ---------- STATS ----------
@bot.message_handler(func=lambda m: m.text == "📊 Статистика")
def stats(message):
    cid = str(message.chat.id)
    u = user(cid)

    text = "📊 Статистика\n\n"
    text += f"🍅 Фокус:\nСессии: {u['focus']['sessions']}\nМинут: {u['focus']['minutes']}\n\n"
    text += "😊 Настроение:\n"

    mood_count = {}
    for m in u["moods"].values():
        mood_count[m] = mood_count.get(m, 0) + 1

    for k, v in mood_count.items():
        text += f"{k} — {v}\n"

    bot.send_message(message.chat.id, text, reply_markup=main_menu())

# ---------- BACK ----------
@bot.message_handler(func=lambda m: m.text == "⬅️ Назад")
def back(message):
    bot.send_message(message.chat.id, "Главное меню:", reply_markup=main_menu())

# ---------- RUN ----------
bot.infinity_polling()
