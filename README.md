# Minimalist Task Manager Telegram Bot

A **lightweight task manager inside a Telegram bot** designed for fast and simple task tracking without the overhead of complicated management tools.

The bot allows you to **quickly record, view, close, and review tasks** directly from Telegram making it perfect for users who just want to keep notes without switching apps.

---

## Features

* **Instant task creation:**
  Simply send a message and the bot automatically treats it as a task and asks for its urgency level.

* **Urgency levels:**
  Task urgency is defined in the `URGENCY_LABELS` list. 
  The higher the index, the longer the time horizon:

  ```
  0 < 1 < 2 = today < week < month
  ```

* **Task listing & ordering:**
  Use the `/tasks` command to view your active tasks. 
  Each task is displayed as a separate message showing:

  * Task text
  * Urgency level
  * Creation date & time

* **Custom sorting:**
  By default, the most urgent tasks appear at the top (today -> week -> month).
  You can reverse this order by setting:

  ```python
  TASKS_REVERSE = True
  ```
* **Close (complete) tasks:**
  Pressing the **Delete❌** button on a task does **not** permanently erase it — the bot marks it as closed (`done = true`) and records the `done_at` timestamp. Closed tasks are excluded from `/tasks` but remain in history.

* **Full task history:**
  Use `/history` to retrieve the full task history (open and closed tasks) including creation times, urgency and close timestamps.

* **Per-user storage:**
  Tasks are stored per Telegram user. The bot upserts basic user info (id, username, fullname) on first interaction.

---

## Tech Stack

* **Framework:** [Aiogram 3](https://docs.aiogram.dev/en/latest/)
* **Database:** PostgreSQL
* **Containerization:** Docker & Docker Compose

---

## Setup & Installation

1. **Clone the repository:**

```bash
git clone https://github.com/samanwirst/taskmanager_tgbot
cd taskmanager_tgbot
```

2. **Create a `.env` file** in the root directory and set your environment variables:

```env
BOT_TOKEN="YOUR_TELEGRAM_BOT_TOKEN"
DATABASE_URL="YOUR_DATABASE_URL"
```

> The running code expects both `BOT_TOKEN` and `DATABASE_URL` to be present — the config validates and raises an error if either is missing.

**Run with Docker Compose (recommended):**

```bash
docker-compose up --build -d
```

**Or run locally:**

1. Create a virtual environment and install dependencies (project provides requirements):

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

2. Start the bot:

```bash
python app/main.py
```

---

## How It Works

1. Send any text message and the bot saves it as a task.
2. Select its urgency level.
3. Retrieve active tasks anytime using `/tasks`.
4. Close a task using the **Delete❌** button.
5. Use `/history` to inspect all tasks (open and closed) and their timestamps.

---

## Configuration

| Variable         | Description                       | Example                                |
| ---------------- | --------------------------------- | -------------------------------------- |
| `URGENCY_LABELS` | List of urgency categories        | `["Today", "This Week", "This Month"]` |
| `TASKS_REVERSE`  | Reverse the order of task display | `True` or `False`                      |
| `BOT_TOKEN`      | Telegram bot token (required)     | `123456:ABC...`                        |
| `DATABASE_URL`   | PostgreSQL DSN (required)         | `postgresql://user:pass@host:5432/db`  |

Notes:

* The database schema is created/updated on startup. The `tasks` table includes `done` (boolean) and `done_at` (timestamp with timezone) columns. Deleting a task in the UI simply marks it done.
* The code uses a small `asyncpg` pool (min_size=1, max_size=5) for efficient async DB access.
* `INFO_MESSAGE` and `INFO_BUTTONS` contain bot information and external links; invalid entries are ignored safely.

---

## Example `.env`

```env
BOT_TOKEN=1234567890:ABCDEFG_your_token_here
DATABASE_URL=postgresql://user:password@db:5432/tasks_db
```

---

## Author

**Mukhammadiev Samandar**

[GitHub: @samanwirst](https://github.com/samanwirst)

[Telegram: @samanwirst](https://t.me/samanwirst)