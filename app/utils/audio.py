# app/utils/audio.py
from __future__ import annotations

import subprocess
from pathlib import Path


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
        raise RuntimeError(
            f"Ошибка при вызове ffmpeg (код {result.returncode}):\n" f"{result.stderr}"
        )


if __name__ == "__main__":
    # Небольшой ручной тест, чтобы проверить, что всё работает.
    src = Path("data/audio/audio_2025-11-13_16-22-04.ogg")
    dst = src.with_name(src.stem + "_utils_16k.wav")
    print(f"Конвертирую {src} -> {dst}")
    convert_to_wav_16k_file(src, dst)
    print("Готово! Проверь файл в проводнике.")
