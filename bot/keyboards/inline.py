# -*- coding: utf-8 -*-
"""Інлайн-клавіатури."""

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from ..core.constants import LOAD_ALL_CANCEL, LOAD_ALL_CONFIRM


def get_load_all_confirmation_keyboard() -> InlineKeyboardMarkup:
    """Інлайн-клавіатура підтвердження для /load_all."""
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✅ Підтвердити", callback_data=LOAD_ALL_CONFIRM),
            InlineKeyboardButton(text="❌ Скасувати", callback_data=LOAD_ALL_CANCEL),
        ],
    ])
