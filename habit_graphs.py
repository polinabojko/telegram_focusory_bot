import sqlite3
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
import os

DB = "database.db"


def get_last_30_days_data(user_id):
    conn = sqlite3.connect(DB)
    cur = conn.cursor()

    today = datetime.now().date()
    data = {}

    for i in range(30):
        day = today - timedelta(days=i)
        cur.execute("""
            SELECT COUNT(*) FROM habit_logs
            WHERE user_id=? AND date=?
        """, (user_id, str(day)))
        count = cur.fetchone()[0]
        data[str(day)] = count

    conn.close()
    return dict(sorted(data.items()))


def generate_bar_chart(user_id):
    data = get_last_30_days_data(user_id)

    dates = list(data.keys())
    values = list(data.values())

    plt.figure()
    plt.bar(dates, values)
    plt.xticks(rotation=90)
    plt.tight_layout()

    filename = f"bar_{user_id}.png"
    plt.savefig(filename)
    plt.close()

    return filename


def generate_heatmap(user_id):
    data = get_last_30_days_data(user_id)
    values = list(data.values())

    matrix = [values[i:i+7] for i in range(0, len(values), 7)]

    plt.figure()
    plt.imshow(matrix)
    plt.colorbar()
    plt.tight_layout()

    filename = f"heatmap_{user_id}.png"
    plt.savefig(filename)
    plt.close()

    return filename
