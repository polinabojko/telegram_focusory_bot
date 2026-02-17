from datetime import date, timedelta
from database import cursor, conn
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

def habit_activity_graph(bot, call, habit_id):
    today = date.today()
    week_ago = today - timedelta(days=6)

    cursor.execute("""
        SELECT marked_date
        FROM habit_logs
        WHERE habit_id = %s
        AND marked_date >= %s
        ORDER BY marked_date ASC
    """, (habit_id, week_ago))

    marked_days = [row[0] for row in cursor.fetchall()]

    graph = "📊 Активность за 7 дней:\n\n"

    for i in range(7):
        day = week_ago + timedelta(days=i)
        symbol = "✅" if day in marked_days else "❌"
        graph += f"{day.strftime('%a %d.%m')} {symbol}\n"

    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("⬅ Назад", callback_data="list_habits"))

    bot.edit_message_text(
        graph,
        call.message.chat.id,
        call.message.message_id,
        reply_markup=markup
    )
