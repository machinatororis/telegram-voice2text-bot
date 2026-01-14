# app/bot.py
import logging
from pathlib import Path

from aiogram import Dispatcher, F
from aiogram.filters import CommandStart
from aiogram.types import Message

from app.handlers.voice import register_voice_handlers

logger = logging.getLogger(__name__)


def create_dispatcher(*, ffmpeg_path: str | Path | None = None) -> Dispatcher:
    dp = Dispatcher()

    @dp.message(CommandStart())
    async def cmd_start(message: Message):
        logger.info(
            "User %s (%s) sent /start",
            message.from_user.id,
            message.from_user.full_name,
        )
        await message.answer(
            "Привет! Я бот BubbleVoice 🎧\n"
            "Отправь мне голосовое — я попробую его обработать."
        )

    @dp.message(F.text)
    async def echo(message: Message):
        logger.debug("Text message received: %r", message.text)
        await message.answer(f"Ты написал(а): {message.text}")

    # 👇 подключаем модуль с voice-логикой
    register_voice_handlers(dp, ffmpeg_path=ffmpeg_path)

    return dp
