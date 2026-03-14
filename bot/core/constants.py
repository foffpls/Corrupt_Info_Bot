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
BTN_DOWNLOAD_TZ = "📎 Завантажити файли ТЗ"
MAIN_MENU_BUTTONS = {BTN_SEARCH, BTN_ANALYZE, BTN_LOAD_ALL, BTN_HELP, BTN_DOWNLOAD_TZ}

# Файли ТЗ (корінь проєкту)
_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
TZ_FILE_IPYNB = _PROJECT_ROOT / "eda_corruptinfo.ipynb"
TZ_FILE_PPTX = _PROJECT_ROOT / "EDA реєстру корупційних правопорушень НАЗК.pptx"

# Шлях до реєстру (корінь проєкту)
CORRUPT_DATA_PATH = Path(__file__).resolve().parent.parent.parent / "corrupt_all_data.json"

# Ліміт довжини повідомлення Telegram
MAX_MESSAGE_LENGTH = 4096
