import matplotlib.pyplot as plt
from datetime import date, timedelta
from database import cursor
import os


def generate_month_graph(user_id):
    today = date.today()
    month_ago = today - timedelta(days=29)

    cursor.execute("""
        SELECT marked_date
        FROM habit_logs
        WHERE user_id = %s
        AND marked_date >= %s
    """, (user_id, month_ago))

    rows = cursor.fetchall()

    days = []
    values = []

    for i in range(30):
        day = month_ago + timedelta(days=i)
        count = sum(1 for r in rows if r[0] == day)
        days.append(day.strftime("%d"))
        values.append(count)

    plt.figure(figsize=(10,4))
    plt.plot(days, values)
    plt.xticks(rotation=45)
    plt.title("Активность за 30 дней")
    plt.tight_layout()

    filename = f"graph_{user_id}.png"
    plt.savefig(filename)
    plt.close()

    return filename
