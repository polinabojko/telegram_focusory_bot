from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
import threading
from datetime import datetime, timedelta

timers = {}
sessions = {}  # хранит состояние пользователя


def focus_menu(bot, message):
    markup = InlineKeyboardMarkup()
    markup.add(
        InlineKeyboardButton("🍅 Режим 25/5", callback_data="pomodoro_start")
    )
    markup.add(
        InlineKeyboardButton("⛔ Остановить", callback_data="focus_stop")
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


# ---------- ЗАПУСК ----------

def start_pomodoro(bot, user_id):
    stop_focus(bot, user_id)  # отменяем если уже был

    sessions[user_id] = {
        "mode": "focus",
        "cycle": 1
    }

    bot.send_message(user_id, "🍅 Фокус начат на 25 минут.")
    start_focus_timer(bot, user_id, 25)


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
    if user_id in timers:
        timers[user_id].cancel()
        timers.pop(user_id, None)

    if user_id in sessions:
        sessions.pop(user_id, None)
        bot.send_message(user_id, "⛔ Pomodoro остановлен.")
