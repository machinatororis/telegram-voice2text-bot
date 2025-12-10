import asyncio
import logging
from datetime import datetime
from io import BytesIO

from aiogram import Bot, Dispatcher, F
from aiogram.types import Message
from aiogram.filters import CommandStart

from app.utils.audio import convert_audio_bytes, check_ffmpeg_available
from app.utils.transcribe import transcribe_wav_bytes
from app.config import get_settings  # 👈 берём конфиг отсюда
from app.logging_config import setup_logging

logger = logging.getLogger(__name__)  # 👈 именованный логгер


async def transcribe_bytes(
    data: bytes,
    *,
    mime_type: str | None = None,
    filename: str | None = None,
) -> str:
    """
    Принимает «сырые» байты аудио (ogg/opus из Телеграм),
    конвертирует их в WAV 16 kHz mono через ffmpeg (convert_audio_bytes),
    а потом отправляет в локальный движок распознавания (Whisper).
    """
    if not data:
        return "Я получила пустое аудио 🤔"

    logger.info(
        "Starting audio processing: filename=%s, mime_type=%s, size=%d bytes",
        filename,
        mime_type,
        len(data),
    )

    # 1. OGG/MP3/MP4 → WAV 16k mono (in-memory)
    try:
        wav_bytes = convert_audio_bytes(data)
    except Exception as e:
        logger.exception("Error converting audio using ffmpeg")
        return f"Не удалось подготовить аудио для распознавания: {e}"

    logger.info(
        "Audio converted to WAV: filename=%s, wav_size=%d bytes",
        filename,
        len(wav_bytes),
    )

    # 2. WAV → текст через Whisper
    try:
        text = transcribe_wav_bytes(wav_bytes)
    except Exception:
        logger.exception("Error during Whisper transcription")
        return (
            "Аудио удалось сконвертировать в WAV, "
            "но при распознавании произошла ошибка 😔"
        )

    logger.info(
        "Transcription completed: filename=%s, text_len=%d",
        filename,
        len(text) if text else 0,
    )

    if not text.strip():
        return "Я не смогла распознать текст в этом аудио 😔"

    return text


async def main():
    # 1. Получаем настройки
    settings = get_settings()

    # 2. Настраиваем логирование на основе этих настроек
    setup_logging(settings)

    logger.info("Starting bot. debug=%s", settings.debug)

    # 2a. Проверяем наличие ffmpeg
    ffmpeg_ok = check_ffmpeg_available()
    if not ffmpeg_ok:
        # Дополнительное пояснение в логах (WARNING уже есть внутри функции)
        logger.warning(
            "ffmpeg was not detected during bot startup. "
            "Voice message conversion may not work."
        )

    # 3. Создаём бота и диспетчер
    bot = Bot(token=settings.bot_token)
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

    @dp.message(F.voice | F.audio | F.video_note)
    async def on_voice(message: Message):
        user = message.from_user
        logger.info(
            "Incoming voice-like message: kind=%s user_id=%s user_name=%s "
            "chat_id=%s message_id=%s",
            ("voice" if message.voice else "audio" if message.audio else "video_note"),
            user.id if user else None,
            user.full_name if user else None,
            message.chat.id,
            message.message_id,
        )

        if message.voice:
            ext = ".ogg"
            kind = "voice"
            file_obj = message.voice
            mime_type = "audio/ogg"
        elif message.audio:
            ext = ".mp3"
            kind = "audio"
            file_obj = message.audio
            mime_type = "audio/mpeg"
        else:
            ext = ".mp4"
            kind = "video_note"
            file_obj = message.video_note
            mime_type = "video/mp4"

        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{kind}_{message.chat.id}_{message.message_id}_{ts}{ext}"

        try:
            # 1. Скачиваем в память
            buffer = BytesIO()
            await message.bot.download(file_obj, destination=buffer)
            buffer.seek(0)
            audio_bytes = buffer.getvalue()

            logger.debug(
                "Downloaded file %s: size=%d bytes, mime_type=%s",
                filename,
                len(audio_bytes),
                mime_type,
            )

            # 2. Кормим в transcribe_bytes — теперь там внутри будет ffmpeg → WAV
            text = await transcribe_bytes(
                audio_bytes,
                mime_type=mime_type,
                filename=filename,
            )

            # 3. Отвечаем пользователю
            logger.info(
                "Transcription success: user_id=%s message_id=%s text_len=%s",
                user.id if user else None,
                message.message_id,
                len(text),
            )

            await message.reply(
                "Голосовое получено 🎧\n" f"Файл: `{filename}`\n\n" f"{text}",
                parse_mode="Markdown",
            )
        except Exception:
            # Структурное логирование ошибки
            logger.exception(
                "Error while handling voice message: "
                "user_id=%s chat_id=%s message_id=%s",
                user.id if user else None,
                message.chat.id,
                message.message_id,
            )
            await message.reply(
                "Упс, что-то пошло не так при распознавании 😔 "
                "Попробуй ещё раз позже."
            )

    logger.info("Bot started. Waiting for updates...")
    await dp.start_polling(bot)
    logger.info("Bot polling stopped. Shutting down.")


if __name__ == "__main__":
    asyncio.run(main())
