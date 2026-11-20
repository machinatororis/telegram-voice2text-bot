# app/transcription/deepgram_backend.py
from __future__ import annotations

import logging
from typing import Any

import httpx

logger = logging.getLogger(__name__)

DEEPGRAM_API_URL = "https://api.deepgram.com/v1/listen"
DEFAULT_MODEL = "nova-3-general"  # General-purpose transcription model


class DeepgramError(Exception):
    """Base exception for Deepgram transcription errors."""


async def transcribe(
    wav_bytes: bytes,
    *,
    api_key: str,
    timeout_s: float = 30.0,
) -> str:
    """
    Send WAV audio to Deepgram and return the transcript.

    Input must already be 16 kHz mono WAV audio, as produced by
    convert_audio_bytes.
    """
    if not wav_bytes:
        logger.warning("Deepgram: empty wav_bytes")
        return ""

    headers = {
        "Authorization": f"Token {api_key}",
        "Content-Type": "audio/wav",
    }

    # Let Deepgram detect the spoken language automatically.
    params = {
        "model": DEFAULT_MODEL,
        "smart_format": "true",
        "detect_language": "true",
    }

    try:
        async with httpx.AsyncClient(timeout=timeout_s) as client:
            response = await client.post(
                DEEPGRAM_API_URL,
                params=params,
                headers=headers,
                content=wav_bytes,
            )
    except httpx.RequestError as exc:
        logger.error("Deepgram request error: %s", exc)
        raise DeepgramError("Deepgram request failed") from exc

    if response.status_code >= 400:
        snippet = response.text[:500]
        logger.error(
            "Deepgram API error: status=%s, body_snippet=%s",
            response.status_code,
            snippet,
        )
        raise DeepgramError(f"Deepgram API error, status={response.status_code}")

    try:
        data: dict[str, Any] = response.json()
    except ValueError as exc:
        logger.error("Failed to parse Deepgram JSON response: %s", exc)
        raise DeepgramError("Deepgram returned invalid JSON") from exc

    # Extract the transcript from the first channel's best alternative.
    # Deepgram response: results.channels[0].alternatives[0].transcript
    try:
        channels = data["results"]["channels"]
        if not channels:
            logger.warning("Deepgram: no channels in results")
            return ""

        first_channel = channels[0] or {}
        alternatives = first_channel.get("alternatives") or []
        if not alternatives:
            logger.warning("Deepgram: no alternatives in first channel")
            return ""

        best_alt = alternatives[0] or {}
        transcript = (best_alt.get("transcript") or "").strip()
        confidence = best_alt.get("confidence")
    except (KeyError, TypeError) as exc:
        logger.error("Unexpected Deepgram response structure: %s", exc)
        raise DeepgramError("Unexpected Deepgram response structure") from exc

    if not transcript:
        logger.warning("Deepgram: transcript is empty")
        return ""

    logger.info(
        "Deepgram transcription success: length=%d chars, confidence=%s",
        len(transcript),
        confidence,
    )
    return transcript
