import logging

from app.config import Settings, TranscriberBackend
from app.transcription.whisper_backend import transcribe_wav_bytes
from app.transcription.deepgram_backend import (
    transcribe as deepgram_transcribe,
    DeepgramError,
)

logger = logging.getLogger(__name__)


async def transcribe(
    wav_bytes: bytes,
    *,
    settings: Settings,
    user_id: int | None = None,
) -> str:
    """
    Общая точка входа для транскрипции.

    В зависимости от settings.transcriber_backend
    выбирает Whisper или Deepgram.
    """

    if settings.transcriber_backend == TranscriberBackend.WHISPER:
        logger.debug("Using Whisper backend for transcription: user_id=%s", user_id)
        return transcribe_wav_bytes(wav_bytes)

    if settings.transcriber_backend == TranscriberBackend.DEEPGRAM:
        # safety: если по каким-то причинам ключа нет в settings,
        # не валимся, а откатываемся на Whisper
        if not getattr(settings, "dg_api_key", None):
            logger.error(
                "Deepgram backend is configured but dg_api_key is missing. "
                "Falling back to Whisper. user_id=%s",
                user_id,
            )
            return transcribe_wav_bytes(wav_bytes)

        try:
            logger.debug(
                "Using Deepgram backend for transcription: user_id=%s", user_id
            )
            return await deepgram_transcribe(
                wav_bytes,
                api_key=settings.dg_api_key,  # type: ignore[attr-defined]
            )
        except DeepgramError:
            logger.exception(
                "Deepgram transcription failed, falling back to Whisper. user_id=%s",
                user_id,
            )
            return transcribe_wav_bytes(wav_bytes)
        except Exception:
            logger.exception(
                "Unexpected error in Deepgram backend, falling back to Whisper. "
                "user_id=%s",
                user_id,
            )
            return transcribe_wav_bytes(wav_bytes)

    # на всякий случай: если пришло что-то странное в settings.transcriber_backend
    logger.warning(
        "Unknown transcriber backend %r. Falling back to Whisper. user_id=%s",
        settings.transcriber_backend,
        user_id,
    )
    return transcribe_wav_bytes(wav_bytes)
