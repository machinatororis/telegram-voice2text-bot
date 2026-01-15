import logging
from pathlib import Path

from aiogram import Dispatcher, F
from aiogram.filters import CommandStart
from aiogram.types import Message

from app.handlers.voice import register_voice_handlers
from app.i18n import t

logger = logging.getLogger(__name__)


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

        await message.answer(t(user_id, "start_greeting"))

    @dp.message(F.text)
    async def echo(message: Message):
        logger.debug("Text message received: %r", message.text)

        user_id = message.from_user.id if message.from_user else None

        await message.answer(t(user_id, "echo_reply", text=message.text))

    # 👇 подключаем модуль с voice-логикой
    register_voice_handlers(dp, ffmpeg_path=ffmpeg_path)

    return dp
