# app/i18n.py
from __future__ import annotations

from typing import Dict, Literal

LangCode = Literal["en", "ru", "uk"]

SUPPORTED_LANGS: tuple[LangCode, ...] = ("en", "ru", "uk")
DEFAULT_LANG: LangCode = "en"

# Temporary in-memory storage: user_id -> language code
_user_language: Dict[int, LangCode] = {}


def set_user_language(user_id: int, lang: LangCode) -> None:
    """Set user's preferred language."""
    if lang not in SUPPORTED_LANGS:
        lang = DEFAULT_LANG
    _user_language[user_id] = lang


def get_user_language(user_id: int | None) -> LangCode:
    """Get user's preferred language. Defaults to English."""
    if user_id is None:
        return DEFAULT_LANG
    return _user_language.get(user_id, DEFAULT_LANG)


MESSAGES: dict[str, dict[LangCode, str]] = {
    # Basic messages
    "start_greeting": {
        "en": "Hi! I'm bot BubbleVoice 🎧\nSend me a voice message and I'll try to transcribe it.",
        "ru": "Привет! Я бот BubbleVoice🎧\nОтправь мне голосовое и я попробую его обработать.",
        "uk": "Привіт! Я бот BubbleVoice 🎧\nНадішли мені голосове і я спробую його розпізнати.",
    },
    "choose_language": {
        "en": "Please choose your language:",
        "ru": "Please choose your language:",
        "uk": "Please choose your language:",
    },
    "language_set": {
        "en": "✅ Language updated.",
        "ru": "✅ Language updated.",
        "uk": "✅ Language updated.",
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
