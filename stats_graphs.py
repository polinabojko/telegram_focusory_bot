import matplotlib.pyplot as plt
from datetime import date, timedelta
from database import get_connection
import os
import uuid


def generate_month_graph(user_id):
    today = date.today()
    month_ago = today - timedelta(days=29)

    conn = get_connection()
    cursor = conn.cursor()

    try:
        # Привычки
        cursor.execute("""
            SELECT marked_date
            FROM habit_logs
            WHERE user_id = %s AND marked_date >= %s
        """, (user_id, month_ago))
        habit_rows = cursor.fetchall()

        # Задачи
        cursor.execute("""
            SELECT created_at, completed
            FROM tasks
            WHERE user_id = %s AND created_at >= %s
        """, (user_id, month_ago))
        task_rows = cursor.fetchall()

    finally:
        cursor.close()
        conn.close()

    # Подготовка данных
    days = []
    habit_counts = []
    task_counts = []

    for i in range(30):
        day = month_ago + timedelta(days=i)
        days.append(day.strftime("%d.%m"))

        # Привычки
        habit_count = sum(1 for r in habit_rows if r[0] == day)
        habit_counts.append(habit_count)

        # Задачи (универсально для DATE и TIMESTAMP)
        count = 0
        for r in task_rows:
            task_date = r[0] if isinstance(r[0], date) else r[0].date()
            if task_date == day and r[1]:
                count += 1
        task_counts.append(count)

    # Построение графика
    plt.figure(figsize=(10, 4))
    plt.plot(days, habit_counts, label="Привычки", marker='o')
    plt.plot(days, task_counts, label="Выполненные задачи", marker='x')

    plt.xticks(rotation=45)
    plt.title("Активность за последние 30 дней")
    plt.xlabel("Дата")
    plt.ylabel("Количество")
    plt.legend()
    plt.tight_layout()

    # Уникальное имя файла
    filename = os.path.join(
        os.getcwd(),
        f"graph_{user_id}_{uuid.uuid4().hex}.png"
    )

    plt.savefig(filename)
    plt.close()

    return filename


def send_month_graph(bot, user_id):
    filename = generate_month_graph(user_id)

    try:
        with open(filename, "rb") as photo:
            bot.send_photo(user_id, photo)
    finally:
        if os.path.exists(filename):
            os.remove(filename)
