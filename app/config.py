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

Minimalist Task Manager is a focused Telegram bot for rapid task capture and lightweight task management

Send any message and it will be treated as a task. The bot immediately prompts you to assign urgency using three quick buttons: <b>Today</b>, <b>This week</b>, <b>This month</b>. In two simple interactions the task is recorded!

Tasks are stored per Telegram user in a persistent database with timestamps. Use /tasks to view active tasks and /history to view the full task history. Each task display includes urgency, creation time, and a button to close the task.

Design principles: minimal UI, minimal friction, and direct capture. Features are introduced only when they preserve the core simplicity and speed of the workflow

This project is non-commercial and open source. Source code and installation instructions are available in the repository
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