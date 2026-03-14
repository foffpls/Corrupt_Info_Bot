# -*- coding: utf-8 -*-
"""
Запуск бота з кореня проєкту. Зберігає коректний sys.path для пакета bot.

Використання (з папки проєкту):
    python run_bot.py
"""
import asyncio
import sys
from pathlib import Path

# Корінь проєкту в sys.path, щоб імпорт bot.* працював
_root = Path(__file__).resolve().parent
if str(_root) not in sys.path:
    sys.path.insert(0, str(_root))

from bot.bot import main

if __name__ == "__main__":
    asyncio.run(main())
