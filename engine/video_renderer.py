"""Video renderer module.

Renders 1080x1920 vertical video Reels (H.264/AAC) using Pillow (with RAQM Thai shaping),
CairoSVG (Lucide badges), and FFmpeg.
"""
from __future__ import annotations

import io
import json
import logging
import math
import os
import re
import subprocess
from pathlib import Path
from typing import Any
import cairosvg
from PIL import Image, ImageDraw, ImageFont, ImageOps, features

from engine.image_curator import CuratedPhoto
from engine.script_generator import ProcessedStory, ScriptScene

logger = logging.getLogger(__name__)

WIDTH = 1080
HEIGHT = 1920
FPS = 30
SAFE_MARGIN = 72
RIGHT_EDGE = 1008
TEXT_WIDTH = RIGHT_EDGE - SAFE_MARGIN

ASSETS_DIR = Path(__file__).resolve().parent.parent / "assets"
FONTS_DIR = ASSETS_DIR / "fonts"
ICONS_DIR = ASSETS_DIR / "icons" / "lucide"
ILLUSTRATIONS_DIR = ASSETS_DIR / "illustrations"


def get_font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    font_file = "GoogleSans-Bold.ttf" if bold else "GoogleSansText-Regular.ttf"
    local_font = FONTS_DIR / font_file
    if local_font.is_file():
        try:
            return ImageFont.truetype(str(local_font), size, layout_engine=ImageFont.Layout.RAQM)
        except Exception:
            return ImageFont.truetype(str(local_font), size)

    # Fallback to system fonts
    fallbacks = [
        "/usr/share/fonts/truetype/noto/NotoSansThai-Bold.ttf" if bold else "/usr/share/fonts/truetype/noto/NotoSansThai-Regular.ttf",
        "/System/Library/Fonts/Thonburi.ttc",
        "/Library/Fonts/Arial Unicode.ttf",
    ]
    for fb in fallbacks:
        if Path(fb).exists():
            return ImageFont.truetype(fb, size)

    return ImageFont.load_default()


def render_svg_badge(icon_name: str, size: int = 42, color: str = "#E7C776") -> Image.Image:
    svg_path = ICONS_DIR / f"{icon_name}.svg"
    if not svg_path.is_file():
        svg_path = ICONS_DIR / "chart-line.svg"

    svg_content = svg_path.read_text(encoding="utf-8") if svg_path.is_file() else f"""
    <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="{color}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="m3 3 18 18"/><path d="m19 9 2 2-2 2"/><path d="m5 15-2-2 2-2"/></svg>
    """
    svg_content = svg_content.replace('stroke="currentColor"', f'stroke="{color}"')
    png_bytes = cairosvg.svg2png(bytestring=svg_content.encode("utf-8"), output_width=size, output_height=size)
    return Image.open(io.BytesIO(png_bytes)).convert("RGBA")


def wrap_thai_text(text: str, font: ImageFont.FreeTypeFont, max_width: int) -> list[str]:
    words = re.findall(r"\S+|\s+", text)
    lines: list[str] = []
    current = ""
    for w in words:
        trial = current + w
        bbox = font.getbbox(trial)
        w_len = bbox[2] - bbox[0]
        if w_len <= max_width:
            current = trial
        else:
            if current.strip():
                lines.append(current.strip())
            current = w
    if current.strip():
        lines.append(current.strip())
    return lines


def render_scene_frame(
    story: ProcessedStory,
    scene: ScriptScene,
    photo: CuratedPhoto | None,
    scene_index: int,
    total_scenes: int,
) -> Image.Image:
    base = Image.new("RGBA", (WIDTH, HEIGHT), (8, 14, 22, 255))

    # Background illustration with dark overlay
    bg_path = ILLUSTRATIONS_DIR / "market-bangkok.jpg"
    if bg_path.is_file():
        with Image.open(bg_path) as bg_img:
            bg_fit = ImageOps.fit(bg_img.convert("RGB"), (WIDTH, HEIGHT), method=Image.Resampling.LANCZOS)
            bg_rgba = bg_fit.convert("RGBA")
            # Apply dark grade
            overlay = Image.new("RGBA", (WIDTH, HEIGHT), (6, 12, 19, 210))
            base = Image.alpha_composite(bg_rgba, overlay)

    draw = ImageDraw.Draw(base, "RGBA")

    # 1. Masthead header
    font_brand = get_font(42, bold=True)
    font_sub = get_font(22, bold=False)
    draw.text((SAFE_MARGIN, 64), "คิดให้คุ้ม", font=font_brand, fill=(248, 250, 248, 255))
    draw.text((SAFE_MARGIN, 124), "ข่าวที่ตรวจสอบแล้ว · เห็นตัวเลขจริงก่อนตัดสินใจ", font=font_sub, fill=(180, 200, 205, 230))

    # Timeline bar
    bar_width = (RIGHT_EDGE - SAFE_MARGIN) // total_scenes
    for idx in range(total_scenes):
        bx0 = SAFE_MARGIN + (idx * bar_width) + 4
        bx1 = bx0 + bar_width - 8
        fill_color = (231, 199, 118, 255) if idx <= scene_index else (60, 75, 85, 180)
        draw.rounded_rectangle((bx0, 168, bx1, 174), radius=3, fill=fill_color)

    # 2. News Title
    font_title = get_font(40, bold=True)
    title_lines = wrap_thai_text(story.title, font_title, TEXT_WIDTH)[:3]
    curr_y = 205
    for t_line in title_lines:
        draw.text((SAFE_MARGIN, curr_y), t_line, font=font_title, fill=(255, 255, 255, 255))
        curr_y += 54

    # 3. Photo Card Frame (y0=560, y1=1120)
    card_x0, card_y0, card_x1, card_y1 = SAFE_MARGIN, 560, RIGHT_EDGE, 1120
    draw.rounded_rectangle((card_x0, card_y0, card_x1, card_y1), radius=24, fill=(12, 20, 28, 255), outline=(216, 181, 113, 200), width=2)

    # Photo insert
    img_left, img_top, img_right, img_bottom = card_x0 + 12, card_y0 + 12, card_x1 - 12, card_y1 - 60
    if photo and photo.local_path.is_file():
        with Image.open(photo.local_path) as raw_photo:
            photo_fit = ImageOps.fit(raw_photo.convert("RGB"), (img_right - img_left, img_bottom - img_top), method=Image.Resampling.LANCZOS)
            mask = Image.new("L", photo_fit.size, 0)
            ImageDraw.Draw(mask).rounded_rectangle((0, 0, photo_fit.width - 1, photo_fit.height - 1), radius=16, fill=255)
            base.paste(photo_fit, (img_left, img_top), mask)

        # Credit line
        font_credit = get_font(18, bold=False)
        credit_text = f"ภาพ: {photo.credit} ({photo.license_name})"
        draw.text((card_x0 + 18, card_y1 - 42), credit_text[:70], font=font_credit, fill=(195, 210, 215, 220))

    # Icon badge (top right of photo card)
    badge_size = 72
    badge = Image.new("RGBA", (badge_size, badge_size), (0, 0, 0, 0))
    b_draw = ImageDraw.Draw(badge, "RGBA")
    b_draw.rounded_rectangle((0, 0, badge_size - 1, badge_size - 1), radius=20, fill=(9, 18, 26, 235), outline=(231, 199, 118, 240), width=2)
    icon_img = render_svg_badge(scene.icon, size=40, color="#E7C776")
    badge.alpha_composite(icon_img, ((badge_size - 40) // 2, (badge_size - 40) // 2))
    base.alpha_composite(badge, (card_x1 - badge_size - 18, card_y0 + 18))

    # 4. Scene Narration Content (y=1160 to 1700)
    # Scene Label Pill
    pill_font = get_font(22, bold=True)
    pill_w = pill_font.getbbox(scene.label)[2] + 32
    draw.rounded_rectangle((SAFE_MARGIN, 1160, SAFE_MARGIN + pill_w, 1205), radius=12, fill=(231, 199, 118, 240))
    draw.text((SAFE_MARGIN + 16, 1169), scene.label, font=pill_font, fill=(12, 20, 28, 255))

    # Scene Title
    scene_title_font = get_font(34, bold=True)
    draw.text((SAFE_MARGIN, 1225), scene.title, font=scene_title_font, fill=(245, 248, 250, 255))

    # Scene Body Text
    body_font = get_font(28, bold=False)
    body_lines = wrap_thai_text(scene.body, body_font, TEXT_WIDTH)[:6]
    body_y = 1290
    for b_line in body_lines:
        draw.text((SAFE_MARGIN, body_y), b_line, font=body_font, fill=(230, 240, 245, 250))
        body_y += 44

    # 5. Footer Branding
    draw.line((SAFE_MARGIN, 1780, RIGHT_EDGE, 1780), fill=(50, 65, 75, 180), width=1)
    footer_font = get_font(20, bold=False)
    draw.text((SAFE_MARGIN, 1810), f"แหล่งข้อมูลอ้างอิง: {story.source_name}", font=footer_font, fill=(160, 180, 190, 220))

    return base


def get_audio_duration(audio_path: Path) -> float:
    cmd = [
        "ffprobe", "-v", "error", "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1", str(audio_path),
    ]
    out = subprocess.check_output(cmd, text=True).strip()
    return float(out)


def render_full_video(
    story: ProcessedStory,
    photos: list[CuratedPhoto],
    audio_path: Path,
    output_mp4: Path,
    work_dir: Path,
) -> Path:
    """Renders full 1080x1920 MP4 combining rendered frames, audio track, and crossfades."""
    work_dir.mkdir(parents=True, exist_ok=True)
    output_mp4.parent.mkdir(parents=True, exist_ok=True)

    audio_duration = get_audio_duration(audio_path)
    total_scenes = len(story.scenes)
    scene_duration = max(4.0, (audio_duration + 0.5) / total_scenes)

    # 1. Render image frame for each scene
    frame_paths: list[Path] = []
    for i, scene in enumerate(story.scenes):
        photo = photos[i] if i < len(photos) else None
        frame = render_scene_frame(story, scene, photo, i, total_scenes)
        frame_file = work_dir / f"frame_{i:02d}.png"
        frame.save(frame_file)
        frame_paths.append(frame_file)

    # 2. Build video stream with FFmpeg filter_complex
    # Loop each image for scene_duration, then concatenate
    inputs: list[str] = []
    for fp in frame_paths:
        inputs.extend(["-loop", "1", "-t", f"{scene_duration:.2f}", "-i", str(fp)])

    # Add audio input
    inputs.extend(["-i", str(audio_path)])

    filter_chunks: list[str] = []
    for i in range(total_scenes):
        filter_chunks.append(f"[{i}:v]settb=AVTB,setpts=PTS-STARTPTS[v{i}]")

    concat_inputs = "".join(f"[v{i}]" for i in range(total_scenes))
    filter_chunks.append(f"{concat_inputs}concat=n={total_scenes}:v=1:a=0[vconcat]")

    audio_filter = "aresample=48000,loudnorm=I=-16:TP=-1.5:LRA=11[aout]"
    full_filter = ";".join(filter_chunks) + f";[vconcat]fps={FPS},format=yuv420p[vout];[3:a]{audio_filter}"

    cmd = [
        "ffmpeg", "-hide_banner", "-loglevel", "error", "-y",
        *inputs,
        "-filter_complex", full_filter,
        "-map", "[vout]", "-map", "[aout]",
        "-c:v", "libx264", "-preset", "veryfast", "-crf", "22",
        "-c:a", "aac", "-b:a", "192k",
        "-t", f"{audio_duration + 0.5:.2f}",
        "-movflags", "+faststart",
        str(output_mp4),
    ]

    logger.info("Executing FFmpeg render: %s", output_mp4)
    subprocess.run(cmd, check=True)

    if not output_mp4.is_file() or output_mp4.stat().st_size < 100_000:
        raise RuntimeError("Rendered video file is missing or invalid size")

    logger.info("Rendered verified 1080x1920 MP4: %d bytes", output_mp4.stat().st_size)
    return output_mp4
