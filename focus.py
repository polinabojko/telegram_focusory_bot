from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
import threading
from datetime import datetime, timedelta
import time
from database import cursor


def focus_menu(bot, message):
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
    markup = InlineKeyboardMarkup()
    markup.add(
        InlineKeyboardButton("⏳ Осталось времени", callback_data="focus_time")
    )
    markup.add(
        InlineKeyboardButton("⛔ Остановить", callback_data="focus_stop")
    )
    return markup

# ---------- ЗАПУСК ----------

def start_pomodoro(bot, user_id):
    # деактивируем старые сессии
    cursor.execute("""
        UPDATE focus_sessions
        SET active = FALSE
        WHERE user_id = %s
    """, (user_id,))

    end_time = datetime.now() + timedelta(minutes=25)

    msg = bot.send_message(
        user_id,
        "🍅 Фокус начат на 25 минут.",
        reply_markup=active_focus_keyboard()
    )

    cursor.execute("""
        INSERT INTO focus_sessions (user_id, mode, cycle, ends_at, active, message_id)
        VALUES (%s, 'focus', 1, %s, TRUE, %s)
    """, (user_id, end_time, msg.message_id))

def start_focus_timer(bot, user_id, minutes):
    def switch_to_break():
        if user_id not in sessions:
            return

        sessions[user_id]["mode"] = "break"
        bot.send_message(user_id, "☕ Перерыв 5 минут.")
        start_break_timer(bot, user_id, 5)

    timer = threading.Timer(minutes * 60, switch_to_break)
    timer.start()
    timers[user_id] = timer


def start_break_timer(bot, user_id, minutes):
    def switch_to_focus():
        if user_id not in sessions:
            return

        sessions[user_id]["cycle"] += 1
        sessions[user_id]["mode"] = "focus"

        bot.send_message(
            user_id,
            f"🍅 Новый фокус (цикл {sessions[user_id]['cycle']}) — 25 минут."
        )

        start_focus_timer(bot, user_id, 25)

    timer = threading.Timer(minutes * 60, switch_to_focus)
    timer.start()
    timers[user_id] = timer


# ---------- ОСТАНОВКА ----------

def stop_focus(bot, user_id):
    cursor.execute("""
        UPDATE focus_sessions
        SET active = FALSE
        WHERE user_id = %s
        AND active = TRUE
    """, (user_id,))

    bot.send_message(user_id, "⛔ Pomodoro остановлен.")


def active_focus_keyboard():
    markup = InlineKeyboardMarkup()
    markup.add(
        InlineKeyboardButton("⏳ Осталось времени", callback_data="focus_time")
    )
    markup.add(
        InlineKeyboardButton("⛔ Остановить", callback_data="focus_stop")
    )
    return markup
def focus_watcher(bot):
    while True:
        cursor.execute("""
            SELECT id, user_id, mode, cycle, ends_at, message_id
            FROM focus_sessions
            WHERE active = TRUE
        """)

        sessions = cursor.fetchall()

        for session_id, user_id, mode, cycle, ends_at, message_id in sessions:

            remaining = ends_at - datetime.now()

            # если время вышло
            if remaining.total_seconds() <= 0:

                if mode == "focus":
                    # логируем завершённый фокус
                    cursor.execute("""
                        INSERT INTO focus_logs (user_id, cycle)
                        VALUES (%s, %s)
                    """, (user_id, cycle))

                    new_end = datetime.now() + timedelta(minutes=5)

                    cursor.execute("""
                        UPDATE focus_sessions
                        SET mode = 'break',
                            ends_at = %s
                        WHERE id = %s
                    """, (new_end, session_id))

                    bot.send_message(user_id, "☕ Перерыв 5 минут.")

                else:
                    new_end = datetime.now() + timedelta(minutes=25)

                    cursor.execute("""
                        UPDATE focus_sessions
                        SET mode = 'focus',
                            cycle = cycle + 1,
                            ends_at = %s
                        WHERE id = %s
                    """, (new_end, session_id))

                    bot.send_message(user_id, f"🍅 Новый фокус (цикл {cycle+1})")

            else:
                # автообновление времени
                minutes = int(remaining.total_seconds() // 60)
                seconds = int(remaining.total_seconds() % 60)

                mode_text = "🍅 Фокус" if mode == "focus" else "☕ Перерыв"

                try:
                    if message_id:
                        bot.edit_message_text(
                            f"{mode_text}\n"
                            f"Цикл: {cycle}\n"
                            f"Осталось: {minutes:02d}:{seconds:02d}",
                            user_id,
                            message_id,
                            reply_markup=active_focus_keyboard()
                        )
                except:
                    pass

        time.sleep(60)

from datetime import datetime


def show_remaining_time(bot, user_id):
    cursor.execute("""
        SELECT mode, cycle, ends_at
        FROM focus_sessions
        WHERE user_id = %s
        AND active = TRUE
        ORDER BY id DESC
        LIMIT 1
    """, (user_id,))

    session = cursor.fetchone()

    if not session:
        bot.send_message(user_id, "Нет активной фокус-сессии.")
        return

    mode, cycle, ends_at = session

    now = datetime.now()
    remaining = ends_at - now

    if remaining.total_seconds() <= 0:
        bot.send_message(user_id, "Сессия почти завершена...")
        return

    minutes = int(remaining.total_seconds() // 60)
    seconds = int(remaining.total_seconds() % 60)

    mode_text = "🍅 Фокус" if mode == "focus" else "☕ Перерыв"

    bot.send_message(
        user_id,
        f"{mode_text}\n"
        f"Цикл: {cycle}\n"
        f"Осталось: {minutes:02d}:{seconds:02d}"
    )
