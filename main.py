import os
import telebot
import sqlite3
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from dotenv import load_dotenv

load_dotenv()
TOKEN = os.getenv("BOT_TOKEN")

bot = telebot.TeleBot(TOKEN)

# ================= MEMORY =================

user_states = {}
task_pages = {}
TASKS_PER_PAGE = 5

# ================= DATABASE =================

conn = sqlite3.connect("database.db", check_same_thread=False)
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS tasks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    title TEXT,
    due_date TEXT,
    done INTEGER DEFAULT 0,
    created_at TEXT
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS habits (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    title TEXT,
    streak INTEGER DEFAULT 0,
    last_done TEXT
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS notes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    content TEXT,
    created_at TEXT
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS mood (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    mood_value INTEGER,
    created_at TEXT
)
""")

conn.commit()

# ================= MENU =================

def main_menu():
    kb = InlineKeyboardMarkup()
    kb.add(InlineKeyboardButton("📋 Задачи", callback_data="tasks"))
    kb.add(InlineKeyboardButton("💪 Привычки", callback_data="habits"))
    kb.add(InlineKeyboardButton("🧠 Фокус", callback_data="focus"))
    kb.add(InlineKeyboardButton("📝 Заметки", callback_data="notes"))
    kb.add(InlineKeyboardButton("😊 Настроение", callback_data="mood"))
    kb.add(InlineKeyboardButton("📊 Статистика", callback_data="stats"))
    return kb

@bot.message_handler(commands=['start'])
def start(message):
    bot.send_message(message.chat.id, "Главное меню:", reply_markup=main_menu())

# ================= TASKS =================

def show_tasks(user_id, page=0, message_id=None, period="all"):
    today = datetime.now().date()
    week = today + timedelta(days=7)

    query = """
    SELECT id, title, due_date FROM tasks
    WHERE user_id=? AND done=0
    """

    params = [user_id]

    if period == "today":
        query += " AND date(due_date)=date(?)"
        params.append(str(today))
    elif period == "week":
        query += " AND date(due_date)<=date(?)"
        params.append(str(week))

    query += """
    ORDER BY
        CASE
            WHEN date(due_date) < date(?) THEN 0
            WHEN date(due_date) = date(?) THEN 1
            WHEN date(due_date) <= date(?) THEN 2
            ELSE 3
        END,
        date(due_date) ASC
    """

    params.extend([str(today), str(today), str(week)])

    cursor.execute(query, tuple(params))
    tasks = cursor.fetchall()

    if not tasks:
        bot.send_message(user_id, "Нет задач.")
        return

    total_pages = (len(tasks)-1)//TASKS_PER_PAGE
    page = max(0, min(page, total_pages))
    task_pages[user_id] = page

    start = page*TASKS_PER_PAGE
    page_tasks = tasks[start:start+TASKS_PER_PAGE]

    text = f"📋 Задачи ({page+1}/{total_pages+1})\n\n"
    for t in page_tasks:
        text += f"• {t[1]}\n"

    kb = InlineKeyboardMarkup()
    for t in page_tasks:
        kb.add(
            InlineKeyboardButton("✅", callback_data=f"done_{t[0]}"),
            InlineKeyboardButton("🗑", callback_data=f"delete_{t[0]}")
        )

    nav = []
    if page>0:
        nav.append(InlineKeyboardButton("⬅", callback_data="prev"))
    if page<total_pages:
        nav.append(InlineKeyboardButton("➡", callback_data="next"))
    if nav:
        kb.row(*nav)

    kb.add(InlineKeyboardButton("➕ Добавить", callback_data="add_task"))
    kb.add(InlineKeyboardButton("📅 Сегодня", callback_data="today"))
    kb.add(InlineKeyboardButton("📆 Неделя", callback_data="week"))
    kb.add(InlineKeyboardButton("📋 Все", callback_data="tasks"))
    kb.add(InlineKeyboardButton("⬅ Назад", callback_data="back"))

    if message_id:
        bot.edit_message_text(text, user_id, message_id, reply_markup=kb)
    else:
        bot.send_message(user_id, text, reply_markup=kb)

@bot.callback_query_handler(func=lambda c: c.data in ["tasks","today","week"])
def open_tasks(call):
    period = "all"
    if call.data=="today": period="today"
    if call.data=="week": period="week"
    show_tasks(call.from_user.id, 0, call.message.message_id, period)

@bot.callback_query_handler(func=lambda c: c.data=="add_task")
def add_task(call):
    user_states[call.from_user.id] = "add_task"
    bot.send_message(call.from_user.id,"Введите текст задачи:")

@bot.message_handler(func=lambda m: user_states.get(m.from_user.id)=="add_task")
def save_task(message):
    cursor.execute("INSERT INTO tasks (user_id,title,due_date,created_at) VALUES (?,?,?,?)",
                   (message.from_user.id,message.text,str(datetime.now().date()),datetime.now().isoformat()))
    conn.commit()
    user_states.pop(message.from_user.id,None)
    bot.send_message(message.chat.id,"Добавлено ✅")

@bot.callback_query_handler(func=lambda c:c.data.startswith("done_"))
def done(call):
    task_id=c.data.split("_")[1]
    cursor.execute("UPDATE tasks SET done=1 WHERE id=?", (task_id,))
    conn.commit()
    show_tasks(call.from_user.id,task_pages.get(call.from_user.id,0),call.message.message_id)

@bot.callback_query_handler(func=lambda c:c.data.startswith("delete_"))
def delete(call):
    task_id=c.data.split("_")[1]
    cursor.execute("DELETE FROM tasks WHERE id=?", (task_id,))
    conn.commit()
    show_tasks(call.from_user.id,task_pages.get(call.from_user.id,0),call.message.message_id)

@bot.callback_query_handler(func=lambda c:c.data=="next")
def next_page(call):
    show_tasks(call.from_user.id,task_pages.get(call.from_user.id,0)+1,call.message.message_id)

@bot.callback_query_handler(func=lambda c:c.data=="prev")
def prev_page(call):
    show_tasks(call.from_user.id,task_pages.get(call.from_user.id,0)-1,call.message.message_id)

# ================= HABITS =================

@bot.callback_query_handler(func=lambda c:c.data=="habits")
def habits(call):
    cursor.execute("SELECT id,title,streak,last_done FROM habits WHERE user_id=?",(call.from_user.id,))
    rows=cursor.fetchall()

    text="💪 Привычки:\n\n"
    for h in rows:
        text+=f"{h[1]} 🔥{h[2]}\n"

    kb=InlineKeyboardMarkup()
    kb.add(InlineKeyboardButton("➕ Добавить",callback_data="add_habit"))
    kb.add(InlineKeyboardButton("⬅ Назад",callback_data="back"))

    bot.edit_message_text(text,call.message.chat.id,call.message.message_id,reply_markup=kb)

@bot.callback_query_handler(func=lambda c:c.data=="add_habit")
def add_habit(call):
    user_states[call.from_user.id]="add_habit"
    bot.send_message(call.from_user.id,"Введите название привычки:")

@bot.message_handler(func=lambda m:user_states.get(m.from_user.id)=="add_habit")
def save_habit(message):
    cursor.execute("INSERT INTO habits (user_id,title) VALUES (?,?)",(message.from_user.id,message.text))
    conn.commit()
    user_states.pop(message.from_user.id,None)
    bot.send_message(message.chat.id,"Привычка добавлена 💪")

# ================= FOCUS =================

@bot.callback_query_handler(func=lambda c:c.data=="focus")
def focus(call):
    end=datetime.now()+timedelta(minutes=25)
    bot.edit_message_text("Фокус 25 минут запущен ⏳\nНапиши /check чтобы узнать остаток.",
                          call.message.chat.id,call.message.message_id,reply_markup=main_menu())
    user_states[call.from_user.id]=end

@bot.message_handler(commands=["check"])
def check_focus(message):
    end=user_states.get(message.from_user.id)
    if isinstance(end,datetime):
        diff=end-datetime.now()
        if diff.total_seconds()>0:
            mins=int(diff.total_seconds()//60)
            bot.send_message(message.chat.id,f"Осталось {mins} минут")
        else:
            bot.send_message(message.chat.id,"Фокус завершён ✅")
            user_states.pop(message.from_user.id,None)
    else:
        bot.send_message(message.chat.id,"Фокус не запущен.")

# ================= NOTES =================

@bot.callback_query_handler(func=lambda c:c.data=="notes")
def notes(call):
    cursor.execute("SELECT content FROM notes WHERE user_id=?",(call.from_user.id,))
    rows=cursor.fetchall()

    text="📝 Заметки:\n\n"
    for n in rows:
        text+=f"- {n[0]}\n"

    kb=InlineKeyboardMarkup()
    kb.add(InlineKeyboardButton("➕ Добавить",callback_data="add_note"))
    kb.add(InlineKeyboardButton("⬅ Назад",callback_data="back"))

    bot.edit_message_text(text,call.message.chat.id,call.message.message_id,reply_markup=kb)

@bot.callback_query_handler(func=lambda c:c.data=="add_note")
def add_note(call):
    user_states[call.from_user.id]="add_note"
    bot.send_message(call.from_user.id,"Введите текст заметки:")

@bot.message_handler(func=lambda m:user_states.get(m.from_user.id)=="add_note")
def save_note(message):
    cursor.execute("INSERT INTO notes (user_id,content,created_at) VALUES (?,?,?)",
                   (message.from_user.id,message.text,datetime.now().isoformat()))
    conn.commit()
    user_states.pop(message.from_user.id,None)
    bot.send_message(message.chat.id,"Заметка сохранена 📝")

# ================= MOOD =================

@bot.callback_query_handler(func=lambda c:c.data=="mood")
def mood(call):
    kb=InlineKeyboardMarkup()
    for i in range(1,6):
        kb.add(InlineKeyboardButton(str(i),callback_data=f"mood_{i}"))
    kb.add(InlineKeyboardButton("⬅ Назад",callback_data="back"))
    bot.edit_message_text("Оцени настроение от 1 до 5:",call.message.chat.id,call.message.message_id,reply_markup=kb)

@bot.callback_query_handler(func=lambda c:c.data.startswith("mood_"))
def save_mood(call):
    val=int(call.data.split("_")[1])
    cursor.execute("INSERT INTO mood (user_id,mood_value,created_at) VALUES (?,?,?)",
                   (call.from_user.id,val,datetime.now().isoformat()))
    conn.commit()
    bot.answer_callback_query(call.id,"Сохранено 😊")

# ================= STATS =================

@bot.callback_query_handler(func=lambda c:c.data=="stats")
def stats(call):
    cursor.execute("SELECT date(created_at),COUNT(*) FROM tasks WHERE user_id=? GROUP BY date(created_at)",
                   (call.from_user.id,))
    rows=cursor.fetchall()

    if not rows:
        bot.send_message(call.from_user.id,"Нет данных.")
        return

    dates=[r[0] for r in rows]
    counts=[r[1] for r in rows]

    plt.figure()
    plt.plot(dates,counts)
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.savefig("stats.png")
    plt.close()

    bot.send_photo(call.from_user.id,open("stats.png","rb"))

# ================= BACK =================

@bot.callback_query_handler(func=lambda c:c.data=="back")
def back(call):
    bot.edit_message_text("Главное меню:",call.message.chat.id,call.message.message_id,reply_markup=main_menu())

# ================= RUN =================

bot.infinity_polling(skip_pending=True)
