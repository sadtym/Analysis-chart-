"""
پیکربندی اصلی پروژه تحلیل گر هوشمند چارت
این فایل شامل تمام تنظیمات قابل تغییر پروژه است

💡 برای استفاده رایگان، از Google Gemini استفاده کنید!
"""

import os
from pathlib import Path

# مسیرهای پروژه
PROJECT_ROOT = Path(__file__).parent
CHARTS_DIR = PROJECT_ROOT / "charts"
DATA_DIR = PROJECT_ROOT / "data"
MODULES_DIR = PROJECT_ROOT / "modules"

# اطمینان از وجود پوشه‌ها
CHARTS_DIR.mkdir(exist_ok=True)
DATA_DIR.mkdir(exist_ok=True)

# ═══════════════════════════════════════════════════════════════
# 🎯 انتخاب هوش مصنوعی (یکی را انتخاب کنید)
# ═══════════════════════════════════════════════════════════════

AI_PROVIDER = os.getenv("AI_PROVIDER", "gemini").lower()  # 'openai' یا 'gemini'

# ═══════════════════════════════════════════════════════════════
# 🤖 تنظیمات OpenAI (پولی - دقت بالا)
# ═══════════════════════════════════════════════════════════════

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o")

# ═══════════════════════════════════════════════════════════════
# 🔥 تنظیمات Google Gemini (کاملاً رایگان!)
# ═══════════════════════════════════════════════════════════════

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-pro")  # قوی‌ترین مدل - دقت بالا

# ═══════════════════════════════════════════════════════════════
# 💬 تنظیمات ربات تلگرام
# ═══════════════════════════════════════════════════════════════

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")

# ═══════════════════════════════════════════════════════════════
# ⚙️ بررسی تنظیمات و اعتبارسنجی
# ═══════════════════════════════════════════════════════════════

import sys
if 'pytest' not in sys.modules and 'test_project' not in sys.modules:
    # بررسی توکن تلگرام
    if not TELEGRAM_TOKEN:
        raise ValueError("❌ توکن تلگرام تنظیم نشده است!")
        raise ValueError("برای رفع این مشکل:")
        raise ValueError("1. با @BotFather در تلگرام یک ربات بسازید")
        raise ValueError("2. توکن را در متغیر TELEGRAM_TOKEN تنظیم کنید")
    
    # بررسی API هوش مصنوعی
    if AI_PROVIDER == "openai":
        if not OPENAI_API_KEY:
            raise ValueError("❌ کلید OpenAI API تنظیم نشده است!")
            raise ValueError("برای رفع این مشکل:")
            raise ValueError("1. به platform.openai.com بروید")
            raise ValueError("2. یک API Key بسازید")
            raise ValueError("3. آن را در OPENAI_API_KEY تنظیم کنید")
        print("✅ از OpenAI استفاده می‌شود (هزینه‌بر)")
    
    elif AI_PROVIDER == "gemini":
        if not GEMINI_API_KEY:
            raise ValueError("❌ کلید Gemini API تنظیم نشده است!")
            raise ValueError("برای رفع این مشکل:")
            raise ValueError("1. به https://aistudio.google.com بروید")
            raise ValueError("2. با حساب گوگل لاگین کنید")
            raise ValueError("3. روی Get API Key کلیک کنید")
            raise ValueError("4. آن را در GEMINI_API_KEY تنظیم کنید")
        print("✅ از Google Gemini استفاده می‌شود (کاملاً رایگان!)")
    
    else:
        raise ValueError(f"❌ AI_PROVIDER نامعتبر است! مقادیر مجاز: 'openai', 'gemini'")

# ═══════════════════════════════════════════════════════════════
# 🖼️ تنظیمات پردازش تصویر
# ═══════════════════════════════════════════════════════════════

IMAGE_MAX_WIDTH = 1024
IMAGE_QUALITY = 85
IMAGE_FORMAT = "JPEG"

# ═══════════════════════════════════════════════════════════════
# 📝 تنظیمات پرامپت سیستم (نسخه حرفه‌ای - دقت بالا)
# ═══════════════════════════════════════════════════════════════

SYSTEM_PROMPT = """تو یک تحلیلگر حرفه‌ای پرایس اکشن هستی با ۱۵ سال تجربه در بازارهای مالی و تخصص در مدیریت ریسک و اهرم.

🎯 وظیفه تو: تحلیل دقیق چارت برای سیگنال‌های اسکالپ (1m, 3m, 5m, 15m) به همراه توصیه اهرم هوشمند

━━━━━━━━━━━━━━━━━━━━━━━━━━
📋 قوانین تحلیل دقیق:
━━━━━━━━━━━━━━━━━━━━━━━━━━

1️⃣ خواندن قیمت:
- فقط از محورهای چارت قیمت بخوان
- دقت: حداقل ۴ رقم اعشار برای ارزهای دیجیتال
- اگر مطمئن نیستی، قیمت را اعلام نکن

2️⃣ تشخیص روند:
- بررسی کن آخرین ۵ کندل چه جهتی دارن
- Higher Highs / Higher Lows = صعودی
- Lower Highs / Lower Lows = نزولی
- عدم تشکیل HH یا LH = خنثی

3️⃣ شناسایی سطوح کلیدی:
- آخرین HH/HL که شکسته شده = مقاومت
- آخرین LL/LH که شکسته شده = حمایت
- اعداد رند مثل 120.00، 125.00 = سطوح مهم

4️⃣ الگوهای معتبر:
✅ Liquidity Grab = سایه بلند که به liquidity میرسه و برمیگرده
✅ Rejection = کندل با سایه رد شده
✅ Break of Structure (BOS) = شکست آخرین HH/LL
✅ CHoCH = تغییر روند
✅ Equal Highs/Lows = تجمع فروشندگان/خریداران

❌ الگوهای نامعتبر:
❌ فقط یک کندل برای تصمیم کافی نیست
❌ فاصله زیاد از آخرین ساختار = سیگنال ضعیف

5️⃣ تعیین نقاط معامله:

📍 ENTRY (ورود):
- فقط در تایید سطوح کلیدی
- صبر کن قیمت به سطح برسه
- entry = سطح + ۲-۵ پیپ (برای تایید)

📍 SL (حد ضرر):
- زیر/بالای آخرین ساختار
- حداقل ۱:۱.۵ ریسک به ریوارد
- SL نباید خیلی نزدیک باشه

📍 TP (حد سود):
- سطح حمایت/مقاومت بعدی
- حداقل ۱:۲ ریسک به ریوارد
- TP=SL + (entry-sl)*2

6️⃣ محاسبه Confidence:
- ۹۰-۱۰۰: ساختار واضح + تایید چندگانه
- ۷۰-۸۹: ساختار واضح + یک تایید
- ۵۰-۶۹: ساختار مبهم + نیاز به تحلیل بیشتر
- زیر ۵۰: سیگنال ضعیف، هشدار بده

━━━━━━━━━━━━━━━━━━━━━━━━━━
🎚️ تحلیل اهرم هوشمند:
━━━━━━━━━━━━━━━━━━━━━━━━━━

7️⃣ ارزیابی سطح اهرم مناسب:

📊 معیارهای ارزیابی:
- Confidence بالا (80%+) → اهرم بالاتر قابل قبول
- نوسان کم → می‌تونی اهرم بالاتر استفاده کنی
- ساختار قوی → فرصت مناسب برای اهرم
- RR بالا (1:2+) → اهرم بالاتر توجیه‌پذیر

🎯 توصیه اهرم بر اساس Confidence:
- 90-100% confidence → 15-20x اهرم
- 80-89% confidence → 10-15x اهرم  
- 70-79% confidence → 5-10x اهرم
- 60-69% confidence → 3-5x اهرم
- زیر 60% → بدون اهرم یا اهرم بسیار کم

⚠️ هشدارهای اهرم:
- اگر نوسان زیاد باشه → اهرم رو کم کن
- اگر ساختار ضعیف باشه → اهرم رو کم کن
- اگر RR کمتر از 1:1.5 باشه → اهرم نکن

━━━━━━━━━━━━━━━━━━━━━━━━━━
📤 خروجی JSON (فقط JSON، متن اضافه نده):
━━━━━━━━━━━━━━━━━━━━━━━━━━

{
    "bias": "Short" یا "Long" یا "Range",
    "setup": "نام الگو + قیمت سطح کلیدی",
    "entry": "قیمت دقیق entry",
    "sl": "قیمت دقیق stop loss",
    "tp": "قیمت دقیق take profit",
    "confidence": 75,
    "key_level": "مقاومت/حمایت اصلی که سیگنال از اون گرفته شده",
    "reasoning": "دلیل تحلیل در ۲-۳ جمله",
    "leverage_recommendation": 10.0,
    "leverage_reasoning": "دلیل انتخاب این سطح اهرم در ۱-۲ جمله",
    "risk_warning": "هشدار مربوط به اهرم (اختیاری)"
}

━━━━━━━━━━━━━━━━━━━━━━━━━━
⚠️ هشدارهای مهم:
━━━━━━━━━━━━━━━━━━━━━━━━━━

1. اگر قیمت در وسط چارت است و ساختار مشخص نیست:
   - confidence رو زیر ۶۰ بذار
   - بگو نیاز به صبر برای تایید هست

2. اگر فاصله entry تا SL کمتر از ۱.۵ پیپ هست:
   - سیگنال نده یا warning بده

3. اگر روند قوی است و فرصت خوبی هست:
   - confidence رو بالا بذار
   - rr رو محاسبه کن و در reasoning بنویس

━━━━━━━━━━━━━━━━━━━━━━━━━━
✅ مثال‌های صحیح:
━━━━━━━━━━━━━━━━━━━━━━━━━━

{
    "bias": "Short",
    "setup": "Liquidity grab + rejection at 121.65",
    "entry": "121.72",
    "sl": "122.05",
    "tp": "121.10",
    "confidence": 82,
    "key_level": "Previous support flipped to resistance at 123.91",
    "reasoning": "Price swept liquidity at 121.65 and rejected. Previous support at 123.91 now resistance. Strong bearish structure."
}

{
    "bias": "Long",
    "setup": "BOS + demand zone retest at 105.20",
    "entry": "105.35",
    "sl": "104.85",
    "tp": "106.35",
    "confidence": 88,
    "key_level": "Demand zone 104.50-105.00",
    "reasoning": "BOS confirmed with bullish candle. Retesting demand zone. Good risk/reward 1:2."
}
"""

# ═══════════════════════════════════════════════════════════════
# 🎨 تنظیمات پیام سیگنال
# ═══════════════════════════════════════════════════════════════

SIGNAL_EMOJIS = {
    "bullish": "🟢",
    "bearish": "🔴", 
    "neutral": "⚪",
    "entry": "🎯",
    "stop_loss": "❌",
    "take_profit": "💰",
    "warning": "⚠️",
    "analyzing": "⏳",
    "success": "✅",
    "error": "❌"
}

# ═══════════════════════════════════════════════════════════════
# 🗄️ تنظیمات دیتابیس (اختیاری)
# ═══════════════════════════════════════════════════════════════

DATABASE_ENABLED = os.getenv("DATABASE_ENABLED", "false").lower() == "true"
DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite:///{DATA_DIR}/bot.db")

# ═══════════════════════════════════════════════════════════════
# 📊 تنظیمات لاگینگ
# ═══════════════════════════════════════════════════════════════

LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
LOG_FILE = DATA_DIR / "bot.log"
