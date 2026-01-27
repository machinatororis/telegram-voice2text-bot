from app.config import Settings, TranscriberBackend
from app.transcription.whisper_backend import transcribe_wav_bytes

# from app.transcription.deepgram_backend import transcribe as deepgram_transcribe


async def transcribe(
    wav_bytes: bytes,
    *,
    settings: Settings,
    user_id: int | None = None,
) -> str:
    if settings.transcriber_backend == TranscriberBackend.WHISPER:
        return transcribe_wav_bytes(wav_bytes)

    if settings.transcriber_backend == TranscriberBackend.DEEPGRAM:
        # временная заглушка, пока не сделан Deepgram
        return "[Deepgram backend is not implemented yet]"

    return transcribe_wav_bytes(wav_bytes)
