from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
import threading
from datetime import datetime, timedelta

timers = {}


def focus_menu(bot, message):
    markup = InlineKeyboardMarkup()
    markup.add(
        InlineKeyboardButton("25 минут", callback_data="focus_25"),
        InlineKeyboardButton("50 минут", callback_data="focus_50")
    )
    markup.add(
        InlineKeyboardButton("⛔ Остановить", callback_data="focus_stop")
    )
    markup.add(
        InlineKeyboardButton("⬅ Назад", callback_data="main")
    )

    bot.edit_message_text(
        "🎯 Фокус-режим\nВыберите длительность:",
        message.chat.id,
        message.message_id,
        reply_markup=markup
    )


def start_focus(bot, user_id, minutes):
    # если уже есть таймер — отменяем
    if user_id in timers:
        timers[user_id].cancel()

    end_time = datetime.now() + timedelta(minutes=minutes)

    bot.send_message(
        user_id,
        f"🎯 Фокус начат на {minutes} минут.\nОкончание в {end_time.strftime('%H:%M')}"
    )

    def finish():
        bot.send_message(user_id, "✅ Фокус завершён.")
        timers.pop(user_id, None)

    timer = threading.Timer(minutes * 60, finish)
    timer.start()

    timers[user_id] = timer


def stop_focus(bot, user_id):
    if user_id in timers:
        timers[user_id].cancel()
        timers.pop(user_id)
        bot.send_message(user_id, "⛔ Фокус остановлен.")
    else:
        bot.send_message(user_id, "Нет активного фокуса.")
