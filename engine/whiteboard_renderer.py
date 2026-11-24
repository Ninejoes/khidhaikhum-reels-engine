"""Whiteboard Doodly Explainer Video Renderer using Chrome Headless.

Renders 1080x1920 vertical video Reels with 100% flawless Thai font shaping
(using Google Chrome/Chromium Blink HarfBuzz layout engine):
- Off-white paper background (#FAF9F6)
- Hand-drawn vector doodles (house, bank transfer, warning, calculator, checklist)
- Marker pen overlay at active annotation areas
- Perfect Thai vowels and tone marks (never broken, never detached)
- Rounded white subtitle card with soft drop shadow
- Synchronized beat rendering + Lo-fi BGM mixing
"""
from __future__ import annotations

import logging
import os
import shutil
import subprocess
import tempfile
from dataclasses import dataclass
from pathlib import Path

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


def find_chrome_executable() -> str:
    """Finds Google Chrome or Chromium executable on macOS or Linux."""
    env_path = os.environ.get("CHROME_PATH", "").strip()
    if env_path and (Path(env_path).is_file() or shutil.which(env_path)):
        return env_path

    mac_candidates = [
        "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
        "/Applications/Chromium.app/Contents/MacOS/Chromium",
        str(Path.home() / "Applications/Google Chrome.app/Contents/MacOS/Google Chrome"),
    ]
    for c in mac_candidates:
        if Path(c).is_file():
            return c

    linux_candidates = [
        "google-chrome",
        "google-chrome-stable",
        "chromium-browser",
        "chromium",
    ]
    for c in linux_candidates:
        found = shutil.which(c)
        if found:
            return found

    raise RuntimeError(
        "Google Chrome or Chromium is required for high-fidelity Thai font rendering. "
        "Please install Google Chrome or set the CHROME_PATH environment variable."
    )


def render_html_to_png(html_content: str, output_png: Path, width: int = WIDTH, height: int = HEIGHT) -> Path:
    """Renders HTML directly to PNG via headless Chrome for flawless font rendering."""
    chrome_bin = find_chrome_executable()
    output_png.parent.mkdir(parents=True, exist_ok=True)

    with tempfile.NamedTemporaryFile("w", suffix=".html", delete=False, encoding="utf-8") as tf:
        tf.write(html_content)
        temp_html_path = tf.name

    try:
        cmd = [
            chrome_bin,
            "--headless",
            "--disable-gpu",
            "--no-sandbox",
            "--disable-dev-shm-usage",
            "--allow-file-access-from-files",
            "--enable-font-antialiasing",
            f"--screenshot={output_png}",
            f"--window-size={width},{height}",
            "--hide-scrollbars",
            f"file://{Path(temp_html_path).resolve()}",
        ]
        res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        if not output_png.is_file() or output_png.stat().st_size < 1000:
            logger.error("Chrome headless render failed: %s", res.stderr)
            raise RuntimeError(f"Failed to render HTML frame to {output_png}")
    finally:
        try:
            os.remove(temp_html_path)
        except OSError:
            pass

    return output_png


def build_beat_html(
    beat: ExplainerBeat,
    subtitle_line1: str,
    subtitle_line2: str = "",
    callouts_visible: int = 2,
    show_marker: bool = True,
) -> str:
    """Builds clean HTML with modern CSS, perfect Thai typography, and SVG doodles."""
    doodle_svg_path = DOODLES_DIR / f"{beat.doodle_name}.svg"
    if not doodle_svg_path.is_file():
        doodle_svg_path = DOODLES_DIR / "house.svg"
    doodle_url = f"file://{doodle_svg_path.resolve()}"

    marker_svg_path = DOODLES_DIR / "marker_pen.svg"
    marker_url = f"file://{marker_svg_path.resolve()}"

    font_bold_url = f"file://{(FONTS_DIR / 'Kanit-Bold.ttf').resolve()}"
    font_med_url = f"file://{(FONTS_DIR / 'Kanit-Medium.ttf').resolve()}"

    # Build Callout Cards
    callout_html = ""
    for idx, text in enumerate(beat.callouts[:callouts_visible]):
        alt_class = " alt" if idx % 2 == 1 else ""
        callout_html += f'<div class="callout-card{alt_class}">{text}</div>\n'

    marker_html = ""
    if show_marker:
        marker_html = f'<img class="marker-pen" src="{marker_url}">'

    sub_l2_html = ""
    if subtitle_line2:
        sub_l2_html = f'<div class="sub-l2">{subtitle_line2}</div>'

    html = f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<style>
  @import url('https://fonts.googleapis.com/css2?family=Kanit:wght@400;500;600;700;800&display=swap');

  @font-face {{
    font-family: 'Kanit';
    src: url('{font_bold_url}') format('truetype');
    font-weight: 700;
  }}
  @font-face {{
    font-family: 'Kanit';
    src: url('{font_med_url}') format('truetype');
    font-weight: 500;
  }}

  * {{ box-sizing: border-box; margin: 0; padding: 0; }}
  body {{
    width: {WIDTH}px;
    height: {HEIGHT}px;
    background: #FAF9F6;
    font-family: 'Kanit', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
    padding: 70px 80px;
    position: relative;
    overflow: hidden;
    -webkit-font-smoothing: antialiased;
  }}

  .header {{
    border-bottom: 2px solid #E2E8F0;
    padding-bottom: 25px;
  }}
  .brand {{
    font-size: 38px;
    font-weight: 700;
    color: #2B3A42;
    display: flex;
    align-items: center;
    gap: 12px;
  }}
  .brand-sub {{
    font-size: 22px;
    font-weight: 500;
    color: #7A8E99;
    margin-top: 6px;
  }}

  .title-group {{ margin-top: 45px; }}
  .title {{
    font-size: 64px;
    font-weight: 800;
    color: #E06D53;
    line-height: 1.25;
  }}
  .subtitle {{
    font-size: 36px;
    font-weight: 600;
    color: #2B3A42;
    margin-top: 15px;
    line-height: 1.3;
  }}

  .doodle-container {{
    width: 100%;
    display: flex;
    justify-content: center;
    align-items: center;
    margin-top: 45px;
    height: 480px;
  }}
  .doodle-img {{
    max-width: 820px;
    max-height: 460px;
    object-fit: contain;
  }}

  .callouts-container {{
    margin-top: 40px;
    display: flex;
    flex-direction: column;
    gap: 24px;
    position: relative;
  }}
  .callout-card {{
    background: #FFFFFF;
    border: 3.5px solid #3F8A8C;
    border-radius: 24px;
    padding: 26px 36px;
    font-size: 32px;
    font-weight: 600;
    color: #3F8A8C;
    box-shadow: 0 8px 24px rgba(0,0,0,0.06);
    line-height: 1.35;
  }}
  .callout-card.alt {{
    border-color: #E06D53;
    color: #E06D53;
    background: #FDF2EE;
  }}

  .marker-pen {{
    position: absolute;
    right: -30px;
    top: 75px;
    width: 180px;
    height: 180px;
    transform: rotate(15deg);
    filter: drop-shadow(0 12px 20px rgba(0,0,0,0.15));
  }}

  .subtitle-card {{
    position: absolute;
    bottom: 80px;
    left: 80px;
    right: 80px;
    background: #FFFFFF;
    border: 2px solid #E2E8F0;
    border-radius: 28px;
    padding: 32px 40px;
    box-shadow: 0 10px 30px rgba(0,0,0,0.07);
  }}
  .sub-l1 {{
    font-size: 32px;
    font-weight: 700;
    color: #2B3A42;
    line-height: 1.4;
  }}
  .sub-l2 {{
    font-size: 28px;
    font-weight: 600;
    color: #E06D53;
    margin-top: 10px;
    line-height: 1.4;
  }}
</style>
</head>
<body>
  <div class="header">
    <div class="brand">คิดให้คุ้ม 💡</div>
    <div class="brand-sub">เห็นตัวเลขจริงก่อนตัดสินใจ</div>
  </div>

  <div class="title-group">
    <div class="title">{beat.title}</div>
    <div class="subtitle">{beat.subtitle}</div>
  </div>

  <div class="doodle-container">
    <img class="doodle-img" src="{doodle_url}">
  </div>

  <div class="callouts-container">
    {callout_html}
    {marker_html}
  </div>

  <div class="subtitle-card">
    <div class="sub-l1">{subtitle_line1}</div>
    {sub_l2_html}
  </div>
</body>
</html>"""
    return html


def render_beat_video_segment(
    beat: ExplainerBeat,
    audio_path: Path,
    output_mp4: Path,
    work_dir: Path,
) -> Path:
    """Renders a single synchronized video segment for one beat using Chrome Headless."""
    work_dir.mkdir(parents=True, exist_ok=True)
    output_mp4.parent.mkdir(parents=True, exist_ok=True)

    # 1. Determine duration from audio
    cmd_probe = [
        "ffprobe", "-v", "error", "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1", str(audio_path),
    ]
    duration = float(subprocess.check_output(cmd_probe, text=True).strip())
    beat.duration = duration

    # 2. Split script into 2 subtitle chunks
    words = beat.spoken_script.split()
    mid = len(words) // 2
    sub1_first = " ".join(words[:mid]) if words else beat.title
    sub1_second = " ".join(words[mid:]) if mid < len(words) else ""

    # Phase 1 Frame (first half)
    html_p1 = build_beat_html(
        beat=beat,
        subtitle_line1=sub1_first,
        subtitle_line2="",
        callouts_visible=1,
        show_marker=True,
    )
    frame1_png = work_dir / f"beat_{beat.beat_id}_p1.png"
    render_html_to_png(html_p1, frame1_png)

    # Phase 2 Frame (second half - all callouts visible)
    html_p2 = build_beat_html(
        beat=beat,
        subtitle_line1=sub1_first,
        subtitle_line2=sub1_second,
        callouts_visible=len(beat.callouts),
        show_marker=False,
    )
    frame2_png = work_dir / f"beat_{beat.beat_id}_p2.png"
    render_html_to_png(html_p2, frame2_png)

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
    """Renders all beats with Chrome Headless, concatenates them, and mixes in the lo-fi BGM."""
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
