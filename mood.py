# mood.py
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from database import get_connection
from datetime import date

MOOD_OPTIONS = ["😃", "🙂", "😐", "😔", "😡"]

def mood_menu(bot, message):
    markup = InlineKeyboardMarkup()
    for m in MOOD_OPTIONS:
        markup.add(InlineKeyboardButton(m, callback_data=f"mood_{m}"))
    markup.add(InlineKeyboardButton("⬅ Назад", callback_data="main"))

    bot.edit_message_text(
        "😊 Выберите настроение за сегодня:",
        message.chat.id,
        message.message_id,
        reply_markup=markup
    )

def save_mood(user_id, mood):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO mood (user_id, mood, created_at) VALUES (%s, %s, CURRENT_DATE)",
        (user_id, mood)
    )
    cursor.close()
    conn.close()
