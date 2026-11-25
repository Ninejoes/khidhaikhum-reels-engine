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
import time
from pathlib import Path

from engine.explainer_script_generator import (
    ExplainerTopic,
    convert_news_to_explainer_topic,
    generate_explainer_topic,
    get_scheduled_slot_topic,
)
from engine.image_curator import CuratedPhoto, curate_photos_for_scenes
from engine.lofi_synthesizer import generate_lofi_background_music
from engine.meta_publisher import ensure_publish_sources, fetch_eligible_newsroom_item, publish_reel
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
    item_id: str | None = None,
    mode: str | None = None,
) -> dict[str, str]:
    """Runs the Whiteboard Doodly Explainer video pipeline matching reference #4742958775935653."""
    if item_id:
        item_id = str(item_id).strip('"\'').strip()
    if topic_prompt:
        topic_prompt = str(topic_prompt).strip('"\'').strip()

    with tempfile.TemporaryDirectory(prefix="khidhaikhum-explainer-") as temp_dir_str:
        temp_dir = Path(temp_dir_str)
        work_dir = temp_dir / "work"
        work_dir.mkdir(parents=True, exist_ok=True)

        newsroom_url = os.environ.get("NEWSROOM_URL", "").strip()
        auto_secret = os.environ.get("AUTO_PUBLISH_SECRET", "").strip()
        siwc_token = os.environ.get("SIWC_BYPASS_TOKEN", "").strip()
        gemini_key = os.environ.get("GEMINI_API_KEY", "").strip()

        active_item_id: str | None = None
        active_sources: list[dict] = []
        news_source_name = "คิดให้คุ้ม (Original Explainer)"
        news_source_url = "https://facebook.com/1183632304836932"

        logger.info("Stage 1: Preparing Explainer topic and 5-beat storyboard...")
        if topic_prompt:
            logger.info("Using explicit user topic prompt: %s", topic_prompt)
            topic = generate_explainer_topic(topic_prompt, api_key=gemini_key)
        else:
            news_item_dict = None
            # Step A: Query Newsroom D1 queue or public news endpoint
            if newsroom_url and auto_secret:
                logger.info("Checking Newsroom D1 queue for eligible news story...")
                try:
                    eligible = fetch_eligible_newsroom_item(
                        newsroom_url, auto_secret, siwc_token, item_id=item_id, mode=mode
                    )
                    if eligible:
                        news_item_dict, active_sources = eligible
                        active_item_id = str(news_item_dict.get("id"))
                        logger.info(
                            "Discovered eligible news item from D1: %s (%s)",
                            active_item_id,
                            news_item_dict.get("title", "")[:40],
                        )
                except Exception as d1_err:
                    logger.warning("Failed querying Newsroom queue: %s", d1_err)

            # Step B: If Newsroom queue is empty, query live economic RSS feeds
            if not news_item_dict:
                logger.info("No unposted news in D1 queue. Checking live economic RSS feeds...")
                try:
                    rss_items = fetch_latest_news()
                    if rss_items:
                        top_rss = rss_items[0]
                        news_item_dict = {
                            "id": f"rss_{int(time.time())}",
                            "title": top_rss.title,
                            "summary": top_rss.summary,
                            "impact": "กระทบต่อต้นทุนและเงินในกระเป๋าที่เราต้องวางแผน",
                            "script": top_rss.summary,
                            "category": top_rss.category,
                            "sources": [{"name": top_rss.source_name, "url": top_rss.link}],
                        }
                        active_sources = news_item_dict["sources"]
                        news_source_name = top_rss.source_name
                        news_source_url = top_rss.link
                        logger.info("Selected fresh news from RSS: %s", top_rss.title[:40])
                except Exception as rss_err:
                    logger.warning("Failed fetching live RSS news: %s", rss_err)

            # Step C: Convert news item to Whiteboard Explainer 5 Beats
            if news_item_dict:
                topic = convert_news_to_explainer_topic(news_item_dict, api_key=gemini_key)
                if active_sources:
                    news_source_name = active_sources[0].get("name", news_source_name)
                    news_source_url = active_sources[0].get("url", news_source_url)
            else:
                slot_topic = get_scheduled_slot_topic()
                logger.info("No live news found; using scheduled editorial slot topic: %s", slot_topic)
                topic = generate_explainer_topic(slot_topic, api_key=gemini_key)

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
            story_metadata = {}
            if active_item_id:
                story_metadata["item_id"] = active_item_id

            explainer_story = ProcessedStory(
                title=topic.title,
                category=topic.category,
                summary=topic.summary,
                script=" ".join(b.spoken_script for b in topic.beats),
                caption=topic.caption,
                scenes=[],
                source_name=news_source_name,
                source_url=news_source_url,
                metadata=story_metadata,
            )

            final_sources = ensure_publish_sources(
                active_sources or [{"name": news_source_name, "url": news_source_url}],
                topic.title,
            )

            photos = [
                CuratedPhoto(
                    local_path=final_output,
                    image_url=s.get("imageUrl", "https://upload.wikimedia.org/wikipedia/commons/thumb/6/66/Gold_bars.jpg/1280px-Gold_bars.jpg"),
                    source_url=s.get("imageSourceUrl") or s.get("url", news_source_url),
                    credit=s.get("credit", "Wikimedia Commons / CC0"),
                    license_name=s.get("imageLicense", "CC0 1.0"),
                    license_url=s.get("imageLicenseUrl", "https://creativecommons.org/publicdomain/zero/1.0/"),
                    reuse_authorized=True,
                )
                for s in final_sources
                if s.get("imageUrl")
            ]
            post_url = publish_reel(final_output, explainer_story, photos)
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
