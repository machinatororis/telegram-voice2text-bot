import asyncio
import logging
from datetime import datetime
from io import BytesIO

from aiogram import Bot, Dispatcher, F
from aiogram.types import Message
from aiogram.filters import CommandStart

from app.utils.audio import convert_audio_bytes
from app.utils.transcribe import transcribe_wav_bytes
from app.config import get_settings  # 👈 берём конфиг отсюда


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

    logging.info(
        "Начинаю обработку аудио: filename=%s, mime_type=%s, size=%d bytes",
        filename,
        mime_type,
        len(data),
    )

    # 1. OGG/MP3/MP4 → WAV 16k mono (in-memory)
    try:
        wav_bytes = convert_audio_bytes(data)
    except Exception as e:
        logging.exception("Ошибка при конвертации аудио через ffmpeg")
        return f"Не удалось подготовить аудио для распознавания: {e}"

    logging.info(
        "Аудио сконвертировано в WAV: filename=%s, wav_size=%d bytes",
        filename,
        len(wav_bytes),
    )

    # 2. WAV → текст через Whisper
    try:
        text = transcribe_wav_bytes(wav_bytes)
    except Exception:
        logging.exception("Ошибка при распознавании аудио через Whisper")
        return (
            "Аудио удалось сконвертировать в WAV, "
            "но при распознавании произошла ошибка 😔"
        )

    logging.info(
        "Распознавание завершено: filename=%s, text_len=%d",
        filename,
        len(text) if text else 0,
    )

    if not text.strip():
        return "Я не смогла распознать текст в этом аудио 😔"

    return text


async def main():
    # 1. Получаем настройки
    settings = get_settings()

    # 2. Настраиваем логирование
    log_file = settings.log_dir / "bot.log"

    # Превращаем строковый уровень ("DEBUG", "INFO", ...) в константу logging
    log_level_name = settings.log_level.upper()
    log_level = getattr(logging, log_level_name, logging.INFO)

    logging.basicConfig(
        level=log_level,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        handlers=[
            logging.FileHandler(log_file, encoding="utf-8"),
            logging.StreamHandler(),  # вывод в консоль
        ],
    )

    logging.info("Запуск бота...")
    logging.info("Текущий уровень логирования: %s", log_level_name)
    logging.info("DEBUG флаг (для информации): %s", settings.debug)
    logging.info("Логи пишутся в: %s", log_file)

    # 3. Создаём бота и диспетчер
    bot = Bot(token=settings.bot_token)
    dp = Dispatcher()

    @dp.message(CommandStart())
    async def cmd_start(message: Message):
        logging.info(
            "Пользователь %s (%s) отправил /start",
            message.from_user.id,
            message.from_user.full_name,
        )
        await message.answer(
            "Привет! Я бот BubbleVoice 🎧\n"
            "Отправь мне голосовое — я попробую его обработать."
        )

    @dp.message(F.text)
    async def echo(message: Message):
        logging.debug("Получен текст: %r", message.text)
        await message.answer(f"Ты написал(а): {message.text}")

    @dp.message(F.voice | F.audio | F.video_note)
    async def on_voice(message: Message):
        user = message.from_user
        logging.info(
            "Получено голосовое от %s (%s), message_id=%s",
            user.id,
            user.full_name,
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

        # 1. Скачиваем в память
        buffer = BytesIO()
        await message.bot.download(file_obj, destination=buffer)
        buffer.seek(0)
        audio_bytes = buffer.getvalue()

        logging.debug(
            "Скачали файл %s: размер=%d байт, mime_type=%s",
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
        await message.reply(
            "Голосовое получено 🎧\n" f"Файл: `{filename}`\n\n" f"{text}",
            parse_mode="Markdown",
        )

    print("Бот запущен. Нажми Ctrl+C, чтобы остановить.")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
