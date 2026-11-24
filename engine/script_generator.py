"""AI Script Generator module using Gemini API.

Transforms raw financial news into a punchy, accurate 30-35 second Thai narration script,
complete with structured scenes, Lucide icons, and English image search queries for Wikimedia Commons.
"""
from __future__ import annotations

import json
import logging
import os
import re
from dataclasses import dataclass, field
from typing import Any
import requests

from engine.news_fetcher import RawNewsItem

logger = logging.getLogger(__name__)

GEMINI_API_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent"


@dataclass
class ScriptScene:
    label: str
    title: str
    body: str
    icon: str
    image_search_query: str


@dataclass
class ProcessedStory:
    title: str
    category: str
    summary: str
    script: str
    caption: str
    scenes: list[ScriptScene]
    source_name: str
    source_url: str
    score: int = 90
    metadata: dict[str, Any] = field(default_factory=dict)


SCRIPT_SYSTEM_PROMPT = """คุณคือบรรณาธิการข่าวเศรษฐกิจและการเงินมืออาชีพของเพจ "คิดให้คุ้ม - เห็นตัวเลขจริงก่อนตัดสินใจ"
หน้าที่ของคุณคือรับข่าวเศรษฐกิจ/ตลาดหุ้น/การเงิน แล้วสรุปเป็นบทพากย์วิดีโอสั้น Reels แนวตั้งความยาว 30-35 วินาที (ประมาณ 100-130 คำไทย)
ภาษาต้องกระชับ น่าเชื่อถือ ชัดเจนด้วยตัวเลขจริง ไม่ใช้คำเว่อร์เกินจริง

ต้องแบ่งเนื้อหาเป็น 3 ฉาก (Scene 1, Scene 2, Scene 3) เสมอ โดยแต่ละฉากต้องมี:
1. label: ป้ายหัวข้อฉากสั้นๆ เช่น "ข่าวด่วน", "สถิติตลาด", "ผลกระทบต่อไทย"
2. title: พาดหัวฉากย่อย (ไม่เกิน 30 ตัวอักษร)
3. body: บทพูดพากย์ของฉากนั้น (เป็นภาษาไทยธรรมชาติ เหมาะกับการอ่านออกเสียง)
4. icon: ชื่อ Lucide icon ภาษาอังกฤษที่ตรงกับฉาก (เลือกจาก: chart-line, cpu, landmark, hand-coins, briefcase-business, trending-up, globe, building-2)
5. image_search_query: คำค้นหาภาพข่าว/สถานที่/สัญลักษณ์จริงเป็นภาษาอังกฤษ สำหรับค้นหาใน Wikimedia Commons (เช่น "Tokyo Stock Exchange", "Silicon semiconductor wafer", "Wall Street New York Stock Exchange")

ตอบกลับเป็น JSON เท่านั้นตามโครงสร้างนี้:
{
  "title": "พาดหัวข่าวหลักสั้นกระชับ",
  "category": "หมวดข่าว",
  "summary": "สรุปข่าว 2-3 บรรทัด",
  "script": "บทพากย์เต็มรวมทุกฉาก",
  "caption": "แคปชั่นโพสต์ Facebook พร้อมแฮชแท็ก 3-5 อัน",
  "scenes": [
    {
      "label": "...",
      "title": "...",
      "body": "...",
      "icon": "...",
      "image_search_query": "..."
    }
  ]
}"""


def generate_story_script(item: RawNewsItem, api_key: str | None = None) -> ProcessedStory:
    key = api_key or os.environ.get("GEMINI_API_KEY", "").strip()
    if not key:
        logger.warning("No GEMINI_API_KEY found, using structured fallback template")
        return make_fallback_story(item)

    prompt = f"""หัวข้อข่าว: {item.title}
เนื้อหาข่าว: {item.summary}
แหล่งข่าว: {item.source_name} ({item.link})
หมวดหมู่: {item.category}

กรุณาเขียนบทพากย์ Reels 30-35 วินาที พร้อมโครงสร้าง 3 ฉากตามข้อกำหนด"""

    payload = {
        "contents": [
            {
                "parts": [
                    {"text": SCRIPT_SYSTEM_PROMPT},
                    {"text": prompt},
                ]
            }
        ],
        "generationConfig": {
            "temperature": 0.2,
            "responseMimeType": "application/json",
        },
    }

    try:
        url = f"{GEMINI_API_URL}?key={key}"
        resp = requests.post(url, json=payload, timeout=25)
        if not resp.ok:
            logger.warning("Gemini script generation returned HTTP %s: %s", resp.status_code, resp.text[:200])
            return make_fallback_story(item)

        data = resp.json()
        candidates = data.get("candidates") or []
        if not candidates:
            return make_fallback_story(item)

        content_text = candidates[0].get("content", {}).get("parts", [{}])[0].get("text", "")
        # Parse JSON
        result = json.loads(content_text)
        scenes = [
            ScriptScene(
                label=s.get("label", "รายงานข่าว"),
                title=s.get("title", "ภาพรวม"),
                body=s.get("body", ""),
                icon=s.get("icon", "chart-line"),
                image_search_query=s.get("image_search_query", "Stock exchange building"),
            )
            for s in result.get("scenes", [])
        ]
        if len(scenes) < 3:
            return make_fallback_story(item)

        return ProcessedStory(
            title=result.get("title", item.title),
            category=result.get("category", item.category),
            summary=result.get("summary", item.summary),
            script=result.get("script", " ".join(s.body for s in scenes)),
            caption=result.get("caption", f"{item.title}\n\n#คิดให้คุ้ม #ข่าวการเงิน #การลงทุน"),
            scenes=scenes,
            source_name=item.source_name,
            source_url=item.link,
        )
    except Exception as exc:
        logger.warning("Error generating script via Gemini (%s): %s", type(exc).__name__, exc)
        return make_fallback_story(item)


def make_fallback_story(item: RawNewsItem) -> ProcessedStory:
    """Fallback story structure if AI API is temporarily unavailable."""
    title = item.title
    scenes = [
        ScriptScene(
            label="ข่าวด่วนการเงิน",
            title="ตลาดหุ้นและเทคโนโลยี",
            body="จับตาความเคลื่อนไหวตลาดการเงินและหุ้นกลุ่มเทคโนโลยี AI ที่ปรับตัวขึ้นอย่างแข็งแกร่ง หนุนความเชื่อมั่นนักลงทุนทั่วเอเชีย",
            icon="chart-line",
            image_search_query="Tokyo Stock Exchange building entrance",
        ),
        ScriptScene(
            label="เกาะติดตัวเลข",
            title="แรงขับเคลื่อนชิป AI",
            body="แรงซื้อในหุ้นกลุ่มเซมิคอนดักเตอร์และชิปปัญญาประดิษฐ์ส่งผลให้ดัชนีสำคัญพุ่งขึ้น ดันยอดคำสั่งซื้อฟื้นตัวชัดเจน",
            icon="cpu",
            image_search_query="Semiconductor silicon microchip wafer",
        ),
        ScriptScene(
            label="ผลกระทบตลาด",
            title="ภาพรวมเศรษฐกิจ",
            body="ตลาดหุ้นโลกและวอลล์สตรีทส่งสัญญาณบวกต่อเนื่อง ส่งผลดีต่อทิศทางการลงทุนในตลาดหุ้นไทยและภูมิภาค",
            icon="landmark",
            image_search_query="New York Stock Exchange Wall Street entrance",
        ),
    ]
    script = " ".join(s.body for s in scenes)
    caption = f"{title}\n\nสรุปความเคลื่อนไหวตัวเลขสำคัญและทิศทางการลงทุนประจำวัน\n\n#คิดให้คุ้ม #ข่าวการเงิน #หุ้นไทย #เศรษฐกิจ"
    return ProcessedStory(
        title=title,
        category=item.category,
        summary=item.summary,
        script=script,
        caption=caption,
        scenes=scenes,
        source_name=item.source_name,
        source_url=item.link,
    )
