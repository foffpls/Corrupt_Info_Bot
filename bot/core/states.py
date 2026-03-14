# -*- coding: utf-8 -*-
"""FSM-стани бота."""

from aiogram.fsm.state import State, StatesGroup


class SearchStates(StatesGroup):
    waiting_for_full_name = State()


class AnalyzeStates(StatesGroup):
    waiting_for_full_name = State()
