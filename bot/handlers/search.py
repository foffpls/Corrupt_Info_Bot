# -*- coding: utf-8 -*-
"""Обробники /search та введення ПІБ для пошуку."""

import asyncio
import aiohttp
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from ..core.constants import MAIN_MENU_BUTTONS, MAX_MESSAGE_LENGTH
from ..core.states import SearchStates
from ..utils import parse_full_name, message_spinner
from .start_help import dispatch_main_menu

try:
    from ..config import get_settings  # type: ignore[import]
    from ..services.corrupt_api import CorruptApiClient  # type: ignore[import]
except ImportError:
    from config import get_settings  # type: ignore[import]
    from services.corrupt_api import CorruptApiClient  # type: ignore[import]


async def cmd_search(message: Message, state: FSMContext) -> None:
    await message.answer(
        "Введи, будь ласка, ПІБ у форматі:\n"
        "Прізвище Ім'я По-батькові\n\n"
        "Наприклад: Петренко Петро Петрович\n\n"
        "Для скасування операції натисніть /stop"
    )
    await state.set_state(SearchStates.waiting_for_full_name)


async def process_full_name(message: Message, state: FSMContext) -> None:
    full_name_text = (message.text or "").strip()
    if full_name_text in MAIN_MENU_BUTTONS:
        await dispatch_main_menu(message, state, full_name_text)
        return
    person = parse_full_name(full_name_text)

    if person is None:
        await message.answer(
            "Не вдалося розпізнати ПІБ. Переконайся, що ти ввів(ла) три частини:\n"
            "Прізвище Ім'я По-батькові (через пробіли).\n"
            "Надішли /search, щоб спробувати ще раз."
        )
        await state.clear()
        return

    status_msg = await message.answer(
        "⏳ Шукаю інформацію про: "
        f"{person.last_name} {person.first_name} {person.patronymic}…\n"
        "Зачекай кілька секунд."
    )
    chat_id = status_msg.chat.id
    message_id = status_msg.message_id
    bot = message.bot
    spinner_text = (
        "{} Шукаю інформацію про: "
        f"{person.last_name} {person.first_name} {person.patronymic}…\n"
        "Зачекай кілька секунд."
    )

    settings = get_settings()
    api_client = CorruptApiClient(
        base_url=settings.corrupt_api_base_url,
        find_endpoint=settings.corrupt_find_endpoint,
        get_all_endpoint=settings.corrupt_get_all_endpoint,
    )

    spinner_task = asyncio.create_task(
        message_spinner(bot, chat_id, message_id, spinner_text)
    )
    try:
        async with aiohttp.ClientSession() as session:
            records = await api_client.find_person_records(session, person)
    except Exception as exc:
        try:
            await bot.edit_message_text(
                chat_id=chat_id,
                message_id=message_id,
                text=f"❌ Сталася помилка при зверненні до API: {exc}",
            )
        except Exception:
            await message.answer(f"Сталася помилка при зверненні до API: {exc}")
        await state.clear()
        return
    finally:
        spinner_task.cancel()
        try:
            await spinner_task
        except asyncio.CancelledError:
            pass

    if not records:
        try:
            await bot.edit_message_text(
                chat_id=chat_id,
                message_id=message_id,
                text="У реєстрі НАЗК не знайдено інформації щодо цієї особи.",
            )
        except Exception:
            await message.answer("У реєстрі НАЗК не знайдено інформації щодо цієї особи.")
        await state.clear()
        return

    matched = [
        item for item in records
        if (item.get("indLastNameOnOffenseMoment") or "").strip().lower() == person.last_name.lower()
        and (item.get("indFirstNameOnOffenseMoment") or "").strip().lower() == person.first_name.lower()
        and (item.get("indPatronymicOnOffenseMoment") or "").strip().lower() == person.patronymic.lower()
    ]

    if not matched:
        try:
            await bot.edit_message_text(
                chat_id=chat_id,
                message_id=message_id,
                text=(
                    "API повернуло дані, але точних збігів за вказаним ПІБ не знайдено.\n"
                    "Можливо, особа є у реєстрі з іншим написанням ПІБ."
                ),
            )
        except Exception:
            await message.answer(
                "API повернуло дані, але точних збігів за вказаним ПІБ не знайдено."
            )
        await state.clear()
        return

    max_records_to_show = 3
    parts = []
    for idx, item in enumerate(matched[:max_records_to_show], start=1):
        full_name = (
            f"{item.get('indLastNameOnOffenseMoment', '').strip()} "
            f"{item.get('indFirstNameOnOffenseMoment', '').strip()} "
            f"{item.get('indPatronymicOnOffenseMoment', '').strip()}"
        ).strip()
        punishment_type = None
        if isinstance(item.get("punishmentType"), dict):
            punishment_type = item["punishmentType"].get("name") or None
        entity_type = None
        if isinstance(item.get("entityType"), dict):
            entity_type = item["entityType"].get("name") or None
        offense_name = item.get("offenseName") or "(немає опису правопорушення)"
        punishment = item.get("punishment") or "(немає опису покарання)"
        court_name = item.get("courtName") or "(невідомий суд)"
        court_case_number = item.get("courtCaseNumber") or "(немає номера справи)"
        sentence_date = item.get("sentenceDate") or "(немає дати вироку)"
        sentence_number = item.get("sentenceNumber") or "(немає номера вироку)"
        punishment_start = item.get("punishmentStart") or "(немає дати початку покарання)"
        articles = []
        for art in item.get("codexArticles") or []:
            if isinstance(art, dict) and art.get("codexArticleName"):
                articles.append(art["codexArticleName"])
        articles_text = "; ".join(articles) if articles else "(немає даних про статті)"
        block = (
            f"🧑‍⚖️ *Запис {idx}*\n"
            f"👤 *ПІБ:* {full_name or '(немає ПІБ)'}\n"
            f"🏷 *Тип суб'єкта:* {entity_type or '(невідомо)'}\n"
            f"⚖️ *Тип покарання:* {punishment_type or '(невідомо)'}\n\n"
            "📌 *Правопорушення*\n"
            f"{offense_name}\n\n"
            "📄 *Опис покарання*\n"
            f"{punishment}\n\n"
            "🏛 *Судове рішення*\n"
            f"Суд: {court_name}\n"
            f"Номер справи: {court_case_number}\n"
            f"Дата вироку: {sentence_date}\n"
            f"Номер вироку: {sentence_number}\n"
            f"Початок покарання: {punishment_start}\n\n"
            "📚 *Статті кодексу*\n"
            f"{articles_text}"
        )
        parts.append(block)

    footer = f"\n\nПоказано перші {max_records_to_show} запис(и) з {len(matched)}." if len(matched) > max_records_to_show else ""
    full_text = "\n\n".join(parts) + footer
    if len(full_text) > MAX_MESSAGE_LENGTH:
        full_text = full_text[: MAX_MESSAGE_LENGTH - 20] + "\n\n… (обрізано)"

    try:
        await bot.edit_message_text(
            chat_id=chat_id,
            message_id=message_id,
            text=full_text,
            parse_mode="Markdown",
        )
    except Exception:
        await message.answer(full_text, parse_mode="Markdown")

    await state.clear()
