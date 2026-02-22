from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from database import get_connection
from datetime import date, timedelta

user_temp_tasks = {}
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
    title = message.text.strip()

    if not title:
        bot.send_message(user_id, "Текст задачи не может быть пустым.")
        return

    user_temp_tasks[user_id] = title

    markup = InlineKeyboardMarkup()
    markup.add(
        InlineKeyboardButton("Сегодня", callback_data="due_today"),
        InlineKeyboardButton("Завтра", callback_data="due_tomorrow")
    )
    markup.add(
        InlineKeyboardButton("Неделя", callback_data="due_week"),
        InlineKeyboardButton("Месяц", callback_data="due_month")
    )
    markup.add(
        InlineKeyboardButton("Без срока", callback_data="due_none")
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
    elif due_type == "month":
        due = today + timedelta(days=30)
    else:
        due = None

    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "INSERT INTO tasks (user_id, title, due_date, completed) VALUES (%s, %s, %s, FALSE)",
            (user_id, title, due)
        )
        conn.commit()
    finally:
        cursor.close()
        conn.close()


# ---------- СПИСОК ----------
def show_tasks(bot, message, page):
    user_id = message.chat.id
    today = date.today()
    week_later = today + timedelta(days=7)
    month_later = today + timedelta(days=30)

    conn = get_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("""
            SELECT id, title, due_date, completed
            FROM tasks
            WHERE user_id = %s
            ORDER BY
                completed ASC,
                CASE
                    WHEN due_date IS NULL THEN 5
                    WHEN due_date < %s THEN 0
                    WHEN due_date = %s THEN 1
                    WHEN due_date <= %s THEN 2
                    WHEN due_date <= %s THEN 3
                    ELSE 4
                END,
                due_date ASC
        """, (user_id, today, today, week_later, month_later))

        tasks_list = cursor.fetchall()
    finally:
        cursor.close()
        conn.close()

    start = page * TASKS_PER_PAGE
    end = start + TASKS_PER_PAGE
    page_tasks = tasks_list[start:end]

    text = "📋 Список задач:\n\n"
    markup = InlineKeyboardMarkup()

    if not page_tasks:
        text += "Пока задач нет."

    for t in page_tasks:
        task_id, title, due_date, completed = t

        status = "✅" if completed else "▫"

        if due_date:
            if not isinstance(due_date, date):
                due_date = due_date.date()
            due_str = due_date.strftime("%d.%m")
        else:
            due_str = "Без срока"

        text += f"{status} {title} — {due_str}\n"

        markup.add(
            InlineKeyboardButton("✔", callback_data=f"complete_task_{task_id}"),
            InlineKeyboardButton("✏", callback_data=f"edit_task_{task_id}"),
            InlineKeyboardButton("🗑", callback_data=f"delete_task_{task_id}")
        )

    # пагинация
    nav = []
    if page > 0:
        nav.append(InlineKeyboardButton("⬅", callback_data=f"tasks_page_{page-1}"))
    if end < len(tasks_list):
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
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "UPDATE tasks SET completed = TRUE WHERE id = %s",
            (task_id,)
        )
        conn.commit()
    finally:
        cursor.close()
        conn.close()


def delete_task(task_id):
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "DELETE FROM tasks WHERE id = %s",
            (task_id,)
        )
        conn.commit()
    finally:
        cursor.close()
        conn.close()


def edit_task(bot, call, task_id):
    msg = bot.send_message(call.message.chat.id, "Введите новый текст:")
    bot.register_next_step_handler(msg, update_task_text, bot, task_id)


def update_task_text(message, bot, task_id):
    new_text = message.text.strip()
    if not new_text:
        bot.send_message(message.chat.id, "Текст не может быть пустым.")
        return

    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "UPDATE tasks SET title = %s WHERE id = %s",
            (new_text, task_id)
        )
        conn.commit()
    finally:
        cursor.close()
        conn.close()

    bot.send_message(message.chat.id, "Обновлено ✅")
