from telebot import types
from database import cursor, conn

# ---------- МЕНЮ ----------
def menu(bot, user_id):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("➕ Добавить", "📋 Список")
    markup.add("🔙 Назад")
    bot.send_message(user_id, "📝 Заметки.", reply_markup=markup)

# ---------- ДОБАВЛЕНИЕ ----------
def add_note(user_id, content):
    cursor.execute(
        "INSERT INTO notes (user_id, content) VALUES (%s, %s)",
        (user_id, content)
    )
    conn.commit()

# ---------- СПИСОК ----------
def list_notes(bot, user_id):
    cursor.execute(
        "SELECT id, content, created_at FROM notes WHERE user_id = %s ORDER BY created_at DESC",
        (user_id,)
    )
    rows = cursor.fetchall()

    if not rows:
        bot.send_message(user_id, "Нет заметок.")
        return

    text = "📋 Ваши заметки:\n\n"
    for note_id, content, created_at in rows:
        text += f"- {content} ({created_at.strftime('%d.%m.%Y')})\n"

    bot.send_message(user_id, text)
