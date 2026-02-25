# reminders.py
from datetime import datetime
from database import get_connection

def send_morning_reminders(bot):
    print("REMINDER CHECK", datetime.utcnow())
    now = datetime.utcnow()
    today = now.date()

    # Ждём пока наступит 03:00 UTC
    if now.hour < 3:
        return

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT user_id, last_reminder_date
        FROM users
        WHERE reminders_enabled = TRUE
    """)
    users = cursor.fetchall()

    for user_id, last_date in users:

        # Если уже отправляли сегодня — пропускаем
        if last_date == today:
            continue

        # --- Задачи ---
        cursor.execute("""
            SELECT title FROM tasks
            WHERE user_id = %s
            AND due_date = CURRENT_DATE
            AND completed = FALSE
        """, (user_id,))
        tasks_today = cursor.fetchall()

        # --- Привычки ---
        cursor.execute("""
            SELECT title, streak FROM habits
            WHERE user_id = %s
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

        # Запоминаем, что сегодня уже отправили
        cursor.execute("""
            UPDATE users
            SET last_reminder_date = %s
            WHERE user_id = %s
        """, (today, user_id))

    conn.commit()
    cursor.close()
    conn.close()
