"""Generates clean hand-drawn doodly vector assets in SVG format."""
from pathlib import Path

DOODLES_DIR = Path(__file__).resolve().parent.parent / "assets" / "doodles"
DOODLES_DIR.mkdir(parents=True, exist_ok=True)

# 1. House doodle
house_svg = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 500 500" width="500" height="500" fill="none">
  <!-- Chimney & smoke -->
  <path d="M340 180 L340 120 L380 120 L380 215" stroke="#2B3A42" stroke-width="12" stroke-linecap="round" stroke-linejoin="round"/>
  <path d="M360 95 C360 80, 375 75, 370 60 C365 45, 390 40, 385 25" stroke="#8CA0AA" stroke-width="8" stroke-linecap="round" stroke-dasharray="16 10"/>
  <!-- Roof -->
  <path d="M80 230 L250 85 L420 230" stroke="#E06D53" stroke-width="16" stroke-linecap="round" stroke-linejoin="round"/>
  <path d="M110 215 L250 105 L390 215" stroke="#E06D53" stroke-width="8" stroke-linecap="round"/>
  <!-- House Body -->
  <path d="M120 225 L120 420 C120 425, 125 430, 130 430 L370 430 C375 430, 380 425, 380 420 L380 225" stroke="#2B3A42" stroke-width="14" stroke-linecap="round" stroke-linejoin="round" fill="#FAF9F6"/>
  <!-- Windows -->
  <rect x="150" y="250" width="65" height="65" rx="8" stroke="#3F8A8C" stroke-width="10" fill="#E8F4F5"/>
  <line x1="182" y1="250" x2="182" y2="315" stroke="#3F8A8C" stroke-width="6"/>
  <line x1="150" y1="282" x2="215" y2="282" stroke="#3F8A8C" stroke-width="6"/>
  
  <rect x="285" y="250" width="65" height="65" rx="8" stroke="#3F8A8C" stroke-width="10" fill="#E8F4F5"/>
  <line x1="317" y1="250" x2="317" y2="315" stroke="#3F8A8C" stroke-width="6"/>
  <line x1="285" y1="282" x2="350" y2="282" stroke="#3F8A8C" stroke-width="6"/>
  <!-- Door -->
  <path d="M215 430 L215 340 C215 330, 225 320, 235 320 L265 320 C275 320, 285 330, 285 340 L285 430" stroke="#2B3A42" stroke-width="10" fill="#F4E9D8"/>
  <circle cx="270" cy="380" r="6" fill="#E06D53"/>
  <!-- Ground Grass -->
  <path d="M60 440 L440 440" stroke="#2B3A42" stroke-width="12" stroke-linecap="round"/>
  <path d="M80 435 L75 415 M85 435 L87 410 M92 435 L98 418" stroke="#3F8A8C" stroke-width="6" stroke-linecap="round"/>
  <path d="M405 435 L400 415 M410 435 L412 410 M417 435 L423 418" stroke="#3F8A8C" stroke-width="6" stroke-linecap="round"/>
</svg>"""

# 2. Bank doodle
bank_svg = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 500 500" width="500" height="500" fill="none">
  <!-- Pediment / Roof Triangle -->
  <polygon points="250,70 70,170 430,170" stroke="#2B3A42" stroke-width="14" stroke-linejoin="round" fill="#FAF9F6"/>
  <polygon points="250,95 105,160 395,160" stroke="#3F8A8C" stroke-width="6" fill="#E8F4F5"/>
  <!-- Baht Sign in Pediment -->
  <text x="250" y="145" font-family="sans-serif" font-size="44" font-weight="bold" fill="#3F8A8C" text-anchor="middle" dominant-baseline="middle">฿</text>
  <!-- Architrave beam -->
  <rect x="60" y="170" width="380" height="30" rx="6" stroke="#2B3A42" stroke-width="12" fill="#FAF9F6"/>
  <!-- 4 Columns -->
  <!-- Col 1 -->
  <rect x="90" y="200" width="45" height="180" rx="6" stroke="#2B3A42" stroke-width="10" fill="#FAF9F6"/>
  <line x1="102" y1="210" x2="102" y2="370" stroke="#3F8A8C" stroke-width="4" stroke-linecap="round"/>
  <line x1="122" y1="210" x2="122" y2="370" stroke="#3F8A8C" stroke-width="4" stroke-linecap="round"/>
  <!-- Col 2 -->
  <rect x="175" y="200" width="45" height="180" rx="6" stroke="#2B3A42" stroke-width="10" fill="#FAF9F6"/>
  <line x1="187" y1="210" x2="187" y2="370" stroke="#3F8A8C" stroke-width="4" stroke-linecap="round"/>
  <line x1="207" y1="210" x2="207" y2="370" stroke="#3F8A8C" stroke-width="4" stroke-linecap="round"/>
  <!-- Col 3 -->
  <rect x="280" y="200" width="45" height="180" rx="6" stroke="#2B3A42" stroke-width="10" fill="#FAF9F6"/>
  <line x1="292" y1="210" x2="292" y2="370" stroke="#3F8A8C" stroke-width="4" stroke-linecap="round"/>
  <line x1="312" y1="210" x2="312" y2="370" stroke="#3F8A8C" stroke-width="4" stroke-linecap="round"/>
  <!-- Col 4 -->
  <rect x="365" y="200" width="45" height="180" rx="6" stroke="#2B3A42" stroke-width="10" fill="#FAF9F6"/>
  <line x1="377" y1="210" x2="377" y2="370" stroke="#3F8A8C" stroke-width="4" stroke-linecap="round"/>
  <line x1="397" y1="210" x2="397" y2="370" stroke="#3F8A8C" stroke-width="4" stroke-linecap="round"/>
  <!-- Base 3 Steps -->
  <rect x="60" y="380" width="380" height="25" rx="4" stroke="#2B3A42" stroke-width="12" fill="#FAF9F6"/>
  <rect x="45" y="405" width="410" height="25" rx="4" stroke="#2B3A42" stroke-width="12" fill="#FAF9F6"/>
  <rect x="30" y="430" width="440" height="25" rx="4" stroke="#2B3A42" stroke-width="12" fill="#FAF9F6"/>
</svg>"""

# 3. Bank Transfer / Refinance comparison doodle
refinance_svg = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 700 400" width="700" height="400" fill="none">
  <!-- Bank A (Old) -->
  <g transform="translate(40, 100) scale(0.55)">
    <polygon points="250,70 70,170 430,170" stroke="#E06D53" stroke-width="16" fill="#FDF2EE"/>
    <rect x="60" y="170" width="380" height="30" rx="6" stroke="#E06D53" stroke-width="14" fill="#FDF2EE"/>
    <rect x="90" y="200" width="45" height="160" rx="6" stroke="#E06D53" stroke-width="12" fill="#FDF2EE"/>
    <rect x="180" y="200" width="45" height="160" rx="6" stroke="#E06D53" stroke-width="12" fill="#FDF2EE"/>
    <rect x="270" y="200" width="45" height="160" rx="6" stroke="#E06D53" stroke-width="12" fill="#FDF2EE"/>
    <rect x="360" y="200" width="45" height="160" rx="6" stroke="#E06D53" stroke-width="12" fill="#FDF2EE"/>
    <rect x="40" y="360" width="420" height="30" rx="6" stroke="#E06D53" stroke-width="14" fill="#FDF2EE"/>
  </g>
  <!-- Label Old Bank -->
  <rect x="50" y="330" width="180" height="45" rx="10" fill="#FDF2EE" stroke="#E06D53" stroke-width="4"/>
  <text x="140" y="360" font-family="sans-serif" font-size="22" font-weight="bold" fill="#E06D53" text-anchor="middle">แบงก์เดิม (ดอกสูง)</text>

  <!-- Big Arched Arrow -->
  <path d="M 230 160 C 350 40, 400 40, 480 160" stroke="#3F8A8C" stroke-width="14" stroke-linecap="round" stroke-dasharray="16 12"/>
  <polygon points="495,175 485,140 460,165" fill="#3F8A8C"/>
  <!-- Floating Coin on Arrow -->
  <circle cx="355" cy="85" r="36" fill="#E8A838" stroke="#2B3A42" stroke-width="8"/>
  <text x="355" y="94" font-family="sans-serif" font-size="28" font-weight="bold" fill="#2B3A42" text-anchor="middle">฿</text>

  <!-- Bank B (New) -->
  <g transform="translate(420, 100) scale(0.55)">
    <polygon points="250,70 70,170 430,170" stroke="#3F8A8C" stroke-width="16" fill="#E8F4F5"/>
    <rect x="60" y="170" width="380" height="30" rx="6" stroke="#3F8A8C" stroke-width="14" fill="#E8F4F5"/>
    <rect x="90" y="200" width="45" height="160" rx="6" stroke="#3F8A8C" stroke-width="12" fill="#E8F4F5"/>
    <rect x="180" y="200" width="45" height="160" rx="6" stroke="#3F8A8C" stroke-width="12" fill="#E8F4F5"/>
    <rect x="270" y="200" width="45" height="160" rx="6" stroke="#3F8A8C" stroke-width="12" fill="#E8F4F5"/>
    <rect x="360" y="200" width="45" height="160" rx="6" stroke="#3F8A8C" stroke-width="12" fill="#E8F4F5"/>
    <rect x="40" y="360" width="420" height="30" rx="6" stroke="#3F8A8C" stroke-width="14" fill="#E8F4F5"/>
  </g>
  <!-- Label New Bank -->
  <rect x="440" y="330" width="180" height="45" rx="10" fill="#E8F4F5" stroke="#3F8A8C" stroke-width="4"/>
  <text x="530" y="360" font-family="sans-serif" font-size="22" font-weight="bold" fill="#3F8A8C" text-anchor="middle">แบงก์ใหม่ (โปรถูก)</text>
</svg>"""

# 4. Marker Pen doodle (Angled 45 deg)
marker_svg = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 300 300" width="300" height="300" fill="none">
  <!-- Tilted Marker Pen -->
  <g transform="translate(60, 40) rotate(35, 100, 100)">
    <!-- Shadow -->
    <path d="M 80 200 L 95 240 L 75 245 Z" fill="rgba(0,0,0,0.15)"/>
    <!-- Tip / Chisel Point -->
    <polygon points="85,210 95,235 75,235 70,210" fill="#3F8A8C" stroke="#2B3A42" stroke-width="4"/>
    <polygon points="80,230 95,235 75,235" fill="#205B5C"/>
    <!-- Grip Collar -->
    <rect x="68" y="185" width="28" height="25" rx="4" fill="#3F8A8C" stroke="#2B3A42" stroke-width="5"/>
    <!-- Main Pen Body -->
    <rect x="64" y="40" width="36" height="145" rx="8" fill="#FFFFFF" stroke="#2B3A42" stroke-width="6"/>
    <!-- Grip Accent Lines -->
    <line x1="68" y1="70" x2="96" y2="70" stroke="#3F8A8C" stroke-width="4"/>
    <line x1="68" y1="80" x2="96" y2="80" stroke="#3F8A8C" stroke-width="4"/>
    <!-- Top Cap / End plug -->
    <path d="M66 40 L66 22 C66 18, 72 15, 82 15 C92 15, 98 18, 98 22 L98 40" fill="#3F8A8C" stroke="#2B3A42" stroke-width="5"/>
  </g>
</svg>"""

# 5. Warning Triangle doodle
warning_svg = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 500 500" width="500" height="500" fill="none">
  <!-- Triangle Outer -->
  <path d="M250 50 L460 420 C470 435, 460 450, 440 450 L60 450 C40 450, 30 435, 40 420 Z" stroke="#E06D53" stroke-width="22" stroke-linejoin="round" fill="#FDF2EE"/>
  <!-- Inner dashed border -->
  <path d="M250 110 L415 410 L85 410 Z" stroke="#E06D53" stroke-width="6" stroke-dasharray="14 10" stroke-linejoin="round"/>
  <!-- Exclamation Mark -->
  <line x1="250" y1="180" x2="250" y2="310" stroke="#2B3A42" stroke-width="24" stroke-linecap="round"/>
  <circle cx="250" cy="370" r="14" fill="#2B3A42"/>
</svg>"""

# 6. Checklist Clipboard doodle
checklist_svg = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 500 500" width="500" height="500" fill="none">
  <!-- Board -->
  <rect x="90" y="60" width="320" height="400" rx="20" stroke="#2B3A42" stroke-width="14" fill="#FAF9F6"/>
  <!-- Top Clip -->
  <rect x="180" y="35" width="140" height="50" rx="10" stroke="#2B3A42" stroke-width="12" fill="#E8F4F5"/>
  <circle cx="250" cy="55" r="10" fill="#2B3A42"/>
  
  <!-- Row 1 -->
  <circle cx="150" cy="160" r="22" stroke="#3F8A8C" stroke-width="8" fill="#E8F4F5"/>
  <path d="M140 160 L147 167 L162 152" stroke="#3F8A8C" stroke-width="8" stroke-linecap="round" stroke-linejoin="round"/>
  <line x1="195" y1="160" x2="360" y2="160" stroke="#2B3A42" stroke-width="10" stroke-linecap="round"/>

  <!-- Row 2 -->
  <circle cx="150" cy="240" r="22" stroke="#3F8A8C" stroke-width="8" fill="#E8F4F5"/>
  <path d="M140 240 L147 247 L162 232" stroke="#3F8A8C" stroke-width="8" stroke-linecap="round" stroke-linejoin="round"/>
  <line x1="195" y1="240" x2="340" y2="240" stroke="#2B3A42" stroke-width="10" stroke-linecap="round"/>

  <!-- Row 3 -->
  <circle cx="150" cy="320" r="22" stroke="#3F8A8C" stroke-width="8" fill="#E8F4F5"/>
  <path d="M140 320 L147 327 L162 312" stroke="#3F8A8C" stroke-width="8" stroke-linecap="round" stroke-linejoin="round"/>
  <line x1="195" y1="320" x2="370" y2="320" stroke="#2B3A42" stroke-width="10" stroke-linecap="round"/>

  <!-- Row 4 -->
  <circle cx="150" cy="400" r="22" stroke="#E8A838" stroke-width="8" fill="#FEF8E8"/>
  <circle cx="150" cy="400" r="8" fill="#E8A838"/>
  <line x1="195" y1="400" x2="310" y2="400" stroke="#8CA0AA" stroke-width="10" stroke-linecap="round"/>
</svg>"""

# 7. Money Bag & Coins doodle
money_bag_svg = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 500 500" width="500" height="500" fill="none">
  <!-- Tie string -->
  <path d="M210 130 C230 110, 270 110, 290 130" stroke="#E06D53" stroke-width="10" stroke-linecap="round"/>
  <path d="M200 120 L180 80 C190 70, 220 75, 250 75 C280 75, 310 70, 320 80 L300 120" stroke="#2B3A42" stroke-width="12" fill="#FAF9F6"/>
  <!-- Main Bag Body -->
  <path d="M200 135 C130 160, 90 250, 90 340 C90 420, 160 450, 250 450 C340 450, 410 420, 410 340 C410 250, 370 160, 300 135 Z" stroke="#2B3A42" stroke-width="14" fill="#FAF9F6"/>
  <!-- Baht Symbol -->
  <text x="250" y="320" font-family="sans-serif" font-size="110" font-weight="bold" fill="#3F8A8C" text-anchor="middle" dominant-baseline="middle">฿</text>
  <!-- Coin Stack Next to Bag -->
  <ellipse cx="400" cy="420" rx="50" ry="18" stroke="#2B3A42" stroke-width="8" fill="#E8A838"/>
  <ellipse cx="400" cy="395" rx="50" ry="18" stroke="#2B3A42" stroke-width="8" fill="#E8A838"/>
  <ellipse cx="400" cy="370" rx="50" ry="18" stroke="#2B3A42" stroke-width="8" fill="#E8A838"/>
</svg>"""

# 8. Calculator doodle
calculator_svg = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 500 500" width="500" height="500" fill="none">
  <!-- Body -->
  <rect x="110" y="50" width="280" height="400" rx="30" stroke="#2B3A42" stroke-width="14" fill="#FAF9F6"/>
  <!-- Screen -->
  <rect x="145" y="90" width="210" height="75" rx="12" stroke="#2B3A42" stroke-width="10" fill="#E8F4F5"/>
  <text x="340" y="142" font-family="monospace" font-size="34" font-weight="bold" fill="#3F8A8C" text-anchor="end">1,600,000</text>
  <!-- Keypad Buttons -->
  <!-- Row 1 -->
  <rect x="145" y="195" width="50" height="45" rx="8" stroke="#2B3A42" stroke-width="8" fill="#FDF2EE"/>
  <text x="170" y="227" font-family="sans-serif" font-size="24" font-weight="bold" fill="#E06D53" text-anchor="middle">%</text>
  <rect x="210" y="195" width="50" height="45" rx="8" stroke="#2B3A42" stroke-width="8" fill="#FAF9F6"/>
  <text x="235" y="227" font-family="sans-serif" font-size="24" font-weight="bold" fill="#2B3A42" text-anchor="middle">÷</text>
  <rect x="275" y="195" width="80" height="45" rx="8" stroke="#2B3A42" stroke-width="8" fill="#3F8A8C"/>
  <text x="315" y="227" font-family="sans-serif" font-size="24" font-weight="bold" fill="#FFFFFF" text-anchor="middle">AC</text>

  <!-- Row 2 -->
  <rect x="145" y="255" width="50" height="45" rx="8" stroke="#2B3A42" stroke-width="8" fill="#FAF9F6"/>
  <text x="170" y="287" font-family="sans-serif" font-size="24" font-weight="bold" fill="#2B3A42" text-anchor="middle">7</text>
  <rect x="210" y="255" width="50" height="45" rx="8" stroke="#2B3A42" stroke-width="8" fill="#FAF9F6"/>
  <text x="235" y="287" font-family="sans-serif" font-size="24" font-weight="bold" fill="#2B3A42" text-anchor="middle">8</text>
  <rect x="275" y="255" width="50" height="45" rx="8" stroke="#2B3A42" stroke-width="8" fill="#FAF9F6"/>
  <text x="300" y="287" font-family="sans-serif" font-size="24" font-weight="bold" fill="#2B3A42" text-anchor="middle">9</text>

  <!-- Row 3 -->
  <rect x="145" y="315" width="50" height="45" rx="8" stroke="#2B3A42" stroke-width="8" fill="#FAF9F6"/>
  <text x="170" y="347" font-family="sans-serif" font-size="24" font-weight="bold" fill="#2B3A42" text-anchor="middle">4</text>
  <rect x="210" y="315" width="50" height="45" rx="8" stroke="#2B3A42" stroke-width="8" fill="#FAF9F6"/>
  <text x="235" y="347" font-family="sans-serif" font-size="24" font-weight="bold" fill="#2B3A42" text-anchor="middle">5</text>
  <rect x="275" y="315" width="50" height="45" rx="8" stroke="#2B3A42" stroke-width="8" fill="#FAF9F6"/>
  <text x="300" y="347" font-family="sans-serif" font-size="24" font-weight="bold" fill="#2B3A42" text-anchor="middle">6</text>

  <!-- Row 4 -->
  <rect x="145" y="375" width="50" height="45" rx="8" stroke="#2B3A42" stroke-width="8" fill="#FAF9F6"/>
  <text x="170" y="407" font-family="sans-serif" font-size="24" font-weight="bold" fill="#2B3A42" text-anchor="middle">1</text>
  <rect x="210" y="375" width="50" height="45" rx="8" stroke="#2B3A42" stroke-width="8" fill="#FAF9F6"/>
  <text x="235" y="407" font-family="sans-serif" font-size="24" font-weight="bold" fill="#2B3A42" text-anchor="middle">2</text>
  <rect x="275" y="375" width="80" height="45" rx="8" stroke="#2B3A42" stroke-width="8" fill="#E8A838"/>
  <text x="315" y="407" font-family="sans-serif" font-size="28" font-weight="bold" fill="#2B3A42" text-anchor="middle">=</text>
</svg>"""

files = {
    "house.svg": house_svg,
    "bank.svg": bank_svg,
    "refinance.svg": refinance_svg,
    "marker_pen.svg": marker_svg,
    "warning.svg": warning_svg,
    "checklist.svg": checklist_svg,
    "money_bag.svg": money_bag_svg,
    "calculator.svg": calculator_svg,
}

for name, content in files.items():
    (DOODLES_DIR / name).write_text(content.strip(), encoding="utf-8")
    print(f"Generated: {DOODLES_DIR / name}")
