from telebot import types
from database import cursor, conn

# ---------- МЕНЮ ----------
def menu(bot, user_id):
    markup = types.InlineKeyboardMarkup()
    markup.add(
        types.InlineKeyboardButton("➕ Добавить заметку", callback_data="add_note"),
        types.InlineKeyboardButton("📋 Список заметок", callback_data="list_notes")
    )
    markup.add(types.InlineKeyboardButton("⬅ Главное меню", callback_data="main"))
    bot.send_message(user_id, "🗒 Заметки", reply_markup=markup)

# ---------- ДОБАВЛЕНИЕ ----------
def ask_note_title(bot, call):
    msg = bot.send_message(call.message.chat.id, "Введите название заметки:")
    bot.register_next_step_handler(msg, ask_note_text)

def ask_note_text(message):
    user_id = message.chat.id
    title = message.text
    msg = message.bot.send_message(user_id, "Введите текст заметки:")
    # Передаем title в следующую функцию через lambda
    message.bot.register_next_step_handler(msg, lambda m: save_note(m, title))

def save_note(message, title):
    user_id = message.chat.id
    content = message.text
    cursor.execute(
        "INSERT INTO notes (user_id, title, content) VALUES (%s, %s, %s)",
        (user_id, title, content)
    )
    conn.commit()
    message.bot.send_message(user_id, f"Заметка '{title}' добавлена ✅")
    # Сразу возвращаем в меню заметок
    menu(message.bot, user_id)

# ---------- СПИСОК ЗАМЕТОК ----------
def list_notes(bot, message):
    user_id = message.chat.id
    cursor.execute(
        "SELECT id, title FROM notes WHERE user_id = %s ORDER BY created_at DESC",
        (user_id,)
    )
    notes_list = cursor.fetchall()

    if not notes_list:
        bot.send_message(user_id, "Пока нет заметок.")
        return

    markup = types.InlineKeyboardMarkup()
    for n in notes_list:
        markup.add(types.InlineKeyboardButton(n[1], callback_data=f"note_{n[0]}"))
    markup.add(types.InlineKeyboardButton("⬅ Главное меню", callback_data="main"))

    bot.send_message(user_id, "Выберите заметку:", reply_markup=markup)

# ---------- ВЫБОР ЗАМЕТКИ ----------
def note_actions(bot, call, note_id):
    cursor.execute("SELECT title, content FROM notes WHERE id = %s", (note_id,))
    note = cursor.fetchone()
    if not note:
        bot.answer_callback_query(call.id, "Заметка не найдена ❌")
        return

    title, content = note
    text = f"🗒 {title}\n\n{content}"

    markup = types.InlineKeyboardMarkup()
    markup.add(
        types.InlineKeyboardButton("✏ Редактировать", callback_data=f"edit_note_{note_id}"),
        types.InlineKeyboardButton("🗑 Удалить", callback_data=f"delete_note_{note_id}")
    )
    markup.add(types.InlineKeyboardButton("⬅ Список заметок", callback_data="list_notes"))

    bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=markup)

# ---------- УДАЛЕНИЕ ----------
def delete_note(bot, note_id, call):
    cursor.execute("DELETE FROM notes WHERE id = %s", (note_id,))
    conn.commit()
    bot.answer_callback_query(call.id, "Заметка удалена ✅")
    list_notes(bot, call.message)

# ---------- РЕДАКТИРОВАНИЕ ----------
def edit_note(bot, call, note_id):
    msg = bot.send_message(call.message.chat.id, "Введите новый текст заметки:")
    bot.register_next_step_handler(msg, lambda m: save_edited_note(m, note_id))

def save_edited_note(message, note_id):
    new_content = message.text
    cursor.execute("UPDATE notes SET content = %s WHERE id = %s", (new_content, note_id))
    conn.commit()
    message.bot.send_message(message.chat.id, "Заметка обновлена ✅")
    # Сразу возвращаем в меню заметок
    menu(message.bot, message.chat.id)
