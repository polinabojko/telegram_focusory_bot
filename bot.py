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
            "focus": {"sessions": 0, "minutes": 0},
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
    bot.send_message(message.chat.id, "Focusory — управление фокусом и задачами.", reply_markup=main_menu())

# ---------------- ПЛАН И НАПОМИНАНИЯ ----------------

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

# Фоновый цикл напоминаний
def reminder_loop():
    while True:
        now = datetime.now().strftime("%Y-%m-%d %H:%M")
        for cid, udata in all_users().items():
            for task in udata["tasks"]:
                if task.get("remind_at") == now:
                    bot.send_message(int(cid), f"⏰ Напоминание о задаче: {task['title']}")
                    task["remind_at"] = None
                    save_data()
        time.sleep(60)

threading.Thread(target=reminder_loop, daemon=True).start()

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

@bot.message_handler(func=lambda m: user(m.chat.id).get("state")=="task_done_select")
def task_done_select(message):
    cid = str(message.chat.id)
    u = user(cid)
    try:
        idx = int(message.text)-1
        task = u["last_task_list"][idx]
    except:
        bot.send_message(cid,"Введите корректный номер задачи.")
        return
    u["selected_task_id"] = task["id"]
    u["state"] = "task_action"
    save_data()
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add("✅ Выполнено","🔕 Отключить напоминание")
    kb.add("⬅️ Назад")
    bot.send_message(cid,f"Задача: {task['title']}", reply_markup=kb)

@bot.message_handler(func=lambda m: user(m.chat.id).get("state")=="task_action")
def task_action(message):
    cid = str(message.chat.id)
    u = user(cid)
    tid = u.get("selected_task_id")
    if not tid: return
    task = next((x for x in u["tasks"] if x["id"]==tid), None)
    if not task: return
    if message.text=="✅ Выполнено": complete_task(task); bot.send_message(cid,"Задача выполнена.",reply_markup=plan_menu())
    elif message.text=="🔕 Отключить напоминание": task["remind_at"]=None; bot.send_message(cid,"Напоминание отключено.",reply_markup=plan_menu())
    elif message.text=="⬅️ Назад": bot.send_message(cid,"Планирование задач:",reply_markup=plan_menu())
    u["state"]=None
    u.pop("selected_task_id",None)
    save_data()

# ---------------- POMODORO с перерывами ----------------

pomodoro_timers = {}  # таймеры фокуса/перерыва по chat_id

def get_user_stats(cid):
    return user(cid)["focus"]

# Меню выбора фокуса
@bot.message_handler(func=lambda m: m.text=="🍅 Фокус")
def focus_menu(message):
    cid = str(message.chat.id)
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add("25","50")
    kb.add("⬅️ Главное меню")
    bot.send_message(cid,"Выберите длительность фокуса (минут):",reply_markup=kb)

# Старт фокуса
@bot.message_handler(func=lambda m: m.text in ["25","50"])
def start_focus(message):
    cid = str(message.chat.id)
    minutes = int(message.text)
    user(cid)["focus_state"]="running"
    save_data()

    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add("🛑 Завершить фокус","⬅️ Главное меню")
    msg = bot.send_message(cid,f"Фокус начался — {minutes} мин",reply_markup=kb)

    # Контрольные минуты (через сколько осталось уведомлять)
    if minutes==25: notify_points=[15,20]  # через 10 и 5 мин
    elif minutes==50: notify_points=[20,40,45] # через 30,10,5 мин
    else: notify_points=[]

    pomodoro_timers[cid] = {
        "minutes_total": minutes,
        "minutes_left": minutes,
        "notify_points": notify_points,
        "thread": None,
        "message_id": msg.message_id,
        "type":"focus"
    }
    threading.Thread(target=run_timer, args=[cid], daemon=True).start()

# Универсальный таймер для фокуса/перерыва
def run_timer(cid):
    data = pomodoro_timers.get(cid)
    if not data: return
    state = user(cid).get("focus_state")
    if state not in ["running","break"]: return

    if data["minutes_left"] <= 0:
        if data["type"]=="focus":
            finish_focus(cid)
        else:
            finish_break(cid)
        return

    minutes_passed = data["minutes_total"] - data["minutes_left"]
    if minutes_passed in data["notify_points"]:
        kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
        if data["type"]=="focus":
            kb.add("🛑 Завершить фокус","⬅️ Главное меню")
            bot.send_message(cid,f"⏱ Осталось {data['minutes_left']} мин",reply_markup=kb)
        else:
            kb.add("⏭ Пропустить перерыв","🍅 Новый фокус","⬅️ Главное меню")
            bot.send_message(cid,f"⏱ Перерыв: {data['minutes_left']} мин осталось",reply_markup=kb)

    data["minutes_left"] -= 1
    threading.Timer(60, run_timer, args=[cid]).start()

# Завершение фокуса вручную
@bot.message_handler(func=lambda m: m.text=="🛑 Завершить фокус")
def stop_focus(message):
    cid = str(message.chat.id)
    user(cid)["focus_state"]="finished"
    tdata = pomodoro_timers.pop(cid,None)
    if tdata and tdata.get("thread"): tdata["thread"].cancel()
    finish_focus(cid)

# Завершение фокуса
def finish_focus(cid):
    data = pomodoro_timers.pop(cid,None)
    minutes_done = data.get("minutes_total",0) if data else 0
    stats = get_user_stats(cid)
    stats["sessions"] += 1
    stats["minutes"] += minutes_done
    user(cid)["focus_state"]=None
    save_data()
    # Начало перерыва
    if data["minutes_total"]==25:
        start_break(cid,5)
    elif data["minutes_total"]==50:
        start_break(cid,10)
    else:
        kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
        kb.add("🍅 Новый фокус","⬅️ Главное меню")
        bot.send_message(cid,"Фокус завершён! Что дальше?",reply_markup=kb)

# Старт перерыва
def start_break(cid,minutes):
    user(cid)["focus_state"]="break"
    save_data()
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add("⏭ Пропустить перерыв","🍅 Новый фокус")
    kb.add("⬅️ Главное меню")
    bot.send_message(cid,f"Перерыв {minutes} минут",reply_markup=kb)
    pomodoro_timers[cid] = {"minutes_total":minutes,"minutes_left":minutes,"notify_points":[],"type":"break"}
    threading.Thread(target=run_timer,args=[cid],daemon=True).start()

# Завершение перерыва автоматически
def finish_break(cid):
    pomodoro_timers.pop(cid,None)
    user(cid)["focus_state"]=None
    save_data()
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add("🍅 Новый фокус","⬅️ Главное меню")
    bot.send_message(cid,"Перерыв завершён! Можно начать новый фокус.",reply_markup=kb)

# Пропуск перерыва
@bot.message_handler(func=lambda m: m.text=="⏭ Пропустить перерыв")
def skip_break(message):
    cid = str(message.chat.id)
    pomodoro_timers.pop(cid,None)
    user(cid)["focus_state"]=None
    save_data()
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add("🍅 Новый фокус","⬅️ Главное меню")
    bot.send_message(cid,"Перерыв пропущен! Можно начать новый фокус.",reply_markup=kb)

# Новый фокус
@bot.message_handler(func=lambda m: m.text=="🍅 Новый фокус")
def new_focus(message):
    focus_menu(message)


# ---------------- СТАТИСТИКА ----------------

@bot.message_handler(func=lambda m: m.text=="📊 Статистика")
def stats(message):
    cid = str(message.chat.id)
    u = user(cid)
    mood_stats = {}
    for m in u["moods"].values(): mood_stats[m]=mood_stats.get(m,0)+1
    text = f"📊 Статистика\n\n🍅 Фокус-сессий: {u['focus']['sessions']}\n⏱ Минут фокуса: {u['focus']['minutes']}\n\n😊 Настроение:\n"
    for k,v in mood_stats.items(): text+=f"{k} — {v}\n"
    bot.send_message(cid,text,reply_markup=main_menu())

# ---------------- RUN ----------------
print("Bot is running")
bot.infinity_polling()
