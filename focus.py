import time
from datetime import datetime
from database import cursor, conn
from redis_storage import set_focus, clear_focus
from config import XP_PER_FOCUS_MIN, POMODORO_BREAK
from levels import add_xp

def start_focus(user_id, minutes):
    end_time = int(time.time()) + minutes * 60
    set_focus(user_id, end_time)
    return end_time

def stop_focus(user_id):
    clear_focus(user_id)

def complete_focus(user_id, minutes):
    cursor.execute(
        "INSERT INTO focus_sessions (user_id, minutes, completed_at) VALUES (?, ?, ?)",
        (user_id, minutes, datetime.now().isoformat())
    )
    conn.commit()

    add_xp(user_id, minutes * XP_PER_FOCUS_MIN)

def get_break_message():
    return f"☕ Перерыв {POMODORO_BREAK} минут!"
