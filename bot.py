import telebot
from telebot import types
import os, json, threading, time
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
            "focus": {"sessions":0,"minutes":0},
            "focus_state": None
        }
    return data[cid]

def all_users():
    return data

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
    kb.add("⬅️ Главное меню")
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
    bot.send_message(message.chat.id, "Focusory — управление фокусом и задачами.", reply_markup=main_menu())

# ---------------- BACK ----------------
@bot.message_handler(func=lambda m: m.text == "⬅️ Главное меню")
def go_main_menu(message):
    cid = str(message.chat.id)
    u = user(cid)
    u["state"] = None
    u["focus_state"] = None
    u.pop("selected_task_id", None)
    save_data()
    bot.send_message(cid, "Главное меню:", reply_markup=main_menu())

# ---------------- MOOD ----------------
@bot.message_handler(func=lambda m: m.text == "😊 Настроение")
def mood_menu(message):
    cid = str(message.chat.id)
    u = user(cid)
    u["state"] = None
    u["focus_state"] = None
    save_data()
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add("😄","🙂","😐","🙁","😣")
    kb.add("⬅️ Главное меню")
    bot.send_message(cid,"Выбери настроение:", reply_markup=kb)

@bot.message_handler(func=lambda m: m.text in ["😄","🙂","😐","🙁","😣"])
def save_mood(message):
    cid = str(message.chat.id)
    today = date.today().isoformat()
    u = user(cid)
    u["moods"][today] = message.text
    save_data()
    bot.send_message(cid,"Настроение сохранено.", reply_markup=main_menu())

# ---------------- NOTES ----------------
@bot.message_handler(func=lambda m: m.text == "📝 Заметки")
def notes_menu(message):
    cid = str(message.chat.id)
    u = user(cid)
    u["state"] = None
    u["focus_state"] = None
    save_data()
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add("➕ Добавить","📂 По категории")
    kb.add("⬅️ Главное меню")
    bot.send_message(cid,"Заметки:", reply_markup=kb)

@bot.message_handler(func=lambda m: m.text == "➕ Добавить")
def note_add(message):
    cid = str(message.chat.id)
    u = user(cid)
    u["state"] = "note_category"
    save_data()
    bot.send_message(cid,"Категория заметки:")

@bot.message_handler(func=lambda m: user(m.chat.id).get("state")=="note_category")
def note_cat(message):
    u = user(message.chat.id)
    u["tmp_cat"] = message.text
    u["state"] = "note_title"
    save_data()
    bot.send_message(message.chat.id,"Название заметки:")

@bot.message_handler(func=lambda m: user(m.chat.id).get("state")=="note_title")
def note_title(message):
    u = user(message.chat.id)
    u["tmp_title"] = message.text
    u["state"] = "note_text"
    save_data()
    bot.send_message(message.chat.id,"Текст заметки:")

@bot.message_handler(func=lambda m: user(m.chat.id).get("state")=="note_text")
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
    bot.send_message(message.chat.id,"Заметка сохранена.", reply_markup=main_menu())

@bot.message_handler(func=lambda m: m.text=="📂 По категории")
def notes_by_cat(message):
    cid = str(message.chat.id)
    u = user(cid)
    cats = sorted(set(n["category"] for n in u["notes"]))
    if not cats:
        bot.send_message(cid,"Нет заметок.", reply_markup=main_menu())
        return
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    for c in cats:
        kb.add(c)
    kb.add("⬅️ Главное меню")
    u["state"] = "notes_view"
    save_data()
    bot.send_message(cid,"Выбери категорию:", reply_markup=kb)

@bot.message_handler(func=lambda m: user(m.chat.id).get("state")=="notes_view")
def notes_list(message):
    cid = str(message.chat.id)
    u = user(cid)
    notes = [n for n in u["notes"] if n["category"]==message.text]
    if not notes:
        bot.send_message(cid,"В этой категории нет заметок.")
        return
    text="Заметки:\n\n"
    for n in notes:
        text+=f"• {n['title']}\n"
    u["current_category"]=message.text
    u["state"]="note_select"
    save_data()
    bot.send_message(cid,text+"\nНапишите название заметки, чтобы открыть:", reply_markup=back_menu())

@bot.message_handler(func=lambda m: user(m.chat.id).get("state")=="note_select")
def open_note(message):
    cid = str(message.chat.id)
    u = user(cid)
    note = next((n for n in u["notes"] if n["category"]==u["current_category"] and n["title"]==message.text),None)
    if not note:
        bot.send_message(cid,"Заметка не найдена. Введите точное название.")
        return
    u["current_note"]=note
    u["state"]="note_open"
    save_data()
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add("🗑 Удалить заметку","⬅️ Назад")
    bot.send_message(cid,f"📝 {note['title']}\n\n{note['text']}", reply_markup=kb)

@bot.message_handler(func=lambda m: m.text=="🗑 Удалить заметку")
def delete_note(message):
    cid = str(message.chat.id)
    u = user(cid)
    note = u.get("current_note")
    if not note:
        bot.send_message(cid,"Ошибка.")
        return
    u["notes"]=[n for n in u["notes"] if n!=note]
    u["state"]=None
    u.pop("current_note",None)
    save_data()
    bot.send_message(cid,"Заметка удалена.", reply_markup=main_menu())

# ----------------- PLAN -----------------
def complete_task(task):
    task["done"]=True
    if not task.get("repeat") or not task.get("date"):
        return
    d = date.fromisoformat(task["date"])
    if task["repeat"]=="daily":
        d+=timedelta(days=1)
    elif task["repeat"]=="weekly":
        d+=timedelta(weeks=1)
    elif task["repeat"]=="monthly":
        if d.month==12:
            d=d.replace(year=d.year+1, month=1)
        else:
            d=d.replace(month=d.month+1)
    task["date"]=d.isoformat()
    task["done"]=False
    task["remind_at"]=None

def reminder_loop():
    while True:
        now = datetime.now().strftime("%Y-%m-%d %H:%M")
        for cid, udata in data.items():  # берём всех пользователей
            for task in udata.get("tasks", []):
                if task.get("remind_at") == now:
                    bot.send_message(int(cid), f"⏰ Напоминание о задаче: {task['title']}")
                    task["remind_at"] = None  # чтобы не повторялось
                    save_data()
        time.sleep(60)

threading.Thread(target=reminder_loop, daemon=True).start()

@bot.message_handler(func=lambda m: m.text=="📅 План")
def open_plan(message):
    cid = str(message.chat.id)
    u = user(cid)
    u["state"]=None
    u["focus_state"]=None
    save_data()
    bot.send_message(cid,"Планирование задач:", reply_markup=plan_menu())
# Добавление задачи
@bot.message_handler(func=lambda m: m.text == "➕ Добавить задачу")
def task_add_start(message):
    cid = str(message.chat.id)
    user(cid)["state"] = "task_title"
    save_data()
    bot.send_message(cid, "Введите название задачи:")

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
    bot.send_message(cid, "Когда выполнить задачу?", reply_markup=kb)

@bot.message_handler(func=lambda m: user(m.chat.id).get("state") == "task_date")
def task_date(message):
    cid = str(message.chat.id)
    today = date.today()
    if message.text == "Сегодня":
        user(cid)["tmp_task_date"] = today.isoformat()
    elif message.text == "На этой неделе":
        user(cid)["tmp_task_date"] = (today + timedelta(days=7)).isoformat()
    elif message.text == "В этом месяце":
        user(cid)["tmp_task_date"] = today.replace(day=28).isoformat()
    elif message.text == "Без даты":
        user(cid)["tmp_task_date"] = None
    else:
        bot.send_message(cid, "Выберите вариант кнопкой.")
        return
    user(cid)["state"] = "task_repeat"
    save_data()
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add("Каждый день", "Каждую неделю")
    kb.add("Каждый месяц", "Без повтора")
    bot.send_message(cid, "Повторять задачу?", reply_markup=kb)

@bot.message_handler(func=lambda m: user(m.chat.id).get("state") == "task_repeat")
def task_repeat(message):
    cid = str(message.chat.id)
    repeat_map = {"Каждый день":"daily","Каждую неделю":"weekly","Каждый месяц":"monthly","Без повтора":None}
    if message.text not in repeat_map:
        bot.send_message(cid,"Выберите вариант кнопкой.")
        return
    user(cid)["tmp_task_repeat"] = repeat_map[message.text]
    user(cid)["state"] = "task_reminder"
    save_data()
    bot.send_message(cid,"Если нужно напоминание, введи дату и время\nФормат: YYYY-MM-DD HH:MM\nили напиши «без напоминания»", reply_markup=types.ReplyKeyboardRemove())

@bot.message_handler(func=lambda m: user(m.chat.id).get("state") == "task_reminder")
def task_reminder(message):
    cid = str(message.chat.id)
    remind_at = None
    if message.text.lower() != "без напоминания":
        try:
            dt = datetime.strptime(message.text, "%Y-%m-%d %H:%M")
            remind_at = dt.strftime("%Y-%m-%d %H:%M")
        except:
            bot.send_message(cid, "Неверный формат. Попробуй ещё раз.")
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
    bot.send_message(cid,"Задача добавлена.", reply_markup=plan_menu())

# Добавление задачи, повтор, напоминания — как в твоем коде выше (оставляем без изменений)
# Фильтр и показ задач
def filter_tasks(cid, mode):
    today = date.today()
    result = []
    for t in user(cid)["tasks"]:
        if t["done"]:
            continue
        if mode=="today" and t["date"]==today.isoformat(): result.append(t)
        elif mode=="week" and t["date"]:
            d = date.fromisoformat(t["date"])
            if today<=d<=today+timedelta(days=7): result.append(t)
        elif mode=="month" and t["date"] and t["date"][:7]==today.isoformat()[:7]: result.append(t)
        elif mode=="nodate" and t["date"] is None: result.append(t)
    return result

@bot.message_handler(func=lambda m: m.text in ["📅 Сегодня","🗓 Неделя","🗂 Месяц","📌 Без даты"])
def show_tasks(message):
    cid = str(message.chat.id)
    mapping = {"📅 Сегодня":"today","🗓 Неделя":"week","🗂 Месяц":"month","📌 Без даты":"nodate"}
    tasks = filter_tasks(cid, mapping[message.text])
    if not tasks:
        bot.send_message(cid,"Нет задач.", reply_markup=plan_menu())
        return
    text = "Задачи:\n\n"
    for i,t in enumerate(tasks,1):
        text += f"{i}. {t['title']}\n"
    u = user(cid)
    u["last_task_list"] = tasks
    u["state"] = "task_done_select"
    save_data()
    bot.send_message(cid, text+"\nВведите номер задачи для действий:", reply_markup=back_menu())

# ---------- Обработка выбора задачи ----------
@bot.message_handler(func=lambda m: user(m.chat.id).get("state") == "task_done_select")
def task_done_select_handler(message):
    cid = str(message.chat.id)
    u = user(cid)

    # --- Если нажали "Назад" ---
    if message.text == "⬅️ Назад":
        u["state"] = None
        u.pop("last_task_list", None)
        save_data()
        bot.send_message(message.chat.id, "Планирование задач:", reply_markup=plan_menu())
        return

    # --- Если ввели цифру ---
    if message.text.isdigit():
        idx = int(message.text) - 1
        tasks = u.get("last_task_list", [])
        if 0 <= idx < len(tasks):
            task = tasks[idx]
            u["selected_task_id"] = task["id"]
            u["state"] = "task_action"
            save_data()

            # Кнопки для действий с выбранной задачей
            kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
            kb.add("✅ Выполнено", "🔕 Отключить напоминание")
            kb.add("⬅️ Назад")
            bot.send_message(cid, f"Задача: {task['title']}", reply_markup=kb)
        else:
            bot.send_message(cid, "Введите корректный номер задачи.")
        return

    # --- Если не цифра и не Назад ---
    bot.send_message(cid, "Введите номер задачи цифрой или нажмите '⬅️ Назад'.")
# ---------- Действия с задачей ----------
@bot.message_handler(func=lambda m: user(m.chat.id).get("state") == "task_action")
def task_action(message):
    cid = str(message.chat.id)
    u = user(cid)
    tid = u.get("selected_task_id")
    if not tid:
        return

    task = next((t for t in u["tasks"] if t["id"] == tid), None)
    if not task:
        return

    if message.text == "✅ Выполнено":
        complete_task(task)
        bot.send_message(cid, f"Задача '{task['title']}' выполнена.", reply_markup=plan_menu())
    elif message.text == "🔕 Отключить напоминание":
        task["remind_at"] = None
        bot.send_message(cid, f"Напоминание для задачи '{task['title']}' отключено.", reply_markup=plan_menu())
    elif message.text == "⬅️ Назад":
        bot.send_message(cid, "Планирование задач:", reply_markup=plan_menu())

    u["state"] = None
    u.pop("selected_task_id", None)
    save_data()
# Фильтр и отображение задач, отметка выполненных — аналогично, добавляем кнопки "✅ Выполнено" и "🔕 Отключить напоминание"
# ----------------- POMODORO -----------------
pomodoro_timers = {}

def get_user_stats(cid):
    u = user(cid)
    return u["focus"]

@bot.message_handler(func=lambda m: m.text=="🍅 Фокус")
def focus_menu(message):
    cid=str(message.chat.id)
    u=user(cid)
    u["state"]=None
    u["focus_state"]=None
    save_data()
    kb=types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add("25","50")
    kb.add("⬅️ Главное меню")
    bot.send_message(cid,"Выберите длительность фокуса (минут):", reply_markup=kb)

@bot.message_handler(func=lambda m: m.text in ["25","50"])
def start_focus(message):
    cid=str(message.chat.id)
    minutes=int(message.text)
    u=user(cid)
    u["focus_state"]="running"
    save_data()
    kb=types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add("🛑 Завершить фокус","⬅️ Главное меню")
    bot.send_message(cid,f"Фокус начался — {minutes} мин", reply_markup=kb)

    if minutes==25:
        notify_points=[15,20]
    else:
        notify_points=[20,40,45]

    pomodoro_timers[cid]={"minutes_total":minutes,"minutes_left":minutes,"notify_points":notify_points,"thread":None}
    run_focus_timer(cid)

def run_focus_timer(cid):
    data=pomodoro_timers.get(cid)
    if not data or user(cid).get("focus_state")!="running":
        return
    if data["minutes_left"]<=0:
        finish_focus(cid)
        return
    minutes_passed=data["minutes_total"]-data["minutes_left"]
    if minutes_passed in data["notify_points"]:
        kb=types.ReplyKeyboardMarkup(resize_keyboard=True)
        kb.add("🛑 Завершить фокус","⬅️ Главное меню")
        bot.send_message(cid,f"⏱ Осталось {data['minutes_left']} мин",reply_markup=kb)
    data["minutes_left"]-=1
    t=threading.Timer(60,run_focus_timer,args=[cid])
    data["thread"]=t
    t.start()

@bot.message_handler(func=lambda m: m.text == "🛑 Завершить фокус")
def stop_focus(message):
    cid = str(message.chat.id)

    # Если таймер есть, останавливаем поток
    timer_data = pomodoro_timers.get(cid)
    if timer_data and timer_data.get("thread"):
        timer_data["thread"].cancel()

    # Завершаем фокус напрямую
    finish_focus(cid)

def finish_focus(cid):
    data = pomodoro_timers.pop(cid, None)
    minutes_done = data.get("minutes_total", 0) if data else 0

    stats = get_user_stats(cid)
    stats["sessions"] += 1
    stats["minutes"] += minutes_done

    user(cid)["focus_state"] = None
    save_data()

    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add("🍅 Новый фокус", "⬅️ Главное меню")
    bot.send_message(int(cid), "Фокус завершён! Что дальше?", reply_markup=kb)

@bot.message_handler(func=lambda m: m.text=="🍅 Новый фокус")
def new_focus(message):
    focus_menu(message)

# ----------------- STATS -----------------
@bot.message_handler(func=lambda m: m.text == "📊 Статистика")
def stats(message):
    cid = str(message.chat.id)
    u = user(cid)

    # Статистика настроений
    mood_stats = {}
    for d, m in u.get("moods", {}).items():
        mood_stats[m] = mood_stats.get(m, 0) + 1

    # Статистика фокуса
    focus_stats = u.get("focus", {"sessions": 0, "minutes": 0})

    text = (
        f"📊 Статистика\n\n"
        f"🍅 Фокус-сессий: {focus_stats['sessions']}\n"
        f"⏱ Минут фокуса: {focus_stats['minutes']}\n\n"
        "😊 Настроение:\n"
    )
    if mood_stats:
        for k,v in mood_stats.items():
            text += f"{k} — {v}\n"
    else:
        text += "Нет данных\n"

    bot.send_message(message.chat.id, text, reply_markup=main_menu())

# ---------------- RUN ----------------
print("Bot is running")
bot.infinity_polling()
