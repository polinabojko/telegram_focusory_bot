from database import cursor
from datetime import date, timedelta
from stats_graphs import generate_month_graph
import os

def check_streak_reset(user_id):
    """Сбрасывает стрик привычки, если пропущен день"""
    cursor.execute("SELECT id, last_marked FROM habits WHERE user_id = %s", (user_id,))
    habits = cursor.fetchall()
    today = date.today()
    for habit_id, last_marked in habits:
        if last_marked and last_marked < today - timedelta(days=1):
            cursor.execute("UPDATE habits SET streak = 0 WHERE id = %s", (habit_id,))

def send_stats(bot, message):
    """Отправляет пользователю статистику за 30 дней"""
    user_id = message.chat.id
    check_streak_reset(user_id)

    # ------------------------
    # Задачи
    # ------------------------
    cursor.execute("SELECT COUNT(*) FROM tasks WHERE user_id = %s", (user_id,))
    total_tasks = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM tasks WHERE user_id = %s AND completed = TRUE", (user_id,))
    completed_tasks = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM tasks WHERE user_id = %s AND created_at >= CURRENT_DATE - INTERVAL '30 days'", (user_id,))
    month_tasks = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM tasks WHERE user_id = %s AND completed = TRUE AND created_at >= CURRENT_DATE - INTERVAL '30 days'", (user_id,))
    month_completed = cursor.fetchone()[0]

    # ------------------------
    # Привычки
    # ------------------------
    cursor.execute("SELECT COUNT(*) FROM habit_logs WHERE user_id = %s", (user_id,))
    total_marks = cursor.fetchone()[0]

    cursor.execute("SELECT MAX(streak) FROM habits WHERE user_id = %s", (user_id,))
    best_streak = cursor.fetchone()[0] or 0

    cursor.execute("SELECT COUNT(*) FROM habit_logs WHERE user_id = %s AND marked_date >= CURRENT_DATE - INTERVAL '30 days'", (user_id,))
    month_marks = cursor.fetchone()[0]

    # ------------------------
    # Настроение
    # ------------------------
    cursor.execute("SELECT mood FROM mood WHERE user_id = %s AND created_at >= CURRENT_DATE - INTERVAL '30 days'", (user_id,))
    moods = [row[0] for row in cursor.fetchall()]
    mood_map = {"😃":5, "🙂":4, "😐":3, "😔":2, "😡":1}
    if moods:
        avg = sum(mood_map.get(m, 3) for m in moods) / len(moods)
        avg_mood_value = round(avg)
        reverse_map = {v:k for k,v in mood_map.items()}
        avg_mood = reverse_map.get(avg_mood_value, "—")
    else:
        avg_mood = "—"

    # ------------------------
    # Фокус
    # ------------------------
    #cursor.execute("SELECT COUNT(*) FROM focus_logs WHERE user_id = %s", (user_id,))
    #total_focus = cursor.fetchone()[0]

    #cursor.execute("SELECT COUNT(*) FROM focus_logs WHERE user_id = %s AND completed_at >= CURRENT_DATE - INTERVAL '30 days'", (user_id,))
    #month_focus = cursor.fetchone()[0]

    # ------------------------
    # Вывод
    # ------------------------
    text = f"""📊 Статистика за 30 дней

📝 Задачи:
Всего: {total_tasks}
Выполнено: {completed_tasks}
За 30 дней: {month_tasks}
Выполнено за 30 дней: {month_completed}

🔁 Привычки:
Всего отметок: {total_marks}
За 30 дней: {month_marks}
Лучший стрик: {best_streak}

😊 Настроение:
Среднее за 30 дней: {avg_mood}
"""
#🎯 Фокус:
#Всего сессий: {total_focus}
#За 30 дней: {month_focus}
    bot.send_message(user_id, text)

    # ------------------------
    # График
    # ------------------------
    filename = generate_month_graph(user_id)
    with open(filename, "rb") as photo:
        bot.send_photo(user_id, photo)
    os.remove(filename)
