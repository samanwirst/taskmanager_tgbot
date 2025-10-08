import logging
from aiogram import types
from aiogram import Dispatcher
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command, Text
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery
from db import Database
from config import URGENCY_LABELS, TASKS_REVERSE
import html
import uuid
import time

logger = logging.getLogger(__name__)

class AddTaskState(StatesGroup):
    waiting_urgency = State()

db: Database = None

def register_handlers(dp: Dispatcher, database: Database):
    global db
    db = database
    dp.message.register(cmd_start, Command(commands=["start", "help"]))
    dp.message.register(cmd_tasks, Command(commands=["tasks"]))
    dp.message.register(cmd_history, Command(commands=["history"]))
    dp.message.register(handle_new_task)
    dp.callback_query.register(handle_urgency_callback, Text(startswith="urg:"))
    dp.callback_query.register(handle_delete_callback, Text(startswith="delete:"))

async def cmd_start(message: Message):
    await message.reply(
        "Hey! Send me a message and I'll save it as a task with\n\n"
        "Command list:\n"
        "/tasks — show all active tasks\n"
        "/history — show full tasks history\n"
    )


async def handle_new_task(message: Message, state: FSMContext):
    if not message.text or message.text.strip().startswith("/"):
        return

    text = message.text.strip()
    if not text:
        await message.reply("Send me a text.")
        return

    token = uuid.uuid4().hex[:12]

    keyboard_rows = []
    row = []
    for idx, label in enumerate(URGENCY_LABELS):
        btn = InlineKeyboardButton(text=label, callback_data=f"urg:{token}:{idx}")
        row.append(btn)
        if len(row) == 2:
            keyboard_rows.append(row)
            row = []
    if row:
        keyboard_rows.append(row)

    kb = InlineKeyboardMarkup(inline_keyboard=keyboard_rows)

    sent = await message.reply("Choose the task urgency:", reply_markup=kb)

    data = await state.get_data()
    pending: dict = data.get("pending_tasks") or {}

    pending[token] = {
        "task_text": text,
        "keyboard_message_id": getattr(sent, "message_id", None),
        "created_at": time.time()
    }

    await state.update_data(pending_tasks=pending)
    await state.set_state(AddTaskState.waiting_urgency)

async def handle_urgency_callback(callback: CallbackQuery, state: FSMContext):
    data = (callback.data or "")
    parts = data.split(":", 2)
    if len(parts) != 3:
        await callback.answer("Incorrect urgency callback.", show_alert=True)
        return

    _prefix, token, sidx = parts
    try:
        urgency = int(sidx)
    except Exception:
        await callback.answer("Incorrect urgency.", show_alert=True)
        return

    data_state = await state.get_data()
    pending: dict = data_state.get("pending_tasks") or {}
    entry = pending.get(token)

    if not entry:
        await callback.answer("This task expired or already handled. Please send it again.", show_alert=True)
        return

    task_text = entry.get("task_text")
    if not task_text:
        await callback.answer("The task text not found. Give me another task", show_alert=True)
        pending.pop(token, None)
        await state.update_data(pending_tasks=pending)
        if not pending:
            try:
                await state.clear()
            except Exception:
                pass
        return

    tg_user = callback.from_user
    user_id = tg_user.id
    username = tg_user.username
    fullname = f"{tg_user.first_name or ''} {tg_user.last_name or ''}".strip()

    try:
        await db.upsert_user(user_id=user_id, username=username, fullname=fullname)
        task_id = await db.add_task(user_id=user_id, task_text=task_text, urgency=urgency)
        logger.info("Saved task id=%s user=%s urgency=%s", task_id, user_id, urgency)
    except Exception as e:
        logger.exception("Error saving task to DB")
        await callback.answer("Error saving task to DB", show_alert=True)
        return

    try:
        urgency_label = URGENCY_LABELS[urgency]
    except Exception:
        urgency_label = str(urgency)

    try:
        if callback.message:
            await callback.message.edit_text(
                f'The task saved!\n<i>{html.escape(task_text)}</i>\nUrgency: {urgency_label}',
                parse_mode="HTML"
            )
    except Exception:
        pass

    pending.pop(token, None)
    await state.update_data(pending_tasks=pending)

    if not pending:
        try:
            await state.clear()
        except Exception:
            pass

    await callback.answer("The task saved✅")

async def cmd_tasks(message: Message):
    user_id = message.from_user.id
    try:
        tasks = await db.get_tasks(user_id=user_id)
    except Exception:
        logger.exception("DB error when fetching tasks")
        await message.reply("DB error when fetching tasks")
        return

    if not tasks:
        await message.reply("You don't have any active tasks")
        return
    
    if TASKS_REVERSE: tasks.reverse()

    for t in tasks:
        created = t["created_at"]
        if hasattr(created, "isoformat"):
            created_str = created.isoformat(sep=" ", timespec="minutes")
        else:
            created_str = str(created)

        try:
            urgency_label = URGENCY_LABELS[t["urgency"]]
        except Exception:
            urgency_label = str(t["urgency"])

        text = (
            f"{html.escape(t['task_text'])}\n\n"
            f"Urgency: <b>{urgency_label}</b>\n"
            f"Added: <i>{created_str}</i>"
        )
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="Delete❌", callback_data=f"delete:{t['id']}")]
        ])
        await message.answer(text, reply_markup=kb, parse_mode="HTML")


async def cmd_history(message: Message):
    user_id = message.from_user.id
    try:
        tasks = await db.get_history(user_id=user_id)
    except Exception:
        logger.exception("DB error when fetching history")
        await message.reply("DB error when fetching history")
        return

    if not tasks:
        await message.reply("No tasks found")
        return

    lines = []
    for t in tasks:
        created = t["created_at"]
        if hasattr(created, "isoformat"):
            created_str = created.isoformat(sep=" ", timespec="minutes")
        else:
            created_str = str(created)

        try:
            urgency_label = URGENCY_LABELS[t["urgency"]]
        except Exception:
            urgency_label = str(t["urgency"])

        status = "Closed" if t.get("done") else "Open"
        line = (
            f"{html.escape(t['task_text'])} (id: {t['id']})\n"
            f"Urgency: <b>{urgency_label}</b>\n"
            f"Added: <i>{created_str}</i>\n"
            f"Status: <b>{status}</b>"
        )
        if t.get("done") and t.get("done_at"):
            done_at = t["done_at"]
            if hasattr(done_at, "isoformat"):
                done_str = done_at.isoformat(sep=" ", timespec="minutes")
            else:
                done_str = str(done_at)
            line += f"\nClosed: <i>{done_str}</i>"

        lines.append(line)

    MAX_LEN = 4000
    chunks = []
    cur = ""
    for entry in lines:
        addition = entry + "\n\n"
        if len(cur) + len(addition) > MAX_LEN:
            chunks.append(cur)
            cur = addition
        else:
            cur += addition
    if cur:
        chunks.append(cur)

    for ch in chunks:
        await message.answer(ch, parse_mode="HTML")


async def handle_delete_callback(callback: CallbackQuery):
    data = callback.data or ""
    user_id = callback.from_user.id

    try:
        _, id_str = data.split(":", 1)
        task_id = int(id_str)
    except Exception:
        await callback.answer("Invalid callback", show_alert=True)
        return

    try:
        ok = await db.delete_task(task_id=task_id, user_id=user_id)
    except Exception:
        logger.exception("DB error when deleting/closing task")
        await callback.answer("DB error when deleting task", show_alert=True)
        return

    if ok:
        try:
            if callback.message:
                await callback.message.edit_text("The task closed")
        except Exception:
            pass
        await callback.answer("The task closed")
    else:
        await callback.answer("The task not found", show_alert=True)