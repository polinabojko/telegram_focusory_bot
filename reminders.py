# reminders.py
import pytz
from datetime import datetime
from database import get_connection

def send_morning_reminders(bot):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT user_id, timezone FROM users WHERE reminders_enabled = TRUE")
    users = cursor.fetchall()

    for user_id, tz_str in users:
        try:
            tz = pytz.timezone(tz_str)
        except:
            tz = pytz.UTC

        now = datetime.now(tz)
        if now.time().hour != 8:
            continue

        cursor.execute("SELECT title FROM tasks WHERE user_id = %s AND due_date = CURRENT_DATE AND completed = FALSE", (user_id,))
        tasks_today = cursor.fetchall()

        cursor.execute("SELECT title, streak FROM habits WHERE user_id = %s", (user_id,))
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
