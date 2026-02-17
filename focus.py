from telebot import types
import threading
from datetime import datetime, timedelta

timers = {}

def menu(bot, user_id):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("25 минут", "50 минут")
    markup.add("🔙 Назад")
    bot.send_message(user_id, "Фокус.\nВыберите длительность.", reply_markup=markup)

def start_focus(bot, user_id, minutes):
    end_time = datetime.now() + timedelta(minutes=minutes)
    bot.send_message(user_id, f"Фокус начат.\nОкончание в {end_time.strftime('%H:%M')}.")

    def finish():
        bot.send_message(user_id, "Фокус завершён.")

    timer = threading.Timer(minutes * 60, finish)
    timer.start()
    timers[user_id] = timer
