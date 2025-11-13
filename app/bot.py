import asyncio

from aiogram import Bot, Dispatcher, F
from aiogram.types import Message
from aiogram.filters import CommandStart

from .config import get_settings


async def main():
    # 1. Получаем настройки и создаём бота
    settings = get_settings()
    bot = Bot(token=settings.bot_token)
    dp = Dispatcher()

    # 2. Обработчик команды /start
    @dp.message(CommandStart())
    async def on_start(message: Message):
        await message.answer(
            "Привет! Я минимальный бот 🤖\n"
            "Сейчас я умею:\n"
            "• отвечать на /start\n"
            "• реагировать на голосовые (voice/audio/video_note)"
        )

    # 3. Обработчик для голосовых/аудио/видео-заметок
    @dp.message(F.voice | F.audio | F.video_note)
    async def on_voice(message: Message):
        await message.reply(
            "Голосовое получено 🎧\n"
            "Пока я только вижу файл. На следующем шаге научимся его расшифровывать."
        )

    print("Бот запущен. Нажми Ctrl+C, чтобы остановить.")
    # 4. Запускаем long polling — бот постоянно спрашивает Telegram о новых сообщениях
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
