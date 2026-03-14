# -*- coding: utf-8 -*-
"""Клавіатури бота."""

from .reply import get_main_reply_keyboard
from .inline import get_load_all_confirmation_keyboard

__all__ = [
    "get_main_reply_keyboard",
    "get_load_all_confirmation_keyboard",
]
