# -*- coding: utf-8 -*-
"""
Парсинг назв областей України з поля courtName.
Враховує всі області, м. Київ, м. Севастополь та Автономну Республіку Крим.
Ручні виправлення завантажуються з court_region_manual.json (якщо файл є).
"""

import json
import re
from pathlib import Path
from typing import Optional

# Шлях до ручного словника (поруч з цим модулем)
_MANUAL_MAPPING_PATH = Path(__file__).resolve().parent / "court_region_manual.json"
_manual_court_to_region: dict[str, str] | None = None


def _load_manual_mapping() -> dict[str, str]:
    """Завантажує court_region_manual.json один раз (кеш)."""
    global _manual_court_to_region
    if _manual_court_to_region is not None:
        return _manual_court_to_region
    _manual_court_to_region = {}
    if _MANUAL_MAPPING_PATH.exists():
        try:
            with _MANUAL_MAPPING_PATH.open("r", encoding="utf-8") as f:
                _manual_court_to_region = json.load(f)
        except Exception:
            pass
    return _manual_court_to_region


def reload_manual_mapping() -> None:
    """Скидає кеш ручного словника (після оновлення court_region_manual.json)."""
    global _manual_court_to_region
    _manual_court_to_region = None

# Офіційні назви регіонів України (області + окремі міста + АР Крим)
REGION_NAMES = [
    "Вінницька область",
    "Волинська область",
    "Дніпропетровська область",
    "Донецька область",
    "Житомирська область",
    "Закарпатська область",
    "Запорізька область",
    "Івано-Франківська область",
    "Київська область",
    "Кіровоградська область",
    "Луганська область",
    "Львівська область",
    "Миколаївська область",
    "Одеська область",
    "Полтавська область",
    "Рівненська область",
    "Сумська область",
    "Тернопільська область",
    "Харківська область",
    "Херсонська область",
    "Хмельницька область",
    "Черкаська область",
    "Чернівецька область",
    "Чернігівська область",
    "Автономна Республіка Крим",
    "м. Київ",
    "м. Севастополь",
]

# Типові помилки в даних (або в парсингу) -> канонічна назва з REGION_NAMES
# Додано варіанти "Xської область" (рід. вживання в записах) та "Xська область" (ном.)
REGION_TYPO_FIX: dict[str, str] = {
    "Віницька область": "Вінницька область",
    "Віницької область": "Вінницька область",
    "Діпропетровська область": "Дніпропетровська область",
    "Діпропетровської область": "Дніпропетровська область",
    "Львіська область": "Львівська область",
    "Львіської область": "Львівська область",
    "Франківська область": "Івано-Франківська область",
    "Франківської область": "Івано-Франківська область",
    "Херснська область": "Херсонська область",
    "Херснської область": "Херсонська область",
    "Запорозька область": "Запорізька область",
    "Запорозької область": "Запорізька область",
}


def _normalize_region(region: str) -> str:
    """Підставляє канонічну назву регіону за наявними виправленнями типів."""
    return REGION_TYPO_FIX.get(region, region)


def normalize_region(region: Optional[str]) -> Optional[str]:
    """
    Застосовує виправлення типів до назви регіону (для вже збережених записів).
    Якщо передано None або порожній рядок — повертає як є.
    """
    if region is None or not isinstance(region, str):
        return region
    s = region.strip()
    return _normalize_region(s) if s else region


# Усі області: у назвах судів — "Xської/цької/зької/льської області" або "Xської обл."
# (Вінницької, Чернівецької, Запорізької, Хмельницької, Тернопільської тощо)
OBLAST_PATTERN = re.compile(
    r"([А-ЯІЇЄҐ][а-яіїєґ\-]+(?:ської|цької|зької|льської|нької))\s+(області|обл\.?)",
    re.IGNORECASE,
)

# Спеціальні регіони: варіанти написання в назвах судів -> канонічна назва
SPECIAL_REGIONS = [
    # Крим — різні формулювання
    (re.compile(r"Автономної\s+Республіки\s+Крим", re.I), "Автономна Республіка Крим"),
    (re.compile(r"Автономна\s+Республіка\s+Крим", re.I), "Автономна Республіка Крим"),
    (re.compile(r"АР\s+Крим", re.I), "Автономна Республіка Крим"),
    (re.compile(r"\bАРК\b", re.I), "Автономна Республіка Крим"),
    (re.compile(r"\bКриму\b", re.I), "Автономна Республіка Крим"),
    (re.compile(r"м\.\s*Сімферополя", re.I), "Автономна Республіка Крим"),
    (re.compile(r"міста\s+Сімферополя", re.I), "Автономна Республіка Крим"),
    # м. Київ
    (re.compile(r"м\.\s*Києва", re.I), "м. Київ"),
    (re.compile(r"міста\s+Києва", re.I), "м. Київ"),
    (re.compile(r"\bКиєва\b.*?(?:суд|район)", re.I), "м. Київ"),  # суд м. Києва
    # м. Севастополь
    (re.compile(r"м\.\s*Севастополя", re.I), "м. Севастополь"),
    (re.compile(r"міста\s+Севастополя", re.I), "м. Севастополь"),
    (re.compile(r"\bСевастополя\b", re.I), "м. Севастополь"),
]

# Обласні центри: родовий відмінок "м. X" / "міста X" -> назва області
# (для судів типу "районний суд м. Полтави" -> Полтавська область)
CITY_GENITIVE_TO_OBLAST: dict[str, str] = {
    "Вінниці": "Вінницька область",
    "Луцька": "Волинська область",
    "Дніпра": "Дніпропетровська область",
    "Дніпропетровська": "Дніпропетровська область",  # рідко
    "Донецька": "Донецька область",
    "Житомира": "Житомирська область",
    "Ужгорода": "Закарпатська область",
    "Запоріжжя": "Запорізька область",
    "Івано-Франківська": "Івано-Франківська область",
    "Кропивницького": "Кіровоградська область",
    "Кіровограда": "Кіровоградська область",
    "Луганська": "Луганська область",
    "Львова": "Львівська область",
    "Миколаєва": "Миколаївська область",
    "Одеси": "Одеська область",
    "Полтави": "Полтавська область",
    "Рівного": "Рівненська область",
    "Сум": "Сумська область",
    "Тернополя": "Тернопільська область",
    "Харкова": "Харківська область",
    "Херсона": "Херсонська область",
    "Хмельницького": "Хмельницька область",
    "Черкас": "Черкаська область",
    "Чернівців": "Чернівецька область",
    "Чернігова": "Чернігівська область",
    # Київ та Севастополь — окремі одиниці, не область
    "Києва": "м. Київ",
    "Севастополя": "м. Севастополь",
    # Великі міста, що явно належать до області (не обласні центри)
    "Кривого Рогу": "Дніпропетровська область",
}

# Патерн: "м. Назва" або "міста Назва" (родовий відмінок), у т.ч. багатослівні (м. Кривого Рогу)
CITY_M_PATTERN = re.compile(
    r"(?:м\.|міста)\s+([А-ЯІЇЄҐа-яіїєґ\-]+(?:\s+[А-ЯІЇЄҐа-яіїєґ\-]+)*)",
    re.I,
)

# Апеляційні/окружні суди: "Київський апеляційний суд" -> м. Київ, "Харківський апеляційний суд" -> Харківська область
APPEAL_COURT_PATTERN = re.compile(
    r"\b([А-ЯІЇЄҐ][а-яіїєґ\-]+(?:ський|цький|зький|вський))\s+(апеляційний|окружний|міський)\s+суд",
    re.I,
)
# Винятки: місто як окремий регіон, не область
APPEAL_SPECIAL: dict[str, str] = {
    "Київський": "м. Київ",
    "Севастопольський": "м. Севастополь",
}


def _appeal_adj_to_region(adj: str) -> Optional[str]:
    """Перетворює 'Харківський'/'Одеський' -> 'Харківська/Одеська область'; Київський -> м. Київ.

    Якщо результат не входить до переліку REGION_NAMES, повертає None.
    Це захищає від неіснуючих областей типу «Багачевська область».
    """
    adj = adj.strip()
    if adj in APPEAL_SPECIAL:
        return APPEAL_SPECIAL[adj]
    for suffix in ("вський", "ський", "цький", "зький"):
        if adj.endswith(suffix):
            candidate = adj[: -len(suffix)] + suffix.replace("кий", "ка") + " область"
            return candidate if candidate in REGION_NAMES else None
    return None


def _oblast_genitive_to_nominative(adj: str) -> str:
    """Перетворює 'Тернопільської'/'Вінницької'/'Запорізької' -> '...ська/цька/зька область'."""
    adj = adj.strip()
    for suffix in ("льської", "нької", "ської", "цької", "зької"):
        if adj.endswith(suffix):
            candidate = adj[: -len(suffix)] + suffix.replace("кої", "ка") + " область"
            # Якщо ми згенерували неіснуючу область, краще повернути як є (для подальшого аналізу)
            return candidate if candidate in REGION_NAMES else adj + " область"
    return adj + " область"


def extract_region_from_court(court_name: Optional[str]) -> Optional[str]:
    """
    Витягує назву області/регіону з тексту назви суду.

    Враховує:
    - усі області України (шаблон «...ської області»);
    - м. Київ, м. Севастополь;
    - Автономну Республіку Крим (у т.ч. АР Крим, Крим, Сімферополь);
    - суди обласних центрів (наприклад «суд м. Полтави» -> Полтавська область).

    Повертає канонічну назву регіону або None, якщо не вдалося визначити.
    """
    if not court_name or not isinstance(court_name, str):
        return None
    text = court_name.strip()
    if not text:
        return None

    # 0. Ручний словник (ВИПРАВЛЕНО.xlsx -> court_region_manual.json)
    manual = _load_manual_mapping()
    if manual:
        if text in manual:
            return _normalize_region(manual[text])
        normalized = " ".join(text.split())
        if normalized in manual:
            return _normalize_region(manual[normalized])
        for key, region in manual.items():
            if " ".join(key.split()) == normalized:
                return _normalize_region(region)

    # 1. Спеціальні регіони (Крим, Київ, Севастополь) — перевіряємо першими
    for pattern, canonical in SPECIAL_REGIONS:
        if pattern.search(text):
            return _normalize_region(canonical)

    # 2. Апеляційний/окружний суд: "Київський апеляційний суд" -> м. Київ, "Харківський апеляційний суд" -> Харківська область
    appeal_m = APPEAL_COURT_PATTERN.search(text)
    if appeal_m:
        region_from_appeal = _appeal_adj_to_region(appeal_m.group(1))
        if region_from_appeal:
            return _normalize_region(region_from_appeal)

    # 3. Шаблон «Xської області» (усі області)
    m = OBLAST_PATTERN.search(text)
    if m:
        return _normalize_region(_oblast_genitive_to_nominative(m.group(1)))

    # 4. Суд міста: «м. Полтави», «міста Одеси», «м. Кривого Рогу»
    city_m = CITY_M_PATTERN.search(text)
    if city_m:
        genitive = " ".join(city_m.group(1).strip().split())  # нормалізація пробілів
        # спочатку найдовші ключі, щоб "Кривого Рогу" збіглось до "Кривого"
        for key in sorted(CITY_GENITIVE_TO_OBLAST, key=len, reverse=True):
            if genitive == key:
                return _normalize_region(CITY_GENITIVE_TO_OBLAST[key])
        if genitive in CITY_GENITIVE_TO_OBLAST:
            return _normalize_region(CITY_GENITIVE_TO_OBLAST[genitive])

    return None


def _normalize_court_name(name: str) -> str:
    """Нормалізація назви суду для зіставлення: об'єднання пробілів, trim."""
    if not name:
        return ""
    return " ".join(name.strip().split())


def lookup_region_from_known(
    court_name: Optional[str],
    known_court_to_region: dict[str, str],
) -> Optional[str]:
    """
    Визначає регіон по назві суду з довідника вже розпізнаних назв (друга фаза).

    - Точний збіг (нормалізований за пробілами);
    - Поточна назва є підрядком відомої → регіон відомої (напр. «Берегівський районний суд»
      входить у «Берегівський районний суд Закарпатської області»);
    - Відома назва є підрядком поточної → той самий регіон.
    """
    if not court_name or not isinstance(court_name, str) or not known_court_to_region:
        return None
    text = court_name.strip()
    if not text:
        return None
    normalized = _normalize_court_name(text)

    if normalized in known_court_to_region:
        return _normalize_region(known_court_to_region[normalized])
    for key, region in known_court_to_region.items():
        if _normalize_court_name(key) == normalized:
            return _normalize_region(region)

    for key in sorted(known_court_to_region, key=len, reverse=True):
        if normalized in _normalize_court_name(key):
            return _normalize_region(known_court_to_region[key])

    for key in sorted(known_court_to_region, key=len, reverse=True):
        kn = _normalize_court_name(key)
        if kn and kn in normalized:
            return _normalize_region(known_court_to_region[key])

    return None
