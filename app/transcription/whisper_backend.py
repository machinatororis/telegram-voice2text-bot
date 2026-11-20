import os
import tempfile
import whisper
import logging

logger = logging.getLogger(__name__)

# Load the Whisper model once at module import.
logger.info("Loading Whisper model 'small'...")
model = whisper.load_model("small")
logger.info("Whisper model 'small' loaded successfully")


def transcribe_wav_bytes(wav_bytes: bytes) -> str:
    """
    Transcribe WAV bytes via a temporary file and remove it afterward.
    """
    if not wav_bytes:
        logger.warning("transcribe_wav_bytes called with empty wav_bytes")
        raise ValueError("wav_bytes пустой — нечего распознавать")

    tmp_path: str | None = None

    try:
        # Create a temporary file that remains available until transcription ends.
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
            tmp.write(wav_bytes)
            tmp.flush()
            tmp_path = tmp.name  # Keep the path for cleanup

        logger.debug(
            "Created temp wav file for transcription: path=%s size=%s",
            tmp_path,
            len(wav_bytes),
        )

        # Run Whisper transcription.
        logger.debug("Starting Whisper transcription: temp_path=%s", tmp_path)
        try:
            result = model.transcribe(
                tmp_path,
                fp16=False,
                temperature=0,
                beam_size=5,
            )
        except Exception:
            # Log the traceback and re-raise the error.
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
        # Remove the temporary file, including when transcription fails.
        if tmp_path and os.path.exists(tmp_path):
            try:
                os.remove(tmp_path)
                logger.debug("Temp wav file removed: %s", tmp_path)
            except OSError:
                # Report cleanup failures without masking transcription results.
                logger.warning("Failed to remove temp wav file: %s", tmp_path)
