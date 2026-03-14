import os
from dataclasses import dataclass

from dotenv import load_dotenv


load_dotenv()


@dataclass
class Settings:
    bot_token: str
    corrupt_api_base_url: str
    corrupt_find_endpoint: str
    corrupt_get_all_endpoint: str
    gemini_api_key: str
    second_gemini_api_key: str


def get_settings() -> Settings:
    bot_token = os.getenv("BOT_TOKEN", "").strip()
    if not bot_token:
        raise RuntimeError("Не задано BOT_TOKEN в змінних оточення.")

    corrupt_api_base_url = os.getenv(
        "API_BASE_URL",
        "https://corruptinfo.nazk.gov.ua/ep",
    ).rstrip("/")

    corrupt_find_endpoint = os.getenv(
        "CORRUPT_FIND_ENDPOINT",
        "/1.0/corrupt/findData",
    )

    corrupt_get_all_endpoint = os.getenv(
        "CORRUPT_GET_ALL_ENDPOINT",
        "/1.0/corrupt/getAllData",
    )

    gemini_api_key = os.getenv("GEMINI_API_KEY", "").strip()
    second_gemini_api_key = os.getenv("SECOND_GEMINI_API_KEY", "").strip()

    return Settings(
        bot_token=bot_token,
        corrupt_api_base_url=corrupt_api_base_url,
        corrupt_find_endpoint=corrupt_find_endpoint,
        corrupt_get_all_endpoint=corrupt_get_all_endpoint,
        gemini_api_key=gemini_api_key,
        second_gemini_api_key=second_gemini_api_key,
    )

