from datetime import datetime, timedelta
from database import cursor, conn
from levels import add_xp
from config import XP_PER_TASK


# -------- СОЗДАНИЕ --------
def create_task(user_id, title, period="today"):
    due_date = None
    today = datetime.now()

    if period == "today":
        due_date = today.date().isoformat()
    elif period == "week":
        due_date = (today + timedelta(days=7)).date().isoformat()
    elif period == "month":
        due_date = (today + timedelta(days=30)).date().isoformat()

    cursor.execute("""
        INSERT INTO tasks (user_id, title, due_date, created_at)
        VALUES (?, ?, ?, ?)
    """, (user_id, title, due_date, datetime.now().isoformat()))

    conn.commit()


# -------- ПОЛУЧЕНИЕ --------
def get_tasks(user_id, filter_type="all"):
    query = "SELECT id, title, due_date FROM tasks WHERE user_id=? AND done=0"
    params = [user_id]

    today = datetime.now().date()

    if filter_type == "today":
        query += " AND due_date=?"
        params.append(today.isoformat())

    elif filter_type == "week":
        week_end = today + timedelta(days=7)
        query += " AND due_date BETWEEN ? AND ?"
        params.extend([today.isoformat(), week_end.isoformat()])

    elif filter_type == "month":
        month_end = today + timedelta(days=30)
        query += " AND due_date BETWEEN ? AND ?"
        params.extend([today.isoformat(), month_end.isoformat()])

    query += " ORDER BY due_date IS NULL, due_date ASC"

    cursor.execute(query, tuple(params))
    return cursor.fetchall()


# -------- ВЫПОЛНЕНИЕ --------
def complete_task(user_id, task_id):
    cursor.execute("SELECT title FROM tasks WHERE id=? AND user_id=?",
                   (task_id, user_id))
    row = cursor.fetchone()

    if not row:
        return False

    title = row[0]

    cursor.execute("UPDATE tasks SET done=1 WHERE id=?", (task_id,))
    cursor.execute("""
        INSERT INTO tasks_archive (id, user_id, title, completed_at)
        VALUES (?, ?, ?, ?)
    """, (task_id, user_id, title, datetime.now().isoformat()))

    conn.commit()
    add_xp(user_id, XP_PER_TASK)

    return True


# -------- АРХИВ --------
def get_archive(user_id):
    cursor.execute("""
        SELECT title, completed_at
        FROM tasks_archive
        WHERE user_id=?
        ORDER BY completed_at DESC
    """, (user_id,))
    return cursor.fetchall()


def clear_archive(user_id):
    cursor.execute("DELETE FROM tasks_archive WHERE user_id=?",
                   (user_id,))
    conn.commit()
