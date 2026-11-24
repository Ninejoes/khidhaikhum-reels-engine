"""Whiteboard Doodly Explainer Video Renderer.

Renders 1080x1920 vertical video Reels in the authentic "เอ๊ะ เรื่องอะไร" whiteboard style:
- Off-white paper background (#FAF9F6)
- Hand-drawn vector doodles (house, bank transfer, warning, calculator, checklist)
- Marker pen overlay at active annotation areas
- Warm terracotta (#E06D53) and sage teal (#3F8A8C) accents
- Rounded white subtitle card with soft drop shadow
- Perfect audio-visual synchronization per beat
"""
from __future__ import annotations

import io
import json
import logging
import math
import os
import re
import subprocess
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any
import cairosvg

logger = logging.getLogger(__name__)

WIDTH = 1080
HEIGHT = 1920
FPS = 30

ASSETS_DIR = Path(__file__).resolve().parent.parent / "assets"
DOODLES_DIR = ASSETS_DIR / "doodles"
FONTS_DIR = ASSETS_DIR / "fonts"


@dataclass
class ExplainerBeat:
    beat_id: str
    doodle_name: str
    title: str
    subtitle: str
    callouts: list[str]
    spoken_script: str
    marker_coords: tuple[int, int] = (820, 1150)
    audio_path: Path | None = None
    duration: float = 0.0


@dataclass
class ExplainerTopic:
    title: str
    category: str
    summary: str
    caption: str
    beats: list[ExplainerBeat]


def _read_doodle_inner(doodle_name: str) -> str:
    path = DOODLES_DIR / f"{doodle_name}.svg"
    if not path.is_file():
        path = DOODLES_DIR / "house.svg"
    raw = path.read_text(encoding="utf-8")
    start = raw.find(">") + 1
    end = raw.rfind("</svg>")
    return raw[start:end]


def render_whiteboard_svg(
    beat: ExplainerBeat,
    subtitle_line1: str,
    subtitle_line2: str = "",
    callouts_visible: int = 2,
    show_marker: bool = True,
) -> str:
    """Builds the full 1080x1920 SVG for a whiteboard explainer beat."""
    doodle_content = _read_doodle_inner(beat.doodle_name)
    marker_content = _read_doodle_inner("marker_pen")

    # Generate Callout Pills
    callouts_svg = ""
    start_y = 1050
    colors = [
        ("#FFFFFF", "#3F8A8C", "#3F8A8C"),  # bg, stroke, text
        ("#FDF2EE", "#E06D53", "#E06D53"),
        ("#FEF8E8", "#E8A838", "#2B3A42"),
    ]

    for idx, text in enumerate(beat.callouts[:callouts_visible]):
        bg, border, txt_color = colors[idx % len(colors)]
        curr_y = start_y + (idx * 145)
        callouts_svg += f"""
        <g transform="translate(90, {curr_y})">
          <rect width="900" height="115" rx="22" fill="{bg}" stroke="{border}" stroke-width="4" filter="url(#shadow)"/>
          <text x="45" y="70" font-family="Kanit, 'Sukhumvit Set', sans-serif" font-size="32" font-weight="600" fill="{txt_color}">{text}</text>
        </g>
        """

    # Marker Pen Position
    marker_x, marker_y = beat.marker_coords
    marker_svg = ""
    if show_marker:
        marker_svg = f"""
        <g transform="translate({marker_x}, {marker_y}) scale(0.85)">
          {marker_content}
        </g>
        """

    # Subtitle Card
    sub_l2_svg = ""
    if subtitle_line2:
        sub_l2_svg = f"""<text x="50" y="115" font-family="Kanit, 'Sukhumvit Set', sans-serif" font-size="28" font-weight="500" fill="#E06D53">{subtitle_line2}</text>"""
        card_h = 155
        card_y = 1620
    else:
        card_h = 125
        card_y = 1650

    svg = f"""<svg xmlns="http://www.w3.org/2000/svg" width="{WIDTH}" height="{HEIGHT}" viewBox="0 0 {WIDTH} {HEIGHT}">
  <defs>
    <filter id="shadow" x="-5%" y="-5%" width="110%" height="110%">
      <feDropShadow dx="0" dy="6" stdDeviation="12" flood-color="#000000" flood-opacity="0.07"/>
    </filter>
  </defs>

  <!-- Background Whiteboard -->
  <rect width="{WIDTH}" height="{HEIGHT}" fill="#FAF9F6"/>

  <!-- Brand Masthead Header -->
  <text x="80" y="85" font-family="Kanit, 'Sukhumvit Set', sans-serif" font-size="36" font-weight="bold" fill="#2B3A42">คิดให้คุ้ม 💡</text>
  <text x="80" y="128" font-family="Kanit, 'Sukhumvit Set', sans-serif" font-size="20" font-weight="500" fill="#7A8E99">เห็นตัวเลขจริงก่อนตัดสินใจ</text>
  <line x1="80" y1="155" x2="1000" y2="155" stroke="#E2E8F0" stroke-width="3" stroke-linecap="round"/>

  <!-- Beat Heading -->
  <text x="80" y="240" font-family="Kanit, 'Sukhumvit Set', sans-serif" font-size="56" font-weight="bold" fill="#E06D53">{beat.title}</text>
  <text x="80" y="315" font-family="Kanit, 'Sukhumvit Set', sans-serif" font-size="34" font-weight="600" fill="#2B3A42">{beat.subtitle}</text>

  <!-- Centered Doodle Graphic -->
  <g transform="translate(265, 420) scale(1.1)">
    {doodle_content}
  </g>

  <!-- Animated Callouts / Info Pills -->
  {callouts_svg}

  <!-- Marker Pen -->
  {marker_svg}

  <!-- Bottom Subtitle Card -->
  <g transform="translate(90, {card_y})">
    <rect width="900" height="{card_h}" rx="24" fill="#FFFFFF" stroke="#E2E8F0" stroke-width="2" filter="url(#shadow)"/>
    <text x="50" y="68" font-family="Kanit, 'Sukhumvit Set', sans-serif" font-size="32" font-weight="bold" fill="#2B3A42">{subtitle_line1}</text>
    {sub_l2_svg}
  </g>
</svg>"""
    return svg


def render_beat_video_segment(
    beat: ExplainerBeat,
    audio_path: Path,
    output_mp4: Path,
    work_dir: Path,
) -> Path:
    """Renders a single synchronized video segment for one beat."""
    work_dir.mkdir(parents=True, exist_ok=True)
    output_mp4.parent.mkdir(parents=True, exist_ok=True)

    # 1. Determine duration from audio
    cmd_probe = [
        "ffprobe", "-v", "error", "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1", str(audio_path),
    ]
    duration = float(subprocess.check_output(cmd_probe, text=True).strip())
    beat.duration = duration

    # 2. Split script into 2-3 subtitle chunks for dynamic reading
    words = beat.spoken_script.split()
    mid = len(words) // 2
    sub1_first = " ".join(words[:mid]) if words else beat.title
    sub1_second = " ".join(words[mid:]) if mid < len(words) else ""

    # Phase 1 Frame (first half)
    svg_phase1 = render_whiteboard_svg(
        beat=beat,
        subtitle_line1=sub1_first,
        subtitle_line2="",
        callouts_visible=1,
        show_marker=True,
    )
    frame1_png = work_dir / f"beat_{beat.beat_id}_p1.png"
    cairosvg.svg2png(bytestring=svg_phase1.encode("utf-8"), write_to=str(frame1_png))

    # Phase 2 Frame (second half - all callouts visible)
    svg_phase2 = render_whiteboard_svg(
        beat=beat,
        subtitle_line1=sub1_first,
        subtitle_line2=sub1_second,
        callouts_visible=len(beat.callouts),
        show_marker=False,
    )
    frame2_png = work_dir / f"beat_{beat.beat_id}_p2.png"
    cairosvg.svg2png(bytestring=svg_phase2.encode("utf-8"), write_to=str(frame2_png))

    t1 = duration * 0.45
    t2 = duration - t1

    # Render beat segment with FFmpeg
    cmd_render = [
        "ffmpeg", "-hide_banner", "-loglevel", "error", "-y",
        "-loop", "1", "-t", f"{t1:.2f}", "-i", str(frame1_png),
        "-loop", "1", "-t", f"{t2:.2f}", "-i", str(frame2_png),
        "-i", str(audio_path),
        "-filter_complex",
        f"[0:v]settb=AVTB,setpts=PTS-STARTPTS[v0];[1:v]settb=AVTB,setpts=PTS-STARTPTS[v1];[v0][v1]concat=n=2:v=1:a=0[vout];[2:a]aresample=48000[aout]",
        "-map", "[vout]", "-map", "[aout]",
        "-c:v", "libx264", "-preset", "veryfast", "-crf", "20",
        "-c:a", "aac", "-b:a", "192k",
        "-t", f"{duration:.2f}",
        "-movflags", "+faststart",
        str(output_mp4),
    ]
    subprocess.run(cmd_render, check=True)
    logger.info("Rendered beat [%s] segment: %s (%.1fs)", beat.beat_id, output_mp4, duration)
    return output_mp4


def render_complete_whiteboard_explainer(
    topic: ExplainerTopic,
    beat_audios: list[Path],
    bgm_path: Path,
    output_mp4: Path,
    work_dir: Path,
) -> Path:
    """Renders all beats, concatenates them, and mixes in the lo-fi BGM."""
    work_dir.mkdir(parents=True, exist_ok=True)
    output_mp4.parent.mkdir(parents=True, exist_ok=True)

    segment_files: list[Path] = []
    for idx, beat in enumerate(topic.beats):
        audio_file = beat_audios[idx]
        seg_out = work_dir / f"segment_{idx:02d}_{beat.beat_id}.mp4"
        render_beat_video_segment(beat, audio_file, seg_out, work_dir)
        segment_files.append(seg_out)

    # Concat file list
    concat_list = work_dir / "concat_list.txt"
    with open(concat_list, "w", encoding="utf-8") as f:
        for seg in segment_files:
            f.write(f"file '{seg.resolve()}'\n")

    unmixed_mp4 = work_dir / "unmixed_video.mp4"
    cmd_concat = [
        "ffmpeg", "-hide_banner", "-loglevel", "error", "-y",
        "-f", "concat", "-safe", "0", "-i", str(concat_list),
        "-c", "copy",
        str(unmixed_mp4),
    ]
    subprocess.run(cmd_concat, check=True)

    # Get total video duration
    cmd_probe = [
        "ffprobe", "-v", "error", "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1", str(unmixed_mp4),
    ]
    total_dur = float(subprocess.check_output(cmd_probe, text=True).strip())

    # Final audio mixing: Speech at 0dB + Lo-fi BGM at -22dB
    cmd_mix = [
        "ffmpeg", "-hide_banner", "-loglevel", "error", "-y",
        "-i", str(unmixed_mp4),
        "-stream_loop", "-1", "-i", str(bgm_path),
        "-filter_complex",
        f"[0:a]volume=1.0[speech];[1:a]volume=0.08[bgm];[speech][bgm]amix=inputs=2:duration=first:dropout_transition=2[aout]",
        "-map", "0:v", "-map", "[aout]",
        "-c:v", "copy",
        "-c:a", "aac", "-b:a", "192k",
        "-t", f"{total_dur:.2f}",
        "-movflags", "+faststart",
        str(output_mp4),
    ]
    subprocess.run(cmd_mix, check=True)

    if not output_mp4.is_file() or output_mp4.stat().st_size < 100_000:
        raise RuntimeError(f"Whiteboard explainer render failed for {output_mp4}")

    logger.info("Verified Whiteboard Explainer Reel created: %s (%d bytes, %.1fs)", output_mp4, output_mp4.stat().st_size, total_dur)
    return output_mp4
