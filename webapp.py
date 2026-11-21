# webapp.py
from __future__ import annotations

import logging

from fastapi import FastAPI, Request
from aiogram import Bot
from aiogram.types import Update

from app.config import get_settings
from app.logging_config import setup_logging
from app.bot import create_dispatcher
from app.utils.audio import check_ffmpeg_available

logger = logging.getLogger(__name__)

# --- Settings and logging initialization ---

settings = get_settings()
setup_logging(settings)

logger.info("Starting FastAPI webhook app. debug=%s", settings.debug)

if not check_ffmpeg_available(settings.ffmpeg_path):
    logger.warning(
        "ffmpeg was not detected during startup. "
        "Voice message conversion may not work in webhook mode."
    )

# --- Webhook path configuration ---

if getattr(settings, "webhook_secret", None):
    WEBHOOK_PATH = f"/webhook/{settings.webhook_secret}"
    logger.info("Using secret webhook path (value hidden)")
else:
    WEBHOOK_PATH = "/webhook"
    logger.warning(
        "WEBHOOK_SECRET is not set. Using public webhook path %s. "
        "For production deployments, it is recommended to set WEBHOOK_SECRET.",
        WEBHOOK_PATH,
    )

# --- Bot and dispatcher initialization ---

bot = Bot(token=settings.bot_token)
dp = create_dispatcher(ffmpeg_path=settings.ffmpeg_path)

logger.info("Bot and dispatcher initialized for webhook mode.")

# --- FastAPI application initialization ---

app = FastAPI()


@app.on_event("startup")
async def on_startup():
    """
    Log successful startup of the FastAPI application.
    """
    logger.info(
        "FastAPI application startup complete. Webhook is ready to receive updates."
    )


@app.get("/")
async def root():
    """Return a simple service status at the root URL."""
    return {"service": "BubbleVoice", "status": "running"}


@app.get("/health")
async def health():
    """
    Health check endpoint for cloud hosting platforms.
    """
    return {"status": "ok"}


@app.post(WEBHOOK_PATH)
async def telegram_webhook(request: Request):
    """
    Receive Telegram webhook updates and forward them to the dispatcher.
    """
    data = await request.json()

    # Log the incoming update without exposing message contents
    logger.debug("Received Telegram update")

    # Parse the incoming JSON as an aiogram Update.
    update = Update.model_validate(data)

    # Dispatch the update to the registered aiogram handlers.
    await dp.feed_update(bot, update)

    # A successful 2xx response acknowledges delivery to Telegram.
    return {"ok": True}
