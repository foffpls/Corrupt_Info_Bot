# -*- coding: utf-8 -*-
"""Обробники /analyze та введення ПІБ для аналізу."""

import asyncio
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from ..core.constants import MAIN_MENU_BUTTONS
from ..core.states import AnalyzeStates
from ..utils import message_spinner
from .start_help import dispatch_main_menu

try:
    from ..config import get_settings  # type: ignore[import]
    from ..services.analyze import get_corruption_risk_summary  # type: ignore[import]
except ImportError:
    from config import get_settings  # type: ignore[import]
    from services.analyze import get_corruption_risk_summary  # type: ignore[import]


async def cmd_analyze(message: Message, state: FSMContext) -> None:
    await message.answer(
        "Введи ПІБ у форматі: Прізвище Ім'я По-батькові\n\n"
        "Наприклад: Петренко Петро Петрович\n\n"
        "Для скасування операції натисніть /stop"
    )
    await state.set_state(AnalyzeStates.waiting_for_full_name)


async def process_analyze_name(message: Message, state: FSMContext) -> None:
    full_name_text = (message.text or "").strip()
    if full_name_text in MAIN_MENU_BUTTONS:
        await dispatch_main_menu(message, state, full_name_text)
        return
    # Якщо прийшла команда як текст (без entity), перенаправити в обробник команди
    if full_name_text in ("/search", "/analyze", "/stop"):
        from .start_help import cmd_stop
        if full_name_text == "/stop":
            await cmd_stop(message, state)
        elif full_name_text == "/search":
            from .search import cmd_search
            await cmd_search(message, state)
        else:
            await cmd_analyze(message, state)
        return
    if not full_name_text:
        await message.answer("ПІБ не введено. Спробуй ще раз або надішли /analyze.")
        await state.clear()
        return

    status_msg = await message.answer("⏳ Аналізую…")
    chat_id = status_msg.chat.id
    message_id = status_msg.message_id
    bot = message.bot

    spinner_task = asyncio.create_task(
        message_spinner(bot, chat_id, message_id, "{} Аналізую…")
    )
    try:
        settings = get_settings()
        summary = await get_corruption_risk_summary(
            full_name_text,
            gemini_api_key=settings.gemini_api_key,
        )
    finally:
        spinner_task.cancel()
        try:
            await spinner_task
        except asyncio.CancelledError:
            pass

    try:
        await bot.edit_message_text(
            chat_id=chat_id,
            message_id=message_id,
            text=summary,
        )
    except Exception:
        await message.answer(summary)
    await state.clear()
