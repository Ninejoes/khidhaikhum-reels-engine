"""Automatic CC0 / Creative Commons Image Curator.

Searches Wikimedia Commons API for editorial news photos matching scene queries,
verifies explicit CC0 / CC BY / Public Domain licenses, extracts credits,
and downloads the rights-cleared photos to local disk.
"""
from __future__ import annotations

import logging
import os
import re
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import quote
import requests

logger = logging.getLogger(__name__)

USER_AGENT = "KhidHaiKhumReelsEngine/1.0 (https://github.com/Ninejoes/khidhaikhum-reels-engine; newsroom@khidhaikhum.local)"
WIKIMEDIA_API = "https://commons.wikimedia.org/w/api.php"

ALLOWED_LICENSES = {"cc0", "cc0 1.0", "public domain", "cc-by-4.0", "cc-by-3.0", "cc-by-sa-4.0"}

FALLBACK_EDITORIAL_PHOTOS = [
    {
        "url": "https://commons.wikimedia.org/wiki/File:The_Entrance_of_Tokyo_Stock_Exchange_Main_Building_20240329.jpg",
        "imageUrl": "https://upload.wikimedia.org/wikipedia/commons/c/c8/The_Entrance_of_Tokyo_Stock_Exchange_Main_Building_20240329.jpg",
        "imageSourceUrl": "https://commons.wikimedia.org/wiki/File:The_Entrance_of_Tokyo_Stock_Exchange_Main_Building_20240329.jpg",
        "credit": "Suicasmo / Wikimedia Commons",
        "imageLicense": "CC0 1.0",
        "imageLicenseUrl": "https://creativecommons.org/publicdomain/zero/1.0/",
    },
    {
        "url": "https://commons.wikimedia.org/wiki/File:Micro-chips_wafer.jpg",
        "imageUrl": "https://upload.wikimedia.org/wikipedia/commons/f/f5/Micro-chips_wafer.jpg",
        "imageSourceUrl": "https://commons.wikimedia.org/wiki/File:Micro-chips_wafer.jpg",
        "credit": "Syced / Wikimedia Commons",
        "imageLicense": "CC0 1.0",
        "imageLicenseUrl": "https://creativecommons.org/publicdomain/zero/1.0/",
    },
    {
        "url": "https://commons.wikimedia.org/wiki/File:New_York_Stock_Exchange_Entrance.jpg",
        "imageUrl": "https://upload.wikimedia.org/wikipedia/commons/5/55/New_York_Stock_Exchange_Entrance.jpg",
        "imageSourceUrl": "https://commons.wikimedia.org/wiki/File:New_York_Stock_Exchange_Entrance.jpg",
        "credit": "Balon Greyjoy / Wikimedia Commons",
        "imageLicense": "CC0 1.0",
        "imageLicenseUrl": "https://creativecommons.org/publicdomain/zero/1.0/",
    },
    {
        "url": "https://commons.wikimedia.org/wiki/File:Bank_of_Thailand_headquarters_2023.jpg",
        "imageUrl": "https://upload.wikimedia.org/wikipedia/commons/thumb/d/d4/Bank_of_Thailand_headquarters_2023.jpg/1280px-Bank_of_Thailand_headquarters_2023.jpg",
        "imageSourceUrl": "https://commons.wikimedia.org/wiki/File:Bank_of_Thailand_headquarters_2023.jpg",
        "credit": "Wikimedia Commons",
        "imageLicense": "CC BY-SA 4.0",
        "imageLicenseUrl": "https://creativecommons.org/licenses/by-sa/4.0/",
    },
]


@dataclass
class CuratedPhoto:
    local_path: Path
    image_url: str
    source_url: str
    credit: str
    license_name: str
    license_url: str
    reuse_authorized: bool = True


def search_wikimedia_photo(query: str, target_dir: Path, index: int) -> CuratedPhoto | None:
    """Searches Wikimedia Commons for an editorial photo matching query."""
    headers = {"User-Agent": USER_AGENT}
    clean_query = re.sub(r"[^\w\s-]", " ", query).strip()
    params = {
        "action": "query",
        "generator": "search",
        "gsrsearch": f"filetype:bitmap {clean_query}",
        "gsrnamespace": "6",
        "gsrlimit": "8",
        "prop": "imageinfo",
        "iiprop": "url|extmetadata|size|mime",
        "format": "json",
    }

    try:
        resp = requests.get(WIKIMEDIA_API, headers=headers, params=params, timeout=12)
        if not resp.ok:
            return None

        data = resp.json()
        pages = data.get("query", {}).get("pages", {})
        for _, page in pages.items():
            imageinfo = (page.get("imageinfo") or [{}])[0]
            width = int(imageinfo.get("width") or 0)
            height = int(imageinfo.get("height") or 0)
            mime = str(imageinfo.get("mime") or "").lower()
            img_url = str(imageinfo.get("url") or "")
            desc_url = str(imageinfo.get("descriptionurl") or "")

            if width < 800 or height < 500 or "image" not in mime:
                continue

            metadata = imageinfo.get("extmetadata") or {}
            license_short = str(metadata.get("LicenseShortName", {}).get("value") or "").strip()
            license_url = str(metadata.get("LicenseUrl", {}).get("value") or "").strip()
            artist = re.sub(r"<[^>]+>", "", str(metadata.get("Artist", {}).get("value") or "")).strip()
            credit = artist if artist else "Wikimedia Commons"

            # Check license compliance
            norm_license = license_short.lower()
            if any(allowed in norm_license for allowed in ALLOWED_LICENSES) or "zero" in norm_license:
                # Download image
                img_resp = requests.get(img_url, headers=headers, timeout=20)
                if img_resp.ok and len(img_resp.content) > 50_000:
                    ext = ".jpg" if "jpeg" in mime or "jpg" in mime else ".png"
                    dest = target_dir / f"scene_photo_{index}{ext}"
                    dest.write_bytes(img_resp.content)
                    return CuratedPhoto(
                        local_path=dest,
                        image_url=img_url,
                        source_url=desc_url or img_url,
                        credit=f"{credit} / Wikimedia Commons",
                        license_name=license_short or "CC0 1.0",
                        license_url=license_url or "https://creativecommons.org/publicdomain/zero/1.0/",
                    )
    except Exception as exc:
        logger.warning("Wikimedia search failed for '%s': %s", query, exc)

    return None


def curate_photos_for_scenes(scenes: list[Any], target_dir: Path) -> list[CuratedPhoto]:
    """Curates distinct, license-verified editorial photos for each scene."""
    target_dir.mkdir(parents=True, exist_ok=True)
    results: list[CuratedPhoto] = []
    headers = {"User-Agent": USER_AGENT}

    for i, scene in enumerate(scenes):
        query = getattr(scene, "image_search_query", "") or "Financial stock market exchange"
        photo = search_wikimedia_photo(query, target_dir, i + 1)

        # If live search didn't return an image, use curated high-res CC0 fallback pool
        if not photo:
            fallback = FALLBACK_EDITORIAL_PHOTOS[i % len(FALLBACK_EDITORIAL_PHOTOS)]
            dest = target_dir / f"scene_photo_{i + 1}.jpg"
            try:
                fb_resp = requests.get(fallback["imageUrl"], headers=headers, timeout=20)
                if fb_resp.ok:
                    dest.write_bytes(fb_resp.content)
                    photo = CuratedPhoto(
                        local_path=dest,
                        image_url=fallback["imageUrl"],
                        source_url=fallback["imageSourceUrl"],
                        credit=fallback["credit"],
                        license_name=fallback["imageLicense"],
                        license_url=fallback["imageLicenseUrl"],
                    )
            except Exception as exc:
                logger.warning("Failed downloading fallback photo: %s", exc)

        if photo:
            results.append(photo)

    logger.info("Curated %d rights-cleared photos for %d scenes", len(results), len(scenes))
    return results
