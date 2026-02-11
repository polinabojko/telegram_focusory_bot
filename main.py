import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from datetime import datetime, timedelta
import threading
import redis
import time

from config import TOKEN
from tasks import *
from habits import *
from notes import *
from stats import generate_focus_graph
from levels import get_level_data, add_xp
from database import cursor, conn

bot = telebot.TeleBot(TOKEN)

r = redis.Redis(host="localhost", port=6379, db=0)

focus_sessions = {}

# ================== МЕНЮ ==================

def main_menu():
    kb = InlineKeyboardMarkup()
    kb.add(
        InlineKeyboardButton("🍅 Фокус", callback_data="focus"),
        InlineKeyboardButton("📅 План", callback_data="plan")
    )
    kb.add(
        InlineKeyboardButton("🧠 Привычки", callback_data="habits"),
        InlineKeyboardButton("📝 Заметки", callback_data="notes")
    )
    kb.add(
        InlineKeyboardButton("📊 Статистика", callback_data="stats")
    )
    return kb


# ================== START ==================

@bot.message_handler(commands=['start'])
def start(message):
    bot.send_message(
        message.chat.id,
        "✨ Добро пожаловать.\n\nВыбери раздел:",
        reply_markup=main_menu()
    )


# ================== ФОКУС ==================

@bot.callback_query_handler(func=lambda c: c.data == "focus")
def focus_menu(call):
    kb = InlineKeyboardMarkup()
    kb.add(
        InlineKeyboardButton("25 мин", callback_data="focus_25"),
        InlineKeyboardButton("50 мин", callback_data="focus_50")
    )
    kb.add(InlineKeyboardButton("⬅ Назад", callback_data="back_main"))
    bot.edit_message_text(
        "Выбери длительность фокуса:",
        call.message.chat.id,
        call.message.message_id,
        reply_markup=kb
    )


@bot.callback_query_handler(func=lambda c: c.data.startswith("focus_"))
def start_focus(call):
    minutes = int(call.data.split("_")[1])
    user_id = call.from_user.id

    end_time = datetime.now() + timedelta(minutes=minutes)

    focus_sessions[user_id] = {
        "end": end_time,
        "minutes": minutes,
        "start": datetime.now()
    }

    r.set(f"focus:{user_id}", end_time.isoformat())

    kb = InlineKeyboardMarkup()
    kb.add(
        InlineKeyboardButton("⏳ Сколько осталось", callback_data="time_left"),
        InlineKeyboardButton("⛔ Завершить", callback_data="stop_focus")
    )
    kb.add(InlineKeyboardButton("⬅ Главное меню", callback_data="exit_focus"))

    bot.edit_message_text(
        f"🍅 Фокус начался на {minutes} минут.\n\nЕсли выйдешь — сессия завершится.",
        call.message.chat.id,
        call.message.message_id,
        reply_markup=kb
    )

    threading.Thread(target=focus_timer, args=(user_id,), daemon=True).start()


def focus_timer(user_id):
    while True:
        if user_id not in focus_sessions:
            return

        end = focus_sessions[user_id]["end"]
        if datetime.now() >= end:
            finish_focus(user_id, completed=True)
            return

        time.sleep(5)


def finish_focus(user_id, completed=False):
    if user_id not in focus_sessions:
        return

    data = focus_sessions[user_id]
    start = data["start"]
    real_minutes = int((datetime.now() - start).total_seconds() / 60)

    cursor.execute("""
        INSERT INTO focus_sessions (user_id, completed_at, minutes)
        VALUES (?, ?, ?)
    """, (user_id, datetime.now().isoformat(), real_minutes))

    conn.commit()
    add_xp(user_id, real_minutes)

    del focus_sessions[user_id]
    r.delete(f"focus:{user_id}")

    bot.send_message(
        user_id,
        f"✅ Фокус завершён.\nРеально отработано: {real_minutes} мин",
        reply_markup=main_menu()
    )

    # Перерыв
    bot.send_message(user_id, "☕ Перерыв 5 минут.")


@bot.callback_query_handler(func=lambda c: c.data == "time_left")
def time_left(call):
    user_id = call.from_user.id
    if user_id not in focus_sessions:
        bot.answer_callback_query(call.id, "Нет активного фокуса")
        return

    end = focus_sessions[user_id]["end"]
    left = int((end - datetime.now()).total_seconds() / 60)

    bot.answer_callback_query(call.id, f"Осталось {left} мин")


@bot.callback_query_handler(func=lambda c: c.data == "stop_focus")
def stop_focus(call):
    finish_focus(call.from_user.id)


@bot.callback_query_handler(func=lambda c: c.data == "exit_focus")
def exit_focus(call):
    if call.from_user.id in focus_sessions:
        finish_focus(call.from_user.id)
    bot.send_message(call.from_user.id, "Главное меню", reply_markup=main_menu())


# ================== ПЛАН ==================

@bot.callback_query_handler(func=lambda c: c.data == "plan")
def plan_menu(call):
    kb = InlineKeyboardMarkup()
    kb.add(
        InlineKeyboardButton("📅 Сегодня", callback_data="tasks_today"),
        InlineKeyboardButton("🗓 Неделя", callback_data="tasks_week")
    )
    kb.add(
        InlineKeyboardButton("🗂 Месяц", callback_data="tasks_month"),
        InlineKeyboardButton("📋 Все", callback_data="tasks_all")
    )
    kb.add(
        InlineKeyboardButton("➕ Добавить", callback_data="add_task"),
        InlineKeyboardButton("🗂 Архив", callback_data="archive")
    )
    kb.add(InlineKeyboardButton("⬅ Назад", callback_data="back_main"))

    bot.edit_message_text(
        "📅 Планирование:",
        call.message.chat.id,
        call.message.message_id,
        reply_markup=kb
    )


# ================== СТАТИСТИКА ==================

@bot.callback_query_handler(func=lambda c: c.data == "stats")
def stats(call):
    user_id = call.from_user.id
    level, xp = get_level_data(user_id)

    cursor.execute("SELECT SUM(minutes) FROM focus_sessions WHERE user_id=?", (user_id,))
    focus_total = cursor.fetchone()[0] or 0

    text = f"""
📊 Статистика

🔥 Уровень: {level}
⭐ XP: {xp}

🍅 Всего минут фокуса: {focus_total}
"""

    bot.edit_message_text(
        text,
        call.message.chat.id,
        call.message.message_id,
        reply_markup=main_menu()
    )


# ================== НАЗАД ==================

@bot.callback_query_handler(func=lambda c: c.data == "back_main")
def back_main(call):
    bot.edit_message_text(
        "Главное меню:",
        call.message.chat.id,
        call.message.message_id,
        reply_markup=main_menu()
    )


# ================== ЕЖЕДНЕВНАЯ РАССЫЛКА ==================

def daily_morning():
    while True:
        now = datetime.now()
        if now.hour == 9 and now.minute == 0:
            cursor.execute("SELECT DISTINCT user_id FROM tasks")
            users = cursor.fetchall()

            for u in users:
                tasks = get_tasks(u[0], "today")
                text = "☀ Доброе утро!\n\nЗадачи на сегодня:\n"
                for t in tasks:
                    text += f"- {t[1]}\n"

                text += "\nНажми «План», чтобы увидеть все задачи.\nХорошего дня ✨"

                bot.send_message(u[0], text)

            time.sleep(60)

        time.sleep(20)


threading.Thread(target=daily_morning, daemon=True).start()


bot.infinity_polling()
