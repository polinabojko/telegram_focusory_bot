import psycopg2
from config import DATABASE_URL

conn = psycopg2.connect(DATABASE_URL, sslmode="require")
conn.autocommit = True
cursor = conn.cursor()

def init_db():
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS tasks (
        id SERIAL PRIMARY KEY,
        user_id BIGINT,
        title TEXT,
        due_date DATE,
        completed BOOLEAN DEFAULT FALSE,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS habits (
        id SERIAL PRIMARY KEY,
        user_id BIGINT,
        title TEXT,
        streak INTEGER DEFAULT 0,
        last_marked DATE
    );
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS habit_logs (
        id SERIAL PRIMARY KEY,
        habit_id INTEGER REFERENCES habits(id) ON DELETE CASCADE,
        user_id BIGINT,
        marked_date DATE NOT NULL
    );
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS notes (
        id SERIAL PRIMARY KEY,
        user_id BIGINT,
        content TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS mood (
        id SERIAL PRIMARY KEY,
        user_id BIGINT,
        mood TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)
    cursor.execute("""
    CREATE INDEX IF NOT EXISTS idx_tasks_user_id
    ON tasks(user_id);
    """)
    cursor.execute("""
    CREATE INDEX IF NOT EXISTS idx_habits_user_id
    ON habits(user_id);
    """)
    cursor.execute("""
    CREATE INDEX IF NOT EXISTS idx_habit_logs_user_id
    ON habit_logs(user_id);
    """)
    cursor.execute("""
    CREATE INDEX IF NOT EXISTS idx_habit_logs_date
    ON habit_logs(marked_date);
    """)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS focus_sessions (
        id SERIAL PRIMARY KEY,
        user_id BIGINT,
        mode TEXT, -- focus / break
        cycle INTEGER DEFAULT 1,
        ends_at TIMESTAMP,
        active BOOLEAN DEFAULT TRUE
    );
    """)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS focus_logs (
        id SERIAL PRIMARY KEY,
        user_id BIGINT,
        cycle INTEGER,
        completed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)
