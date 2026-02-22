from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from database import get_connection
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
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        "INSERT INTO habits (user_id, title) VALUES (%s, %s)",
        (message.chat.id, message.text)
    )
    cursor.close()
    conn.close()
    bot.send_message(message.chat.id, "Добавлено 🔥")

    


# ---------- СПИСОК ----------
def list_habits(bot, message):
    user_id = message.chat.ID
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        "SELECT id, title, streak FROM habits WHERE user_id = %s",
        (user_id,)
    )
    habits_list = cursor.fetchall()
    cursor.close()
    conn.close()

    if not habits_list:
        bot.edit_message_text(
            "Пока нет привычек.",
            message.chat.id,
            message.message_id,
            reply_markup=InlineKeyboardMarkup().add(
                InlineKeyboardButton("⬅ Назад", callback_data="habits")
            )
        )
        return

    text = "📋 Ваши привычки:\n\n"
    markup = InlineKeyboardMarkup()

    for h in habits_list:
        text += f"🔥 {h[1]} — {h[2]} дней\n"

        markup.add(
            InlineKeyboardButton("✅ Отметить", callback_data=f"mark_habit_{h[0]}"),
            InlineKeyboardButton("🗑 Удалить", callback_data=f"delete_habit_{h[0]}")
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
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        "SELECT streak, last_marked, user_id FROM habits WHERE id = %s",
        (habit_id,)
    )
    habit = cursor.fetchone()

    if not habit:
        cursor.close()
        conn.close()
        bot.answer_callback_query(call.id, "Ошибка! Привычка не найдена ❌")
        return

    streak, last_marked, user_id = habit

    if last_marked == today:
        cursor.close()
        conn.close()
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

    cursor.close()
    conn.close()

    bot.answer_callback_query(call.id, f"Отмечено 🔥 Стрик: {streak}")


# ---------- УДАЛЕНИЕ ----------
def delete_habit(bot, call, habit_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM habits WHERE id = %s", (habit_id,))
    cursor.close()
    conn.close()
    bot.answer_callback_query(call.id, "Привычка удалена ✅")
    list_habits(bot, call.message)



