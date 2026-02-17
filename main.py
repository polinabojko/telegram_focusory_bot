import telebot
from config import TOKEN
from database import init_db
import keyboards
import tasks

bot = telebot.TeleBot(TOKEN)

init_db()

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

bot.polling()
