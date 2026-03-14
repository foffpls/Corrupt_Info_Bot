# -*- coding: utf-8 -*-
"""
Точка входу бота. Реєстрація обробників та запуск polling.
Запуск з кореня проєкту: python -m bot.bot  або  python run_bot.py
"""

import asyncio
import sys
from pathlib import Path

_PROJECT_ROOT = Path(__file__).resolve().parent.parent

from aiogram import Bot, Dispatcher, F
from aiogram.filters import Command
from aiogram.fsm.storage.memory import MemoryStorage

try:
    from .core import (
        LOAD_ALL_CONFIRM,
        LOAD_ALL_CANCEL,
        MAIN_MENU_BUTTONS,
        SearchStates,
        AnalyzeStates,
    )
    from .config import get_settings  # type: ignore[import]
    from .handlers import (
        cmd_start,
        cmd_help,
        cmd_stop,
        cmd_revelio,
        handle_main_menu_button,
        handle_unknown_input,
        cmd_search,
        process_full_name,
        cmd_analyze,
        process_analyze_name,
        cmd_load_all,
        callback_load_all_confirm,
        callback_load_all_cancel,
    )
except ImportError:
    # Запуск як скрипт (python bot/bot.py): корінь проєкту має бути першим у sys.path
    sys.path.insert(0, str(_PROJECT_ROOT))
    from bot.core import (
        LOAD_ALL_CONFIRM,
        LOAD_ALL_CANCEL,
        MAIN_MENU_BUTTONS,
        SearchStates,
        AnalyzeStates,
    )
    from bot.config import get_settings  # type: ignore[import]
    from bot.handlers import (
        cmd_start,
        cmd_help,
        cmd_stop,
        cmd_revelio,
        handle_main_menu_button,
        handle_unknown_input,
        cmd_search,
        process_full_name,
        cmd_analyze,
        process_analyze_name,
        cmd_load_all,
        callback_load_all_confirm,
        callback_load_all_cancel,
    )


async def main() -> None:
    settings = get_settings()
    bot = Bot(token=settings.bot_token)
    dp = Dispatcher(storage=MemoryStorage())

    # Порядок реєстрації важливий: спочатку команди, потім кнопки меню, потім FSM, в кінці — catch-all.
    dp.message.register(cmd_start, Command("start"))
    dp.message.register(cmd_help, Command("help"))
    dp.message.register(cmd_stop, Command("stop"))
    dp.message.register(cmd_search, Command("search"))
    dp.message.register(cmd_analyze, Command("analyze"))
    dp.message.register(cmd_load_all, Command("load_all"))
    dp.message.register(cmd_revelio, Command("revelio"))
    dp.message.register(handle_main_menu_button, F.text.in_(MAIN_MENU_BUTTONS))
    dp.callback_query.register(callback_load_all_confirm, F.data == LOAD_ALL_CONFIRM)
    dp.callback_query.register(callback_load_all_cancel, F.data == LOAD_ALL_CANCEL)
    dp.message.register(
        process_full_name,
        SearchStates.waiting_for_full_name,
        F.text,
    )
    dp.message.register(
        process_analyze_name,
        AnalyzeStates.waiting_for_full_name,
        F.text,
    )
    dp.message.register(handle_unknown_input)

    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
