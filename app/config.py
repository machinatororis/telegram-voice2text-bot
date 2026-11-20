# app/config.py
from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from enum import Enum

from dotenv import load_dotenv

# Load environment variables from .env.
load_dotenv()


class TranscriberBackend(str, Enum):
    WHISPER = "whisper"
    DEEPGRAM = "deepgram"


@dataclass
class Settings:
    bot_token: str  # Telegram bot token
    transcriber_backend: TranscriberBackend  # Selected transcription backend
    debug: bool  # Enable debug mode
    log_dir: Path  # Directory for log files
    ffmpeg_path: (
        Path | None
    )  # Custom ffmpeg path, or None to use the system PATH
    log_level: str = "INFO"  # Logging level name

    # Deepgram
    dg_api_key: str | None = None  # Optional Deepgram API key

    # Webhook (optional secret path)
    webhook_secret: str | None = None


def _str_to_bool(value: str | None, *, default: bool = False) -> bool:
    """
    Parse a boolean environment variable.

    Accept 1/0, true/false, yes/no, and on/off (case-insensitive).
    Return default for missing or unrecognized values.
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
    # Read the required Telegram bot token.
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

    # Read optional debug mode (disabled by default).
    debug_env = os.getenv("DEBUG")  # May be absent
    debug = _str_to_bool(debug_env, default=False)

    # Use ./logs unless LOG_DIR is configured.
    log_dir_env = os.getenv("LOG_DIR", "logs")
    log_dir = Path(log_dir_env).resolve()
    log_dir.mkdir(parents=True, exist_ok=True)

    # Use LOG_LEVEL when set; otherwise default to DEBUG in debug mode
    # and INFO in normal mode.
    ffmpeg_path_env = os.getenv("FFMPEG_PATH")
    ffmpeg_path = (
        Path(ffmpeg_path_env).expanduser().resolve() if ffmpeg_path_env else None
    )

    log_level_env = os.getenv("LOG_LEVEL")
    if log_level_env:
        log_level = log_level_env.strip().upper()
    else:
        log_level = "DEBUG" if debug else "INFO"

    # Read the optional Deepgram API key.
    dg_api_key = os.getenv("DG_API_KEY")
    # Require an API key when the Deepgram backend is selected.
    if transcriber_backend == TranscriberBackend.DEEPGRAM and not dg_api_key:
        raise RuntimeError(
            "TRANSCRIBER_BACKEND=deepgram, но DG_API_KEY не задан.\n"
            "Добавь в .env строку:\n"
            "DG_API_KEY=твоя_строка_ключа_Deepgram"
        )

    # Read the optional webhook path secret.
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
