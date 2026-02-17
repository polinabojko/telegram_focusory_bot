import matplotlib.pyplot as plt
from datetime import date, timedelta
from database import cursor
import os

def generate_month_graph(user_id):
    today = date.today()
    month_ago = today - timedelta(days=29)

    # Привычки
    cursor.execute("""
        SELECT marked_date FROM habit_logs
        WHERE user_id = %s AND marked_date >= %s
    """, (user_id, month_ago))
    habit_rows = cursor.fetchall()

    # Задачи
    cursor.execute("""
        SELECT created_at, completed FROM tasks
        WHERE user_id = %s AND created_at >= %s
    """, (user_id, month_ago))
    task_rows = cursor.fetchall()

    days = []
    habit_counts = []
    task_counts = []

    for i in range(30):
        day = month_ago + timedelta(days=i)
        days.append(day.strftime("%d"))

        habit_count = sum(1 for r in habit_rows if r[0] == day)
        habit_counts.append(habit_count)

        task_count = sum(1 for r in task_rows if r[0].date() == day and r[1])
        task_counts.append(task_count)

    plt.figure(figsize=(10,4))
    plt.plot(days, habit_counts, label="Привычки")
    plt.plot(days, task_counts, label="Выполненные задачи")
    plt.xticks(rotation=45)
    plt.title("Активность за 30 дней")
    plt.legend()
    plt.tight_layout()

    filename = os.path.join(os.getcwd(), f"graph_{user_id}.png")
    plt.savefig(filename)
    plt.close()
    return filename
