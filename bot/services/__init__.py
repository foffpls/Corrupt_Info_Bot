# -*- coding: utf-8 -*-
"""Сервіси: API НАЗК, аналіз через Gemini."""

from .corrupt_api import CorruptApiClient, PersonName
from .analyze import get_corruption_risk_summary

__all__ = [
    "CorruptApiClient",
    "PersonName",
    "get_corruption_risk_summary",
]
