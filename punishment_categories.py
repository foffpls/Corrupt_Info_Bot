# -*- coding: utf-8 -*-
"""
Правила категоризації покарань (поле punishment).
Використовується в export_punishment_list.py та в ноутбуці eda_corruptinfo.ipynb.
"""


def punishment_category(text: str) -> str:
    """
    Визначає категорію покарання за ключовими словами (регістр не враховується).
    Порядок перевірок важливий: спочатку більш специфічні формулювання.
    """
    if not text or not isinstance(text, str):
        return "Інше"
    t = text.lower().strip()
    if not t:
        return "Інше"

    if "сувора догана" in t:
        return "Сувора догана"
    if "догана" in t:
        return "Догана"
    # Звільнення — лише якщо немає ознак покарання у вигляді позбавлення/обмеження волі чи засудження
    if ("звільнення" in t or "звільнння" in t) and "позбавлення волі" not in t and "обмеження волі" not in t and "засуджено" not in t:
        return "Звільнення"
    if "попередження" in t:
        return "Попередження"
    # Відсутні, але не якщо є "визнано винним"
    if "визнано винним" not in t:
        if "відсутні" in t or "відсчутні" in t or "відсутін" in t or "відстуні" in t:
            return "Відсутні"
        if t.strip() == "-":
            return "Відсутні"
    if (
        "штраф" in t or "штрафу" in t or "стягнути" in t or "відрахуванням" in t
        or "неоподаткованих мінімумів" in t or "грн" in t or "гривень" in t
    ):
        return "Штраф"
    if "зауваження" in t:
        return "Зауваження"
    if (
        "волі" in t or "обмеження волі" in t or "засуджено" in t or "обмеженням волі" in t
        or "арешту" in t or "обмеженна волі" in t or "волі строком" in t
    ):
        return "Позбавлення волі"
    if "без розгляду" in t or "позов не заявлено" in t or "позову відмовити" in t:
        return "Без розгляду"
    if "громадських робіт" in t or "громадські роботи" in t:
        return "Громадські роботи"

    return "Інше"
