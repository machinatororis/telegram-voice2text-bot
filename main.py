import asyncio
import logging

from aiogram import Bot

from app.config import get_settings
from app.logging_config import setup_logging
from app.utils.audio import check_ffmpeg_available
from app.bot import create_dispatcher

logger = logging.getLogger(__name__)


async def main() -> None:
    settings = get_settings()
    setup_logging(settings)

    logger.info("Starting app. debug=%s", settings.debug)

    if not check_ffmpeg_available(settings.ffmpeg_path):
        logger.warning(
            "ffmpeg was not detected during startup. Voice message conversion may not work."
        )

    bot = Bot(token=settings.bot_token)
    dp = create_dispatcher(ffmpeg_path=settings.ffmpeg_path)

    logger.info("Bot started. Waiting for updates...")
    await dp.start_polling(bot)
    logger.info("Bot polling stopped. Shutting down.")


if __name__ == "__main__":
    asyncio.run(main())
