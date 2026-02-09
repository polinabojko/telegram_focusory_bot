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

# ----------- ПЛАН -----------

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
        d = d.replace(
            month=d.month + 1 if d.month < 12 else 1,
            year=d.year + 1 if d.month == 12 else d.year
        )

    task["date"] = d.isoformat()
    task["done"] = False
    task["remind_at"] = None


@bot.message_handler(func=lambda m: m.text == "📅 План")
def open_plan(message):
    bot.send_message(
        message.chat.id,
        "Планирование задач:",
        reply_markup=plan_menu()
    )


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
        task_date = today.isoformat()
    elif message.text == "На этой неделе":
        task_date = (today + timedelta(days=7)).isoformat()
    elif message.text == "В этом месяце":
        task_date = today.replace(day=28).isoformat()
    elif message.text == "Без даты":
        task_date = None
    else:
        bot.send_message(message.chat.id, "Выберите вариант кнопкой.")
        return

    user(cid)["tmp_task_date"] = task_date
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

    bot.send_message(
        message.chat.id,
        "Если нужно напоминание, введи дату и время\nФормат: YYYY-MM-DD HH:MM\nили напиши «без напоминания»",
        reply_markup=types.ReplyKeyboardRemove()
    )


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

    bot.send_message(
        message.chat.id,
        "Задача добавлена.",
        reply_markup=plan_menu()
    )


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


@bot.message_handler(func=lambda m: m.text in ["📅 Сегодня", "🗓 Неделя", "🗂 Месяц", "📌 Без даты"])
def show_tasks(message):
    cid = str(message.chat.id)

    mapping = {
        "📅 Сегодня": "today",
        "🗓 Неделя": "week",
        "🗂 Месяц": "month",
        "📌 Без даты": "nodate"
    }

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

    bot.send_message(
        message.chat.id,
        text + "\nВведите номер выполненной задачи:",
        reply_markup=back_menu()
    )


@bot.message_handler(func=lambda m: user(m.chat.id).get("state") == "task_done_select")
def task_done(message):
    cid = str(message.chat.id)

    try:
        idx = int(message.text) - 1
        task = user(cid)["last_task_list"][idx]
    except:
        bot.send_message(message.chat.id, "Введите номер задачи.")
        return

    for t in user(cid)["tasks"]:
        if t["id"] == task["id"]:
            complete_task(t)

    user(cid)["state"] = None
    save_data()

    bot.send_message(
        message.chat.id,
        "Задача выполнена.",
        reply_markup=plan_menu()
    )


# ----------------- POMODORO -----------------

pomodoro_timers = {}  # для хранения таймеров
pomodoro_stats = {}   # статистика фокуса: {chat_id: {"sessions": int, "minutes": int}}

def get_user_stats(cid):
    if cid not in pomodoro_stats:
        pomodoro_stats[cid] = {"sessions": 0, "minutes": 0}
    return pomodoro_stats[cid]

def start_focus_timer(cid, minutes):
    # создаем сообщение с кнопками
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add("🛑 Завершить фокус", "⬅️ Главное меню")
    msg = bot.send_message(cid, f"Фокус начался — {minutes} мин.\nОсталось: {minutes} мин", reply_markup=kb)

    # сохраняем таймер
    pomodoro_timers[cid] = {
        "minutes_left": minutes,
        "msg_id": msg.message_id,
        "thread": None
    }

    # запускаем обновление каждую минуту
    update_focus(cid)

def update_focus(cid):
    data = pomodoro_timers.get(cid)
    if not data:
        return

    minutes_left = data["minutes_left"]
    msg_id = data["msg_id"]

    if minutes_left <= 0:
        finish_focus(cid)
        return

    # обновляем сообщение с оставшимся временем
    try:
        bot.edit_message_text(
            f"Фокус идёт — осталось: {minutes_left} мин",
            chat_id=int(cid),
            message_id=msg_id
        )
    except:
        pass

    # уменьшаем счетчик
    data["minutes_left"] -= 1

    # запускаем следующую минуту
    t = threading.Timer(60, update_focus, args=[cid])
    data["thread"] = t
    t.start()

# ----------------- Старт фокуса -----------------
@bot.message_handler(func=lambda m: m.text == "🍅 Фокус")
def focus_menu(message):
    cid = str(message.chat.id)
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add("25", "50")
    kb.add("⬅️ Главное меню")
    bot.send_message(cid, "Выберите длительность фокуса (минут):", reply_markup=kb)

@bot.message_handler(func=lambda m: m.text in ["25", "50"])
def start_focus(message):
    cid = str(message.chat.id)
    minutes = int(message.text)
    start_focus_timer(cid, minutes)
    user(cid)["state"] = "focus"
    save_data()

# ----------------- Завершение фокуса вручную -----------------
@bot.message_handler(func=lambda m: m.text == "🛑 Завершить фокус")
def stop_focus(message):
    cid = str(message.chat.id)
    data = pomodoro_timers.pop(cid, None)
    if data and data["thread"]:
        data["thread"].cancel()
    finish_focus(cid)

# ----------------- Финиш фокуса -----------------
def finish_focus(cid):
    stats = get_user_stats(cid)
    # вычисляем сколько минут прошло (если таймер был принудительно завершен)
    minutes_done = pomodoro_timers.get(cid, {}).get("minutes_left", 0)
    total_minutes = 0 if minutes_done == 0 else stats["minutes"] - minutes_done

    stats["sessions"] += 1
    stats["minutes"] += total_minutes
    save_data()

    # удаляем таймер, если есть
    pomodoro_timers.pop(cid, None)

    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add("🍅 Новый фокус")
    kb.add("⬅️ Главное меню")
    bot.send_message(int(cid), "Фокус завершён! Что дальше?", reply_markup=kb)
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
