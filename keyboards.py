from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
def main_menu():
    markup = InlineKeyboardMarkup()
    markup.add(
        InlineKeyboardButton("📝 Задачи", callback_data="tasks"),
        InlineKeyboardButton("🔁 Привычки", callback_data="habits")
    )
    markup.add(
        InlineKeyboardButton("🎯 Фокус", callback_data="focus"),
        InlineKeyboardButton("📊 Статистика", callback_data="stats")
    )
    markup.add(
        InlineKeyboardButton("🗒 Заметки", callback_data="notes"),
        InlineKeyboardButton("😊 Настроение", callback_data="mood")
    )
    return markup
