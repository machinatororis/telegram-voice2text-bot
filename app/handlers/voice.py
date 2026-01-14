import logging
from datetime import datetime
from io import BytesIO
from pathlib import Path

from aiogram import Dispatcher, F
from aiogram.types import Message

from app.utils.audio import convert_audio_bytes
from app.utils.transcribe import transcribe_wav_bytes

logger = logging.getLogger(__name__)


async def transcribe_bytes(
    data: bytes,
    *,
    mime_type: str | None = None,
    filename: str | None = None,
    ffmpeg_path: str | Path | None = None,
) -> str:
    if not data:
        return "Я получила пустое аудио 🤔"

    logger.info(
        "Starting audio processing: filename=%s, mime_type=%s, size=%d bytes",
        filename,
        mime_type,
        len(data),
    )

    try:
        wav_bytes = convert_audio_bytes(data, ffmpeg_path=ffmpeg_path)
    except Exception as e:
        logger.exception("Error converting audio using ffmpeg")
        return f"Не удалось подготовить аудио для распознавания: {e}"

    logger.info(
        "Audio converted to WAV: filename=%s, wav_size=%d bytes",
        filename,
        len(wav_bytes),
    )

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


def register_voice_handlers(
    dp: Dispatcher,
    *,
    ffmpeg_path: str | Path | None = None,
) -> None:
    @dp.message(F.voice | F.audio | F.video_note)
    async def on_voice(message: Message):
        user = message.from_user
        kind = "voice" if message.voice else "audio" if message.audio else "video_note"

        logger.info(
            "Incoming voice-like message: kind=%s user_id=%s user_name=%s chat_id=%s message_id=%s",
            kind,
            user.id if user else None,
            user.full_name if user else None,
            message.chat.id,
            message.message_id,
        )

        if message.voice:
            ext = ".ogg"
            file_obj = message.voice
            mime_type = "audio/ogg"
        elif message.audio:
            ext = ".mp3"
            file_obj = message.audio
            mime_type = "audio/mpeg"
        else:
            ext = ".mp4"
            file_obj = message.video_note
            mime_type = "video/mp4"

        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{kind}_{message.chat.id}_{message.message_id}_{ts}{ext}"

        try:
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

            text = await transcribe_bytes(
                audio_bytes,
                mime_type=mime_type,
                filename=filename,
                ffmpeg_path=ffmpeg_path,
            )

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
            logger.exception(
                "Error while handling voice message: user_id=%s chat_id=%s message_id=%s",
                user.id if user else None,
                message.chat.id,
                message.message_id,
            )
            await message.reply(
                "Упс, что-то пошло не так при распознавании 😔 Попробуй ещё раз позже."
            )
