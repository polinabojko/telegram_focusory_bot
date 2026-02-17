import telebot
from config import TOKEN
from database import init_db
from database import cursor
import keyboards
import tasks
import habits
import stats
import focus
import threading


bot = telebot.TeleBot(TOKEN)

init_db()


# --- запуск focus_watcher ---
watcher_thread = threading.Thread(target=focus.focus_watcher, args=(bot,), daemon=True)
watcher_thread.start()

@bot.message_handler(commands=["start"])
def start(message):
    bot.send_message(
        message.chat.id,
        "Управление задачами и привычками.",
        reply_markup=keyboards.main_menu()
    )

@bot.callback_query_handler(func=lambda call: True)
def callback_router(call):
    data = call.data
    user_id = call.message.chat.id

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
        habits.list_habits(bot, call.message)

    elif data == "stats":
        stats.send_stats(bot, call.message)

    elif data == "main":
        bot.edit_message_text(
            "Главное меню",
            call.message.chat.id,
            call.message.message_id,
            reply_markup=keyboards.main_menu()
        )
    elif data == "focus":
        focus.focus_menu(bot, call.message)
    elif data == "pomodoro_start":
        focus.start_pomodoro(bot, user_id)
    elif data == "focus_stop":
        focus.stop_focus(bot, user_id)
    elif data == "focus_time":
        focus.show_remaining_time(bot, user_id)
    elif data == "notes":
        import notes
        notes.menu(bot, call.message.chat.id)

    elif data == "add_note":
        import notes
        notes.ask_note_text(bot, call)

    elif data == "list_notes":
        import notes
        notes.list_notes(bot, call.message)
        

bot.polling()
