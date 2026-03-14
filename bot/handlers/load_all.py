# -*- coding: utf-8 -*-
"""Обробники /load_all та callback підтвердження/скасування."""

import asyncio
import json
import time

import aiohttp
from aiogram import Bot
from aiogram.types import CallbackQuery, FSInputFile, Message

from ..core.constants import LOAD_ALL_CONFIRM, LOAD_ALL_CANCEL, CORRUPT_DATA_PATH
from ..keyboards import get_load_all_confirmation_keyboard

try:
    from ..config import get_settings  # type: ignore[import]
    from ..services.corrupt_api import CorruptApiClient  # type: ignore[import]
except ImportError:
    from config import get_settings  # type: ignore[import]
    from services.corrupt_api import CorruptApiClient  # type: ignore[import]


async def _load_all_status_updater(
    bot: Bot,
    chat_id: int,
    message_id: int,
    interval_sec: float = 5.0,
) -> None:
    elapsed = 0
    while True:
        await asyncio.sleep(interval_sec)
        elapsed += int(interval_sec)
        try:
            await bot.edit_message_text(
                chat_id=chat_id,
                message_id=message_id,
                text=f"⏳ Завантаження реєстру... минуло {elapsed} сек.",
            )
        except Exception:
            break


async def cmd_load_all(message: Message) -> None:
    text = (
        "⚠️ <b>Завантаження всього реєстру НАЗК</b>\n\n"
        "Процедура завантаження даних зазвичай займає <b>2–4 хвилини</b>.\n\n"
        "Підтвердити запуск чи скасувати?"
    )
    await message.answer(
        text,
        parse_mode="HTML",
        reply_markup=get_load_all_confirmation_keyboard(),
    )


def _format_duration_uk(seconds: float) -> str:
    """Формує рядок часу у форматі 'X хвилин Y секунд' з правильним відмінюванням."""
    total_sec = int(round(seconds))
    mins, secs = divmod(total_sec, 60)
    parts = []
    if mins:
        if mins == 1:
            parts.append("1 хвилина")
        elif 2 <= mins <= 4:
            parts.append(f"{mins} хвилини")
        else:
            parts.append(f"{mins} хвилин")
    if secs == 1:
        parts.append("1 секунда")
    elif 2 <= secs <= 4:
        parts.append(f"{secs} секунди")
    else:
        parts.append(f"{secs} секунд")
    return " ".join(parts) if parts else "0 секунд"


async def _do_load_all(bot: Bot, chat_id: int, message_id: int) -> None:
    started_at = time.monotonic()
    try:
        await bot.edit_message_text(
            chat_id=chat_id,
            message_id=message_id,
            text="⏳ Завантаження реєстру... минуло 0 сек.",
            reply_markup=None,
        )
    except Exception:
        pass

    settings = get_settings()
    api_client = CorruptApiClient(
        base_url=settings.corrupt_api_base_url,
        find_endpoint=settings.corrupt_find_endpoint,
        get_all_endpoint=settings.corrupt_get_all_endpoint,
    )

    updater = asyncio.create_task(
        _load_all_status_updater(bot, chat_id, message_id, interval_sec=5.0),
    )
    try:
        async with aiohttp.ClientSession() as session:
            data = await api_client.get_all_data(session)
    except Exception as exc:
        updater.cancel()
        try:
            await updater
        except asyncio.CancelledError:
            pass
        try:
            await bot.edit_message_text(
                chat_id=chat_id,
                message_id=message_id,
                text=f"❌ Помилка при зверненні до API: {exc}",
            )
        except Exception:
            await bot.send_message(chat_id, f"Сталася помилка при зверненні до API: {exc}")
        return
    finally:
        updater.cancel()
        try:
            await updater
        except asyncio.CancelledError:
            pass

    if not data:
        try:
            await bot.edit_message_text(
                chat_id=chat_id,
                message_id=message_id,
                text="API повернуло порожній список записів.",
            )
        except Exception:
            await bot.send_message(chat_id, "API повернуло порожній список записів.")
        return

    try:
        await bot.edit_message_text(
            chat_id=chat_id,
            message_id=message_id,
            text="✅ Завантаження завершено. Готую файл...",
        )
    except Exception:
        pass

    file_path = CORRUPT_DATA_PATH
    try:
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False)
    except Exception as exc:
        await bot.send_message(chat_id, f"Не вдалося зберегти файл: {exc}")
        return

    elapsed = time.monotonic() - started_at
    duration_text = _format_duration_uk(elapsed)
    caption = (
        "Файл із усіма записами реєстру корупційних правопорушень. "
        f"Час формування: {duration_text}."
    )
    doc = FSInputFile(str(file_path))
    await bot.send_document(
        chat_id=chat_id,
        document=doc,
        caption=caption,
    )


async def callback_load_all_confirm(callback: CallbackQuery) -> None:
    await callback.answer()
    if not callback.message:
        return
    await _do_load_all(
        callback.bot,
        callback.message.chat.id,
        callback.message.message_id,
    )


async def callback_load_all_cancel(callback: CallbackQuery) -> None:
    await callback.answer()
    if not callback.message:
        return
    try:
        await callback.bot.edit_message_text(
            chat_id=callback.message.chat.id,
            message_id=callback.message.message_id,
            text="❌ Команду завантаження реєстру скасовано.",
            reply_markup=None,
        )
    except Exception:
        pass
