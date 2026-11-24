"""Master pipeline orchestrator.

Coordinates news fetching, script generation, image curation, voice synthesis,
video rendering, and Facebook Reels publishing into one unified automated pipeline.
"""
from __future__ import annotations

import argparse
import logging
import os
import shutil
import tempfile
from pathlib import Path

from engine.image_curator import curate_photos_for_scenes
from engine.meta_publisher import publish_reel
from engine.news_fetcher import RawNewsItem, fetch_latest_news
from engine.script_generator import ProcessedStory, generate_story_script
from engine.video_renderer import render_full_video
from engine.voice_synthesizer import synthesize_narration

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)


def run_pipeline(
    output_path: Path | None = None,
    publish: bool = False,
    custom_story: ProcessedStory | None = None,
) -> dict[str, str]:
    """Runs the full end-to-end automated news Reel pipeline."""
    with tempfile.TemporaryDirectory(prefix="khidhaikhum-engine-") as temp_dir_str:
        temp_dir = Path(temp_dir_str)
        work_dir = temp_dir / "work"
        work_dir.mkdir(parents=True, exist_ok=True)

        # Stage 1 & 2: Ingestion and Scripting
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

        # Stage 3: Asset Sourcing (Rights-cleared CC0 photos)
        logger.info("Stage 3: Curating verified CC0 editorial photos...")
        photos_dir = work_dir / "photos"
        photos = curate_photos_for_scenes(story.scenes, photos_dir)
        if len(photos) < len(story.scenes):
            logger.warning("Warning: %d photos for %d scenes", len(photos), len(story.scenes))

        # Stage 4: Voice Synthesis and Video Rendering
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
        logger.info("Video successfully generated and saved to: %s", final_output)

        # Stage 5: Publishing
        post_url = "render_only"
        if publish:
            logger.info("Stage 5: Publishing Reel to Facebook...")
            post_url = publish_reel(final_output, story, photos)
            logger.info("Publish result: %s", post_url)
        else:
            logger.info("Stage 5: Publish skipped (--publish=false or render-only)")

        return {
            "title": story.title,
            "video_path": str(final_output),
            "video_size": str(final_output.stat().st_size),
            "publish_url": post_url,
        }
