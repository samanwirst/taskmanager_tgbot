from aiogram import types
from aiogram import Dispatcher
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command, Text
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery
from db import Database
import logging

logger = logging.getLogger(__name__)

class AddTaskState(StatesGroup):
    waiting_urgency = State()

URGENCY_LABELS = {
    0: "Сегодня",
    1: "На неделю",
    2: "На месяц",
}

db: Database = None

def register_handlers(dp: Dispatcher, database: Database):
    global db
    db = database
    dp.message.register(cmd_start, Command(commands=["start", "help"]))
    dp.message.register(cmd_tasks, Command(commands=["tasks"]))
    dp.message.register(handle_new_task)
    dp.callback_query.register(handle_urgency_callback, Text(startswith="urg:"))
    dp.callback_query.register(handle_delete_callback, Text(startswith="delete:"))

async def cmd_start(message: Message):
    await message.reply(
        "Hey! Send me a message and I'll save it as a task with\n\n"
        "Command list:\n"
        "/tasks — show all tasks\n"
    )


async def handle_new_task(message: Message, state: FSMContext):
    if not message.text or message.text.strip().startswith("/"):
        return

    text = message.text.strip()
    if not text:
        await message.reply("Send me a text.")
        return

    current_state = await state.get_state()
    if current_state == AddTaskState.waiting_urgency.state:
        return

    await state.update_data(task_text=text)
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Today", callback_data="urg:0"),
         InlineKeyboardButton(text="This week", callback_data="urg:1")],
        [InlineKeyboardButton(text="This month", callback_data="urg:2")]
    ])

    sent = await message.reply("Choose the task urgency:", reply_markup=kb)
    await state.set_state(AddTaskState.waiting_urgency)


async def handle_urgency_callback(callback: CallbackQuery, state: FSMContext):
    data = (callback.data or "")
    try:
        _, s = data.split(":", 1)
        urgency = int(s)
    except Exception:
        await callback.answer("Incorrect urgency.", show_alert=True)
        return

    current_state = await state.get_state()
    if current_state != AddTaskState.waiting_urgency.state:
        await callback.answer("The dialog expired or already handled. Give me another task")
        try:
            await state.clear()
        except Exception:
            pass
        return

    data_state = await state.get_data()
    task_text = data_state.get("task_text")
    if not task_text:
        await callback.answer("The task text not found. Give me another task", show_alert=True)
        await state.clear()
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
        await state.clear()
        return

    try:
        if callback.message:
            await callback.message.edit_text(f'The task saved!\n<i>{task_text}</i>\nUrgency: {URGENCY_LABELS.get(urgency)}')
    except Exception:
        pass

    await callback.answer("The task saved✅")
    await state.clear()


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

    for t in tasks:
        created = t["created_at"]
        if hasattr(created, "isoformat"):
            created_str = created.isoformat(sep=" ", timespec="minutes")
        else:
            created_str = str(created)
        text = f"📝 <b>#{t['id']}</b>\n{t['task_text']}\n\nUrgency: <b>{URGENCY_LABELS.get(t['urgency'], t['urgency'])}</b>\nAdded: <i>{created_str}</i>"
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="Delete❌", callback_data=f"delete:{t['id']}")]
        ])
        await message.answer(text, reply_markup=kb, parse_mode="HTML")


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
        logger.exception("DB error when deleting task")
        await callback.answer("DB error when deleting task", show_alert=True)
        return

    if ok:
        try:
            if callback.message:
                await callback.message.edit_text(f"~~The task deleted~~")
        except Exception:
            pass
        await callback.answer("The task deleted")
    else:
        await callback.answer("The task not found", show_alert=True)