from telebot import types
from database import cursor, conn
from datetime import datetime, timedelta

def menu(bot, user_id):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("➕ Добавить", "📋 Список")
    markup.add("📅 Планирование", "🔙 Назад")
    bot.send_message(user_id, "Задачи.", reply_markup=markup)

def add_task(user_id, title, due):
    cursor.execute(
        "INSERT INTO tasks (user_id, title, due_date) VALUES (?, ?, ?)",
        (user_id, title, due)
    )
    conn.commit()

def get_tasks(user_id):
    return cursor.execute("""
        SELECT id, title, due_date, completed
        FROM tasks
        WHERE user_id=?
        ORDER BY completed, due_date
    """, (user_id,)).fetchall()
