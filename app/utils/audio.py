# app/utils/audio.py
from __future__ import annotations

import subprocess
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


def convert_to_wav_16k_file(
    input_path: str | Path,
    output_path: str | Path,
) -> None:
    """
    Конвертация файла на диске в WAV 16 kHz mono (PCM 16-bit) через ffmpeg.
    Нужна нам:
    - для отладки
    - для скриптов/утилит
    Бот может её вообще не использовать.
    """

    input_path = Path(input_path)
    output_path = Path(output_path)

    logger.debug(
        "Converting file to wav16k: src=%s dst=%s",
        input_path,
        output_path,
    )

    if not input_path.is_file():
        raise FileNotFoundError(f"Входной файл не найден: {input_path}")

    cmd = [
        "ffmpeg",
        "-y",
        "-i",
        str(input_path),
        "-ac",
        "1",
        "-ar",
        "16000",
        "-c:a",
        "pcm_s16le",
        str(output_path),
    ]

    result = subprocess.run(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )

    if result.returncode != 0:
        error_text = result.stderr.decode("utf-8", errors="ignore")

        logger.error(
            "ffmpeg failed in convert_to_wav_16k_file: returncode=%s, input=%s, "
            "output=%s, stderr=%s",
            result.returncode,
            input_path,
            output_path,
            error_text[:500],  # ограничим объём для логов
        )
        raise RuntimeError(
            f"Ошибка при вызове ffmpeg (код {result.returncode}):\n" f"{result.stderr}"
        )

    logger.debug(
        "ffmpeg conversion success (file mode). input=%s output=%s",
        input_path,
        output_path,
    )


def convert_audio_bytes(input_bytes: bytes) -> bytes:
    """
    Принимает байты аудио (например, OGG/OPUS из Телеграма)
    и возвращает байты WAV 16 kHz mono (PCM 16-bit).

    - Никаких временных файлов.
    - Вся конвертация через stdin/stdout ffmpeg.
    """

    if not input_bytes:
        raise ValueError("input_bytes пустой — нечего конвертировать.")

    logger.debug(
        "Starting ffmpeg conversion from bytes. input_size=%d",
        len(input_bytes),
    )

    # Команда ffmpeg:
    # -i pipe:0            читать вход из stdin
    # -ac 1                моно
    # -ar 16000            16 kHz
    # -c:a pcm_s16le       WAV PCM 16-bit
    # -f wav               формат WAV
    # pipe:1               вывод в stdout
    cmd = [
        "ffmpeg",
        "-hide_banner",
        "-loglevel",
        "error",
        "-i",
        "pipe:0",
        "-ac",
        "1",
        "-ar",
        "16000",
        "-c:a",
        "pcm_s16le",
        "-f",
        "wav",
        "pipe:1",
    ]

    process = subprocess.Popen(
        cmd,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )

    wav_bytes, stderr = process.communicate(input_bytes)

    # ffmpeg вернул ошибку?
    if process.returncode != 0:
        error_text = stderr.decode("utf-8", errors="ignore")
        logger.error(
            "ffmpeg failed in convert_audio_bytes: returncode=%s, stderr=%s",
            process.returncode,
            error_text[:500],  # обрежем, чтобы лог не раздувался
        )
        raise RuntimeError(f"Ошибка ffmpeg (код {process.returncode}):\n{error_text}")

    if not wav_bytes:
        logger.error("ffmpeg did not return any WAV data.")
        raise RuntimeError("ffmpeg не вернул WAV данные.")

    logger.debug(
        "ffmpeg conversion success. input_size=%d, output_size=%d",
        len(input_bytes),
        len(wav_bytes),
    )

    return wav_bytes


if __name__ == "__main__":
    # Небольшой ручной тест, чтобы проверить, что всё работает.
    src = Path("data/audio/audio_2025-11-13_16-22-04.ogg")
    dst = src.with_name(src.stem + "_utils_16k.wav")
    print(f"Конвертирую {src} -> {dst}")
    convert_to_wav_16k_file(src, dst)
    print("Готово! Проверь файл в проводнике.")

    # Ручной тест для проверки convert_audio_bytes

    from pathlib import Path

    # подставь любое .ogg, которое у тебя есть в data/audio
    src = Path("data/audio/audio_2025-11-13_16-22-04.ogg")
    dst = src.with_name(src.stem + "_bytes_test.wav")

    print(f"Читаю {src}...")
    ogg_bytes = src.read_bytes()

    print("Конвертирую в WAV...")
    wav_bytes_result = convert_audio_bytes(ogg_bytes)

    print(f"Записываю результат в {dst}...")
    dst.write_bytes(wav_bytes_result)

    print("Готово! Открой .wav и послушай ☑")
