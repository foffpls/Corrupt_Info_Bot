# -*- coding: utf-8 -*-
"""Константи бота: callback_data, кнопки, шляхи, ліміти."""

from pathlib import Path

# Інлайн-кнопки /load_all
LOAD_ALL_CONFIRM = "load_all:confirm"
LOAD_ALL_CANCEL = "load_all:cancel"

# Контакт розробника для /help (екранується для HTML)
DEVELOPER_CONTACT = "@foff_pls"

# Тексти кнопок reply-клавіатури
BTN_SEARCH = "🔍 Пошук"
BTN_ANALYZE = "🤖 Аналіз (AI)"
BTN_LOAD_ALL = "📥 Завантажити реєстр (JSON)"
BTN_HELP = "📋 Переглянути довідку"
MAIN_MENU_BUTTONS = {BTN_SEARCH, BTN_ANALYZE, BTN_LOAD_ALL, BTN_HELP}

# Шлях до реєстру (корінь проєкту)
CORRUPT_DATA_PATH = Path(__file__).resolve().parent.parent.parent / "corrupt_all_data.json"

# Ліміт довжини повідомлення Telegram
MAX_MESSAGE_LENGTH = 4096
