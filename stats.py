import matplotlib.pyplot as plt
from database import cursor
from datetime import datetime
import io


def generate_focus_graph(user_id):
    cursor.execute("""
        SELECT completed_at, minutes
        FROM focus_sessions
        WHERE user_id=?
    """, (user_id,))

    rows = cursor.fetchall()

    dates = {}
    for r in rows:
        date = datetime.fromisoformat(r[0]).date()
        dates[date] = dates.get(date, 0) + r[1]

    x = list(dates.keys())
    y = list(dates.values())

    plt.figure()
    plt.plot(x, y)
    plt.xlabel("Дата")
    plt.ylabel("Минуты фокуса")

    img = io.BytesIO()
    plt.savefig(img, format="png")
    img.seek(0)
    plt.close()

    return img
