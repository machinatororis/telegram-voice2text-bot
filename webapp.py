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

# --- Инициализация настроек и логирования ---

settings = get_settings()
setup_logging(settings)

logger.info("Starting FastAPI webhook app. debug=%s", settings.debug)

if not check_ffmpeg_available(settings.ffmpeg_path):
    logger.warning(
        "ffmpeg was not detected during startup. "
        "Voice message conversion may not work in webhook mode."
    )

# --- Инициализация бота и диспетчера ---

bot = Bot(token=settings.bot_token)
dp = create_dispatcher(ffmpeg_path=settings.ffmpeg_path)

logger.info("Bot and dispatcher initialized for webhook mode.")

# --- Инициализация FastAPI-приложения ---

app = FastAPI()


@app.on_event("startup")
async def on_startup():
    """
    Хук запуска FastAPI: хорошее место для логов "приложение поднялось".
    """
    logger.info(
        "FastAPI application startup complete. Webhook is ready to receive updates."
    )


@app.get("/health")
async def health():
    """
    Простой healthcheck для платформы деплоя.
    Например, justrunmy.app, Railway, Fly.io и т.п.
    """
    return {"status": "ok"}


@app.post("/webhook")
async def telegram_webhook(request: Request):
    """
    Endpoint, куда Telegram будет присылать апдейты.
    """
    data = await request.json()

    # Легкий лог, чтобы видеть "сырые" апдейты (на первое время)
    logger.debug("Received update from Telegram: %s", data)

    # Превращаем JSON в объект Update из aiogram
    update = Update.model_validate(data)

    # Передаем апдейт в диспетчер — он уже разрулит handlers
    await dp.feed_update(bot, update)

    # Telegram ожидает любой 2xx, но JSON ok=true — классика
    return {"ok": True}
