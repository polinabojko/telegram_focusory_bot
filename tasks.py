from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from database import cursor
from datetime import date

TASKS_PER_PAGE = 5

def tasks_menu(bot, message):
    markup = InlineKeyboardMarkup()
    markup.add(
        InlineKeyboardButton("➕ Добавить", callback_data="add_task")
    )
    markup.add(
        InlineKeyboardButton("📋 Список", callback_data="tasks_page_0")
    )
    markup.add(
        InlineKeyboardButton("⬅ Назад", callback_data="main")
    )

    bot.edit_message_text(
        "Задачи.",
        message.chat.id,
        message.message_id,
        reply_markup=markup
    )

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

    text = "Список задач:\n\n"

    for t in page_tasks:
        status = "✓" if t[3] else " "
        text += f"[{status}] {t[1]}\n"

    markup = InlineKeyboardMarkup()

    if page > 0:
        markup.add(
            InlineKeyboardButton("⬅", callback_data=f"tasks_page_{page-1}")
        )

    if end < len(tasks):
        markup.add(
            InlineKeyboardButton("➡", callback_data=f"tasks_page_{page+1}")
        )

    markup.add(
        InlineKeyboardButton("⬅ Назад", callback_data="tasks")
    )

    bot.edit_message_text(
        text,
        message.chat.id,
        message.message_id,
        reply_markup=markup
    )
