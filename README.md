# Think for Value (คิดให้คุ้ม) — All-in-One Automated News Reel Engine

ระบบผลิตและเผยแพร่วิดีโอสั้น Facebook Reels (1080×1920) อัตโนมัติ 100% บน GitHub Actions คลาวด์ฟรี ($0/เดือน)
ไม่ต้องเปิดคอมพิวเตอร์ทิ้งไว้ พร้อมดึงภาพข่าวลิขสิทธิ์เสรี CC0 จาก Wikimedia Commons และเสียงพากย์ AI ภาษาไทยคุณภาพสูง

---

## 🌟 ฟีเจอร์เด่น
- **All-in-One Cloud Native:** รวมทุกขั้นตอน (ดึงข่าว -> เขียนบท -> หาภาพลิขสิทธิ์ -> เรนเดอร์ 1080×1920 -> โพสต์ Facebook) ไว้ใน GitHub Actions ตัวเดียว
- **ฟรี 100% ($0/เดือน):** ทำงานบน GitHub Actions Public Free Tier, Gemini API Free Tier, และ Meta Graph API
- **ภาพข่าวลิขสิทธิ์เสรี (Rights-Cleared):** ดึงภาพ CC0 1.0 และ Public Domain จาก Wikimedia Commons API อัตโนมัติ ปลอดภัยจากการละเมิดลิขสิทธิ์
- **เสียงพากย์ AI ภาษาไทย:** ใช้ Gemini 3.8 Flash TTS (Charon Voice) เสียงธรรมชาติ ระดับเสียง Broadcast-standard (-16 LUFS)
- **กราฟิกและฟอนต์ไทยแท้:** จัดรูปอักษรไทยด้วย Pillow RAQM ไร้ปัญหาสระลอย ซ้อนด้วย Lucide Topic SVG Badges

---

## 📁 โครงสร้างโปรเจกต์
```
khidhaikhum-reels-engine/
├── .github/workflows/
│   └── auto-publish.yml     # ตารางรันอัตโนมัติบนคลาวด์ (08:30, 12:30, 16:30, 20:30 น.)
├── engine/
│   ├── news_fetcher.py      # ดึง RSS ข่าวเศรษฐกิจ/ตลาดหุ้นไทย
│   ├── script_generator.py  # สรุปบทข่าว 30-35s และคีย์เวิร์ดด้วย Gemini Flash
│   ├── image_curator.py     # ค้นหาและดึงภาพข่าว CC0 จาก Wikimedia Commons
│   ├── voice_synthesizer.py # สังเคราะห์เสียงพากย์ไทยด้วย Gemini TTS
│   ├── video_renderer.py    # เรนเดอร์คลิป 1080x1920 (FFmpeg + Pillow RAQM + SVG)
│   ├── meta_publisher.py    # โพสต์ขึ้น Facebook Reels ตรงผ่าน Graph API v27.0
│   └── pipeline.py          # ตัวเชื่อมโยงไปป์ไลน์แม่บท (Master Orchestrator)
├── assets/
│   ├── fonts/               # ฟอนต์ Google Sans Text & Bold
│   ├── icons/lucide/        # ไอคอน Lucide SVG สัญลักษณ์ข่าว
│   └── illustrations/       # ภาพพื้นหลังกราฟิกข่าวเศรษฐกิจ
├── outputs/                 # ที่เก็บคลิปวิดีโอที่สร้างเสร็จ
├── requirements.txt         # รายการไลบรารี Python
├── main.py                  # สคริปต์คำสั่งหลัก
└── README.md
```

---

## 🚀 วิธีใช้งานบนเครื่อง (Local Usage)
```bash
# 1. ติดตั้งไลบรารี
pip install -r requirements.txt

# 2. เรนเดอร์คลิปพรีวิว (ไม่โพสต์)
python main.py

# 3. เรนเดอร์และโพสต์ขึ้น Facebook ทันที
python main.py --publish
```

---

## ☁️ การติดตั้งบน GitHub Actions เพื่อให้รันออโต้บนคลาวด์
1. Push โค้ดทั้งหมดขึ้น GitHub Repository (ตั้งเป็น **Public** เพื่อใช้งาน Actions ฟรีไม่จำกัดนาที)
2. ไปที่ **Settings > Secrets and variables > Actions** และเพิ่ม Secrets:
   - `GEMINI_API_KEY`: Google AI Studio API Key (ฟรี)
   - `FB_PAGE_ID`: ID ของเพจ Facebook เช่น `1183632304836932`
   - `FB_PAGE_TOKEN`: Page Access Token ของเพจ Facebook
3. ระบบจะรันอัตโนมัติวันละ 4 รอบ (08:30, 12:30, 16:30, 20:30 น. เวลาไทย) ทันทีโดยไม่ต้องเปิดคอม!
