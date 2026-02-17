from telebot import types
from database import cursor, conn
from datetime import datetime

def menu(bot, user_id):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("➕ Добавить", "📌 Список")
    markup.add("🔙 Назад")
    bot.send_message(user_id, "Привычки.", reply_markup=markup)

def add_habit(user_id, title):
    cursor.execute(
        "INSERT INTO habits (user_id, title) VALUES (?, ?)",
        (user_id, title)
    )
    conn.commit()
