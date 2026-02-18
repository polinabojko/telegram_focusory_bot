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
        "📌 Важные моменты в использовании бота
        🔙 Возврат в главное меню
        В некоторых разделах (например, «Статистика», «Режим 25/5» и «Остановить» после запуска Pomodoro) нет отдельной кнопки возврата в главное меню.
        Чтобы вернуться назад:
        -пролистайте чат вверх до сообщения с кнопкой «⬅️Назад» или «⬅️Главное меню»
        -либо закрепите сообщение с главным меню, чтобы всегда иметь к нему быстрый доступ (его можно открепить в любой момент)
        🍅 Режим Pomodoro (25/5)
        -Кнопку «⏳ Осталось времени» можно не использовать — в сообщении
        «🍅 Фокус | Цикл | Осталось» время автоматически обновляется каждую минуту.
        -После 25 минут фокуса бот отправит сообщение о начале 5-минутного перерыва.
        -Если вы решили завершить сессию раньше — нажмите «Остановить».
        Бот пришлёт уведомление об остановке, а завершённая сессия будет учтена в статистике.
        -Для возврата в меню после остановки нужно пролистать чат вверх до кнопки «⬅️Назад» или «⬅️Главное меню», либо нажать на закрепленное сообщение.
        📋 Список задач
        -На одной странице отображается 5 задач в хронологическом порядке.
        Если задач больше — появляются дополнительные страницы и кнопки «➡️» / «⬅️» для навигации.
        -Выполненные задачи автоматически перемещаются в конец списка.
        -Возле каждой задачи указана дата (пример: Название — дд.мм).
        Это дедлайн, выбранный при создании задачи:
        Сегодня / Завтра / Неделя / Месяц / Без срока.
        Установить произвольную дату вручную нельзя.
        😊 Настроение
        Настроение можно выбирать неограниченное количество раз в день.
        Однако в разделе «Статистика» отображается среднее значение за последние 30 дней, поэтому:
        Если вам важно отслеживать динамику — лучше выбирать настроение один раз в день, чтобы данные были более точными и показательными.",
        reply_markup=keyboards.main_menu()
    )
# --- Основной callback router ---
@bot.callback_query_handler(func=lambda call: True)
def callback_router(call):
    data = call.data
    user_id = call.message.chat.id
    print("CALLBACK:", data)

    try:
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
        elif data.startswith("complete_task_"):
            task_id = int(data.split("_")[2])
            tasks.complete_task(task_id)
            tasks.show_tasks(bot, call.message, 0)
        elif data.startswith("delete_task_"):
            task_id = int(data.split("_")[2])
            tasks.delete_task(task_id)
            tasks.show_tasks(bot, call.message, 0)
        elif data.startswith("edit_task_"):
            task_id = int(data.split("_")[2])
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

        elif data.startswith("mark_habit_"):
            habit_id = int(data.split("_")[2])
            habits.mark_habit(bot, call, habit_id)

        elif data.startswith("delete_habit_"):
            habit_id = int(data.split("_")[2])
            cursor.execute("DELETE FROM habits WHERE id = %s", (habit_id,))
            conn.commit()
            bot.answer_callback_query(call.id, "Привычка удалена ✅")
        # Обновляем список привычек после удаления
            habits.list_habits(bot, call.message)
    


        # --- Статистика ---
        elif data == "stats":
            stats.send_stats(bot, call.message)

        # --- Фокус ---
        elif data == "focus":
            focus.focus_menu(bot, call)
        elif data.startswith("pomodoro_"):
            parts = data.split("_")
            work, rest = int(parts[1]), int(parts[2])
            focus.start_pomodoro(bot, call.message.chat.id, work, rest)
        elif data == "focus_stop":
            focus.stop_focus(bot, call.message.chat.id)
        elif data == "focus_time":
            focus.show_remaining_time(bot, call.message.chat.id)
        elif data == "back_focus":
            focus.focus_menu(bot, call)
    

        # ------------------ ЗАМЕТКИ ------------------
        elif data == "notes":
            notes.show_notes_menu(bot, call.message.chat.id, call.message.message_id)

        elif data == "add_note":
            notes.ask_note_title(bot, call)
        elif data == "list_notes":
            notes.list_notes(bot, call)

        elif data.startswith("edit_note_"):
            note_id = int(data.split("_")[2])
            notes.edit_note(bot, call, note_id)

        elif data.startswith("delete_note_"):
            note_id = int(data.split("_")[2])
            notes.delete_note(bot, note_id, call)
            notes.list_notes(bot, call)
        elif data.startswith("note_"):
            note_id = int(data.split("_")[1])
            notes.note_actions(bot, call, note_id)
        # ------------------ НАСТРОЕНИЕ ------------------
        elif data == "mood":
            mood.mood_menu(bot, call.message)

        elif data.startswith("mood_"):
            mood_choice = data.split("_")[1]
            mood.save_mood(user_id, mood_choice)
            bot.answer_callback_query(call.id, f"Сохранено настроение {mood_choice}")
    except Exception as e:
        print("ERROR:", e)

    
bot.polling()
