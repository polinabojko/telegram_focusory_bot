import psycopg2
from config import DATABASE_URL

try:
    conn = psycopg2.connect(DATABASE_URL, sslmode="require")
    conn.autocommit = True
    cursor = conn.cursor()
except Exception as e:
    print("Ошибка подключения к БД:", e)
    raise

def init_db():
    # Tasks
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS tasks (
        id SERIAL PRIMARY KEY,
        user_id BIGINT NOT NULL,
        title TEXT NOT NULL,
        due_date DATE,
        completed BOOLEAN DEFAULT FALSE,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_tasks_user_id ON tasks(user_id);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_tasks_user_due ON tasks(user_id, due_date);")

    # Habits
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS habits (
        id SERIAL PRIMARY KEY,
        user_id BIGINT NOT NULL,
        title TEXT NOT NULL,
        streak INTEGER DEFAULT 0,
        last_marked DATE
    );
    """)
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_habits_user_id ON habits(user_id);")

    # Habit logs
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS habit_logs (
        id SERIAL PRIMARY KEY,
        habit_id INTEGER REFERENCES habits(id) ON DELETE CASCADE,
        user_id BIGINT NOT NULL,
        marked_date DATE NOT NULL,
        UNIQUE(habit_id, marked_date)
    );
    """)
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_habit_logs_user_id ON habit_logs(user_id);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_habit_logs_date ON habit_logs(marked_date);")

    # Notes
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS notes (
            id SERIAL PRIMARY KEY,
            user_id BIGINT NOT NULL,
            content TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)

# Добавляем колонку title, если её нет
    cursor.execute("""
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1
                FROM information_schema.columns
                WHERE table_name='notes' AND column_name='title'
            ) THEN
                ALTER TABLE notes ADD COLUMN title TEXT;
            END IF;
        END
        $$;
    """)
    conn.commit()
    # Mood
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS mood (
        id SERIAL PRIMARY KEY,
        user_id BIGINT NOT NULL,
        mood TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)

    # Focus sessions
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS focus_sessions (
        id SERIAL PRIMARY KEY,
        user_id BIGINT NOT NULL,
        mode TEXT,
        cycle INTEGER DEFAULT 1,
        ends_at TIMESTAMP,
        active BOOLEAN DEFAULT TRUE,
        message_id BIGINT
    );
    """)

    # Focus logs
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS focus_logs (
        id SERIAL PRIMARY KEY,
        user_id BIGINT NOT NULL,
        cycle INTEGER,
        completed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)

    print("✅ Database initialized successfully")
