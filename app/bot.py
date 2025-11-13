import asyncio
import logging
from datetime import datetime
from io import BytesIO

from aiogram import Bot, Dispatcher, F
from aiogram.types import Message
from aiogram.filters import CommandStart

from config import get_settings  # 👈 берём конфиг отсюда


async def transcribe_bytes(
    data: bytes,
    *,
    mime_type: str | None = None,
    filename: str | None = None,
) -> str:
    """
    Логическая заготовка для распознавания аудио из байтов.

    На будущее:
    - сюда будем передавать байты файла (data)
    - mime_type (например, 'audio/ogg', 'audio/mpeg') — чтобы движок понимал формат
    - filename — иногда движкам нужно "имя файла" (даже если он из памяти)

    Сейчас это просто заглушка, чтобы проверить, что всё "склеено".
    """
    # Здесь позже будет реальный вызов распознавания:
    #   - ffmpeg (для конвертации) +
    #   - движок распознавания (Whisper, OpenAI, что выберем)
    # Пока вернём "фейковый" текст:
    size_kb = len(data) / 1024
    logging.debug(
        "transcribe_bytes: filename=%s, mime_type=%s, size_kb=%.1f",
        filename,
        mime_type,
        size_kb,
    )
    return f"[Псевдо-распознавание] Получено ~{size_kb:.1f} КБ аудио"


async def main():
    # 1. Получаем настройки
    settings = get_settings()

    # 2. Настраиваем логирование
    log_file = settings.log_dir / "bot.log"

    logging.basicConfig(
        level=logging.DEBUG if settings.debug else logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        handlers=[
            logging.FileHandler(log_file, encoding="utf-8"),
            logging.StreamHandler(),  # вывод в консоль
        ],
    )

    logging.info("Запуск бота...")
    logging.info("DEBUG режим: %s", settings.debug)
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

        text = await transcribe_bytes(
            audio_bytes,
            mime_type=mime_type,
            filename=filename,
        )

        await message.reply(
            "Голосовое получено 🎧\n" f"Файл: `{filename}`\n\n" f"{text}",
            parse_mode="Markdown",
        )

    print("Бот запущен. Нажми Ctrl+C, чтобы остановить.")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
