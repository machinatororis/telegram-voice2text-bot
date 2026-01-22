import logging
from pathlib import Path

from aiogram import Dispatcher, F
from aiogram.filters import CommandStart, Command
from aiogram.types import (
    Message,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    CallbackQuery,
)

from app.handlers.voice import register_voice_handlers
from app.i18n import t, set_user_language, LangCode

logger = logging.getLogger(__name__)


def get_language_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="English 🇬🇧", callback_data="lang:en"),
                InlineKeyboardButton(text="Українська 🇺🇦", callback_data="lang:uk"),
                InlineKeyboardButton(text="Русский 🇷🇺", callback_data="lang:ru"),
            ]
        ]
    )


def create_dispatcher(*, ffmpeg_path: str | Path | None = None) -> Dispatcher:
    dp = Dispatcher()

    @dp.message(CommandStart())
    async def cmd_start(message: Message):
        user = message.from_user

        if user:
            logger.info(
                "User %s (%s) sent /start",
                user.id,
                user.full_name,
            )
            user_id = user.id
        else:
            logger.info("Received /start from unknown user")
            user_id = None

        await message.answer(
            t(user_id, "choose_language"),
            reply_markup=get_language_keyboard(),
        )

    @dp.message(Command("language"))
    async def cmd_language(message: Message):
        user = message.from_user
        user_id = user.id if user else None

        logger.info(
            "User %s requested /language",
            user_id,
        )

        await message.answer(
            t(user_id, "choose_language"),
            reply_markup=get_language_keyboard(),
        )

    @dp.message(F.text)
    async def echo(message: Message):
        logger.debug("Text message received: %r", message.text)

        user_id = message.from_user.id if message.from_user else None

        await message.answer(t(user_id, "echo_reply", text=message.text))

    @dp.callback_query(F.data.startswith("lang:"))
    async def on_language_chosen(callback: CallbackQuery):
        user = callback.from_user
        user_id = user.id if user else None

        raw = callback.data.split(":", 1)[1] if callback.data else "en"
        lang: LangCode
        if raw in ("en", "ru", "uk"):
            lang = raw  # type: ignore[assignment]
        else:
            lang = "en"

        if user_id is not None:
            set_user_language(user_id, lang)

        # закрываем "часики" на кнопке
        await callback.answer()

        # убираем клавиатуру под исходным сообщением
        if callback.message:
            await callback.message.edit_reply_markup(reply_markup=None)

            # сообщение "язык изменён"
            await callback.message.answer(t(user_id, "language_set"))
            # приветствие на выбранном языке
            await callback.message.answer(t(user_id, "start_greeting"))

    # подключаем модуль с voice-логикой
    register_voice_handlers(dp, ffmpeg_path=ffmpeg_path)

    return dp
