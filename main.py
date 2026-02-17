import telebot
from config import TOKEN
from database import init_db, cursor, conn
import keyboards
import tasks
import habits
import stats
import focus
import notes
import threading
import mood

bot = telebot.TeleBot(TOKEN)
init_db()

# --- Функция реплай "Главное меню" ---
from telebot import types
def add_main_menu_reply(bot, user_id, text=""):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("🏠 Главное меню")
    bot.send_message(user_id, text, reply_markup=markup)

# --- Запуск фокуса в отдельном потоке ---
watcher_thread = threading.Thread(target=focus.focus_watcher, args=(bot,), daemon=True)
watcher_thread.start()

# --- Обработчик возврата в главное меню ---
@bot.message_handler(func=lambda m: m.text == "🏠 Главное меню")
def return_to_main(message):
    try:
        bot.edit_message_reply_markup(message.chat.id, message.message_id, reply_markup=None)
    except:
        pass
    bot.send_message(
        message.chat.id,
        "Вы вернулись в главное меню",
        reply_markup=keyboards.main_menu()
    )

# --- Команда /start ---
@bot.message_handler(commands=["start"])
def start(message):
    bot.send_message(
        message.chat.id,
        "Управление задачами, привычками и заметками.",
        reply_markup=keyboards.main_menu()
    )

# --- Основной callback router ---
@bot.callback_query_handler(func=lambda call: True)
def callback_router(call):
    data = call.data
    user_id = call.message.chat.id

    # --- Задачи ---
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
    elif data == "main":
        try:
            bot.edit_message_reply_markup(call.message.chat.id, call.message.message_id, reply_markup=None)
        except:
            pass
        bot.send_message(
            call.message.chat.id,
            "Главное меню",
            reply_markup=keyboards.main_menu()
        )

    # --- Привычки ---
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
        from database import conn  # убедись, что conn импортирован
        cursor.execute("DELETE FROM habits WHERE id = %s", (habit_id,))
        conn.commit()
        # Обновляем список привычек
        habits.list_habits(bot, call.message)
        # Можно показать уведомление
        bot.answer_callback_query(call.id, "Привычка удалена ✅")

    # --- Статистика ---
    elif data == "stats":
        stats.send_stats(bot, call.message)

    # --- Фокус ---
    elif data == "focus":
        focus.focus_menu(bot, call.message)
    elif data == "pomodoro_start":
        focus.start_pomodoro(bot, user_id)
    elif data == "focus_stop":
        focus.stop_focus(bot, user_id)
    elif data == "focus_time":
        focus.show_remaining_time(bot, user_id)

    # --- Заметки ---
    elif data == "notes":
        notes.notes_menu(bot, call.message)
    elif data == "add_note":
        notes.ask_note_title(bot, call)
    elif data.startswith("view_note_") or data.startswith("edit_note_") or data.startswith("delete_note_"):
        notes.handle_note_callback(bot, call)
    elif data == "mood":
        mood.menu(bot, call.message.chat.id)

bot.polling()
