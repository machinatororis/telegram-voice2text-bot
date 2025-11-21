import os
import tempfile
import whisper

# Загружаем модель один раз
model = whisper.load_model("small")


def transcribe_wav_bytes(wav_bytes: bytes) -> str:
    """
    Принимает WAV-байты, сохраняет во временный файл, передаёт Whisper'у,
    потом удаляет файл.
    """
    tmp_path = None

    try:
        # 1. создаём временный файл, НО не удаляем автоматически
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
            tmp.write(wav_bytes)
            tmp.flush()
            tmp_path = tmp.name  # запоминаем путь

        # 2. теперь файл закрыт, ffmpeg может его открыть
        result = model.transcribe(
            tmp_path,
            fp16=False,
            temperature=0,
            beam_size=5,
        )

        return result["text"].strip()

    finally:
        # 3. пробуем удалить временный файл
        if tmp_path and os.path.exists(tmp_path):
            try:
                os.remove(tmp_path)
            except OSError:
                # если не получилось удалить — просто молча игнорируем
                pass
