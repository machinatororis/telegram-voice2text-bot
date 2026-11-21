# app/i18n.py
from __future__ import annotations

import os
import sqlite3
from contextlib import closing
from pathlib import Path
from typing import Literal

LangCode = Literal["en", "ru", "uk"]

SUPPORTED_LANGS: tuple[LangCode, ...] = ("en", "ru", "uk")
DEFAULT_LANG: LangCode = "en"


def _connect_language_db() -> sqlite3.Connection:
    """Open the language store, creating it when first needed."""
    configured_path = os.getenv("LANGUAGE_DB_PATH")
    db_path = (
        Path(configured_path).expanduser()
        if configured_path
        else Path(__file__).resolve().parent.parent / "data" / "user_languages.sqlite3"
    )
    db_path.parent.mkdir(parents=True, exist_ok=True)

    connection = sqlite3.connect(db_path, timeout=10)
    try:
        connection.execute(
            "CREATE TABLE IF NOT EXISTS user_languages "
            "(user_id INTEGER PRIMARY KEY, lang TEXT NOT NULL)"
        )
    except Exception:
        connection.close()
        raise
    return connection


def set_user_language(user_id: int, lang: LangCode) -> None:
    """Persist the user's language across bot restarts."""
    if lang not in SUPPORTED_LANGS:
        lang = DEFAULT_LANG

    with closing(_connect_language_db()) as connection, connection:
        connection.execute(
            "INSERT INTO user_languages (user_id, lang) VALUES (?, ?) "
            "ON CONFLICT(user_id) DO UPDATE SET lang = excluded.lang",
            (user_id, lang),
        )


def get_user_language(user_id: int | None) -> LangCode:
    """Read the selected language, or English if none was saved."""
    if user_id is None:
        return DEFAULT_LANG

    with closing(_connect_language_db()) as connection:
        row = connection.execute(
            "SELECT lang FROM user_languages WHERE user_id = ?",
            (user_id,),
        ).fetchone()

    return row[0] if row and row[0] in SUPPORTED_LANGS else DEFAULT_LANG


MESSAGES: dict[str, dict[LangCode, str]] = {
    # Basic messages
    "start_greeting": {
        "en": "Hi! I'm bot BubbleVoice 🎧\nSend me a voice message and I'll try to transcribe it.",
        "ru": "Привет! Я бот BubbleVoice🎧\nОтправь мне голосовое и я попробую его обработать.",
        "uk": "Привіт! Я бот BubbleVoice 🎧\nНадішли мені голосове і я спробую його розпізнати.",
    },
    "choose_language": {
        "en": "Please choose your language:",
        "ru": "Пожалуйста, выберите язык:",
        "uk": "Будь ласка, оберіть мову:",
    },
    "language_set": {
        "en": "✅ Language set to English.",
        "ru": "✅ Язык переключён на русский.",
        "uk": "✅ Мову змінено на українську.",
    },
    "echo_reply": {
        "en": "You wrote: {text}",
        "ru": "Ты написал(а): {text}",
        "uk": "Ти написав(ла): {text}",
    },
    # Errors
    "error_general": {
        "en": "Oops, something went wrong 😔 Please try again later.",
        "ru": "Oops, something went wrong 😔 Please try again later.",
        "uk": "Oops, something went wrong 😔 Please try again later.",
    },
    "empty_audio": {
        "en": "I received an empty audio file 🤔",
        "ru": "Я получила пустое аудио 🤔",
        "uk": "Я отримала порожнє аудіо 🤔",
    },
    "ffmpeg_convert_error": {
        "en": "Failed to prepare audio for transcription: {error}",
        "ru": "Не удалось подготовить аудио для распознавания: {error}",
        "uk": "Не вдалося підготувати аудіо для розпізнавання: {error}",
    },
    "whisper_transcription_error": {
        "en": "Audio was converted to WAV, but an error occurred during transcription 😔",
        "ru": "Аудио удалось сконвертировать в WAV, но при распознавании произошла ошибка 😔",
        "uk": "Аудіо вдалося сконвертувати у WAV, але під час розпізнавання сталася помилка 😔",
    },
    "no_text_recognized": {
        "en": "I couldn’t recognize any text in this audio 😔",
        "ru": "Я не смогла распознать текст в этом аудио 😔",
        "uk": "Я не змогла розпізнати текст у цьому аудіо 😔",
    },
    "voice_received": {
        "en": "Voice message received 🎧\nFile: `{filename}`\n\n{text}",
        "ru": "Голосовое получено 🎧\nФайл: `{filename}`\n\n{text}",
        "uk": "Голосове отримано 🎧\nФайл: `{filename}`\n\n{text}",
    },
}


def t(
    user_id: int | None,
    key: str,
    *,
    lang: LangCode | None = None,
    **kwargs,
) -> str:
    """
    Translate a message by key for a user.

    - Uses user's stored language (or DEFAULT_LANG).
    - Falls back to English if translation is missing.
    - Supports formatting via **kwargs.
    """
    lang_code = lang or get_user_language(user_id)

    translations = MESSAGES.get(key)
    if not translations:
        # Missing key: return key itself to make it obvious during testing.
        return key

    template = translations.get(lang_code) or translations.get(DEFAULT_LANG) or ""
    try:
        return template.format(**kwargs)
    except Exception:
        # If formatting fails, return raw template (still better than crashing)
        return template
