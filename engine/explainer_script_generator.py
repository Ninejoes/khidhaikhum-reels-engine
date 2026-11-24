"""Explainer Script Generator module.

Generates 5-beat educational financial explainer scripts matching the
"คิดให้คุ้ม - เห็นตัวเลขจริงก่อนตัดสินใจ" brand identity:
1. The Hook (Pain Point)
2. The Mechanism (Concept)
3. Hidden Costs & Caveats (Warning)
4. Real Math & Calculation (Seeing the actual numbers)
5. Actionable Checklist & Call to Action
"""
from __future__ import annotations

import json
import logging
import os
import re
from pathlib import Path
from typing import Any
import requests

from engine.whiteboard_renderer import ExplainerBeat, ExplainerTopic

logger = logging.getLogger(__name__)

GEMINI_API_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent"

EXPLAINER_SYSTEM_PROMPT = """คุณคือบรรณาธิการและผู้เชี่ยวชาญด้านการเงินส่วนบุคคลของเพจ "คิดให้คุ้ม - เห็นตัวเลขจริงก่อนตัดสินใจ"
หน้าที่ของคุณคือสร้างบทวิดีโอสั้น Whiteboard Explainer ความยาว 1.5 - 2 นาที (ประมาณ 180-250 คำ) ในสไตล์คุยง่าย เข้าใจทันที มีตัวเลขชัดเจน
ห้ามใช้คำศัพท์วิชาการยากๆ ให้เล่าเหมือนเพื่อนที่มีความรู้การเงินอธิบายให้ฟัง

โครงสร้างต้องแบ่งออกเป็น 5 Beats เสมอ:
1. beat_id: "hook" -> เปิดด้วยปัญหาคาใจ เช่น ผ่อนบ้านครบ 3 ปี ดอกเบี้ยพุ่ง (doodle_name: "house")
2. beat_id: "mechanism" -> อธิบายหลักการทำงาน ย้ายหนี้ไปแบงก์ใหม่ (doodle_name: "refinance" หรือ "bank")
3. beat_id: "warning" -> ข้อควรระวังและค่าใช้จ่ายแฝง (doodle_name: "warning")
4. beat_id: "math" -> ตัวเลขจริง คำนวณให้ดูจะๆ ว่าประหยัดได้เท่าไหร่ (doodle_name: "calculator" หรือ "money_bag")
5. beat_id: "checklist" -> เช็กลิสต์ก่อนตัดสินใจ 3-5 ข้อ พร้อมชวนคอมเมนต์ (doodle_name: "checklist")

ตอบกลับเป็น JSON เท่านั้นตามโครงสร้างนี้:
{
  "title": "หัวข้อหลัก เช่น รีไฟแนนซ์บ้าน คืออะไร?",
  "category": "กู้บ้าน & ดอกเบี้ย",
  "summary": "สรุปสาระสำคัญสั้นๆ",
  "caption": "แคปชั่นสำหรับโพสต์ Reels พร้อมแฮชแท็ก",
  "beats": [
    {
      "beat_id": "hook",
      "doodle_name": "house",
      "title": "...",
      "subtitle": "...",
      "callouts": ["...", "..."],
      "spoken_script": "...",
      "marker_coords": [820, 1150]
    }
  ]
}"""


def get_curated_refinance_topic() -> ExplainerTopic:
    """Returns the flagship Refinance Explainer matching reference reel #4742958775935653."""
    beats = [
        ExplainerBeat(
            beat_id="hook",
            doodle_name="house",
            title="รีไฟแนนซ์บ้าน คืออะไร?",
            subtitle="ครบ 3 ปี ดอกเบี้ยพุ่งขึ้นเท่าตัว!",
            callouts=[
                "🏠 3 ปีแรก ดอกเบี้ยโปรโมชันเฉลี่ย 2.8 - 3.5%",
                "📈 ปีที่ 4 เป็นต้นไป ลอยตัวพุ่งสูงถึง 5.5 - 6.5%!",
            ],
            spoken_script="ผ่อนบ้านมาครบ 3 ปี สังเกตไหมครับว่าดอกเบี้ยปรับพุ่งสูงขึ้นเกือบเท่าตัว จากที่เคยจ่ายดอกเบี้ยต่ำๆ เงินต้นแทบไม่ลดเลย วันนี้ คิดให้คุ้ม พามาดูวิธีลดดอกเบี้ยกันครับ",
            marker_coords=(840, 1200),
        ),
        ExplainerBeat(
            beat_id="mechanism",
            doodle_name="refinance",
            title="ย้ายหนี้ไป แบงก์ใหม่",
            subtitle="กู้ที่ใหม่ ดอกเบี้ยถูกกว่าเดิม มาปิดที่เก่า",
            callouts=[
                "🏦 แบงก์เดิม: ดอกเบี้ยลอยตัว 6.0% ต่อปี",
                "✨ แบงก์ใหม่: โปรโมชันลดเหลือเพียง 3.2% ต่อปี",
            ],
            spoken_script="รีไฟแนนซ์ ก็คือการขอกู้เงินจากธนาคารใหม่ ที่ให้ดอกเบี้ยโปรโมชันถูกกว่าเดิม มาปิดยอดหนี้คงเหลือกับธนาคารเดิม เพื่อให้เราจ่ายค่างวดลดลง หรือตัดเงินต้นได้มากขึ้นครับ",
            marker_coords=(820, 1220),
        ),
        ExplainerBeat(
            beat_id="warning",
            doodle_name="warning",
            title="ระวัง 3 ค่าใช้จ่ายแฝง!",
            subtitle="คิดให้คุ้ม ก่อนตัดสินใจย้ายแบงก์",
            callouts=[
                "⚠️ ค่าปรับไถ่ถอนก่อน 3 ปี (1-3% ของยอดหนี้)",
                "📑 ค่าจดจำนอง 1% + ค่าประเมินหลักทรัพย์",
            ],
            spoken_script="แต่ช้าก่อนครับ ก่อนจะย้ายแบงก์ ต้องระวังค่าใช้จ่ายแฝง เช่น ค่าจดจำนอง 1 เปอร์เซ็นต์ และค่าประเมินราคาหลักทรัพย์ ถ้าประหยัดดอกเบี้ยได้น้อยกว่าค่าธรรมเนียมพวกนี้ ก็อาจจะไม่คุ้มครับ",
            marker_coords=(840, 1210),
        ),
        ExplainerBeat(
            beat_id="math",
            doodle_name="calculator",
            title="ตัวเลขจริง: หนี้ 2 ล้านบาท",
            subtitle="ผ่อนต่อ 20 ปี ประหยัดได้ขนาดไหน?",
            callouts=[
                "💰 แบบเดิม: จ่ายดอกเบี้ย 3 ปี รวม 360,000 บาท",
                "🎉 รีไฟแนนซ์: ดอกเบี้ยเหลือ 192,000 บาท (ประหยัด 1.6 แสน!)",
            ],
            spoken_script="มาดูตัวเลขจริงกันครับ สมมติยอดหนี้คงเหลือ 2 ล้านบาท ถ้าปล่อยดอกเบี้ย 6 เปอร์เซ็นต์ 3 ปีจะเสียดอก 3.6 แสน แต่ถ้ารีไฟแนนซ์เหลือ 3.2 เปอร์เซ็นต์ 3 ปีจ่ายดอกแค่ 1.9 แสน ประหยัดเงินในกระเป๋าไปได้ถึง 1.6 แสนบาทเลยครับ",
            marker_coords=(820, 1220),
        ),
        ExplainerBeat(
            beat_id="checklist",
            doodle_name="checklist",
            title="เช็กลิสต์ 4 ข้อก่อนเริ่ม",
            subtitle="ทำตามนี้ คุ้มชัวร์ ไม่เสียเที่ยว",
            callouts=[
                "1. ผ่อนครบ 3 ปีหรือยังเพื่อเลี่ยงค่าปรับ",
                "2. ลองขอ Retention ขอลดดอกกับแบงก์เดิมก่อน",
            ],
            spoken_script="สรุป 4 ข้อต้องเช็ก 1. ผ่อนครบ 3 ปีแล้ว 2. ลองขอลดดอกเบี้ยกับแบงก์เดิมก่อน ถ้าไม่ได้ค่อยย้าย 3. เปรียบเทียบโปรโมชันอย่างน้อย 3 แบงก์ ใครกำลังผ่อนบ้านอยู่ คอมเมนต์ปรึกษาได้เลยครับ",
            marker_coords=(840, 1200),
        ),
    ]

    return ExplainerTopic(
        title="รีไฟแนนซ์บ้าน คืออะไร? ดูจบรู้เลยว่าควรทำไหม 🏠",
        category="กู้บ้าน & ดอกเบี้ย",
        summary="เจาะลึกการรีไฟแนนซ์บ้าน ผ่อนครบ 3 ปี ย้ายหนี้ไปแบงก์ใหม่คุ้มจริงไหม พร้อมสูตรคำนวณเงินหนี้ 2 ล้าน ประหยัดดอกเบี้ยได้เป็นแสน",
        caption=(
            "ผ่อนบ้านครบ 3 ปี ดอกเบี้ยพุ่งขึ้นเท่าตัว! 🏠💸\n\n"
            "รีไฟแนนซ์บ้านคุ้มจริงไหม หรือแค่ย้ายหนี้ไปมา? วันนี้ 'คิดให้คุ้ม' พามาดูตัวเลขจริง หนี้ 2 ล้านบาท ช่วยประหยัดเงินในกระเป๋าได้ถึง 1.6 แสนบาท พร้อมเช็กลิสต์ 4 ข้อที่ต้องรู้ก่อนตัดสินใจ!\n\n"
            "#คิดให้คุ้ม #รีไฟแนนซ์บ้าน #ผ่อนบ้าน #ดอกเบี้ยบ้าน #วางแผนการเงิน #การเงินส่วนบุคคล"
        ),
        beats=beats,
    )


def generate_explainer_topic(
    topic_prompt: str | None = None, api_key: str | None = None
) -> ExplainerTopic:
    """Generates an explainer topic via Gemini 2.5 Flash, or returns the curated flagship topic."""
    key = api_key or os.environ.get("GEMINI_API_KEY", "").strip()
    if not key or not topic_prompt:
        logger.info("Using curated flagship Refinance Explainer topic")
        return get_curated_refinance_topic()

    try:
        user_msg = f"สร้างบทความรู้การเงิน Whiteboard Explainer 5 Beats ในหัวข้อ: {topic_prompt}"
        payload = {
            "contents": [
                {
                    "parts": [
                        {"text": EXPLAINER_SYSTEM_PROMPT},
                        {"text": user_msg},
                    ]
                }
            ],
            "generationConfig": {
                "temperature": 0.3,
                "responseMimeType": "application/json",
            },
        }

        resp = requests.post(
            f"{GEMINI_API_URL}?key={key}",
            headers={"Content-Type": "application/json"},
            json=payload,
            timeout=30,
        )
        if resp.ok:
            data = resp.json()
            text = data["candidates"][0]["content"]["parts"][0]["text"]
            clean_json = re.sub(r"^```(?:json)?\s*|\s*```$", "", text.strip())
            obj = json.loads(clean_json)

            beats = []
            for b in obj.get("beats", []):
                beats.append(
                    ExplainerBeat(
                        beat_id=b.get("beat_id", "beat"),
                        doodle_name=b.get("doodle_name", "house"),
                        title=b.get("title", ""),
                        subtitle=b.get("subtitle", ""),
                        callouts=b.get("callouts", []),
                        spoken_script=b.get("spoken_script", ""),
                        marker_coords=tuple(b.get("marker_coords", [820, 1150])),
                    )
                )

            return ExplainerTopic(
                title=obj.get("title", topic_prompt),
                category=obj.get("category", "การเงินส่วนบุคคล"),
                summary=obj.get("summary", ""),
                caption=obj.get("caption", ""),
                beats=beats,
            )
    except Exception as exc:
        logger.warning("Gemini explainer generation failed (%s): %s", type(exc).__name__, exc)

    return get_curated_refinance_topic()
