import telebot
from config import BOT_TOKEN
from database import init_db
from modules import tasks, habits, focus, notes, stats

bot = telebot.TeleBot(BOT_TOKEN)

init_db()

tasks.register(bot)
habits.register(bot)
focus.register(bot)
notes.register(bot)
stats.register(bot)

bot.infinity_polling()
