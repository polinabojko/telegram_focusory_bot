from telebot import types
from database import cursor, conn

# ---------- МЕНЮ ЗАМЕТОК ----------
def menu(bot, message):
    """Главное меню заметок"""
    markup = types.InlineKeyboardMarkup()
    markup.add(
        types.InlineKeyboardButton("➕ Добавить заметку", callback_data="add_note"),
        types.InlineKeyboardButton("📋 Список заметок", callback_data="list_notes")
    )
    markup.add(types.InlineKeyboardButton("⬅ Главное меню", callback_data="main"))
    try:
        bot.edit_message_text(
            "🗒 Заметки",
            message.chat.id,
            message.message_id,
            reply_markup=markup
        )
    except:
        bot.send_message(message.chat.id, "🗒 Заметки", reply_markup=markup)

# ---------- ДОБАВЛЕНИЕ ЗАМЕТКИ ----------
def ask_note_title(bot, call):
    msg = bot.send_message(call.message.chat.id, "Введите название заметки:")
    bot.register_next_step_handler(msg, lambda m: ask_note_text(bot, m, m.text))

def ask_note_text(bot, message, title):
    msg = bot.send_message(message.chat.id, "Введите текст заметки:")
    bot.register_next_step_handler(msg, lambda m: save_note(bot, m, title))

def save_note(bot, message, title):
    user_id = message.chat.id
    content = message.text

    # Сохраняем в БД
    cursor.execute(
        "INSERT INTO notes (user_id, title, content) VALUES (%s, %s, %s)",
        (user_id, title, content)
    )
    conn.commit()

    # Отправляем уведомление
    bot.send_message(user_id, f"✅ Заметка '{title}' добавлена!")

    # Показываем меню заметок
    menu(bot, message)
def list_notes(bot, call):
    user_id = call.message.chat.id
    cursor.execute(
        "SELECT id, title FROM notes WHERE user_id = %s ORDER BY created_at DESC",
        (user_id,)
    )
    notes_list = cursor.fetchall()

    if not notes_list:
        bot.edit_message_text("Пока нет заметок.", user_id, call.message.message_id)
        return

    markup = types.InlineKeyboardMarkup()
    for n in notes_list:
        markup.add(types.InlineKeyboardButton(n[1], callback_data=f"note_{n[0]}"))
    markup.add(types.InlineKeyboardButton("⬅ Главное меню", callback_data="main"))

    bot.edit_message_text("Выберите заметку:", user_id, call.message.message_id, reply_markup=markup)

# ---------- ДЕЙСТВИЯ С ЗАМЕТКОЙ ----------
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

    bot.edit_message_text(
        text,
        call.message.chat.id,
        call.message.message_id,
        reply_markup=markup
    )
    bot.answer_callback_query(call.id)

# ---------- УДАЛЕНИЕ ЗАМЕТКИ ----------
def delete_note(bot, note_id, call):
    cursor.execute("DELETE FROM notes WHERE id = %s", (note_id,))
    conn.commit()
    bot.answer_callback_query(call.id, "Заметка удалена ✅")
    list_notes(bot, call.message)

# ---------- РЕДАКТИРОВАНИЕ ЗАМЕТКИ ----------
def edit_note(bot, call, note_id):
    msg = bot.send_message(call.message.chat.id, "Введите новый текст заметки:")
    bot.register_next_step_handler(msg, lambda m: save_edited_note(bot, m, note_id))

def save_edited_note(bot, message, note_id):
    new_content = message.text
    cursor.execute("UPDATE notes SET content = %s WHERE id = %s", (new_content, note_id))
    conn.commit()
    bot.send_message(message.chat.id, "Заметка обновлена ✅")
    # Возвращаем в меню заметок
    menu(bot, message)
