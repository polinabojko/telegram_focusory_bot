import os

TOKEN = os.getenv("BOT_TOKEN")
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
DB_NAME = "bot.db"

POMODORO_BREAK = 5  # минут перерыв
XP_PER_FOCUS_MIN = 2
XP_PER_TASK = 5
XP_PER_HABIT = 3
