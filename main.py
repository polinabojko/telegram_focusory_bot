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


# --- Запуск фокуса в отдельном потоке ---
watcher_thread = threading.Thread(target=focus.focus_watcher, args=(bot,), daemon=True)
watcher_thread.start()


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
    # ------------------ ГЛАВНОЕ МЕНЮ ------------------
    elif data == "main":
        bot.edit_message_text(
            "Вы вернулись в главное меню",
            call.message.chat.id,
            call.message.message_id,
            reply_markup=keyboards.main_menu()
        )
        bot.answer_callback_query(call.id)
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
        cursor.execute("DELETE FROM habits WHERE id = %s", (habit_id,))
        conn.commit()
        # Обновляем список привычек
        habits.list_habits(bot, call.message)
        # Можно показать уведомление
        bot.answer_callback_query(call.id, "Привычка удалена ✅")
    elif data.startswith("graph_habit_"):
        habit_id = int(data.split("_")[2])
        habits.habit_activity_graph(bot, call, habit_id)


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
    elif data == "back_focus":
        focus.focus_menu(bot, call.message)

    # ------------------ ЗАМЕТКИ ------------------
    elif data == "notes":
        import notes
        notes.menu(bot, call.message)

    elif data == "add_note":
        import notes
        notes.ask_note_title(bot, call)

    elif data == "list_notes":
        import notes
        notes.list_notes(bot, call)

    elif data.startswith("note_"):
        note_id = int(data.split("_")[1])
        import notes
        notes.note_actions(bot, call, note_id)

    elif data.startswith("edit_note_"):
        note_id = int(data.split("_")[2])
        import notes
        notes.edit_note(bot, call, note_id)

    elif data.startswith("delete_note_"):
        note_id = int(data.split("_")[2])
        import notes
        notes.delete_note(bot, note_id, call)

    # ------------------ НАСТРОЕНИЕ ------------------
    elif data == "mood":
        import mood
        mood.mood_menu(bot, call.message)

    elif data.startswith("mood_"):
        mood_choice = data.split("_")[1]
        import mood
        mood.save_mood(user_id, mood_choice)
        bot.answer_callback_query(call.id, f"Сохранено настроение {mood_choice}")

bot.polling()
