from database import cursor, conn


def create_note(user_id, title, content):
    cursor.execute("""
        INSERT INTO notes (user_id, title, content)
        VALUES (?, ?, ?)
    """, (user_id, title, content))
    conn.commit()


def get_notes(user_id):
    cursor.execute("""
        SELECT id, title FROM notes
        WHERE user_id=?
    """, (user_id,))
    return cursor.fetchall()


def get_note(user_id, note_id):
    cursor.execute("""
        SELECT title, content FROM notes
        WHERE id=? AND user_id=?
    """, (note_id, user_id))
    return cursor.fetchone()


def delete_note(user_id, note_id):
    cursor.execute("""
        DELETE FROM notes
        WHERE id=? AND user_id=?
    """, (note_id, user_id))
    conn.commit()
