import matplotlib.pyplot as plt
from datetime import date, timedelta
from database import get_connection
import os
from telebot import types

def generate_month_graph(user_id):
    today = date.today()
    month_ago = today - timedelta(days=29)
    conn = get_connection()
    cursor = conn.cursor()

    # Получаем данные по привычкам
    cursor.execute("""
        SELECT marked_date FROM habit_logs
        WHERE user_id = %s AND marked_date >= %s
    """, (user_id, month_ago))
    habit_rows = cursor.fetchall()

    # Получаем данные по задачам
    cursor.execute("""
        SELECT created_at, completed FROM tasks
        WHERE user_id = %s AND created_at >= %s
    """, (user_id, month_ago))
    task_rows = cursor.fetchall()
    cursor.close()
    conn.close()

    days = []
    habit_counts = []
    task_counts = []

    for i in range(30):
        day = month_ago + timedelta(days=i)
        days.append(day.strftime("%d.%m"))

        habit_count = sum(1 for r in habit_rows if r[0] == day)
        habit_counts.append(habit_count)

        task_count = sum(1 for r in task_rows if r[0].date() == day and r[1])
        task_counts.append(task_count)

    # Создаём график
    plt.figure(figsize=(10, 4))
    plt.plot(days, habit_counts, label="Привычки", marker='o', color='tab:blue')
    plt.plot(days, task_counts, label="Выполненные задачи", marker='x', color='tab:green')
    plt.xticks(rotation=45)
    plt.title("Активность за последние 30 дней")
    plt.xlabel("Дата")
    plt.ylabel("Количество")
    plt.legend()
    plt.tight_layout()

    # Сохраняем файл
    filename = os.path.join(os.getcwd(), f"graph_{user_id}_{today}.png")
    plt.savefig(filename)
    plt.close()
    return filename


def send_month_graph(bot, user_id):
    """Отправка графика пользователю с кнопкой 'Главное меню'"""
    filename = generate_month_graph(user_id)

    with open(filename, "rb") as photo:
        bot.send_photo(user_id, photo)

    os.remove(filename)
