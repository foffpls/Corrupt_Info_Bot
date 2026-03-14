# -*- coding: utf-8 -*-
"""Reply-клавіатури."""

from aiogram.types import KeyboardButton, ReplyKeyboardMarkup

from ..core.constants import BTN_ANALYZE, BTN_HELP, BTN_LOAD_ALL, BTN_SEARCH


def get_main_reply_keyboard() -> ReplyKeyboardMarkup:
    """Reply-клавіатура для керування ботом."""
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=BTN_SEARCH), KeyboardButton(text=BTN_ANALYZE)],
            [KeyboardButton(text=BTN_LOAD_ALL)],
            [KeyboardButton(text=BTN_HELP)],
        ],
        resize_keyboard=True,
        is_persistent=True,
    )
