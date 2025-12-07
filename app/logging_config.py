# app/logging_config.py
from __future__ import annotations

import logging
from logging import Logger
from pathlib import Path

from app.config import Settings


def _get_log_level(level_name: str) -> int:
    """
    Преобразует текстовый уровень ("DEBUG", "INFO" и т.п.)
    в числовое значение logging.DEBUG и т.п.
    Если что-то не то — по умолчанию INFO.
    """
    level_name = (level_name or "").upper()
    level = getattr(logging, level_name, None)
    if isinstance(level, int):
        return level
    return logging.INFO


def setup_logging(settings: Settings) -> Logger:
    """
    Централизованная настройка логирования:
    - создаёт папку для логов
    - настраивает root-логгер
    - добавляет хендлер в файл + в консоль
    Возвращает логгер текущего модуля (по желанию).
    """
    log_dir = Path(settings.log_dir)
    log_dir.mkdir(parents=True, exist_ok=True)

    log_file = log_dir / "bot.log"
    log_level = _get_log_level(settings.log_level)

    # Общий формат для всех сообщений
    formatter = logging.Formatter(
        "%(asctime)s [%(levelname)s] [%(name)s] " "%(message)s"
    )

    # Берём root-логгер и чистим старые хендлеры,
    # чтобы не дублировались сообщения.
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)
    root_logger.handlers.clear()

    # Логи в файл
    file_handler = logging.FileHandler(log_file, encoding="utf-8")
    file_handler.setFormatter(formatter)
    root_logger.addHandler(file_handler)

    # Логи в консоль
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)

    # Можно вернуть логгер для модуля logging_config,
    # но обычно нам важен сам факт настройки.
    logger = logging.getLogger(__name__)
    logger.debug(
        "Logging initialized. level=%s, log_file=%s",
        settings.log_level,
        log_file,
    )
    return logger
