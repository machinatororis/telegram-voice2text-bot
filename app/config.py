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
    log_level: str = "INFO"  # уровень логирования (строкой)


def _str_to_bool(value: str | None, *, default: bool = False) -> bool:
    """
    Аккуратно превращает строку из переменной окружения в bool.
    Поддерживаем: 1/0, true/false, yes/no, on/off.
    Если значение непонятно — возвращаем default.
    """
    if value is None:
        return default

    value = value.strip().lower()
    if value in ("1", "true", "yes", "y", "on"):
        return True
    if value in ("0", "false", "no", "n", "off"):
        return False

    return default


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
    log_dir.mkdir(parents=True, exist_ok=True)

    # 4. Уровень логирования LOG_LEVEL
    # Если LOG_LEVEL не задан, то:
    #   - при DEBUG=True → "DEBUG"
    #   - иначе → "INFO"
    log_level_env = os.getenv("LOG_LEVEL")
    if log_level_env:
        log_level = log_level_env.strip().upper()
    else:
        log_level = "DEBUG" if debug else "INFO"

    return Settings(
        bot_token=token,
        debug=debug,
        log_dir=log_dir,
        log_level=log_level,
    )
