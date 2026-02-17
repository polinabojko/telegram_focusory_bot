from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from database import cursor
from datetime import date, timedelta

TASKS_PER_PAGE = 5

# ---------- МЕНЮ ----------

def tasks_menu(bot, message):
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("➕ Добавить", callback_data="add_task"))
    markup.add(InlineKeyboardButton("📋 Список", callback_data="tasks_page_0"))
    markup.add(InlineKeyboardButton("⬅ Назад", callback_data="main"))

    bot.edit_message_text(
        "📝 Управление задачами",
        message.chat.id,
        message.message_id,
        reply_markup=markup
    )


# ---------- ДОБАВЛЕНИЕ ----------

def ask_task_text(bot, call):
    msg = bot.send_message(call.message.chat.id, "Введите текст задачи:")
    bot.register_next_step_handler(msg, save_task_text, bot)


def save_task_text(message, bot):
    user_id = message.chat.id
    title = message.text

    markup = InlineKeyboardMarkup()
    markup.add(
        InlineKeyboardButton("Сегодня", callback_data=f"due_today|{title}"),
        InlineKeyboardButton("Завтра", callback_data=f"due_tomorrow|{title}")
    )
    markup.add(
        InlineKeyboardButton("Неделя", callback_data=f"due_week|{title}"),
        InlineKeyboardButton("Без срока", callback_data=f"due_none|{title}")
    )

    bot.send_message(user_id, "Выберите срок:", reply_markup=markup)


def save_task(user_id, title, due_type):
    today = date.today()

    if due_type == "today":
        due = today
    elif due_type == "tomorrow":
        due = today + timedelta(days=1)
    elif due_type == "week":
        due = today + timedelta(days=7)
    else:
        due = None

    cursor.execute(
        "INSERT INTO tasks (user_id, title, due_date) VALUES (%s, %s, %s)",
        (user_id, title, due)
    )


# ---------- СПИСОК ----------

def show_tasks(bot, message, page):
    user_id = message.chat.id
    today = date.today()

    cursor.execute("""
        SELECT id, title, due_date, completed
        FROM tasks
        WHERE user_id = %s
        ORDER BY
            completed ASC,
            CASE
                WHEN due_date IS NULL THEN 3
                WHEN due_date < %s THEN 0
                WHEN due_date = %s THEN 1
                ELSE 2
            END,
            due_date ASC
    """, (user_id, today, today))

    tasks = cursor.fetchall()

    start = page * TASKS_PER_PAGE
    end = start + TASKS_PER_PAGE
    page_tasks = tasks[start:end]

    text = "📋 Список задач:\n\n"

    markup = InlineKeyboardMarkup()

    for t in page_tasks:
        status = "✅" if t[3] else "▫"
        text += f"{status} {t[1]}\n"

        markup.add(
            InlineKeyboardButton("✔", callback_data=f"complete_{t[0]}"),
            InlineKeyboardButton("✏", callback_data=f"edit_{t[0]}"),
            InlineKeyboardButton("🗑", callback_data=f"delete_{t[0]}")
        )

    # пагинация
    nav = []
    if page > 0:
        nav.append(InlineKeyboardButton("⬅", callback_data=f"tasks_page_{page-1}"))
    if end < len(tasks):
        nav.append(InlineKeyboardButton("➡", callback_data=f"tasks_page_{page+1}"))
    if nav:
        markup.row(*nav)

    markup.add(InlineKeyboardButton("⬅ Назад", callback_data="tasks"))

    bot.edit_message_text(
        text,
        message.chat.id,
        message.message_id,
        reply_markup=markup
    )


# ---------- ДЕЙСТВИЯ ----------

def complete_task(task_id):
    cursor.execute(
        "UPDATE tasks SET completed = TRUE WHERE id = %s",
        (task_id,)
    )


def delete_task(task_id):
    cursor.execute(
        "DELETE FROM tasks WHERE id = %s",
        (task_id,)
    )


def edit_task(bot, call, task_id):
    msg = bot.send_message(call.message.chat.id, "Введите новый текст:")
    bot.register_next_step_handler(msg, update_task_text, bot, task_id)


def update_task_text(message, bot, task_id):
    cursor.execute(
        "UPDATE tasks SET title = %s WHERE id = %s",
        (message.text, task_id)
    )
    bot.send_message(message.chat.id, "Обновлено ✅")
