# -*- coding: utf-8 -*-
"""Обробники /start, /help, /stop, /revelio, меню та невідомий ввід."""

import html

from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from ..core.constants import (
    DEVELOPER_CONTACT,
    MAIN_MENU_BUTTONS,
    BTN_HELP,
    BTN_SEARCH,
    BTN_ANALYZE,
    BTN_LOAD_ALL,
)
from ..keyboards import get_main_reply_keyboard


async def cmd_start(message: Message) -> None:
    text = (
        "Привіт! Я бот для пошуку інформації в реєстрі корупційних правопорушень НАЗК.\n\n"
        "Доступні команди:\n"
        "/start — привітання\n"
        "/help — опис можливостей\n"
        "/search — пошук за ПІБ (Прізвище Ім'я По батькові)\n"
        "/load_all — завантажити весь реєстр у файлі JSON\n"
        "/analyze — короткий висновок про корупційні ризики за ПІБ\n\n"
        "Можна також керувати кнопками внизу 👇"
    )
    await message.answer(text, reply_markup=get_main_reply_keyboard())


async def cmd_help(message: Message) -> None:
    contact = html.escape(DEVELOPER_CONTACT)
    nazk_url = "https://corruptinfo.nazk.gov.ua/"
    text = (
        "📋 <b>Довідка по боту</b>\n\n"
        "🔍 <b>Що вміє бот</b>\n"
        "Пошук та аналіз інформації в офіційному реєстрі корупційних правопорушень НАЗК: пошук за ПІБ, завантаження реєстру, короткий висновок про корупційні ризики (AI).\n\n"
        "📌 <b>Команди</b>\n\n"
        "▶ /start — привітання та список команд\n\n"
        "▶ /search — пошук особи в реєстрі за ПІБ\n"
        "   Введи ПІБ після команди → отримаєш записи з реєстру (суд, покарання, статті тощо).\n\n"
        "▶ /load_all — завантажити весь реєстр у один JSON-файл\n"
        "   Під час завантаження показується прогрес по часу; у кінці надсилається файл.\n\n"
        "▶ /analyze — висновок про корупційні ризики за ПІБ\n"
        "   Потрібен попередньо завантажений реєстр (/load_all) та налаштований GEMINI_API_KEY. Текст висновку — з урахуванням давності, суду та рекомендацією.\n\n"
        "✏️ <b>Формат ПІБ</b>\n"
        "Три частини через пробіл:\n"
        "• <b>Прізвище</b> <b>Ім'я</b> <b>По батькові</b>\n"
        "Приклад: <i>Петренко Петро Петрович</i>\n\n"
        "📩 <b>Контакт розробника</b>\n"
        f"Питання та пропозиції: {contact}\n"
        f"NAZK: {nazk_url}\n"
    )
    await message.answer(text, parse_mode="HTML", reply_markup=get_main_reply_keyboard())


async def cmd_stop(message: Message, state: FSMContext) -> None:
    await state.clear()
    await message.answer("Операцію скасовано.")


async def cmd_revelio(message: Message) -> None:
    from ..utils import get_random_pib_from_register
    pib = get_random_pib_from_register()
    if not pib:
        await message.answer(
            "Реєстр не знайдено або він порожні. Спочатку виконай /load_all."
        )
        return
    text = f"Випадкова особа з реєстру:\n\n<code>{html.escape(pib)}</code>"
    await message.answer(text, parse_mode="HTML")


async def dispatch_main_menu(message: Message, state: FSMContext, button_text: str) -> None:
    """Викликає відповідну команду за текстом кнопки reply-меню."""
    await state.clear()
    if button_text == BTN_HELP:
        await cmd_help(message)
    elif button_text == BTN_SEARCH:
        from .search import cmd_search
        await cmd_search(message, state)
    elif button_text == BTN_ANALYZE:
        from .analyze import cmd_analyze
        await cmd_analyze(message, state)
    elif button_text == BTN_LOAD_ALL:
        from .load_all import cmd_load_all
        await cmd_load_all(message)


async def handle_main_menu_button(message: Message, state: FSMContext) -> None:
    text = (message.text or "").strip()
    if text in MAIN_MENU_BUTTONS:
        await dispatch_main_menu(message, state, text)


async def handle_unknown_input(message: Message, state: FSMContext) -> None:
    await state.clear()
    text = (
        "Мене писали вночі. Мій розробник обділив мене інтелектом спілкуватися із Вами повноцінно.\n\n"
        "Користуйтесь, будь ласка, меню чи командами!"
    )
    await message.answer(text, reply_markup=get_main_reply_keyboard())
