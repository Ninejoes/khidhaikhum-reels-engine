"""Explainer Script Generator module.

Generates 5-beat educational financial and news explainer scripts matching the
"คิดให้คุ้ม - เห็นตัวเลขจริงก่อนตัดสินใจ" brand identity:
1. The Hook (Pain Point / Breaking Impact)
2. The Mechanism (Root Cause / Underlying Concept)
3. Hidden Costs & Caveats (Warning / Risks)
4. Real Math & Calculation (Seeing the actual numbers)
5. Actionable Checklist & Call to Action (How to prepare + Comment invite)
"""
from __future__ import annotations

import json
import logging
import os
import re
from datetime import datetime
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo
import requests

from engine.whiteboard_renderer import ExplainerBeat, ExplainerTopic

logger = logging.getLogger(__name__)

GEMINI_PRIMARY_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent"
GEMINI_FALLBACK_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent"

NEWS_EXPLAINER_SYSTEM_PROMPT = """คุณคือบรรณาธิการและผู้เชี่ยวชาญด้านการเงินของเพจ "คิดให้คุ้ม - เห็นตัวเลขจริงก่อนตัดสินใจ"
หน้าที่ของคุณคือนำ "ข่าวเศรษฐกิจ/การเงิน/กระแสสังคม/นโยบาย" มาแปลงเป็นบทวิดีโอสั้น Whiteboard Explainer 5 Beats
ความยาวประมาณ 1.5 - 2 นาที (180-250 คำ) ในสไตล์คุยง่าย สบายๆ เหมือนเพื่อนเล่าให้ฟัง เห็นตัวเลขชัดเจน

กฎสำคัญในการเล่าเรื่อง:
1. หากเป็นข่าวทั่วไป ข่าวกระแสสังคม หรือนโยบายรัฐ ให้เชื่อมโยงเข้าสู่มุมมอง "กระทบเงินในกระเป๋าเรากี่บาท" หรือ "เห็นตัวเลขจริงก่อนตัดสินใจ" เสมอ
2. ตัวเลขและสถิติต้องแม่นยำ อิงตามเนื้อหาข่าวจริง
3. แฮชแท็กและแคปชั่นต้องทำ Facebook SEO เพื่อการเข้าถึงสูงสุด

โครงสร้างต้องแบ่งออกเป็น 5 Beats เสมอ:
1. beat_id: "hook" -> เปิดด้วยประเด็นข่าวร้อน/ข้อเท็จจริงชวนคิด ทำไมคนดูต้องแคร์ (doodle_name: "money_bag", "chart", "globe", "bank", "house", หรือ "warning")
2. beat_id: "mechanism" -> อธิบายสาเหตุ ที่มาที่ไป ทำไมถึงเกิดเหตุการณ์นี้ขึ้น (doodle_name: "chart", "bank", "globe", "refinance")
3. beat_id: "warning" -> ข้อควรระวัง ความเสี่ยง ผลกระทบ หรือสิ่งที่ต้องจับตา (doodle_name: "warning")
4. beat_id: "math" -> ตัวเลขจริง คำนวณให้ดูจะๆ: ราคากระทบกี่บาท, ขาดทุน/กำไรเท่าไหร่, กระทบค่าครองชีพยังไง (doodle_name: "calculator", "money_bag", หรือ "chart")
5. beat_id: "checklist" -> 3-4 ข้อต้องรู้เพื่อรับมือ/วางแผน พร้อมคำถามชวนคอมเมนต์ (doodle_name: "checklist")

doodle_name ที่ระบบรองรับ: "bank", "calculator", "checklist", "house", "money_bag", "refinance", "warning", "chart", "globe"

ตอบกลับเป็น JSON เท่านั้นตามโครงสร้างนี้:
{
  "title": "หัวข้อคลิปที่น่าสนใจ ชัดเจน ตรงประเด็น",
  "category": "หมวดหมู่ เช่น ราคาทองคำ, ตลาดหุ้น, ดอกเบี้ย, การบริหารเงิน",
  "summary": "สรุปเนื้อหาข่าวแบบกระชับ 2-3 ประโยค",
  "caption": "แคปชั่น Facebook Reels แบบเต็ม พร้อม Hook, ตัวเลขสำคัญ, และแฮชแท็ก SEO 4-5 อัน",
  "beats": [
    {
      "beat_id": "hook",
      "doodle_name": "money_bag",
      "title": "หัวข้อสั้นบนกระดาน (ไม่เกิน 30 ตัวอักษร)",
      "subtitle": "คำอธิบายกระชับ (ไม่เกิน 40 ตัวอักษร)",
      "callouts": [
        "ข้อความไฮไลต์ที่ 1",
        "ข้อความไฮไลต์ที่ 2"
      ],
      "spoken_script": "บทพูดภาษาไทยสำหรับเสียงบรรยาย ชัดเจน ลื่นไหล เป็นธรรมชาติ",
      "marker_coords": [820, 1150]
    }
  ]
}"""

TOPIC_EXPLAINER_SYSTEM_PROMPT = """คุณคือบรรณาธิการและผู้เชี่ยวชาญด้านการเงินส่วนบุคคลของเพจ "คิดให้คุ้ม - เห็นตัวเลขจริงก่อนตัดสินใจ"
หน้าที่ของคุณคือสร้างบทวิดีโอสั้น Whiteboard Explainer ความยาว 1.5 - 2 นาที (ประมาณ 180-250 คำ) ในสไตล์คุยง่าย เข้าใจทันที มีตัวเลขชัดเจน
ห้ามใช้คำศัพท์วิชาการยากๆ ให้เล่าเหมือนเพื่อนที่มีความรู้การเงินอธิบายให้ฟัง

โครงสร้างต้องแบ่งออกเป็น 5 Beats เสมอ:
1. beat_id: "hook" -> เปิดด้วยปัญหาคาใจ (doodle_name: "house", "bank", "money_bag")
2. beat_id: "mechanism" -> อธิบายหลักการทำงาน (doodle_name: "refinance", "bank", "chart")
3. beat_id: "warning" -> ข้อควรระวังและค่าใช้จ่ายแฝง (doodle_name: "warning")
4. beat_id: "math" -> ตัวเลขจริง คำนวณให้ดูจะๆ ว่าประหยัดหรือได้ผลตอบแทนเท่าไหร่ (doodle_name: "calculator", "money_bag")
5. beat_id: "checklist" -> เช็กลิสต์ก่อนตัดสินใจ 3-5 ข้อ พร้อมชวนคอมเมนต์ (doodle_name: "checklist")

ตอบกลับเป็น JSON เท่านั้นตามโครงสร้างมาตรฐาน"""


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
            "💡 ตัวเลขจริงที่ต้องรู้:\n"
            "• ดอกเบี้ยเดิม 6.0% = 3 ปี เสียดอกเบี้ย 360,000 บาท\n"
            "• ดอกเบี้ยใหม่ 3.2% = 3 ปี เสียดอกเบี้ย 192,000 บาท\n"
            "• ประหยัดเงินต้น-ดอกเบี้ยทันที 168,000 บาท!\n\n"
            "คิดให้คุ้ม อยากชวนทุกคนมาแชร์กันครับว่า ดอกเบี้ยบ้านตอนนี้ผ่อนอยู่กี่เปอร์เซ็นต์? คอมเมนต์แลกเปลี่ยนกันได้เลย!\n\n"
            "#คิดให้คุ้ม #รีไฟแนนซ์บ้าน #ผ่อนบ้าน #ดอกเบี้ยบ้าน #วางแผนการเงิน"
        ),
        beats=beats,
    )


def select_doodle_for_text(text: str) -> str:
    """Intelligently picks a suitable doodle icon matching the topic keywords."""
    lower = text.lower()
    if any(k in lower for k in ["ทอง", "gold", "เหรียญ", "เงิน", "บาท", "ดอลลาร์", "currency", "crypto"]):
        return "money_bag"
    if any(k in lower for k in ["หุ้น", "set", "ตลาด", "เศรษฐกิจ", "gdp", "ดัชนี", "trade", "ชิป", "ai"]):
        return "chart"
    if any(k in lower for k in ["โลก", "ต่างประเทศ", "fed", "สงคราม", "สหรัฐ", "จีน", "ยุโรป", "global"]):
        return "globe"
    if any(k in lower for k in ["บ้าน", "คอนโด", "ที่ดิน", "อสังหา", "เช่า"]):
        return "house"
    if any(k in lower for k in ["หนี้", "ดอกเบี้ย", "รีไฟแนนซ์", "บัตร", "กู้", "เงินกู้"]):
        return "refinance"
    if any(k in lower for k in ["ธนาคาร", "แบงก์", "bot", "แบงก์ชาติ", "ฝากเงิน"]):
        return "bank"
    if any(k in lower for k in ["ระวัง", "ร่วง", "เตือน", "หลุมพราง", "วิกฤต", "ระเบิด"]):
        return "warning"
    if any(k in lower for k in ["คำนวณ", "ตัวเลข", "ภาษี", "สูตร"]):
        return "calculator"
    return "money_bag"


def build_seo_caption(title: str, summary: str, math_points: list[str], hashtags: list[str] | None = None) -> str:
    """Builds a high-converting Facebook Reels SEO caption."""
    tags = hashtags or ["#คิดให้คุ้ม", "#สรุปข่าวเศรษฐกิจ", "#ข่าวการเงิน", "#การเงินส่วนบุคคล", "#เห็นตัวเลขจริงก่อนตัดสินใจ"]
    tag_str = " ".join(tags[:5])

    points_str = "\n".join(f"• {p}" for p in math_points if p)
    if not points_str:
        points_str = "• ติดตามตัวเลขและความคุ้มค่าแบบเจาะลึกได้ในคลิปนี้"

    return (
        f"{title.strip()} 📊💡\n\n"
        f"{summary.strip()}\n\n"
        f"🔍 ตัวเลขจริงที่ต้องรู้:\n"
        f"{points_str}\n\n"
        f"คิดให้คุ้ม อยากชวนทุกคนมาแลกเปลี่ยนความคิดเห็นกันครับ คุณมองเรื่องนี้ยังไง คอมเมนต์บอกเราได้เลย!\n\n"
        f"{tag_str}"
    )


def deterministic_news_to_explainer(news_item: dict[str, Any]) -> ExplainerTopic:
    """Deterministic, 100% resilient converter that transforms any news item into 5 beats."""
    title = news_item.get("title", "").strip() or "สรุปข่าวเศรษฐกิจล่าสุด"
    summary = news_item.get("summary", "").strip()
    impact = news_item.get("impact", "").strip() or "กระทบต่อต้นทุนและเงินในกระเป๋าที่เราต้องวางแผน"
    category = news_item.get("category", "ข่าวเศรษฐกิจและการเงิน")

    # Extract numbers or percentages for the math beat
    found_numbers = re.findall(r"(\d+(?:[.,]\d+)?\s*(?:%|ดอลลาร์|บาท|ล้าน|จุด|แสน|เหรียญ|เท่า))", f"{title} {summary}")
    num_highlight1 = found_numbers[0] if len(found_numbers) > 0 else "ตัวเลขสำคัญที่ต้องจับตา"
    num_highlight2 = found_numbers[1] if len(found_numbers) > 1 else "กระทบการตัดสินใจทางการเงิน"

    hook_doodle = select_doodle_for_text(title)
    math_doodle = "calculator" if hook_doodle != "calculator" else "money_bag"

    # Clean short title for frame
    clean_title = re.sub(r"^(?:ด่วน[^\s—–-]*|\d+[:.]\d+\s*น\.?|\d+\s*(?:ม\.ค\.|ก\.พ\.|มี\.ค\.|เม\.ย\.|พ\.ค\.|มิ\.ย\.|ก\.ค\.|ส\.ค\.|ก\.ย\.|ต\.ค\.|พ\.ย\.|ธ\.ค\.)|[—–\-:!|•\s])+", "", title).strip()
    if len(clean_title) > 30:
        cutoff = clean_title[:30].rfind(" ")
        short_title = clean_title[:cutoff].strip() if cutoff > 12 else clean_title[:30].strip()
    else:
        short_title = clean_title

    beats = [
        ExplainerBeat(
            beat_id="hook",
            doodle_name=hook_doodle,
            title=short_title,
            subtitle="สรุปประเด็นร้อน กระทบเรายังไง?",
            callouts=[
                f"🚨 {clean_title[:38]}",
                f"📌 สิ่งที่ต้องรู้: {summary[:40]}...",
            ],
            spoken_script=f"มีข่าวด่วนที่ต้องจับตาครับ {clean_title} เรื่องนี้ส่งผลกระทบต่อเรายังไง วันนี้ คิดให้คุ้ม สรุปเนื้อหาสำคัญและตัวเลขจริงมาให้ฟังกันครับ",
            marker_coords=(840, 1200),
        ),
        ExplainerBeat(
            beat_id="mechanism",
            doodle_name="chart" if hook_doodle != "chart" else "globe",
            title="เกิดอะไรขึ้น เบื้องหลังคืออะไร?",
            subtitle="เจาะลึกสาเหตุและกลไกที่เกิดขึ้น",
            callouts=[
                f"📈 สาเหตุหลัก: {summary[:42]}",
                "⚙️ ปัจจัยขับเคลื่อนที่ต้องติดตาม",
            ],
            spoken_script=f"สาเหตุของเรื่องนี้ เกิดจาก {summary[:120]} ซึ่งเป็นกลไกที่ตลาดและผู้เชี่ยวชาญกำลังจับตามองอย่างใกล้ชิดครับ",
            marker_coords=(820, 1220),
        ),
        ExplainerBeat(
            beat_id="warning",
            doodle_name="warning",
            title="ข้อควรระวัง & ผลกระทบ!",
            subtitle="คิดให้คุ้ม ก่อนตัดสินใจ",
            callouts=[
                f"⚠️ ผลกระทบ: {impact[:40]}",
                "🛑 อย่าเพิ่งตื่นตระหนก วางแผนให้รอบคอบ",
            ],
            spoken_script=f"ข้อควรระวังคือ {impact[:100]} หากเราไม่วางแผนให้ดี อาจส่งผลกระทบต่อต้นทุนหรือเงินในกระเป๋าได้ครับ",
            marker_coords=(840, 1210),
        ),
        ExplainerBeat(
            beat_id="math",
            doodle_name=math_doodle,
            title="ตัวเลขจริงที่ต้องรู้",
            subtitle="คำนวณผลกระทบให้เห็นชัดๆ",
            callouts=[
                f"🔢 ตัวเลขหลัก: {num_highlight1}",
                f"💡 จุดสังเกต: {num_highlight2}",
            ],
            spoken_script=f"มาดูตัวเลขจริงกันครับ การเคลื่อนไหวครั้งนี้มีตัวเลขสำคัญคือ {num_highlight1} และ {num_highlight2} ซึ่งเป็นเกณฑ์ชี้วัดทิศทางต่อจากนี้ครับ",
            marker_coords=(820, 1220),
        ),
        ExplainerBeat(
            beat_id="checklist",
            doodle_name="checklist",
            title="เช็กลิสต์ 3 ข้อรับมือ",
            subtitle="ทำตามนี้ รับมือได้ทุกสถานการณ์",
            callouts=[
                "1. ติดตามข้อมูลข่าวสารอย่างต่อเนื่อง",
                "2. บริหารจัดการสภาพคล่องและเงินสด",
            ],
            spoken_script=f"สรุปสิ่งที่ต้องทำ 1. เช็กตัวเลขจริงก่อนตัดสินใจ 2. รักษาสภาพคล่อง 3. ปรับแผนให้สอดคล้องกับสถานการณ์ คุณคิดเห็นอย่างไรกับเรื่องนี้ คอมเมนต์บอกเราได้เลยครับ",
            marker_coords=(840, 1200),
        ),
    ]

    math_points = [
        f"ตัวเลขสำคัญ: {num_highlight1}",
        f"การเปลี่ยนแปลง: {num_highlight2}",
        f"ผลกระทบ: {impact[:80]}",
    ]
    caption = build_seo_caption(title, summary, math_points)

    return ExplainerTopic(
        title=f"{short_title} — สรุปประเด็นตัวเลขจริง",
        category=category,
        summary=summary,
        caption=caption,
        beats=beats,
    )


def call_gemini_json(system_prompt: str, user_prompt: str, api_key: str) -> dict[str, Any] | None:
    """Calls Gemini API with fallbacks across model versions."""
    payload = {
        "contents": [
            {
                "parts": [
                    {"text": system_prompt},
                    {"text": user_prompt},
                ]
            }
        ],
        "generationConfig": {
            "temperature": 0.25,
            "responseMimeType": "application/json",
        },
    }

    headers = {"Content-Type": "application/json"}
    for url in [GEMINI_PRIMARY_URL, GEMINI_FALLBACK_URL]:
        try:
            logger.info("Calling Gemini API: %s", url.split("/models/")[1].split(":")[0])
            resp = requests.post(f"{url}?key={api_key}", headers=headers, json=payload, timeout=35)
            if resp.ok:
                data = resp.json()
                text = data["candidates"][0]["content"]["parts"][0]["text"]
                clean_json = re.sub(r"^```(?:json)?\s*|\s*```$", "", text.strip())
                return json.loads(clean_json)
            else:
                logger.warning("Gemini model %s returned HTTP %s: %s", url, resp.status_code, resp.text[:200])
        except Exception as exc:
            logger.warning("Gemini call error (%s): %s", url, exc)

    return None


def convert_news_to_explainer_topic(
    news_item: dict[str, Any],
    api_key: str | None = None,
) -> ExplainerTopic:
    """Converts a live news item into a 5-beat Whiteboard Explainer storyboard."""
    key = api_key or os.environ.get("GEMINI_API_KEY", "").strip()

    title = news_item.get("title", "").strip()
    summary = news_item.get("summary", "").strip()
    impact = news_item.get("impact", "").strip()
    category = news_item.get("category", "ข่าวเศรษฐกิจ")

    if key:
        user_msg = (
            f"แปลงข่าวนี้เป็นบทวิดีโอ Whiteboard Explainer 5 Beats:\n"
            f"หัวข้อข่าว: {title}\n"
            f"หมวดหมู่: {category}\n"
            f"สรุปเนื้อหา: {summary}\n"
            f"ผลกระทบ: {impact}\n"
        )
        obj = call_gemini_json(NEWS_EXPLAINER_SYSTEM_PROMPT, user_msg, key)
        if obj and obj.get("beats") and len(obj["beats"]) >= 5:
            beats = []
            for b in obj.get("beats", [])[:5]:
                doodle = b.get("doodle_name", "money_bag")
                if doodle not in ["bank", "calculator", "checklist", "house", "money_bag", "refinance", "warning", "chart", "globe"]:
                    doodle = select_doodle_for_text(b.get("title", ""))

                beats.append(
                    ExplainerBeat(
                        beat_id=b.get("beat_id", "beat"),
                        doodle_name=doodle,
                        title=b.get("title", "")[:32],
                        subtitle=b.get("subtitle", "")[:42],
                        callouts=b.get("callouts", [])[:2],
                        spoken_script=b.get("spoken_script", ""),
                        marker_coords=tuple(b.get("marker_coords", [820, 1150])),
                    )
                )

            return ExplainerTopic(
                title=obj.get("title", title),
                category=obj.get("category", category),
                summary=obj.get("summary", summary),
                caption=obj.get("caption", ""),
                beats=beats,
            )

    logger.info("Using deterministic news converter for: %s", title[:40])
    return deterministic_news_to_explainer(news_item)


def get_scheduled_slot_topic() -> str:
    """Returns scheduled topic prompt aligned with Bangkok editorial calendar."""
    hour = datetime.now(ZoneInfo("Asia/Bangkok")).hour
    if 6 <= hour < 11:
        # 08:25 Morning Personal Finance & Morning Market
        return "สรุปข่าวเศรษฐกิจเช้า & การบริหารจัดการเงิน ดอกเบี้ย และเงินออม"
    elif 11 <= hour < 15:
        # 12:25 Midday Trending Newsjacking
        return "เกาะติดข่าวร้อนกระแสสังคมเที่ยงวัน ผลกระทบต่อค่าครองชีพและราคาสินค้า"
    elif 15 <= hour < 19:
        # 17:25 Evening Big Assets & Debt
        return "นโยบายการเงิน ภาษี อสังหาริมทรัพย์ และการบริหารหนี้สินอย่างคุ้มค่า"
    else:
        # 20:25 Night Global Markets & Commodities
        return "สรุปตลาดโลก ทองคำ ค่าเงิน ดัชนีหุ้น และแนวโน้มเศรษฐกิจวันพรุ่งนี้"


def generate_explainer_topic(
    topic_prompt: str | None = None,
    api_key: str | None = None,
) -> ExplainerTopic:
    """Generates an explainer topic via Gemini 2.0 Flash or returns curated topics."""
    key = api_key or os.environ.get("GEMINI_API_KEY", "").strip()

    if not topic_prompt:
        topic_prompt = get_scheduled_slot_topic()
        logger.info("Auto-selected slot topic: %s", topic_prompt)

    if not key:
        logger.info("No Gemini key provided; using flagship Refinance Explainer")
        return get_curated_refinance_topic()

    user_msg = f"สร้างบทความรู้การเงิน Whiteboard Explainer 5 Beats ในหัวข้อ: {topic_prompt}"
    obj = call_gemini_json(TOPIC_EXPLAINER_SYSTEM_PROMPT, user_msg, key)
    if obj and obj.get("beats") and len(obj["beats"]) >= 5:
        beats = []
        for b in obj.get("beats", [])[:5]:
            doodle = b.get("doodle_name", "house")
            if doodle not in ["bank", "calculator", "checklist", "house", "money_bag", "refinance", "warning", "chart", "globe"]:
                doodle = select_doodle_for_text(b.get("title", ""))
            beats.append(
                ExplainerBeat(
                    beat_id=b.get("beat_id", "beat"),
                    doodle_name=doodle,
                    title=b.get("title", "")[:32],
                    subtitle=b.get("subtitle", "")[:42],
                    callouts=b.get("callouts", [])[:2],
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

    return get_curated_refinance_topic()
