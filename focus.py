from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from datetime import datetime, timedelta
import time
from database import cursor, conn

# ----------------- КЛАВИАТУРЫ -----------------

def focus_menu(bot, message):
    """Главное меню Pomodoro"""
    markup = InlineKeyboardMarkup()
    markup.add(
        InlineKeyboardButton("🍅 Режим 25/5", callback_data="pomodoro_start")
    )
    markup.add(
        InlineKeyboardButton("⬅ Назад", callback_data="main")
    )

    bot.edit_message_text(
        "🎯 Pomodoro режим\n25 минут фокус → 5 минут перерыв",
        message.chat.id,
        message.message_id,
        reply_markup=markup
    )

def active_focus_keyboard():
    """Кнопки активного фокуса"""
    markup = InlineKeyboardMarkup()
    markup.add(
        InlineKeyboardButton("⏳ Осталось времени", callback_data="focus_time")
    )
    markup.add(
        InlineKeyboardButton("⛔ Остановить", callback_data="focus_stop")
    )
    return markup

# ----------------- ЗАПУСК -----------------

def start_pomodoro(bot, user_id):
    """Запуск Pomodoro 25/5"""
    # Деактивируем предыдущие сессии
    cursor.execute("""
        UPDATE focus_sessions
        SET active = FALSE
        WHERE user_id = %s
    """, (user_id,))
    conn.commit()

    end_time = datetime.now() + timedelta(minutes=25)

    # Отправляем сообщение с прогрессом
    msg = bot.send_message(
        user_id,
        "🍅 Фокус\nЦикл: 1\nОсталось: 25:00",
        reply_markup=active_focus_keyboard()
    )

    # Создаем запись в БД
    cursor.execute("""
        INSERT INTO focus_sessions (user_id, mode, cycle, ends_at, active, message_id)
        VALUES (%s, 'focus', 1, %s, TRUE, %s)
    """, (user_id, end_time, msg.message_id))
    conn.commit()

# ----------------- ОСТАНОВКА -----------------

def stop_focus(bot, user_id):
    """Остановка активной сессии"""
    cursor.execute("""
        SELECT message_id FROM focus_sessions
        WHERE user_id = %s AND active = TRUE
        ORDER BY id DESC
        LIMIT 1
    """, (user_id,))
    result = cursor.fetchone()

    if result:
        message_id = result[0]
        bot.edit_message_text(
            "⛔ Pomodoro остановлен.",
            user_id,
            message_id
        )

    cursor.execute("""
        UPDATE focus_sessions
        SET active = FALSE
        WHERE user_id = %s
    """, (user_id,))
    conn.commit()

# ----------------- WATCHER -----------------

def focus_watcher(bot):
    """Фоновый watcher, обновляющий время и меняющий режим"""
    while True:
        cursor.execute("""
            SELECT id, user_id, mode, cycle, ends_at, message_id
            FROM focus_sessions
            WHERE active = TRUE
        """)
        sessions = cursor.fetchall()

        for session_id, user_id, mode, cycle, ends_at, message_id in sessions:

            if not message_id:
                continue

            remaining = ends_at - datetime.now()

            # Если время вышло — переключаем режим
            if remaining.total_seconds() <= 0:

                if mode == "focus":
                    # Логируем завершённый фокус
                    cursor.execute("""
                        INSERT INTO focus_logs (user_id, cycle)
                        VALUES (%s, %s)
                    """, (user_id, cycle))
                    conn.commit()

                    new_mode = "break"
                    new_cycle = cycle
                    new_end = datetime.now() + timedelta(minutes=5)
                    mode_text = "☕ Перерыв 5 минут"

                else:
                    new_mode = "focus"
                    new_cycle = cycle + 1
                    new_end = datetime.now() + timedelta(minutes=25)
                    mode_text = f"🍅 Новый фокус (цикл {new_cycle})"

                cursor.execute("""
                    UPDATE focus_sessions
                    SET mode = %s, cycle = %s, ends_at = %s
                    WHERE id = %s
                """, (new_mode, new_cycle, new_end, session_id))
                conn.commit()

                remaining = new_end - datetime.now()
                mode = new_mode
                cycle = new_cycle

            # Обновляем сообщение с оставшимся временем
            minutes = int(remaining.total_seconds() // 60)
            seconds = int(remaining.total_seconds() % 60)

            mode_text = "🍅 Фокус" if mode == "focus" else "☕ Перерыв"

            try:
                bot.edit_message_text(
                    f"{mode_text}\nЦикл: {cycle}\nОсталось: {minutes:02d}:{seconds:02d}",
                    user_id,
                    message_id,
                    reply_markup=active_focus_keyboard()
                )
            except:
                # Если сообщение удалено или недоступно
                pass

        time.sleep(60)  # автообновление каждую минуту

# ----------------- ПОКАЗ ОСТАВШЕГОСЯ ВРЕМЕНИ -----------------

def show_remaining_time(bot, user_id):
    """Отображение текущей сессии без спама"""
    cursor.execute("""
        SELECT mode, cycle, ends_at
        FROM focus_sessions
        WHERE user_id = %s AND active = TRUE
        ORDER BY id DESC
        LIMIT 1
    """, (user_id,))
    session = cursor.fetchone()

    if not session:
        bot.send_message(user_id, "Нет активной фокус-сессии.")
        return

    mode, cycle, ends_at = session
    remaining = ends_at - datetime.now()

    if remaining.total_seconds() <= 0:
        bot.send_message(user_id, "Сессия почти завершена...")
        return

    minutes = int(remaining.total_seconds() // 60)
    seconds = int(remaining.total_seconds() % 60)
    mode_text = "🍅 Фокус" if mode == "focus" else "☕ Перерыв"

    bot.send_message(
        user_id,
        f"{mode_text}\nЦикл: {cycle}\nОсталось: {minutes:02d}:{seconds:02d}"
    )
