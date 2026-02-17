import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
REDIS_URL = os.getenv("REDIS_URL")

TASKS_PER_PAGE = 5
HABITS_PER_PAGE = 5
FOCUS_DEFAULT_MINUTES = 25
FOCUS_BREAK_MINUTES = 5
