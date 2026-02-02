# app/config.py
from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from enum import Enum

from dotenv import load_dotenv

# Загружаем переменные окружения из .env один раз здесь
load_dotenv()


class TranscriberBackend(str, Enum):
    WHISPER = "whisper"
    DEEPGRAM = "deepgram"


@dataclass
class Settings:
    bot_token: str  # токен бота
    transcriber_backend: TranscriberBackend  # backend-переключатель
    debug: bool  # режим DEBUG (подробные логи)
    log_dir: Path  # папка для логов
    ffmpeg_path: (
        Path | None
    )  # Path("/usr/local/bin/ffmpeg"), если переменная задана, None, если не задана
    log_level: str = "INFO"  # уровень логирования (строкой)

    # Deepgram
    dg_api_key: str | None = None  # ключ для Deepgram, может быть не задан

    # Webhook (optional secret path)
    webhook_secret: str | None = None


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

    backend_raw = os.getenv("TRANSCRIBER_BACKEND", "whisper").lower()
    try:
        transcriber_backend = TranscriberBackend(backend_raw)
    except ValueError:
        transcriber_backend = TranscriberBackend.WHISPER

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
    ffmpeg_path_env = os.getenv("FFMPEG_PATH")
    ffmpeg_path = (
        Path(ffmpeg_path_env).expanduser().resolve() if ffmpeg_path_env else None
    )

    log_level_env = os.getenv("LOG_LEVEL")
    if log_level_env:
        log_level = log_level_env.strip().upper()
    else:
        log_level = "DEBUG" if debug else "INFO"

    # 5. Deepgram API key (опционально)
    dg_api_key = os.getenv("DG_API_KEY")
    # Если явно выбран Deepgram, но ключа нет — это явная ошибка конфигурации
    if transcriber_backend == TranscriberBackend.DEEPGRAM and not dg_api_key:
        raise RuntimeError(
            "TRANSCRIBER_BACKEND=deepgram, но DG_API_KEY не задан.\n"
            "Добавь в .env строку:\n"
            "DG_API_KEY=твоя_строка_ключа_Deepgram"
        )

    # 6. Optional webhook secret
    webhook_secret = os.getenv("WEBHOOK_SECRET")

    return Settings(
        bot_token=token,
        transcriber_backend=transcriber_backend,
        debug=debug,
        log_dir=log_dir,
        ffmpeg_path=ffmpeg_path,
        log_level=log_level,
        dg_api_key=dg_api_key,
        webhook_secret=webhook_secret,
    )
