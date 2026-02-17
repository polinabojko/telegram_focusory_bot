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

bot.polling()
