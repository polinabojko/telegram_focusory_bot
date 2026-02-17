from telebot import types
from database import cursor, conn

# ---------- МЕНЮ ----------
def menu(bot, message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("➕ Добавить", "📋 Список")
    markup.add("🔙 Назад")
    bot.send_message(message.chat.id, "📝 Заметки.", reply_markup=markup)
    # Добавляем реплай-кнопку "Главное меню" внизу чата
    from main import add_main_menu_reply
    add_main_menu_reply(bot, message.chat.id, text="Можно вернуться в главное меню:")
# ---------- ДОБАВЛЕНИЕ ----------
def ask_note_text(bot, call):
    msg = bot.send_message(call.message.chat.id, "Введите текст заметки:")
    bot.register_next_step_handler(msg, save_note, bot)

def save_note(message, bot):
    user_id = message.chat.id
    content = message.text
    cursor.execute(
        "INSERT INTO notes (user_id, content) VALUES (%s, %s)",
        (user_id, content)
    )
    conn.commit()
    bot.send_message(user_id, "Заметка добавлена ✅")

# ---------- СПИСОК ----------
def list_notes(bot, message):
    user_id = message.chat.id
    cursor.execute(
        "SELECT id, content, created_at FROM notes WHERE user_id = %s ORDER BY created_at DESC",
        (user_id,)
    )
    rows = cursor.fetchall()

    if not rows:
        bot.edit_message_text(
            "Нет заметок.",
            message.chat.id,
            message.message_id
        )
        return

    text = "📋 Ваши заметки:\n\n"
    for note_id, content, created_at in rows:
        text += f"- {content} ({created_at.strftime('%d.%m.%Y')})\n"

    bot.edit_message_text(
        text,
        message.chat.id,
        message.message_id
    )
