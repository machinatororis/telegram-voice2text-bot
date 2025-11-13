from dataclasses import dataclass
from dotenv import load_dotenv
import os

# Загружаем переменные из .env при старте программы
load_dotenv()


@dataclass
class Settings:
    bot_token: str


def get_settings() -> Settings:
    token = os.getenv("BOT_TOKEN", "")
    if not token:
        # Если в .env нет BOT_TOKEN — сразу падаем с понятной ошибкой
        raise RuntimeError("BOT_TOKEN не найден. Создай .env и добавь BOT_TOKEN=...")
    return Settings(bot_token=token)
