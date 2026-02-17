from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from database import cursor, conn
from datetime import date, timedelta
from telebot import types

# ---------- МЕНЮ ----------
def habits_menu(bot, message):
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("➕ Добавить привычку", callback_data="add_habit"))
    markup.add(InlineKeyboardButton("📋 Список привычек", callback_data="list_habits"))
    markup.add(InlineKeyboardButton("⬅ Назад", callback_data="main"))

    bot.edit_message_text(
        "🔁 Привычки",
        message.chat.id,
        message.message_id,
        reply_markup=markup
    )


# ---------- ДОБАВЛЕНИЕ ----------
def ask_habit_text(bot, call):
    msg = bot.send_message(call.message.chat.id, "Введите название привычки:")
    bot.register_next_step_handler(msg, save_habit, bot)


def save_habit(message, bot):
    cursor.execute(
        "INSERT INTO habits (user_id, title) VALUES (%s, %s)",
        (message.chat.id, message.text)
    )
    conn.commit()
    bot.send_message(message.chat.id, "Добавлено 🔥")

    # Добавим кнопку «Главное меню»
    add_main_menu_reply(bot, message.chat.id, "Вы можете вернуться в главное меню:")


# ---------- СПИСОК ----------
def list_habits(bot, message):
    user_id = message.chat.id

    cursor.execute(
        "SELECT id, title, streak, last_marked FROM habits WHERE user_id = %s",
        (user_id,)
    )
    habits_list = cursor.fetchall()

    if not habits_list:
        bot.edit_message_text(
            "Пока нет привычек.",
            message.chat.id,
            message.message_id
        )
        return

    text = "📋 Ваши привычки:\n\n"
    markup = InlineKeyboardMarkup()

    for h in habits_list:
        text += f"🔥 {h[1]} — {h[2]} дней\n"

        markup.add(
            InlineKeyboardButton("✅ Отметить", callback_data=f"mark_{h[0]}"),
            InlineKeyboardButton("🗑", callback_data=f"delete_habit_{h[0]}")
        )

    markup.add(InlineKeyboardButton("⬅ Назад", callback_data="habits"))

    bot.edit_message_text(
        text,
        message.chat.id,
        message.message_id,
        reply_markup=markup
    )


# ---------- ЛОГИКА СТРИКА ----------
def mark_habit(bot, call, habit_id):
    today = date.today()

    cursor.execute(
        "SELECT streak, last_marked, user_id FROM habits WHERE id = %s",
        (habit_id,)
    )
    habit = cursor.fetchone()

    if not habit:
        bot.answer_callback_query(call.id, "Ошибка! Привычка не найдена ❌")
        return

    streak, last_marked, user_id = habit

    if last_marked == today:
        bot.answer_callback_query(call.id, "Сегодня уже отмечено 👀")
        return

    # Если отмечали вчера — продолжаем стрик, иначе начинаем заново
    if last_marked == today - timedelta(days=1):
        streak += 1
    else:
        streak = 1

    # Обновляем привычку
    cursor.execute(
        "UPDATE habits SET streak = %s, last_marked = %s WHERE id = %s",
        (streak, today, habit_id)
    )

    # Добавляем запись в журнал
    cursor.execute(
        "INSERT INTO habit_logs (habit_id, user_id, marked_date) VALUES (%s, %s, %s) ON CONFLICT DO NOTHING",
        (habit_id, user_id, today)
    )

    conn.commit()

    bot.answer_callback_query(call.id, f"Отмечено 🔥 Стрик: {streak}")


# ---------- УДАЛЕНИЕ ----------
def delete_habit(bot, call, habit_id):
    cursor.execute("DELETE FROM habits WHERE id = %s", (habit_id,))
    conn.commit()
    bot.answer_callback_query(call.id, "Привычка удалена ❌")
    list_habits(bot, call.message)


# ---------- ВСПОМОГАТЕЛЬНОЕ ----------
def add_main_menu_reply(bot, user_id, text=""):
    """Добавляет реплай-кнопку 'Главное меню'"""
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("🏠 Главное меню")
    bot.send_message(user_id, text, reply_markup=markup)
