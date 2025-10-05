# Minimalist Task Manager Telegram Bot

A **lightweight task manager inside a Telegram bot** designed for fast and simple task tracking without the overhead of complicated management tools.

The bot allows you to **quickly record, view, and delete tasks** directly from Telegram making it perfect for users who just want to keep notes without switching apps.

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

* **Task listing:**
  Use the `/tasks` command to view your saved tasks.
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

3. **Build and run the container:**

   ```bash
   docker-compose up --build -d
   ```

---

## How It Works

1. Send any text message and the bot saves it as a task.
2. Select its urgency level.
3. Retrieve all tasks anytime using `/tasks`.
4. Delete or manage tasks directly via Telegram messages.

---

## Configuration

| Variable         | Description                       | Example                                |
| ---------------- | --------------------------------- | -------------------------------------- |
| `URGENCY_LABELS` | List of urgency categories        | `["Today", "This Week", "This Month"]` |
| `TASKS_REVERSE`  | Reverse the order of task display | `True` or `False`                      |

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