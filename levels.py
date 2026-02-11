from database import cursor, conn

LEVELS = {
    1: 0,
    2: 100,
    3: 250,
    4: 500,
    5: 1000
}

def add_xp(user_id, amount):
    cursor.execute("SELECT xp, level FROM users WHERE id=?", (user_id,))
    row = cursor.fetchone()

    if not row:
        cursor.execute("INSERT INTO users (id, xp, level) VALUES (?, ?, ?)",
                       (user_id, amount, 1))
        conn.commit()
        return

    xp, level = row
    xp += amount

    for lvl, req in LEVELS.items():
        if xp >= req:
            level = lvl

    cursor.execute("UPDATE users SET xp=?, level=? WHERE id=?",
                   (xp, level, user_id))
    conn.commit()
