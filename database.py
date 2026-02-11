import sqlite3
from config import DB_NAME

def get_connection():
    return sqlite3.connect(DB_NAME, check_same_thread=False)

conn = get_connection()
cursor = conn.cursor()

def init_db():
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY,
        xp INTEGER DEFAULT 0,
        level INTEGER DEFAULT 1
    )
    """)

    cursor.execute("""
CREATE TABLE IF NOT EXISTS tasks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    title TEXT,
    due_date TEXT,
    done INTEGER DEFAULT 0,
    created_at TEXT
)
""")

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS tasks_archive (
        id INTEGER,
        user_id INTEGER,
        title TEXT,
        completed_at TEXT
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS habits (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        title TEXT,
        streak INTEGER DEFAULT 0,
        last_done TEXT,
        active INTEGER DEFAULT 1
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS notes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        title TEXT,
        content TEXT
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS focus_sessions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        minutes INTEGER,
        completed_at TEXT
    )
    """)

    conn.commit()

init_db()
