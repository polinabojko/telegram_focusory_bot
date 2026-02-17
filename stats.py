from telebot import types
from database import cursor
from datetime import datetime, timedelta

def show(bot, user_id):
    week_ago = datetime.now() - timedelta(days=7)

    completed = cursor.execute("""
        SELECT COUNT(*) FROM tasks
        WHERE user_id=? AND completed=1
        AND created_at >= ?
    """, (user_id, week_ago)).fetchone()[0]

    bot.send_message(
        user_id,
        f"Статистика за 7 дней.\n\nВыполнено задач: {completed}"
    )

def mood_menu(bot, user_id):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("😃", "🙂", "😐", "😔", "😡")
    markup.add("🔙 Назад")
    bot.send_message(user_id, "Оцените день.", reply_markup=markup)
