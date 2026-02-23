# reminders.py
from datetime import datetime
from database import get_connection

def send_morning_reminders(bot):
    """Отправляет всем пользователям ежедневное уведомление в 3:00 UTC"""
    now = datetime.utcnow()
    if now.hour != 3:  # проверяем, что сейчас 3:00 UTC
        return

    conn = get_connection()
    cursor = conn.cursor()

    # Берём всех пользователей
    cursor.execute("SELECT id FROM users")
    users = cursor.fetchall()

    for (user_id,) in users:
        # Задачи на сегодня
        cursor.execute("""
            SELECT title FROM tasks
            WHERE user_id = %s AND due_date = CURRENT_DATE AND completed = FALSE
        """, (user_id,))
        tasks_today = cursor.fetchall()

        # Привычки
        cursor.execute("""
            SELECT title, streak FROM habits WHERE user_id = %s
        """, (user_id,))
        habits_list = cursor.fetchall()

        text = "☀ Доброе утро!\n\n"

        if tasks_today:
            text += "📋 Задачи на сегодня:\n"
            for t in tasks_today:
                text += f"▫ {t[0]}\n"
        else:
            text += "📋 Сегодня задач нет 🎉\n"

        if habits_list:
            text += "\n🔥 Привычки:\n"
            for h in habits_list:
                text += f"{h[0]} — {h[1]} дней подряд\n"
        else:
            text += "\n🔥 Привычек нет\n"

        bot.send_message(user_id, text)

    cursor.close()
    conn.close()
