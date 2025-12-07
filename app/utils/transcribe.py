import os
import tempfile
import whisper
import logging

logger = logging.getLogger(__name__)

# Загружаем модель один раз
logger.info("Loading Whisper model 'small'...")
model = whisper.load_model("small")
logger.info("Whisper model 'small' loaded successfully")


def transcribe_wav_bytes(wav_bytes: bytes) -> str:
    """
    Принимает WAV-байты, сохраняет во временный файл, передаёт Whisper'у,
    потом удаляет файл.
    """
    if not wav_bytes:
        logger.warning("transcribe_wav_bytes called with empty wav_bytes")
        raise ValueError("wav_bytes пустой — нечего распознавать")

    tmp_path: str | None = None

    try:
        # 1. создаём временный файл, НО не удаляем автоматически
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
            tmp.write(wav_bytes)
            tmp.flush()
            tmp_path = tmp.name  # запоминаем путь

        logger.debug(
            "Created temp wav file for transcription: path=%s size=%s",
            tmp_path,
            len(wav_bytes),
        )

        # 2. запускаем распознавание
        logger.debug("Starting Whisper transcription: temp_path=%s", tmp_path)
        try:
            result = model.transcribe(
                tmp_path,
                fp16=False,
                temperature=0,
                beam_size=5,
            )
        except Exception:
            # Логируем с трейсбеком и пробрасываем дальше
            logger.exception(
                "Error during Whisper transcription. temp_path=%s", tmp_path
            )
            raise

        text = (result.get("text") or "").strip()
        logger.info(
            "Transcription completed: temp_path=%s, text_len=%s",
            tmp_path,
            len(text),
        )

        return text

    finally:
        # 3. пробуем удалить временный файл
        if tmp_path and os.path.exists(tmp_path):
            try:
                os.remove(tmp_path)
                logger.debug("Temp wav file removed: %s", tmp_path)
            except OSError:
                # если не получилось удалить
                logger.warning("Failed to remove temp wav file: %s", tmp_path)
