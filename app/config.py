from dotenv import load_dotenv
import os

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
DATABASE_URL = os.getenv("DATABASE_URL")

URGENCY_LABELS = [
    "Today",
    "This week",
    "This month",
]

# For me much better if there are a lot of tasks and the most urgent ones are in the end of the chat 
TASKS_REVERSE = True

INFO_MESSAGE = """
<b>About this bot</b>

This bot saves quick tasks for you — send a message, choose urgency and it's stored.
You can view active tasks with /tasks and full history with /history.
"""

INFO_BUTTONS = [
    ("Source code", "https://github.com/samanwirst/taskmanager_tgbot"),
    ("Author", "https://t.me/samanwirst"),
]

if not BOT_TOKEN:
    raise RuntimeError("BOT_TOKEN is not set in environment")
if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL is not set in environment")
if not URGENCY_LABELS:
    raise RuntimeError("URGENCY_LABELS is not defined")