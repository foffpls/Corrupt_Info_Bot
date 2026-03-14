# -*- coding: utf-8 -*-
"""
Формування короткого висновку про корупційні ризики людини за допомогою Google Gemini.
Дані беруться з реєстру (corrupt_all_data.json / DataFrame з пункту 3).
"""

from __future__ import annotations

import asyncio
import json
import re
from pathlib import Path
from typing import Any


def _format_gemini_error(exc: BaseException) -> str:
    """Повертає зрозуміле українською повідомлення для помилок Gemini API."""
    msg = str(exc).strip()
    # 429 / квота перевищена (free tier)
    if "429" in msg or "RESOURCE_EXHAUSTED" in msg or "quota" in msg.lower() or "exceeded" in msg.lower():
        out = (
            "⚠️ Перевищено ліміт запитів до сервісу аналізу (Gemini). "
            "Безкоштовний рівень обмежує кількість запитів на день."
        )
        # Спроба витягнути час очікування (наприклад "Please retry in 18.49688816s" або retryDelay)
        retry_match = re.search(r"retry in (\d+(?:\.\d+)?)\s*s", msg, re.IGNORECASE)
        if not retry_match:
            retry_match = re.search(r"retryDelay['\"]?\s*:\s*['\"]?(\d+)", msg)
        if retry_match:
            try:
                sec = float(retry_match.group(1))
                if sec >= 60:
                    out += f" Спробуй ще раз через {int(sec // 60)} хв."
                else:
                    out += f" Спробуй ще раз через {int(round(sec))} сек."
            except (ValueError, IndexError):
                out += " Спробуй повторити запит через кілька хвилин."
        else:
            out += " Спробуй повторити запит через кілька хвилин або завтра."
        return out
    # Загальна помилка
    if len(msg) > 200:
        msg = msg[:197] + "..."
    return f"Помилка при формуванні висновку: {msg}"

# Шлях до дампу реєстру (корінь проєкту)
DEFAULT_DATA_PATH = Path(__file__).resolve().parent.parent.parent / "corrupt_all_data.json"

# Інструкція для Gemini
GEMINI_SYSTEM_INSTRUCTION = """Ти — аналітичний асистент, який формує короткий висновок про корупційні ризики особи 
на основі даних з офіційного реєстру НАЗК.

На вхід передаються записи з реєстру корупційних правопорушень щодо конкретної особи.

Проаналізуй записи та врахуй такі фактори:
1. Наявність особи в реєстрі.
2. Тип правопорушення (адміністративне або кримінальне).
3. Важкість порушення (характер статті та тип покарання).
4. Тип вироку або санкції (штраф, заборона займати посади, громадські роботи, позбавлення волі тощо).
5. Кількість правопорушень.
6. Дату справи або рішення суду (якщо є) та давність події.

Правила оцінки ризику:
- Якщо особа відсутня у реєстрі → ризик низький.
- Якщо є одне адміністративне правопорушення зі штрафом → ризик середній.
- Якщо є кілька правопорушень → ризик підвищений.
- Якщо є кримінальні статті, заборона займати посади або інші серйозні санкції → ризик високий.
- Старі справи (більше 5–7 років) можуть зменшувати рівень ризику, якщо нових порушень немає. (Врахуй що зараз уже 2026 рік)

Твоє завдання — написати короткий висновок природною мовою.

Формат відповіді:
3–5 речень українською мовою.

Структура відповіді:
1. Чи присутня особа в реєстрі та короткий опис порушень.
2. Характер правопорушень, їх важкість, тип покарання та давність справ. Якщо був штрав то вкаши суму в гривнях.
3. Узагальнений рівень корупційного ризику.
4. Коротка рекомендація щодо видачі позики (рекомендується / потребує додаткової перевірки / не рекомендується).

Пиши нейтрально, без емоційних оцінок, лише на основі наданих даних.
Якщо певної інформації (наприклад дати або виду покарання) немає — не роби припущень і не згадуй її у висновку."""


def _load_register_data(path: Path | None = None) -> list[dict[str, Any]] | None:
    path = path or DEFAULT_DATA_PATH
    if not path.exists():
        return None
    try:
        with path.open("r", encoding="utf-8") as f:
            data = json.load(f)
    except (json.JSONDecodeError, OSError):
        return None
    if isinstance(data, list):
        return data
    if isinstance(data, dict) and "items" in data and isinstance(data["items"], list):
        return data["items"]
    return None


def _find_person_in_data(
    records: list[dict[str, Any]],
    last_name: str,
    first_name: str,
    patronymic: str,
) -> list[dict[str, Any]]:
    last = last_name.strip().lower()
    first = first_name.strip().lower()
    pat = patronymic.strip().lower()
    matched: list[dict[str, Any]] = []
    for item in records:
        ln = (item.get("indLastNameOnOffenseMoment") or "").strip().lower()
        fn = (item.get("indFirstNameOnOffenseMoment") or "").strip().lower()
        pn = (item.get("indPatronymicOnOffenseMoment") or "").strip().lower()
        if ln == last and fn == first and pn == pat:
            matched.append(item)
    return matched


def _format_records_for_prompt(records: list[dict[str, Any]]) -> str:
    parts: list[str] = []
    for i, item in enumerate(records, start=1):
        full_name = (
            f"{item.get('indLastNameOnOffenseMoment', '')} "
            f"{item.get('indFirstNameOnOffenseMoment', '')} "
            f"{item.get('indPatronymicOnOffenseMoment', '')}"
        ).strip()
        punishment_type = ""
        if isinstance(item.get("punishmentType"), dict):
            punishment_type = (item["punishmentType"].get("name") or "").strip()
        entity_type = ""
        if isinstance(item.get("entityType"), dict):
            entity_type = (item["entityType"].get("name") or "").strip()
        offense_name = (item.get("offenseName") or "").strip()
        punishment = (item.get("punishment") or "").strip()
        court_name = (item.get("courtName") or "").strip()
        sentence_date = (item.get("sentenceDate") or "").strip()
        articles: list[str] = []
        for art in item.get("codexArticles") or []:
            if isinstance(art, dict) and art.get("codexArticleName"):
                articles.append(art["codexArticleName"].strip())
        block = (
            f"[Запис {i}] ПІБ: {full_name}. "
            f"Тип суб'єкта: {entity_type}. Тип покарання: {punishment_type}. "
            f"Правопоручення: {offense_name}. Покарання: {punishment}. "
            f"Суд: {court_name}. Дата вироку: {sentence_date}. "
            f"Статті: {'; '.join(articles) if articles else '—'}."
        )
        parts.append(block)
    return "\n\n".join(parts)


def _call_gemini_sync(api_key: str, person_full_name: str, records_text: str) -> str:
    try:
        from google import genai
    except ImportError as e:
        return (
            "Не вдалося підключити сервіс аналізу (Gemini). "
            "Встановіть пакет: pip install google-genai"
        ) + f" [{e}]"

    client = genai.Client(api_key=api_key)
    # Системну інструкцію вставляємо в початок запиту, щоб обійти помилку
    # TypedDict.extra_items при передачі config (несумісність google-genai з частиною середовищ Python).
    prompt = (
        f"{GEMINI_SYSTEM_INSTRUCTION}\n\n---\n\n"
        f"Особа: {person_full_name}\n\n"
        "Записи з реєстру:\n"
        f"{records_text}"
    )
    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt,
    )
    if not response or not response.text:
        return "Не вдалося отримати відповідь від сервісу аналізу."
    return response.text.strip()


async def get_corruption_risk_summary(
    full_name: str,
    *,
    data_path: Path | None = None,
    gemini_api_key: str = "",
    second_gemini_api_key: str = "",
) -> str:
    parts = full_name.strip().split()
    if len(parts) < 3:
        return "Некоректний формат ПІБ. Потрібно: Прізвище Ім'я По батькові."

    last_name = parts[0]
    first_name = parts[1]
    patronymic = " ".join(parts[2:])

    data = _load_register_data(data_path)
    if data is None:
        return (
            "Файл реєстру (corrupt_all_data.json) не знайдено або він пошкоджений. "
            "Спочатку виконай команду /load_all, щоб завантажити дані реєстру."
        )

    matched = _find_person_in_data(data, last_name, first_name, patronymic)
    if not matched:
        return (
            f"У реєстрі корупційних правопорушень НАЗК не знайдено записів щодо особи "
            f"«{last_name} {first_name} {patronymic}». Дані про корупційні ризики цієї особи в реєстрі відсутні."
        )

    if not gemini_api_key:
        return (
            "Не налаштовано GEMINI_API_KEY. Додай ключ у .env для отримання текстового висновку. "
            "Зараз особа знайдена в реєстрі, записів: " + str(len(matched)) + "."
        )

    records_text = _format_records_for_prompt(matched)
    person_display = f"{last_name} {first_name} {patronymic}"
    loop = asyncio.get_event_loop()

    # Спочатку пробуємо основний ключ
    try:
        result = await loop.run_in_executor(
            None,
            lambda: _call_gemini_sync(gemini_api_key, person_display, records_text),
        )
        return result
    except Exception as e:
        # Якщо є другий ключ (429/квота або будь-яка помилка) — пробуємо його
        if second_gemini_api_key:
            try:
                result = await loop.run_in_executor(
                    None,
                    lambda: _call_gemini_sync(
                        second_gemini_api_key, person_display, records_text
                    ),
                )
                return result
            except Exception as e2:
                return _format_gemini_error(e2)
        return _format_gemini_error(e)
