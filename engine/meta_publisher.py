"""Facebook Reels publisher module.

Publishes rendered vertical MP4 video to Facebook Page Reels via:
1. Direct Facebook Graph API v27.0 (when FB_PAGE_ID & FB_PAGE_TOKEN are configured)
2. Or Newsroom Publisher Endpoint (when NEWSROOM_URL & AUTO_PUBLISH_SECRET are configured)
"""
from __future__ import annotations

import json
import logging
import os
from pathlib import Path
from typing import Any
import requests

from engine.image_curator import CuratedPhoto
from engine.script_generator import ProcessedStory

logger = logging.getLogger(__name__)

GRAPH_VERSION = "v27.0"


def format_post_caption(story: ProcessedStory, photos: list[CuratedPhoto]) -> str:
    """Builds clean Facebook caption with proper editorial image credits and SEO hashtags."""
    base_caption = story.caption.strip()
    credits_list: list[str] = []
    seen: set[str] = set()

    for p in photos:
        if p.image_url not in seen:
            seen.add(p.image_url)
            credits_list.append(f"• ภาพ: {p.credit} ({p.license_name}) - ที่มา: {p.source_url}")

    if credits_list:
        credits_block = "เครดิตภาพประกอบ (มีการจัดวางและปรับสัดส่วน):\n" + "\n".join(credits_list)
        return f"{base_caption}\n\n{credits_block}"

    return base_caption


def publish_direct_meta(
    video_path: Path,
    story: ProcessedStory,
    photos: list[CuratedPhoto],
    page_id: str,
    access_token: str,
) -> str:
    """Publishes MP4 to Facebook Reels directly using Graph API v27.0."""
    logger.info("Publishing Reel directly to Facebook Page %s...", page_id)
    caption = format_post_caption(story, photos)

    # 1. Initialize upload session
    start_url = f"https://graph.facebook.com/{GRAPH_VERSION}/{page_id}/video_reels"
    start_resp = requests.post(
        start_url,
        data={"upload_phase": "START", "access_token": access_token},
        timeout=30,
    )
    if not start_resp.ok:
        raise RuntimeError(f"Meta Graph START phase failed ({start_resp.status_code}): {start_resp.text}")

    start_data = start_resp.json()
    video_id = start_data.get("video_id")
    upload_url = start_data.get("upload_url")
    if not video_id or not upload_url:
        raise RuntimeError(f"Meta Graph did not return video_id or upload_url: {start_data}")

    # 2. Upload video bytes
    video_bytes = video_path.read_bytes()
    upload_headers = {
        "Authorization": f"OAuth {access_token}",
        "offset": "0",
        "file_size": str(len(video_bytes)),
        "Content-Type": "application/octet-stream",
    }
    upload_resp = requests.post(upload_url, headers=upload_headers, data=video_bytes, timeout=300)
    if not upload_resp.ok:
        raise RuntimeError(f"Meta Graph video upload phase failed ({upload_resp.status_code}): {upload_resp.text}")

    # 3. Finish and publish Reel
    finish_data = {
        "upload_phase": "FINISH",
        "video_id": video_id,
        "video_state": "PUBLISHED",
        "title": story.title[:255],
        "description": caption,
        "is_ai_generated": "true",
        "access_token": access_token,
    }
    finish_resp = requests.post(start_url, data=finish_data, timeout=30)
    if not finish_resp.ok:
        raise RuntimeError(f"Meta Graph FINISH phase failed ({finish_resp.status_code}): {finish_resp.text}")

    finish_res = finish_resp.json()
    post_id = finish_res.get("post_id") or finish_res.get("video_id") or video_id
    reel_url = f"https://www.facebook.com/{post_id}"
    logger.info("Facebook accepted the Reel: %s", reel_url)
    return reel_url


def publish_via_newsroom(
    video_path: Path,
    story: ProcessedStory,
    photos: list[CuratedPhoto],
    base_url: str,
    secret: str,
    siwc_token: str | None = None,
) -> str:
    """Publishes via the existing Newsroom Cloudflare Worker endpoint."""
    logger.info("Publishing Reel via Newsroom Worker: %s", base_url)
    url = f"{base_url.rstrip('/')}/api/automation/publish"
    headers = {"Authorization": f"Bearer {secret}"}
    if siwc_token:
        headers["OAI-Sites-Authorization"] = f"Bearer {siwc_token}"

    sources_payload = [
        {
            "name": p.credit,
            "url": p.source_url,
            "imageUrl": p.image_url,
            "imageSourceUrl": p.source_url,
            "credit": p.credit,
            "imageLicense": p.license_name,
            "imageLicenseUrl": p.license_url,
            "imageReuseAuthorized": True,
        }
        for p in photos
    ]
    # Add main news source
    sources_payload.append({"name": story.source_name, "url": story.source_url})

    form_data = {
        "itemId": story.metadata.get("item_id") or "auto_story_latest",
        "width": "1080",
        "height": "1920",
        "sources_json": json.dumps(sources_payload),
    }

    with video_path.open("rb") as handle:
        resp = requests.post(
            url,
            headers=headers,
            data=form_data,
            files={"video": ("news-reel.mp4", handle, "video/mp4")},
            timeout=240,
        )

    if not resp.ok:
        raise RuntimeError(f"Newsroom publish returned HTTP {resp.status_code}: {resp.text}")

    data = resp.json()
    post_url = data.get("postUrl") or "https://www.facebook.com"
    logger.info("Newsroom accepted the Reel: %s", post_url)
    return post_url


def publish_reel(
    video_path: Path,
    story: ProcessedStory,
    photos: list[CuratedPhoto],
) -> str:
    """Intelligently routes publish request to direct Meta Graph API or Newsroom Worker."""
    page_id = os.environ.get("FB_PAGE_ID", "").strip()
    page_token = os.environ.get("FB_PAGE_TOKEN", "").strip()

    if page_id and page_token:
        return publish_direct_meta(video_path, story, photos, page_id, page_token)

    newsroom_url = os.environ.get("NEWSROOM_URL", "").strip()
    auto_secret = os.environ.get("AUTO_PUBLISH_SECRET", "").strip()
    siwc_token = os.environ.get("SIWC_BYPASS_TOKEN", "").strip()

    if newsroom_url and auto_secret:
        return publish_via_newsroom(video_path, story, photos, newsroom_url, auto_secret, siwc_token)

    logger.warning("No publishing credentials configured (FB_PAGE_TOKEN or AUTO_PUBLISH_SECRET). Running in dry-run mode.")
    return "dry_run_no_publish"
