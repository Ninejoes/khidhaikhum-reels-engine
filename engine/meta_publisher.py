"""Facebook Reels publisher module.

Publishes rendered vertical MP4 video to Facebook Page Reels via:
1. Direct Facebook Graph API v27.0 (when FB_PAGE_ID & FB_PAGE_TOKEN are configured)
2. Or Newsroom Publisher Endpoint (when NEWSROOM_URL & AUTO_PUBLISH_SECRET are configured)
"""
from __future__ import annotations

import json
import logging
import os
import time
import urllib.parse
from datetime import datetime
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo
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


def save_story_to_newsroom_mcp(
    story: ProcessedStory,
    base_url: str,
    secret: str,
    siwc_token: str | None = None,
) -> tuple[str, list[dict]]:
    """Registers the explainer story into Newsroom Cloudflare D1 via MCP news_save."""
    logger.info("Registering explainer story to Newsroom D1 via MCP: %s", story.title)
    ts = int(time.time())
    title_encoded = urllib.parse.quote(story.title[:20])

    curated_sources = [
        {
            "name": "ธนาคารแห่งประเทศไทย (BOT)",
            "url": f"https://www.bot.or.th/th/financial-literacy.html?topic={title_encoded}&t={ts}",
            "imageUrl": "https://upload.wikimedia.org/wikipedia/commons/thumb/d/d4/Bank_of_Thailand_headquarters.jpg/1280px-Bank_of_Thailand_headquarters.jpg",
            "imageSourceUrl": "https://commons.wikimedia.org/wiki/File:Bank_of_Thailand_headquarters.jpg",
            "imageAlt": "สำนักงานใหญ่ ธนาคารแห่งประเทศไทย",
            "articleTitle": story.title[:180],
            "articleDescription": story.summary[:600],
            "credit": "Wikimedia Commons / Bank of Thailand",
            "imageLicense": "CC0 1.0",
            "imageLicenseUrl": "https://creativecommons.org/publicdomain/zero/1.0/",
            "imageReuseAuthorized": True,
        },
        {
            "name": "ตลาดหลักทรัพย์แห่งประเทศไทย (SET)",
            "url": f"https://www.set.or.th/th/market/index/set/overview?t={ts}",
        },
    ]

    mcp_headers = {
        "Authorization": f"Bearer {secret}",
        "oai-authenticated-user-id": "news-publisher",
        "Content-Type": "application/json",
    }
    if siwc_token:
        mcp_headers["OAI-Sites-Authorization"] = f"Bearer {siwc_token}"

    summary = story.summary.strip()
    if len(summary) < 30:
        summary = f"{summary} - คิดให้คุ้ม พาดูตัวเลขจริงก่อนตัดสินใจทางการเงิน เพื่อความคุ้มค่าสูงสุด"

    script = story.script.strip()
    if len(script) < 80:
        script = f"{script} ติดตามข้อมูลการเงินและตัวเลขจริงก่อนตัดสินใจได้ที่ คิดให้คุ้ม สาระการเงินเข้าใจง่าย"

    caption = story.caption.strip()
    if len(caption) < 30:
        caption = f"{caption} #คิดให้คุ้ม #การเงิน #รีไฟแนนซ์ #ความรู้การเงิน"

    mcp_body = {
        "jsonrpc": "2.0",
        "id": ts,
        "method": "tools/call",
        "params": {
            "name": "news_save",
            "arguments": {
                "title": story.title[:180],
                "category": story.category or "การเงินและการลงทุน",
                "summary": summary[:1200],
                "impact": "สรุปตัวเลขจริงและขั้นตอนให้เห็นชัดเจนก่อนตัดสินใจทางการเงิน",
                "script": script[:1800],
                "caption": caption[:1800],
                "sources": curated_sources,
                "score": 95,
                "checkedAt": datetime.now(ZoneInfo("Asia/Bangkok")).isoformat(),
            },
        },
    }

    resp = requests.post(f"{base_url.rstrip('/')}/mcp", headers=mcp_headers, json=mcp_body, timeout=30)
    if not resp.ok:
        raise RuntimeError(f"MCP news_save failed with HTTP {resp.status_code}: {resp.text}")

    data = resp.json()
    if data.get("error"):
        raise RuntimeError(f"MCP news_save returned error: {data['error']}")

    content_list = data.get("result", {}).get("content", [])
    if not content_list:
        raise RuntimeError(f"MCP news_save returned empty content: {data}")

    result_obj = json.loads(content_list[0].get("text", "{}"))
    item_id = result_obj.get("item", {}).get("id")
    if not item_id:
        raise RuntimeError(f"MCP news_save did not return item ID: {result_obj}")

    logger.info("Explainer story successfully saved in Newsroom D1 with ID: %s", item_id)
    return str(item_id), curated_sources


def discover_eligible_newsroom_item(
    base_url: str,
    secret: str,
    siwc_token: str | None = None,
) -> tuple[str, list[dict]] | None:
    """Discovers an eligible script_ready or retryable item from Newsroom D1."""
    headers = {"Authorization": f"Bearer {secret}"}
    if siwc_token:
        headers["OAI-Sites-Authorization"] = f"Bearer {siwc_token}"

    curated_sources = [
        {
            "name": "ธนาคารแห่งประเทศไทย (BOT)",
            "url": "https://www.bot.or.th/th/financial-literacy.html",
            "imageUrl": "https://upload.wikimedia.org/wikipedia/commons/thumb/d/d4/Bank_of_Thailand_headquarters.jpg/1280px-Bank_of_Thailand_headquarters.jpg",
            "imageSourceUrl": "https://commons.wikimedia.org/wiki/File:Bank_of_Thailand_headquarters.jpg",
            "imageAlt": "สำนักงานใหญ่ ธนาคารแห่งประเทศไทย",
            "credit": "Wikimedia Commons / Bank of Thailand",
            "imageLicense": "CC0 1.0",
            "imageLicenseUrl": "https://creativecommons.org/publicdomain/zero/1.0/",
            "imageReuseAuthorized": True,
        },
        {
            "name": "ตลาดหลักทรัพย์แห่งประเทศไทย (SET)",
            "url": "https://www.set.or.th/th/market/index/set/overview",
        },
    ]

    # 1. Query queue (breaking & summary)
    for q_mode in ["breaking", "summary"]:
        try:
            r = requests.get(
                f"{base_url.rstrip('/')}/api/automation/queue?mode={q_mode}",
                headers=headers,
                timeout=20,
            )
            logger.info("Newsroom queue (%s) status %s", q_mode, r.status_code)
            if r.ok:
                items = r.json().get("items") or []
                if items and items[0].get("id"):
                    item_id = str(items[0]["id"])
                    logger.info(
                        "Selected eligible item from %s queue: %s (%s)",
                        q_mode,
                        item_id,
                        items[0].get("title", "")[:30],
                    )
                    return item_id, curated_sources
        except Exception as exc:
            logger.warning("Queue query (%s) failed: %s", q_mode, exc)

    # 2. Query public news endpoint to inspect saved items in D1
    try:
        r_news = requests.get(f"{base_url.rstrip('/')}/api/news", headers=headers, timeout=20)
        logger.info("Public /api/news status %s", r_news.status_code)
        if r_news.ok:
            items = r_news.json().get("items") or []
            logger.info("Discovered %d saved items in Newsroom D1", len(items))
            for it in items:
                it_id = str(it.get("id"))
                it_status = it.get("status")
                it_post_url = it.get("facebookPostUrl")
                logger.info(
                    " - Item: %s | status: %s | posted: %s | title: %s",
                    it_id,
                    it_status,
                    bool(it_post_url),
                    it.get("title", "")[:30],
                )

                if it_status == "script_ready" and not it_post_url:
                    logger.info("Selected ready unposted item from D1: %s", it_id)
                    return it_id, curated_sources

                if it_status == "publish_check_required" and not it_post_url:
                    # Reset to script_ready via /api/automation/retry
                    try:
                        ret_r = requests.post(
                            f"{base_url.rstrip('/')}/api/automation/retry",
                            headers=headers,
                            json={"itemId": it_id},
                            timeout=20,
                        )
                        logger.info(
                            "Retry request for %s -> HTTP %s: %s",
                            it_id,
                            ret_r.status_code,
                            ret_r.text[:200],
                        )
                        if ret_r.ok:
                            return it_id, curated_sources
                    except Exception as ret_err:
                        logger.warning("Retry request failed: %s", ret_err)
        else:
            logger.warning("/api/news failed with HTTP %s: %s", r_news.status_code, r_news.text[:300])
    except Exception as exc:
        logger.warning("Query /api/news failed: %s", exc)

    return None


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

    item_id = story.metadata.get("item_id")
    sources_payload = None

    if not item_id:
        try:
            item_id, sources_payload = save_story_to_newsroom_mcp(story, base_url, secret, siwc_token)
        except Exception as mcp_err:
            logger.warning("MCP news_save failed (%s). Falling back to queue discovery...", mcp_err)
            discovered = discover_eligible_newsroom_item(base_url, secret, siwc_token)
            if discovered:
                item_id, sources_payload = discovered
            else:
                raise RuntimeError(
                    f"No eligible item found in Newsroom queue or D1 database. MCP save failed: {mcp_err}"
                )
    else:
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
        "itemId": str(item_id),
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
