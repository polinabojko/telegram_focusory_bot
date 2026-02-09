import telebot
from telebot.types import ReplyKeyboardMarkup
import os, json, threading
from datetime import date

TOKEN = os.getenv("TOKEN")
bot = telebot.TeleBot(TOKEN)

DATA_FILE = "data.json"

# ================== DATA ==================

data = {
    "state": {},
    "mood": {},
    "tasks": {},
    "notes": {},
    "task_draft": {},
    "note_draft": {},
    "pomodoro_today": {},
    "timers": {}
}

def load():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            data.update(json.load(f))

def save():
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

load()

def cid(m): return str(m.chat.id)
def today(): return date.today().isoformat()

def set_state(c, s):
    data["state"][c] = s
    save()

def get_state(c):
    return data["state"].get(c)

def kb(*rows):
    k = ReplyKeyboardMarkup(resize_keyboard=True)
    for r in rows:
        k.add(*r)
    return k

# ================== TEXT ==================

MENU = kb(
    ["⏳ Фокус", "🙂 Настроение"],
    ["📋 Планирование", "📝 Заметки"],
    ["📊 Статистика"]
)

MOODS = ["😁", "🙂", "😐", "😕", "😞"]

# ================== START ==================

@bot.message_handler(commands=["start"])
def start(m):
    bot.send_message(m.chat.id, "🧭 Главное меню", reply_markup=MENU)

# ================== MOOD ==================

@bot.message_handler(func=lambda m: m.text == "🙂 Настроение")
def mood(m):
    set_state(cid(m), "mood")
    bot.send_message(
        m.chat.id,
        "Как ты сегодня?",
        reply_markup=kb(MOODS, ["↩️ В меню"])
    )

@bot.message_handler(func=lambda m: get_state(cid(m)) == "mood")
def save_mood(m):
    if m.text in MOODS:
        data["mood"][cid(m)] = {"date": today(), "value": m.text}
        set_state(cid(m), None)
        save()
        bot.send_message(m.chat.id, "Настроение сохранено.", reply_markup=MENU)

# ================== POMODORO ==================

@bot.message_handler(func=lambda m: m.text == "⏳ Фокус")
def focus_menu(m):
    bot.send_message(
        m.chat.id,
        "Выбери длительность фокуса:",
        reply_markup=kb(["15", "25", "50"], ["↩️ В меню"])
    )

def start_focus(chat_id, minutes):
    bot.send_message(chat_id, f"⏳ Фокус начался — {minutes} минут")

    timer = threading.Timer(minutes * 60, finish_focus, args=[chat_id])
    data["timers"][chat_id] = timer
    timer.start()

def finish_focus(chat_id):
    data["pomodoro_today"][today()] = data["pomodoro_today"].get(today(), 0) + 1
    save()

    bot.send_message(
        chat_id,
        "✅ Фокус завершён\n☕ Перерыв — 5 минут",
        reply_markup=kb(
            ["⏭ Пропустить перерыв", "🔄 Новый фокус"],
            ["🚪 Выйти из Pomodoro"]
        )
    )

    timer = threading.Timer(5 * 60, end_break, args=[chat_id])
    data["timers"][chat_id] = timer
    timer.start()

def end_break(chat_id):
    bot.send_message(
        chat_id,
        "Выбери следующий фокус:",
        reply_markup=kb(["15", "25", "50"], ["🚪 Выйти из Pomodoro"])
    )

@bot.message_handler(func=lambda m: m.text in ["15", "25", "50"])
def handle_focus(m):
    start_focus(m.chat.id, int(m.text))

@bot.message_handler(func=lambda m: m.text == "⏭ Пропустить перерыв")
def skip_break(m):
    t = data["timers"].pop(m.chat.id, None)
    if t: t.cancel()
    end_break(m.chat.id)

@bot.message_handler(func=lambda m: m.text == "🚪 Выйти из Pomodoro")
def exit_focus(m):
    t = data["timers"].pop(m.chat.id, None)
    if t: t.cancel()
    bot.send_message(m.chat.id, "🧭 Главное меню", reply_markup=MENU)

# ================== TASKS ==================

@bot.message_handler(func=lambda m: m.text == "📋 Планирование")
def plan(m):
    bot.send_message(
        m.chat.id,
        "📋 Планирование",
        reply_markup=kb(
            ["➕ Добавить задачу", "📂 Посмотреть"],
            ["↩️ В меню"]
        )
    )

@bot.message_handler(func=lambda m: m.text == "➕ Добавить задачу")
def add_task(m):
    set_state(cid(m), "task_text")
    bot.send_message(m.chat.id, "Введите текст задачи:")

@bot.message_handler(func=lambda m: get_state(cid(m)) == "task_text")
def task_text(m):
    data["task_draft"][cid(m)] = m.text
    set_state(cid(m), "task_date")
    bot.send_message(
        m.chat.id,
        "Когда?",
        reply_markup=kb(["Сегодня", "Неделя", "Месяц", "Без даты"])
    )

@bot.message_handler(func=lambda m: get_state(cid(m)) == "task_date")
def task_date(m):
    data.setdefault("tasks", {}).setdefault(cid(m), []).append({
        "text": data["task_draft"][cid(m)],
        "date": m.text,
        "done": False
    })
    set_state(cid(m), None)
    save()
    bot.send_message(m.chat.id, "Задача добавлена.", reply_markup=MENU)

@bot.message_handler(func=lambda m: m.text == "📂 Посмотреть")
def view_tasks(m):
    tasks = data.get("tasks", {}).get(cid(m), [])
    if not tasks:
        bot.send_message(m.chat.id, "Задач нет.")
        return

    text = "📋 Задачи:\n\n"
    for i, t in enumerate(tasks, 1):
        mark = "✔️" if t["done"] else "◻️"
        text += f"{i}. {mark} {t['text']} ({t['date']})\n"

    text += "\nНапиши: done <номер>"
    bot.send_message(m.chat.id, text)

@bot.message_handler(func=lambda m: m.text.startswith("done "))
def mark_done(m):
    try:
        idx = int(m.text.split()[1]) - 1
        data["tasks"][cid(m)][idx]["done"] = True
        save()
        bot.send_message(m.chat.id, "✔️ Готово")
    except:
        bot.send_message(m.chat.id, "Ошибка")

# ================== NOTES ==================

@bot.message_handler(func=lambda m: m.text == "📝 Заметки")
def notes(m):
    bot.send_message(
        m.chat.id,
        "📝 Заметки",
        reply_markup=kb(
            ["➕ Новая заметка", "📂 Просмотреть"],
            ["↩️ В меню"]
        )
    )

@bot.message_handler(func=lambda m: m.text == "➕ Новая заметка")
def new_note(m):
    set_state(cid(m), "note_title")
    bot.send_message(m.chat.id, "Заголовок заметки:")

@bot.message_handler(func=lambda m: get_state(cid(m)) == "note_title")
def note_title(m):
    data["note_draft"][cid(m)] = {"title": m.text}
    set_state(cid(m), "note_text")
    bot.send_message(m.chat.id, "Текст заметки:")

@bot.message_handler(func=lambda m: get_state(cid(m)) == "note_text")
def note_text(m):
    note = data["note_draft"][cid(m)]
    note["text"] = m.text
    data.setdefault("notes", {}).setdefault(cid(m), []).append(note)
    set_state(cid(m), None)
    save()
    bot.send_message(m.chat.id, "Заметка сохранена.", reply_markup=MENU)

@bot.message_handler(func=lambda m: m.text == "📂 Просмотреть")
def view_notes(m):
    notes = data.get("notes", {}).get(cid(m), [])
    if not notes:
        bot.send_message(m.chat.id, "Заметок нет.")
        return

    text = "🗂 Заметки:\n\n"
    for i, n in enumerate(notes, 1):
        text += f"{i}. {n['title']}\n"
    text += "\nНапиши номер или: search текст"
    set_state(cid(m), "view_notes")
    bot.send_message(m.chat.id, text)

@bot.message_handler(func=lambda m: get_state(cid(m)) == "view_notes" and m.text.isdigit())
def open_note(m):
    n = data["notes"][cid(m)][int(m.text)-1]
    bot.send_message(m.chat.id, f"📝 {n['title']}\n\n{n['text']}")

@bot.message_handler(func=lambda m: get_state(cid(m)) == "view_notes" and m.text.startswith("search "))
def search_notes(m):
    q = m.text[7:].lower()
    res = [n for n in data["notes"][cid(m)] if q in n["title"].lower() or q in n["text"].lower()]
    if not res:
        bot.send_message(m.chat.id, "Ничего не найдено.")
        return
    bot.send_message(m.chat.id, "\n".join(f"• {n['title']}" for n in res))

# ================== STATS ==================

@bot.message_handler(func=lambda m: m.text == "📊 Статистика")
def stats(m):
    mood = data["mood"].get(cid(m))
    focus = data["pomodoro_today"].get(today(), 0)

    text = "📊 Статистика:\n\n"
    if mood:
        text += f"🙂 Настроение сегодня: {mood['value']}\n"
    text += f"⏳ Фокусов сегодня: {focus}"

    bot.send_message(m.chat.id, text, reply_markup=MENU)

# ================== BACK ==================

@bot.message_handler(func=lambda m: m.text == "↩️ В меню")
def back(m):
    set_state(cid(m), None)
    bot.send_message(m.chat.id, "🧭 Главное меню", reply_markup=MENU)

# ================== RUN ==================

print("Bot is running")
bot.infinity_polling()
