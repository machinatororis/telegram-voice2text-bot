# config.py
from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

# Загружаем переменные окружения из .env один раз здесь
load_dotenv()


@dataclass
class Settings:
    bot_token: str  # токен бота
    debug: bool  # режим DEBUG (подробные логи)
    log_dir: Path  # папка для логов


def _str_to_bool(value: str | None, default: bool = False) -> bool:
    """
    Превращаем строку из окружения в bool.
    Примеры истинных значений: "1", "true", "yes", "on" (без учёта регистра).
    """
    if value is None:
        return default
    return value.strip().lower() in ("1", "true", "yes", "on")


def get_settings() -> Settings:
    # 1. Обязательный токен
    token = os.getenv("BOT_TOKEN", "")
    if not token:
        raise RuntimeError(
            "BOT_TOKEN не найден. Создай .env и добавь строку:\n"
            "BOT_TOKEN=твой_токен_от_@BotFather"
        )

    # 2. Необязательный DEBUG (по умолчанию False)
    debug_env = os.getenv("DEBUG")  # может быть None
    debug = _str_to_bool(debug_env, default=False)

    # 3. Необязательная папка для логов (по умолчанию ./logs)
    log_dir_env = os.getenv("LOG_DIR", "logs")
    log_dir = Path(log_dir_env).resolve()

    # Убедимся, что папка существует
    log_dir.mkdir(parents=True, exist_ok=True)

    return Settings(
        bot_token=token,
        debug=debug,
        log_dir=log_dir,
    )
