from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional
import json

import aiohttp


@dataclass
class PersonName:
    last_name: str
    first_name: str
    patronymic: str


class CorruptApiClient:
    """
    Клієнт для роботи з API реєстру корупційних правопорушень НАЗК.
    """

    def __init__(
        self,
        base_url: str,
        find_endpoint: str = "/1.0/corrupt/findData",
        get_all_endpoint: str = "/1.0/corrupt/getAllData",
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.find_endpoint = (
            find_endpoint if find_endpoint.startswith("/") else "/" + find_endpoint
        )
        self.get_all_endpoint = (
            get_all_endpoint
            if get_all_endpoint.startswith("/")
            else "/" + get_all_endpoint
        )

    async def find_person_records(
        self,
        session: aiohttp.ClientSession,
        person: PersonName,
    ) -> List[Dict[str, Any]]:
        url = f"{self.base_url}{self.find_endpoint}"
        payload: Dict[str, Optional[str]] = {
            "indLastNameOnOffenseMoment": person.last_name,
            "indFirstNameOnOffenseMoment": person.first_name,
            "indPatronymicOnOffenseMoment": person.patronymic,
        }
        async with session.post(url, json=payload) as resp:
            text = await resp.text()
            if resp.status != 200:
                raise RuntimeError(f"API error: HTTP {resp.status}, body: {text}")
            if not text.strip():
                return []
            try:
                data: Any = json.loads(text)
            except json.JSONDecodeError as exc:
                raise RuntimeError(
                    f"Не вдалося розпарсити JSON з відповіді API: {exc}; raw text: {text!r}"
                )
            if isinstance(data, list):
                return data
            if isinstance(data, dict) and "items" in data and isinstance(data["items"], list):
                return data["items"]
            raise RuntimeError("Неочікуваний формат відповіді API Corrupt_Find.")

    async def get_all_data(
        self,
        session: aiohttp.ClientSession,
    ) -> List[Dict[str, Any]]:
        url = f"{self.base_url}{self.get_all_endpoint}"
        async with session.get(url) as resp:
            text = await resp.text()
            if resp.status != 200:
                raise RuntimeError(f"API error: HTTP {resp.status}, body: {text}")
            if not text.strip():
                return []
            try:
                data: Any = json.loads(text)
            except json.JSONDecodeError as exc:
                raise RuntimeError(
                    f"Не вдалося розпарсити JSON з відповіді API: {exc}; raw text: {text!r}"
                )
            if isinstance(data, list):
                return data
            if isinstance(data, dict) and "items" in data and isinstance(data["items"], list):
                return data["items"]
            raise RuntimeError("Неочікуваний формат відповіді API Corrupt_GetAllData.")
