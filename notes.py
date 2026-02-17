from telebot import types
from database import cursor, conn

def menu(bot, user_id):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("➕ Добавить", "📋 Список")
    markup.add("🔙 Назад")
    bot.send_message(user_id, "Заметки.", reply_markup=markup)

def add_note(user_id, content):
    cursor.execute(
        "INSERT INTO notes (user_id, content) VALUES (?, ?)",
        (user_id, content)
    )
    conn.commit()
