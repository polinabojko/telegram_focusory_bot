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
def plan_menu():
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add("➕ Добавить задачу")
    kb.add("📅 Сегодня", "🗓 Неделя", "🗂 Месяц")
    kb.add("📌 Без даты")
    kb.add("⬅️ Назад")
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



@bot.message_handler(func=lambda m: m.text == "⬅️ Главное меню")
def go_main_menu(message):
    cid = str(message.chat.id)
    # Сбрасываем все состояния
    u = user(cid)
    u["state"] = None
    u["focus_state"] = None
    u.pop("selected_task_id", None)
    save_data()

    # Открываем главное меню
    bot.send_message(cid, "Главное меню:", reply_markup=main_menu())
    
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
    cid = str(message.chat.id)
    u = user(cid)

    notes = [n for n in u["notes"] if n["category"] == message.text]

    if not notes:
        bot.send_message(message.chat.id, "В этой категории нет заметок.")
        return

    text = "Заметки:\n\n"
    for n in notes:
        text += f"• {n['title']}\n"

    u["current_category"] = message.text
    u["state"] = "note_select"
    save_data()

    bot.send_message(
        message.chat.id,
        text + "\nНапишите название заметки, которую хотите открыть:",
        reply_markup=back_menu()
    )
@bot.message_handler(func=lambda m: user(m.chat.id)["state"] == "notes_view")
def notes_list(message):
    ...
@bot.message_handler(func=lambda m: user(m.chat.id)["state"] == "note_select")
def open_note(message):
    cid = str(message.chat.id)
    u = user(cid)

    note = next(
        (n for n in u["notes"]
         if n["category"] == u["current_category"] and n["title"] == message.text),
        None
    )

    if not note:
        bot.send_message(
            message.chat.id,
            "Заметка с таким названием не найдена. Введите точное название."
        )
        return

    u["current_note"] = note
    u["state"] = "note_open"
    save_data()

    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add("🗑 Удалить заметку")
    kb.add("⬅️ Назад")

    bot.send_message(
        message.chat.id,
        f"📝 {note['title']}\n\n{note['text']}",
        reply_markup=kb
    )
@bot.message_handler(func=lambda m: m.text == "🗑 Удалить заметку")
def delete_note(message):
    cid = str(message.chat.id)
    u = user(cid)

    note = u.get("current_note")
    if not note:
        bot.send_message(message.chat.id, "Ошибка.")
        return

    u["notes"] = [n for n in u["notes"] if n != note]
    u["state"] = None
    u.pop("current_note", None)
    save_data()

    bot.send_message(
        message.chat.id,
        "Заметка удалена.",
        reply_markup=main_menu()
    )

# ----------- ПЛАН --------------

import threading
import time
from datetime import datetime, date, timedelta
from telebot import types

# функция для завершения повторяющейся задачи
def complete_task(task):
    task["done"] = True

    if not task.get("repeat") or not task.get("date"):
        return

    d = date.fromisoformat(task["date"])

    if task["repeat"] == "daily":
        d += timedelta(days=1)
    elif task["repeat"] == "weekly":
        d += timedelta(weeks=1)
    elif task["repeat"] == "monthly":
        if d.month == 12:
            d = d.replace(year=d.year+1, month=1)
        else:
            d = d.replace(month=d.month+1)

    task["date"] = d.isoformat()
    task["done"] = False
    task["remind_at"] = None

# ---------- Фоновый цикл напоминаний ----------
def reminder_loop():
    while True:
        now = datetime.now().strftime("%Y-%m-%d %H:%M")
        for cid, udata in all_users().items():  # функция возвращает всех пользователей
            for task in udata["tasks"]:
                if task.get("remind_at") == now:
                    bot.send_message(int(cid), f"⏰ Напоминание о задаче: {task['title']}")
                    task["remind_at"] = None  # чтобы не повторялось
                    save_data()
        time.sleep(60)

threading.Thread(target=reminder_loop, daemon=True).start()

# ---------- Открытие меню планирования ----------
@bot.message_handler(func=lambda m: m.text == "📅 План")
def open_plan(message):
    bot.send_message(message.chat.id, "Планирование задач:", reply_markup=plan_menu())

# ---------- Добавление задачи ----------
@bot.message_handler(func=lambda m: m.text == "➕ Добавить задачу")
def task_add_start(message):
    cid = str(message.chat.id)
    user(cid)["state"] = "task_title"
    save_data()
    bot.send_message(message.chat.id, "Введите название задачи:")

@bot.message_handler(func=lambda m: user(m.chat.id).get("state") == "task_title")
def task_title(message):
    cid = str(message.chat.id)
    user(cid)["tmp_task_title"] = message.text
    user(cid)["state"] = "task_date"
    save_data()

    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add("Сегодня", "На этой неделе")
    kb.add("В этом месяце", "Без даты")
    kb.add("⬅️ Назад")
    bot.send_message(message.chat.id, "Когда выполнить задачу?", reply_markup=kb)

@bot.message_handler(func=lambda m: user(m.chat.id).get("state") == "task_date")
def task_date(message):
    cid = str(message.chat.id)
    today = date.today()

    if message.text == "Сегодня":
        task_date_val = today.isoformat()
    elif message.text == "На этой неделе":
        task_date_val = (today + timedelta(days=7)).isoformat()
    elif message.text == "В этом месяце":
        task_date_val = today.replace(day=28).isoformat()
    elif message.text == "Без даты":
        task_date_val = None
    else:
        bot.send_message(message.chat.id, "Выберите вариант кнопкой.")
        return

    user(cid)["tmp_task_date"] = task_date_val
    user(cid)["state"] = "task_repeat"
    save_data()

    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add("Каждый день", "Каждую неделю")
    kb.add("Каждый месяц", "Без повтора")
    bot.send_message(message.chat.id, "Повторять задачу?", reply_markup=kb)

@bot.message_handler(func=lambda m: user(m.chat.id).get("state") == "task_repeat")
def task_repeat(message):
    cid = str(message.chat.id)
    repeat_map = {
        "Каждый день": "daily",
        "Каждую неделю": "weekly",
        "Каждый месяц": "monthly",
        "Без повтора": None
    }

    if message.text not in repeat_map:
        bot.send_message(message.chat.id, "Выберите вариант кнопкой.")
        return

    user(cid)["tmp_task_repeat"] = repeat_map[message.text]
    user(cid)["state"] = "task_reminder"
    save_data()

    bot.send_message(message.chat.id,
                     "Если нужно напоминание, введи дату и время\nФормат: YYYY-MM-DD HH:MM\nили напиши «без напоминания»",
                     reply_markup=types.ReplyKeyboardRemove())

@bot.message_handler(func=lambda m: user(m.chat.id).get("state") == "task_reminder")
def task_reminder(message):
    cid = str(message.chat.id)
    remind_at = None
    if message.text.lower() != "без напоминания":
        try:
            datetime.strptime(message.text, "%Y-%m-%d %H:%M")
            remind_at = message.text
        except:
            bot.send_message(message.chat.id, "Неверный формат. Попробуй ещё раз.")
            return

    user(cid)["tasks"].append({
        "id": str(datetime.now().timestamp()),
        "title": user(cid)["tmp_task_title"],
        "date": user(cid)["tmp_task_date"],
        "done": False,
        "repeat": user(cid)["tmp_task_repeat"],
        "remind_at": remind_at,
        "created": datetime.now().isoformat()
    })

    user(cid)["state"] = None
    save_data()
    bot.send_message(message.chat.id, "Задача добавлена.", reply_markup=plan_menu())

# ---------- Фильтр задач ----------
def filter_tasks(cid, mode):
    today = date.today()
    tasks = user(cid)["tasks"]
    result = []
    for t in tasks:
        if t["done"]:
            continue
        if mode == "today" and t["date"] == today.isoformat():
            result.append(t)
        elif mode == "week" and t["date"]:
            d = date.fromisoformat(t["date"])
            if today <= d <= today + timedelta(days=7):
                result.append(t)
        elif mode == "month" and t["date"] and t["date"][:7] == today.isoformat()[:7]:
            result.append(t)
        elif mode == "nodate" and t["date"] is None:
            result.append(t)
    return result

# ---------- Показ задач ----------
@bot.message_handler(func=lambda m: m.text in ["📅 Сегодня", "🗓 Неделя", "🗂 Месяц", "📌 Без даты"])
def show_tasks(message):
    cid = str(message.chat.id)
    mapping = {"📅 Сегодня": "today", "🗓 Неделя": "week", "🗂 Месяц": "month", "📌 Без даты": "nodate"}
    tasks = filter_tasks(cid, mapping[message.text])
    if not tasks:
        bot.send_message(message.chat.id, "Нет задач.", reply_markup=plan_menu())
        return

    text = "Задачи:\n\n"
    for i, t in enumerate(tasks, 1):
        text += f"{i}. {t['title']}\n"

    user(cid)["state"] = "task_done_select"
    user(cid)["last_task_list"] = tasks
    save_data()

    bot.send_message(message.chat.id, text + "\nВведите номер выполненной задачи:", reply_markup=back_menu())

# ---------- Отметка задачи выполненной ----------
@bot.message_handler(func=lambda m: True)
def task_done_select_handler(message):
    cid = str(message.chat.id)
    u = user(cid)
    if u.get("state") != "task_done_select":
        return

    try:
        idx = int(message.text) - 1
        task = u["last_task_list"][idx]
    except:
        bot.send_message(message.chat.id, "Введите корректный номер задачи.")
        return

    for t in u["tasks"]:
        if t["id"] == task["id"]:
            complete_task(t)

    u["state"] = None
    u.pop("last_task_list", None)
    save_data()
    bot.send_message(message.chat.id, f"Задача '{task['title']}' выполнена.", reply_markup=plan_menu())

# ---------- Действия с задачей ----------
@bot.message_handler(func=lambda m: user(m.chat.id).get("state") == "task_action")
def task_action(message):
    cid = str(message.chat.id)
    tid = user(cid).get("selected_task_id")
    if not tid:
        return
    t = next((x for x in user(cid)["tasks"] if x["id"] == tid), None)
    if not t:
        return

    if message.text == "✅ Выполнено":
        complete_task(t)
        bot.send_message(message.chat.id, "Задача выполнена.", reply_markup=plan_menu())
    elif message.text == "🔕 Отключить напоминание":
        t["remind_at"] = None
        bot.send_message(message.chat.id, "Напоминание отключено.", reply_markup=plan_menu())
    elif message.text == "⬅️ Назад":
        bot.send_message(message.chat.id, "Планирование задач:", reply_markup=plan_menu())

    user(cid)["state"] = None
    user(cid).pop("selected_task_id", None)
    save_data()
    

# ----------------- POMODORO ——————————————

pomodoro_timers = {}  # таймеры по chat_id
pomodoro_stats = {}   # статистика: {chat_id: {"sessions": int, "minutes": int}}

def get_user_stats(cid):
    if cid not in pomodoro_stats:
        pomodoro_stats[cid] = {"sessions": 0, "minutes": 0}
    return pomodoro_stats[cid]

# ---------------- Старт фокуса ----------------
@bot.message_handler(func=lambda m: m.text == "🍅 Фокус")
def focus_menu(message):
    cid = str(message.chat.id)
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add("25", "50")
    kb.add("⬅️ Главное меню")
    bot.send_message(cid, "Выберите длительность фокуса (минут):", reply_markup=kb)

@bot.message_handler(func=lambda m: m.text in ["25","50"])
def start_focus(message):
    cid = str(message.chat.id)
    minutes = int(message.text)

    user(cid)["focus_state"] = "running"
    save_data()

    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add("🛑 Завершить фокус", "⬅️ Главное меню")
    bot.send_message(cid, f"Фокус начался — {minutes} мин", reply_markup=kb)

    # определяем контрольные минуты
    if minutes == 25:
        notify_points = [15, 20]  # через 10 и 5 минут до конца
    elif minutes == 50:
        notify_points = [20, 40, 45]  # через 30, 10 и 5 минут до конца
    else:
        notify_points = []

    pomodoro_timers[cid] = {
        "minutes_total": minutes,
        "minutes_left": minutes,
        "notify_points": notify_points,
        "thread": None
    }

    # запускаем таймер каждую минуту
    run_focus_timer(cid)

def run_focus_timer(cid):
    data = pomodoro_timers.get(cid)
    if not data:
        return

    if data["minutes_left"] <= 0 or user(cid).get("focus_state") != "running":
        finish_focus(cid)
        return

    # проверяем, нужно ли прислать уведомление
    minutes_passed = data["minutes_total"] - data["minutes_left"]
    if minutes_passed in data["notify_points"]:
        bot.send_message(int(cid), f"⏱ Осталось {data['minutes_left']} мин", reply_markup=types.ReplyKeyboardMarkup(resize_keyboard=True).add("🛑 Завершить фокус","⬅️ Главное меню"))

    data["minutes_left"] -= 1
    t = threading.Timer(60, run_focus_timer, args=[cid])
    data["thread"] = t
    t.start()

# ---------------- Завершение фокуса вручную ----------------
@bot.message_handler(func=lambda m: m.text == "🛑 Завершить фокус")
def stop_focus(message):
    cid = str(message.chat.id)
    user(cid)["focus_state"] = "finished"
    data = pomodoro_timers.pop(cid, None)
    if data and data["thread"]:
        data["thread"].cancel()
    finish_focus(cid)

# ---------------- Завершение фокуса ----------------
def finish_focus(cid):
    data = pomodoro_timers.get(cid)
    if not data:
        return

    minutes_done = data.get("minutes_total", 0)

    stats = get_user_stats(cid)
    stats["sessions"] += 1
    stats["minutes"] += minutes_done
    save_data()

    # удаляем таймер и сбрасываем состояние
    pomodoro_timers.pop(cid, None)
    user(cid)["focus_state"] = None

    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add("🍅 Новый фокус")
    kb.add("⬅️ Главное меню")

    bot.send_message(int(cid), "Фокус завершён! Что дальше?", reply_markup=kb)

def start_break(cid, minutes=5):
    user(cid)["focus_state"] = "break"
    save_data()

    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add("⏭ Пропустить перерыв", "🍅 Новый фокус")
    kb.add("⬅️ Главное меню")

    bot.send_message(cid, f"Перерыв {minutes} минут", reply_markup=kb)

    # Таймер перерыва
    t = threading.Timer(minutes*60, finish_break, args=[cid])
    pomodoro_timers[cid] = {"thread": t}
    t.start()

def finish_break(cid):
    pomodoro_timers.pop(cid, None)
    user(cid)["focus_state"] = None
    bot.send_message(cid, "Перерыв завершён! Можно начать новый фокус.", reply_markup=types.ReplyKeyboardMarkup(resize_keyboard=True).add("🍅 Новый фокус","⬅️ Главное меню"))

# ---------------- Новый фокус ----------------
@bot.message_handler(func=lambda m: m.text == "🍅 Новый фокус")
def new_focus(message):
    focus_menu(message)
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
