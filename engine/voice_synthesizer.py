"""Voice synthesis module.

Generates broadcast-quality Thai news voice narration using:
1. Gemini 3.8 Flash TTS (Charon voice) when GEMINI_API_KEY is available.
2. Microsoft Edge Neural TTS (th-TH-NiwatNeural / th-TH-PremwadeeNeural) as free, high-fidelity neural fallback.
3. macOS Native Thai TTS (Kanya) as local system fallback.
"""
from __future__ import annotations

import asyncio
import base64
import logging
import os
import shutil
import subprocess
from pathlib import Path
import requests

logger = logging.getLogger(__name__)

GEMINI_TTS_ENDPOINT = "https://generativelanguage.googleapis.com/v1beta/interactions"
DEFAULT_EDGE_VOICE = "th-TH-NiwatNeural"  # Professional Thai male news anchor


async def _synthesize_edge_tts(script: str, output_path: Path, voice: str = DEFAULT_EDGE_VOICE) -> bool:
    """Generates natural Thai speech using Microsoft Edge Neural TTS."""
    try:
        import edge_tts

        temp_mp3 = output_path.with_suffix(".temp.mp3")
        communicate = edge_tts.Communicate(script, voice, rate="+2%", pitch="-1Hz")
        await communicate.save(str(temp_mp3))

        if temp_mp3.is_file() and temp_mp3.stat().st_size > 10_000:
            # Convert to standard 48kHz WAV
            cmd = [
                "ffmpeg", "-hide_banner", "-loglevel", "error", "-y",
                "-i", str(temp_mp3),
                "-ar", "48000", "-ac", "2",
                str(output_path),
            ]
            subprocess.run(cmd, check=True)
            temp_mp3.unlink(missing_ok=True)
            logger.info("Edge-TTS (%s) narration created: %d bytes", voice, output_path.stat().st_size)
            return True
    except Exception as exc:
        logger.warning("Edge-TTS synthesis failed (%s): %s", type(exc).__name__, exc)

    return False


def _synthesize_gemini_tts(script: str, output_path: Path, api_key: str) -> bool:
    """Generates Thai speech using Gemini 3.8 Flash TTS Interactions API."""
    try:
        model = os.environ.get("GEMINI_TTS_MODEL", "gemini-3.8-flash-tts").strip()
        voice = os.environ.get("GEMINI_TTS_VOICE", "Charon").strip()
        style = (
            "A calm, warm, low-pitched adult Thai male news anchor; "
            "clear Thai pronunciation, steady pace, confident and natural."
        )
        request_body = {
            "model": model,
            "input": [
                {
                    "type": "user_input",
                    "content": [
                        {
                            "type": "text",
                            "text": script,
                            "annotations": [{"type": "speech_metadata", "style": style}],
                        }
                    ],
                }
            ],
            "response_format": {"type": "audio"},
            "generation_config": {"speech_config": [{"voice": voice}]},
        }

        resp = requests.post(
            GEMINI_TTS_ENDPOINT,
            headers={"x-goog-api-key": api_key, "Content-Type": "application/json"},
            json=request_body,
            timeout=(15, 180),
        )
        if resp.ok:
            payload = resp.json()
            encoded_audio = (payload.get("output_audio") or {}).get("data")
            if not encoded_audio:
                for step in reversed(payload.get("steps") or []):
                    if step.get("type") != "model_output":
                        continue
                    for part in step.get("content") or []:
                        if part.get("type") == "audio" and part.get("data"):
                            encoded_audio = part["data"]
                            break
                    if encoded_audio:
                        break

            if encoded_audio:
                audio_bytes = base64.b64decode(encoded_audio)
                if len(audio_bytes) > 50_000:
                    output_path.write_bytes(audio_bytes)
                    logger.info("Gemini TTS narration created: %d bytes", len(audio_bytes))
                    return True
    except Exception as exc:
        logger.warning("Gemini TTS failed (%s): %s", type(exc).__name__, exc)

    return False


def _synthesize_macos_tts(script: str, output_path: Path) -> bool:
    """Generates Thai speech using macOS native voice (Kanya)."""
    if shutil.which("say"):
        try:
            temp_aiff = output_path.with_suffix(".temp.aiff")
            cmd_say = ["say", "-v", "Kanya", "-r", "185", "-o", str(temp_aiff), script]
            subprocess.run(cmd_say, check=True)
            if temp_aiff.is_file() and temp_aiff.stat().st_size > 10_000:
                cmd_ffmpeg = [
                    "ffmpeg", "-hide_banner", "-loglevel", "error", "-y",
                    "-i", str(temp_aiff),
                    "-ar", "48000", "-ac", "2",
                    str(output_path),
                ]
                subprocess.run(cmd_ffmpeg, check=True)
                temp_aiff.unlink(missing_ok=True)
                logger.info("macOS Kanya TTS created: %d bytes", output_path.stat().st_size)
                return True
        except Exception as exc:
            logger.warning("macOS TTS failed (%s): %s", type(exc).__name__, exc)

    return False


def synthesize_narration(script: str, output_path: Path, api_key: str | None = None) -> Path:
    """Synthesizes high-quality Thai news narration audio (always genuine speech, never sine beeps)."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    key = api_key or os.environ.get("GEMINI_API_KEY", "").strip()

    # 1. First priority: Gemini 3.8 Flash TTS (when API key is provided)
    if key:
        logger.info("Attempting Gemini 3.8 Flash TTS synthesis...")
        if _synthesize_gemini_tts(script, output_path, key):
            return output_path
        logger.info("Gemini TTS unavailable, falling back to Neural Edge-TTS...")

    # 2. Second priority: Microsoft Neural Edge-TTS (th-TH-NiwatNeural) - free, high fidelity
    logger.info("Synthesizing Thai speech with Neural Edge-TTS (th-TH-NiwatNeural)...")
    if asyncio.run(_synthesize_edge_tts(script, output_path)):
        return output_path

    # 3. Third priority: macOS native TTS (Kanya)
    logger.info("Falling back to macOS system Thai voice...")
    if _synthesize_macos_tts(script, output_path):
        return output_path

    raise RuntimeError("All Thai speech synthesis providers failed; cannot produce audio")
