from datetime import datetime
from database import cursor, conn
from levels import add_xp
from config import XP_PER_HABIT


def create_habit(user_id, title):
    cursor.execute("""
        INSERT INTO habits (user_id, title)
        VALUES (?, ?)
    """, (user_id, title))
    conn.commit()


def get_active_habits(user_id):
    cursor.execute("""
        SELECT id, title, streak, last_done
        FROM habits
        WHERE user_id=? AND active=1
    """, (user_id,))
    return cursor.fetchall()


def complete_habit(user_id, habit_id):
    cursor.execute("""
        SELECT streak, last_done
        FROM habits
        WHERE id=? AND user_id=?
    """, (habit_id, user_id))

    row = cursor.fetchone()
    if not row:
        return False

    streak, last_done = row
    today = datetime.now().date()

    if last_done:
        last_done_date = datetime.fromisoformat(last_done).date()
        if (today - last_done_date).days == 1:
            streak += 1
        elif (today - last_done_date).days > 1:
            streak = 1
    else:
        streak = 1

    cursor.execute("""
        UPDATE habits
        SET streak=?, last_done=?
        WHERE id=?
    """, (streak, today.isoformat(), habit_id))

    conn.commit()
    add_xp(user_id, XP_PER_HABIT)
    return True


def deactivate_habit(user_id, habit_id):
    cursor.execute("""
        UPDATE habits
        SET active=0
        WHERE id=? AND user_id=?
    """, (habit_id, user_id))
    conn.commit()
