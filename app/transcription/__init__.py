import logging

from app.config import Settings, TranscriberBackend
from app.transcription.deepgram_backend import (
    transcribe as deepgram_transcribe,
    DeepgramError,
)

logger = logging.getLogger(__name__)


def _transcribe_with_whisper(wav_bytes: bytes) -> str:
    """
    Load the local Whisper backend only when transcription requires it.

    Deferred import lets the cloud Docker image run without Whisper
    dependencies unless the Whisper backend is selected.
    """
    try:
        from app.transcription.whisper_backend import transcribe_wav_bytes
    except ImportError as exc:
        logger.error(
            "Whisper backend was requested but is not available in this environment. "
            "Install Whisper packages or switch TRANSCRIBER_BACKEND to 'deepgram'."
        )
        raise RuntimeError("Whisper backend is not available") from exc

    return transcribe_wav_bytes(wav_bytes)


async def transcribe(
    wav_bytes: bytes,
    *,
    settings: Settings,
    user_id: int | None = None,
) -> str:
    """
    Transcribe WAV audio using the backend selected in settings.

    Dispatch to local Whisper or cloud Deepgram based on
    settings.transcriber_backend.
    """

    # --- Local Whisper backend ---
    if settings.transcriber_backend == TranscriberBackend.WHISPER:
        logger.debug("Using Whisper backend for transcription: user_id=%s", user_id)
        return _transcribe_with_whisper(wav_bytes)

    # --- Cloud Deepgram backend ---
    if settings.transcriber_backend == TranscriberBackend.DEEPGRAM:
        if not getattr(settings, "dg_api_key", None):
            logger.error(
                "Deepgram backend is configured but dg_api_key is missing. "
                "user_id=%s",
                user_id,
            )
            # Fall back to Whisper if its dependencies are installed.
            try:
                return _transcribe_with_whisper(wav_bytes)
            except RuntimeError:
                logger.error(
                    "Whisper fallback is not available. Returning empty transcription."
                )
                return ""

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
                "Deepgram transcription failed, attempting Whisper fallback. "
                "user_id=%s",
                user_id,
            )
            try:
                return _transcribe_with_whisper(wav_bytes)
            except RuntimeError:
                logger.error(
                    "Whisper fallback is not available. Returning empty transcription."
                )
                return ""
        except Exception:
            logger.exception(
                "Unexpected error in Deepgram backend. user_id=%s", user_id
            )
            try:
                return _transcribe_with_whisper(wav_bytes)
            except RuntimeError:
                logger.error(
                    "Whisper fallback is not available. Returning empty transcription."
                )
                return ""

    # --- Unrecognized transcription backend ---
    logger.warning(
        "Unknown transcriber backend %r. Falling back to Whisper if available. "
        "user_id=%s",
        settings.transcriber_backend,
        user_id,
    )
    try:
        return _transcribe_with_whisper(wav_bytes)
    except RuntimeError:
        logger.error("Whisper backend is not available. Returning empty transcription.")
        return ""
