import telebot
from config import TOKEN
from database import init_db, cursor, conn
import keyboards
import tasks
import habits
import stats
import focus
import threading
import notes
import mood

bot = telebot.TeleBot(TOKEN)
init_db()

from telebot import types

# ---------- ВСПОМОГАТЕЛЬНОЕ: Главное меню как реплай ----------
def add_main_menu_reply(bot, user_id, text=""):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("🏠 Главное меню")
    bot.send_message(user_id, text, reply_markup=markup)

# ---------- ЗАПУСК focus_watcher ----------
watcher_thread = threading.Thread(target=focus.focus_watcher, args=(bot,), daemon=True)
watcher_thread.start()

# ---------- ОБРАБОТКА НАТИВНЫХ СООБЩЕНИЙ ----------
@bot.message_handler(func=lambda m: m.text == "🏠 Главное меню")
def return_to_main(message):
    bot.send_message(
        message.chat.id,
        "Вы вернулись в главное меню",
        reply_markup=keyboards.main_menu()  # inline-кнопки
    )

@bot.message_handler(commands=["start"])
def start(message):
    bot.send_message(
        message.chat.id,
        "Управление задачами и привычками.",
        reply_markup=keyboards.main_menu()
    )

# ---------- CALLBACK HANDLER ----------
@bot.callback_query_handler(func=lambda call: True)
def callback_router(call):
    data = call.data
    user_id = call.message.chat.id

    # -------- ЗАДАЧИ --------
    if data == "tasks":
        tasks.tasks_menu(bot, call.message)
    elif data.startswith("tasks_page_"):
        page = int(data.split("_")[-1])
        tasks.show_tasks(bot, call.message, page)
    elif data == "add_task":
        tasks.ask_task_text(bot, call)
    elif data.startswith("due_"):
        parts = data.split("|")
        due_type = parts[0].replace("due_", "")
        title = parts[1]
        tasks.save_task(user_id, title, due_type)
        tasks.tasks_menu(bot, call.message)
    elif data.startswith("complete_"):
        task_id = int(data.split("_")[1])
        tasks.complete_task(task_id)
        tasks.show_tasks(bot, call.message, 0)
    elif data.startswith("delete_"):
        task_id = int(data.split("_")[1])
        tasks.delete_task(task_id)
        tasks.show_tasks(bot, call.message, 0)
    elif data.startswith("edit_"):
        task_id = int(data.split("_")[1])
        tasks.edit_task(bot, call, task_id)

    # -------- ПРИВЫЧКИ --------
    elif data == "habits":
        habits.habits_menu(bot, call.message)
    elif data == "add_habit":
        habits.ask_habit_text(bot, call)
    elif data == "list_habits":
        habits.list_habits(bot, call.message)
    elif data.startswith("mark_"):
        habit_id = int(data.split("_")[1])
        habits.mark_habit(bot, call, habit_id)
    elif data.startswith("delete_habit_"):
        habit_id = int(data.split("_")[2])
        cursor.execute("DELETE FROM habits WHERE id = %s", (habit_id,))
        conn.commit()
        habits.list_habits(bot, call.message)

    # -------- СТАТИСТИКА --------
    elif data == "stats":
        stats.send_stats(bot, call.message)

    # -------- FOCUS --------
    elif data == "focus":
        focus.focus_menu(bot, call.message)
    elif data == "pomodoro_start":
        focus.start_pomodoro(bot, user_id)
    elif data == "focus_stop":
        focus.stop_focus(bot, user_id)
    elif data == "focus_time":
        focus.show_remaining_time(bot, user_id)

    # -------- ЗАМЕТКИ --------
    elif data == "notes":
        notes.menu(bot, user_id)
    elif data == "add_note":
        notes.ask_note_title(bot, call)
    elif data == "list_notes":
        notes.list_notes(bot, call.message)
    elif data.startswith("note_"):
        note_id = int(data.split("_")[1])
        notes.note_actions(bot, call, note_id)
    elif data.startswith("delete_note_"):
        note_id = int(data.split("_")[2])
        notes.delete_note(bot, note_id, call)
    elif data.startswith("edit_note_"):
        note_id = int(data.split("_")[2])
        notes.edit_note(bot, call, note_id)

    # -------- НАСТРОЕНИЕ --------
    elif data == "mood":
        mood.menu(bot, user_id)
    elif data.startswith("mood_"):
        mood_choice = data.split("_")[1]
        mood.save_mood(user_id, mood_choice)
        bot.answer_callback_query(call.id, f"Сохранено настроение {mood_choice}")

bot.polling()
