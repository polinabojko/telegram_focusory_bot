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

from database import cursor


def habit_statistics(user_id):
    cursor.execute("""
        SELECT COUNT(*) FROM habit_logs
        WHERE user_id = %s
    """, (user_id,))
    total_marks = cursor.fetchone()[0]

    cursor.execute("""
        SELECT MAX(streak) FROM habits
        WHERE user_id = %s
    """, (user_id,))
    best_streak = cursor.fetchone()[0] or 0

    return total_marks, best_streak

total, best = habit_statistics(message.chat.id)

text += f"\n\n🔥 Всего отметок: {total}"
text += f"\n🏆 Лучший стрик: {best}"
