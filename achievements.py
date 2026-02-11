from datetime import datetime
import sqlite3

DB = "database.db"

ACHIEVEMENTS = {
    "first_habit": {
        "title": "Первая привычка",
        "desc": "Вы создали свою первую привычку"
    },
    "streak_7": {
        "title": "7 дней подряд",
        "desc": "Привычка выполнялась 7 дней подряд"
    },
    "streak_30": {
        "title": "30 дней дисциплины",
        "desc": "30 дней без пропуска"
    },
    "first_task": {
        "title": "Первая выполненная задача",
        "desc": "Вы закрыли первую задачу"
    },
    "focus_10": {
        "title": "10 фокус-сессий",
        "desc": "Вы провели 10 фокус-сессий"
    }
}


def unlock(user_id, code, bot):
    conn = sqlite3.connect(DB)
    cur = conn.cursor()

    cur.execute("SELECT id FROM achievements WHERE user_id=? AND code=?", (user_id, code))
    if cur.fetchone():
        conn.close()
        return

    cur.execute(
        "INSERT INTO achievements (user_id, code, unlocked_at) VALUES (?, ?, ?)",
        (user_id, code, datetime.now().isoformat())
    )
    conn.commit()
    conn.close()

    ach = ACHIEVEMENTS[code]

    bot.send_message(
        user_id,
        f"🏆 Новое достижение!\n\n"
        f"✨ {ach['title']}\n"
        f"{ach['desc']}"
    )
