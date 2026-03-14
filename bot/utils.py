# -*- coding: utf-8 -*-
"""Допоміжні функції: парсинг ПІБ, випадковий ПІБ з реєстру, спінер повідомлень."""

import asyncio
import json
import random
from pathlib import Path

from aiogram import Bot

from .core.constants import CORRUPT_DATA_PATH

try:
    from .services.corrupt_api import PersonName  # type: ignore[import]
except ImportError:
    from services.corrupt_api import PersonName  # type: ignore[import]


def parse_full_name(text: str) -> PersonName | None:
    """Парсить рядок у Прізвище Ім'я По батькові. Повертає None, якщо менше 3 частин."""
    parts = text.strip().split()
    if len(parts) < 3:
        return None
    return PersonName(
        last_name=parts[0],
        first_name=parts[1],
        patronymic=" ".join(parts[2:]),
    )


def get_random_pib_from_register(path: Path | None = None) -> str | None:
    """Повертає ПІБ однієї випадкової особи з corrupt_all_data.json або None."""
    data_path = path or CORRUPT_DATA_PATH
    if not data_path.exists():
        return None
    try:
        with data_path.open("r", encoding="utf-8") as f:
            data = json.load(f)
    except (json.JSONDecodeError, OSError):
        return None
    if isinstance(data, dict) and "items" in data:
        data = data["items"]
    if not isinstance(data, list) or not data:
        return None
    seen: set[tuple[str, str, str]] = set()
    persons: list[tuple[str, str, str]] = []
    for item in data:
        ln = (item.get("indLastNameOnOffenseMoment") or "").strip()
        fn = (item.get("indFirstNameOnOffenseMoment") or "").strip()
        pn = (item.get("indPatronymicOnOffenseMoment") or "").strip()
        if ln and fn and pn and (ln, fn, pn) not in seen:
            seen.add((ln, fn, pn))
            persons.append((ln, fn, pn))
    if not persons:
        return None
    ln, fn, pn = random.choice(persons)
    return f"{ln} {fn} {pn}"


# Емодзі для анімації очікування (пісочний годинник)
SPINNER_EMOJI = ("⏳", "⌛")
SPINNER_INTERVAL = 1.0


async def message_spinner(
    bot: Bot,
    chat_id: int,
    message_id: int,
    text_with_placeholder: str,
) -> None:
    """
    Оновлює повідомлення кожні SPINNER_INTERVAL сек, чергуючи ⏳ та ⌛.
    text_with_placeholder — рядок з одним «{}» на початку для емодзі, напр. «{} Шукаю…».
    Зупиняється по CancelledError (task.cancel()).
    """
    try:
        i = 0
        while True:
            emoji = SPINNER_EMOJI[i % 2]
            text = text_with_placeholder.format(emoji)
            try:
                await bot.edit_message_text(
                    chat_id=chat_id,
                    message_id=message_id,
                    text=text,
                )
            except Exception:
                pass
            i += 1
            await asyncio.sleep(SPINNER_INTERVAL)
    except asyncio.CancelledError:
        pass
