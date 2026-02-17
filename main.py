import telebot
from telebot import types
from config import TOKEN
from database import init_db
import tasks
import habits
import focus
import notes
import stats

bot = telebot.TeleBot(TOKEN)
init_db()

user_states = {}

def main_menu():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("📝 Задачи", "🔁 Привычки")
    markup.add("🎯 Фокус", "📊 Статистика")
    markup.add("🗒 Заметки", "😊 Настроение")
    return markup

@bot.message_handler(commands=["start"])
def start(message):
    bot.send_message(
        message.chat.id,
        "Управление задачами и привычками.\nВыберите раздел.",
        reply_markup=main_menu()
    )

@bot.message_handler(func=lambda m: True)
def router(message):
    text = message.text
    user_id = message.chat.id

    if text == "📝 Задачи":
        tasks.menu(bot, user_id)

    elif text == "🔁 Привычки":
        habits.menu(bot, user_id)

    elif text == "🎯 Фокус":
        focus.menu(bot, user_id)

    elif text == "🗒 Заметки":
        notes.menu(bot, user_id)

    elif text == "📊 Статистика":
        stats.show(bot, user_id)

    elif text == "😊 Настроение":
        stats.mood_menu(bot, user_id)

bot.polling()
