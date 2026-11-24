"""Master pipeline orchestrator.

Coordinates news fetching, script generation, image curation, voice synthesis,
video rendering, and Facebook Reels publishing into unified automated pipelines:
1. News Reels Engine (30-40s breaking economic news)
2. Whiteboard Explainer Engine (1.5-2.5m doodly educational financial explainer)
"""
from __future__ import annotations

import argparse
import logging
import os
import shutil
import tempfile
from pathlib import Path

from engine.explainer_script_generator import ExplainerTopic, generate_explainer_topic
from engine.image_curator import CuratedPhoto, curate_photos_for_scenes
from engine.lofi_synthesizer import generate_lofi_background_music
from engine.meta_publisher import publish_reel
from engine.news_fetcher import RawNewsItem, fetch_latest_news
from engine.script_generator import ProcessedStory, generate_story_script
from engine.video_renderer import render_full_video
from engine.voice_synthesizer import synthesize_narration
from engine.whiteboard_renderer import render_complete_whiteboard_explainer

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)


def run_explainer_pipeline(
    topic_prompt: str | None = None,
    output_path: Path | None = None,
    publish: bool = False,
) -> dict[str, str]:
    """Runs the Whiteboard Doodly Explainer video pipeline matching reference #4742958775935653."""
    with tempfile.TemporaryDirectory(prefix="khidhaikhum-explainer-") as temp_dir_str:
        temp_dir = Path(temp_dir_str)
        work_dir = temp_dir / "work"
        work_dir.mkdir(parents=True, exist_ok=True)

        logger.info("Stage 1: Preparing Explainer topic and 5-beat storyboard...")
        topic = generate_explainer_topic(topic_prompt)
        logger.info("Topic ready: %s (%d beats)", topic.title, len(topic.beats))

        # Synthesize narration for each beat individually for perfect sync
        logger.info("Stage 2: Synthesizing neural Thai narration per beat...")
        beat_audios: list[Path] = []
        for idx, beat in enumerate(topic.beats):
            audio_f = work_dir / f"beat_{idx:02d}_{beat.beat_id}.wav"
            synthesize_narration(beat.spoken_script, audio_f)
            beat_audios.append(audio_f)

        # Calculate total duration
        import subprocess
        total_voice_dur = 0.0
        for ba in beat_audios:
            out = subprocess.check_output(
                ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "default=noprint_wrappers=1:nokey=1", str(ba)],
                text=True,
            ).strip()
            total_voice_dur += float(out)

        logger.info("Total explainer voice duration: %.1fs", total_voice_dur)

        # Stage 3: Synthesize warm lo-fi BGM loop
        logger.info("Stage 3: Procedurally generating warm lo-fi background music...")
        bgm_path = work_dir / "lofi_bgm.wav"
        generate_lofi_background_music(total_voice_dur + 5.0, bgm_path)

        # Stage 4: Render complete whiteboard explainer video
        logger.info("Stage 4: Rendering 1080x1920 Whiteboard Doodly Explainer Reel...")
        temp_video = work_dir / "whiteboard_reel.mp4"
        render_complete_whiteboard_explainer(topic, beat_audios, bgm_path, temp_video, work_dir)

        final_output = output_path or (Path.cwd() / "outputs" / "whiteboard-explainer.mp4")
        final_output.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(temp_video, final_output)
        logger.info("Whiteboard Explainer Reel saved: %s (%.1f MB)", final_output, final_output.stat().st_size / (1024 * 1024))

        # Stage 5: Publish if requested
        post_url = "render_only"
        if publish:
            logger.info("Stage 5: Publishing Explainer Reel to Facebook...")
            dummy_story = ProcessedStory(
                title=topic.title,
                category=topic.category,
                summary=topic.summary,
                script=" ".join(b.spoken_script for b in topic.beats),
                caption=topic.caption,
                scenes=[],
                source_name="คิดให้คุ้ม (Original Explainer)",
                source_url="https://facebook.com/1183632304836932",
            )
            dummy_photos = [
                CuratedPhoto(
                    title="Original Doodly Whiteboard Vector Art",
                    source_url="https://creativecommons.org/publicdomain/zero/1.0/",
                    credit="KhidHaiKhum Whiteboard Engine",
                    license_name="CC0 1.0 Universal",
                    local_path=final_output,
                )
            ]
            post_url = publish_reel(final_output, dummy_story, dummy_photos)
            logger.info("Publish result: %s", post_url)

        return {
            "title": topic.title,
            "video_path": str(final_output),
            "video_size": str(final_output.stat().st_size),
            "duration": f"{total_voice_dur:.1f}s",
            "publish_url": post_url,
        }


def run_pipeline(
    output_path: Path | None = None,
    publish: bool = False,
    custom_story: ProcessedStory | None = None,
) -> dict[str, str]:
    """Runs the news Reel pipeline."""
    with tempfile.TemporaryDirectory(prefix="khidhaikhum-engine-") as temp_dir_str:
        temp_dir = Path(temp_dir_str)
        work_dir = temp_dir / "work"
        work_dir.mkdir(parents=True, exist_ok=True)

        if custom_story:
            story = custom_story
            logger.info("Using provided custom story: %s", story.title)
        else:
            logger.info("Stage 1: Ingesting fresh news...")
            news_items = fetch_latest_news()
            if not news_items:
                raise RuntimeError("No news items retrieved from sources")
            top_item = news_items[0]
            logger.info("Selected top story: %s", top_item.title)

            logger.info("Stage 2: Generating AI script and scenes with Gemini...")
            story = generate_story_script(top_item)

        logger.info("Story prepared: %s (%d scenes)", story.title, len(story.scenes))

        logger.info("Stage 3: Curating verified CC0 editorial photos...")
        photos_dir = work_dir / "photos"
        photos = curate_photos_for_scenes(story.scenes, photos_dir)

        logger.info("Stage 4a: Synthesizing Thai voice narration...")
        audio_path = work_dir / "narration.wav"
        synthesize_narration(story.script, audio_path)

        logger.info("Stage 4b: Rendering 1080x1920 video Reel...")
        temp_video = work_dir / "rendered_reel.mp4"
        frames_dir = work_dir / "frames"
        render_full_video(story, photos, audio_path, temp_video, frames_dir)

        final_output = output_path or (Path.cwd() / "outputs" / "latest-reel.mp4")
        final_output.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(temp_video, final_output)

        post_url = "render_only"
        if publish:
            logger.info("Stage 5: Publishing Reel to Facebook...")
            post_url = publish_reel(final_output, story, photos)

        return {
            "title": story.title,
            "video_path": str(final_output),
            "video_size": str(final_output.stat().st_size),
            "publish_url": post_url,
        }
