"""Lo-fi / Acoustic Background Music procedural synthesizer.

Generates royalty-free, warm, soothing lo-fi background music (48kHz stereo WAV)
using pure Python numpy harmonics + gentle warm low-pass filtering.
100% self-contained, zero external API costs, works offline and in GitHub Actions.
"""
from __future__ import annotations

import logging
import math
import subprocess
import wave
from pathlib import Path
import numpy as np

logger = logging.getLogger(__name__)

SAMPLE_RATE = 48000


def synth_warm_rhodes_tone(
    freq: float, duration: float, sr: int = SAMPLE_RATE
) -> np.ndarray:
    """Synthesizes a warm, resonant electric piano/acoustic bell tone."""
    t = np.linspace(0, duration, int(sr * duration), endpoint=False)
    decay = np.exp(-t * 2.2)

    # Fundamental + warm musical harmonics
    h1 = np.sin(2 * np.pi * freq * t) * 0.65
    h2 = np.sin(2 * np.pi * (freq * 2) * t) * 0.22 * np.exp(-t * 3.5)
    h3 = np.sin(2 * np.pi * (freq * 3) * t) * 0.08 * np.exp(-t * 5.0)
    # Warm chorus detune
    h_detune = np.sin(2 * np.pi * (freq * 1.003) * t) * 0.15 * decay

    tone = (h1 + h2 + h3 + h_detune) * decay
    return tone


def generate_lofi_background_music(
    target_duration: float, output_path: Path
) -> Path:
    """Generates a warm, looping 4-chord lo-fi progression (Fmaj7 - Em7 - Dm7 - Cmaj7)."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    chord_len = 4.0  # 4 seconds per chord
    loop_duration = 16.0  # 4 chords = 16s loop

    # Chord frequencies (Hz) in warm lower-mid register
    # Fmaj7: F3, A3, C4, E4
    # Em7:   E3, G3, B3, D4
    # Dm7:   D3, F3, A3, C4
    # Cmaj7: C3, E3, G3, B3
    progression = [
        [174.61, 220.00, 261.63, 329.63],
        [164.81, 196.00, 246.94, 293.66],
        [146.83, 174.61, 220.00, 261.63],
        [130.81, 164.81, 196.00, 246.94],
    ]

    total_samples = int(SAMPLE_RATE * target_duration)
    left_channel = np.zeros(total_samples, dtype=np.float32)
    right_channel = np.zeros(total_samples, dtype=np.float32)

    current_t = 0.0
    chord_idx = 0

    while current_t < target_duration:
        freqs = progression[chord_idx % len(progression)]
        start_sample = int(current_t * SAMPLE_RATE)

        # Arpeggiate chord notes slightly for organic strummed acoustic feel
        for n_i, freq in enumerate(freqs):
            offset_s = n_i * 0.045
            note_dur = min(4.5, target_duration - (current_t + offset_s))
            if note_dur <= 0.1:
                continue

            tone = synth_warm_rhodes_tone(freq, note_dur, sr=SAMPLE_RATE)
            note_start = int((current_t + offset_s) * SAMPLE_RATE)
            note_end = note_start + len(tone)

            if note_start < total_samples:
                avail = min(len(tone), total_samples - note_start)
                pan_l = 0.5 - (n_i * 0.08)
                pan_r = 0.5 + (n_i * 0.08)
                left_channel[note_start : note_start + avail] += tone[:avail] * pan_l
                right_channel[note_start : note_start + avail] += tone[:avail] * pan_r

        current_t += chord_len
        chord_idx += 1

    # Subtle vinyl crackle / tape atmosphere
    np.random.seed(42)
    crackle = np.random.normal(0, 0.008, total_samples).astype(np.float32)
    left_channel += crackle
    right_channel += crackle

    # Normalize gently to -18 dBFS so it never overpowers speech
    max_amp = max(np.max(np.abs(left_channel)), np.max(np.abs(right_channel))) + 1e-6
    left_channel = (left_channel / max_amp) * 0.22
    right_channel = (right_channel / max_amp) * 0.22

    # Interleave to 16-bit PCM stereo
    stereo = np.empty((total_samples * 2,), dtype=np.int16)
    stereo[0::2] = np.clip(left_channel * 32767, -32768, 32767).astype(np.int16)
    stereo[1::2] = np.clip(right_channel * 32767, -32768, 32767).astype(np.int16)

    raw_wav = output_path.with_suffix(".temp.wav")
    with wave.open(str(raw_wav), "wb") as wf:
        wf.setnchannels(2)
        wf.setsampwidth(2)
        wf.setframerate(SAMPLE_RATE)
        wf.writeframes(stereo.tobytes())

    # Apply lowpass filter (1800Hz) via ffmpeg for authentic lo-fi warmth
    cmd = [
        "ffmpeg", "-hide_banner", "-loglevel", "error", "-y",
        "-i", str(raw_wav),
        "-af", "lowpass=f=2200,highpass=f=80,volume=-4dB",
        str(output_path),
    ]
    subprocess.run(cmd, check=True)
    raw_wav.unlink(missing_ok=True)

    logger.info("Generated lo-fi BGM track (%0.1fs): %s", target_duration, output_path)
    return output_path
