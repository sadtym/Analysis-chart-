"""
ماژول تحلیل هوشمند چارت با استفاده از هوش مصنوعی
پشتیبانی از OpenAI و Google Gemini

💡 برای استفاده رایگان، GEMINI_API_KEY را تنظیم کنید
"""

import json
import logging
import base64
from typing import Dict, Any, Optional
from pathlib import Path

# تنظیم لاگینگ
logger = logging.getLogger(__name__)

# ═══════════════════════════════════════════════════════════════
# 📦 وارد کردن تنظیمات
# ═══════════════════════════════════════════════════════════════

try:
    from config import (
        AI_PROVIDER,
        OPENAI_API_KEY, OPENAI_MODEL,
        GEMINI_API_KEY, GEMINI_MODEL,
        SYSTEM_PROMPT
    )
except ImportError:
    # حالت تست - مقادیر پیش‌فرض
    AI_PROVIDER = "gemini"
    OPENAI_API_KEY = None
    OPENAI_MODEL = "gpt-4o"
    GEMINI_API_KEY = None
    GEMINI_MODEL = "gemini-1.5-flash"
    SYSTEM_PROMPT = ""


# ═══════════════════════════════════════════════════════════════
# 🧠 کلاس تحلیلگر چارت
# ═══════════════════════════════════════════════════════════════

class ChartAnalyzer:
    """کلاس اصلی تحلیل چارت با هوش مصنوعی"""
    
    def __init__(self):
        """راه‌اندازی تحلیلگر بر اساس تنظیمات"""
        self.provider = AI_PROVIDER
        self.client = None
        self.model = None
        
        if self.provider == "openai":
            self._init_openai()
        elif self.provider == "gemini":
            self._init_gemini()
        else:
            raise ValueError(f"❌ AI_PROVIDER نامعتبر: {self.provider}")
    
    def _init_openai(self):
        """راه‌اندازی OpenAI"""
        try:
            from openai import OpenAI
            self.client = OpenAI(api_key=OPENAI_API_KEY)
            self.model = OPENAI_MODEL
            logger.info(f"✅ تحلیلگر OpenAI راه‌اندازی شد: {self.model}")
        except ImportError:
            logger.error("❌ کتابخانه openai نصب نیست! اجرای: pip install openai")
            raise
    
    def _init_gemini(self):
        """راه‌اندازی Google Gemini"""
        try:
            import google.generativeai as genai
            self.client = genai
            self.client.configure(api_key=GEMINI_API_KEY)
            self.model = GEMINI_MODEL
            logger.info(f"✅ تحلیلگر Gemini راه‌اندازی شد: {self.model}")
        except ImportError:
            logger.error("❌ کتابخانه google-generativeai نصب نیست!")
            logger.error("اجرای: pip install google-generativeai")
            raise
    
    def analyze(self, base64_image: str) -> Dict[str, Any]:
        """
        ارسال تصویر به هوش مصنوعی و دریافت تحلیل
        
        Args:
            base64_image: تصویر به صورت base64
            
        Returns:
            دیکشنری حاوی نتیجه تحلیل
        """
        try:
            logger.info(f"🚀 شروع تحلیل با {self.provider.upper()}...")
            
            if self.provider == "openai":
                return self._analyze_with_openai(base64_image)
            elif self.provider == "gemini":
                return self._analyze_with_gemini(base64_image)
                
        except Exception as e:
            logger.error(f"❌ خطا در تحلیل: {e}")
            return self._create_default_result(f"خطای سیستمی: {str(e)}")
    
    def _analyze_with_openai(self, base64_image: str) -> Dict[str, Any]:
        """تحلیل با OpenAI GPT-4o"""
        from openai import OpenAI
        
        client = OpenAI(api_key=OPENAI_API_KEY)
        
        response = client.chat.completions.create(
            model=self.model,
            messages=[
                {
                    "role": "system",
                    "content": SYSTEM_PROMPT
                },
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": "این تصویر چارت را با دقت بسیار بالا تحلیل کن و اطلاعات زیر را استخراج نمایید:\n"
                                    "- نماد معاملاتی\n"
                                    "- تایم‌فریم\n"
                                    "- روند قیمت\n"
                                    "- نقاط ورود، حد ضرر و حد سود\n"
                                    "- توضیح تحلیل"
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{base64_image}"
                            }
                        }
                    ]
                }
            ],
            max_tokens=1000,
            temperature=0.2,
            response_format={"type": "json_object"}
        )
        
        content = response.choices[0].message.content
        logger.info("✅ پاسخ OpenAI دریافت شد")
        
        result = json.loads(content)
        
        if self._validate_result(result):
            return result
        else:
            return self._create_default_result("نتیجه تحلیل نامعتبر است")
    
    def _analyze_with_gemini(self, base64_image: str) -> Dict[str, Any]:
        """تحلیل با Google Gemini (رایگان!)"""
        import google.generativeai as genai
        
        # تبدیل base64 به تصویر
        image_data = base64.b64decode(base64_image)
        
        # ایجاد مدل
        model = genai.GenerativeModel(
            model_name=self.model,
            system_instruction=SYSTEM_PROMPT
        )
        
        # ارسال درخواست - فرمت جدید اسکالپ
        response = model.generate_content([
            {"inline_data": {"mime_type": "image/jpeg", "data": image_data}}
        ])
        
        # استخراج متن از پاسخ
        content = response.text
        logger.info("✅ پاسخ Gemini دریافت شد")
        
        # حذف علامت‌های markdown اگر وجود داشته باشد
        content = content.strip()
        if content.startswith("```json"):
            content = content[7:]
        if content.startswith("```"):
            content = content[3:]
        if content.endswith("```"):
            content = content[:-3]
        content = content.strip()
        
        result = json.loads(content)
        
        if self._validate_result(result):
            return result
        else:
            return self._create_default_result("نتیجه تحلیل نامعتبر است")
    
    def _validate_result(self, result: Dict[str, Any]) -> bool:
        """اعتبارسنجی نتیجه تحلیل اسکالپ حرفه‌ای با قابلیت اهرم"""
        # فیلدهای مورد نیاز برای فرمت اسکالپ
        required_fields = ['bias', 'setup', 'entry', 'sl', 'tp', 'confidence', 'key_level', 'reasoning']
        
        for field in required_fields:
            if field not in result:
                logger.warning(f"❌ فیلد {field} در نتیجه وجود ندارد")
                return False
        
        # بررسی منطقی بودن مقادیر
        try:
            entry = float(str(result['entry']).replace(',', ''))
            sl = float(str(result['sl']).replace(',', ''))
            tp = float(str(result['tp']).replace(',', ''))
            confidence = int(str(result['confidence']).replace('%', ''))
            
            if entry <= 0 or sl <= 0 or tp <= 0:
                logger.warning("❌ مقادیر قیمت نامعتبر هستند")
                return False
            
            if not (0 <= confidence <= 100):
                logger.warning("❌ درصد اعتماد باید بین 0 تا 100 باشد")
                return False
            
            # اعتبارسنجی اهرم (اختیاری اما اگر وجود داشته باشد باید معتبر باشد)
            if 'leverage_recommendation' in result:
                try:
                    leverage = float(str(result['leverage_recommendation']))
                    if leverage < 1.0 or leverage > 100.0:
                        logger.warning(f"⚠️ اهرم {leverage} خارج از محدوده مجاز (1-100x)")
                        # اهرم نامعتبر را حذف کن اما نتیجه را رد نکن
                        result.pop('leverage_recommendation', None)
                except (ValueError, TypeError):
                    logger.warning("⚠️ مقدار اهرم نامعتبر")
                    result.pop('leverage_recommendation', None)
            
            # بررسی حداقل RR
            try:
                bias = str(result['bias']).lower()
                if bias == 'long':
                    risk = entry - sl
                    reward = tp - entry
                elif bias == 'short':
                    risk = sl - entry
                    reward = entry - tp
                else:
                    risk = 1
                    reward = 0
                
                if risk > 0:
                    rr = reward / risk
                    if rr < 1.0:
                        logger.warning(f"⚠️ RR ({rr:.2f}) کمتر از ۱ است - سیگنال ضعیف")
                        # فقط warning بده، رد نکن
            except:
                pass
                
        except (ValueError, TypeError) as e:
            logger.warning(f"❌ خطا در اعتبارسنجی اعداد: {e}")
            return False
        
        return True
    
    def _create_default_result(self, error_message: str) -> Dict[str, Any]:
        """ایجاد نتیجه پیش‌فرض در صورت خطا - فرمت اسکالپ حرفه‌ای"""
        return {
            "bias": "Range",
            "setup": f"خطا در تحلیل: {error_message}",
            "entry": "0",
            "sl": "0",
            "tp": "0",
            "confidence": "0",
            "key_level": "نامشخص",
            "reasoning": "تحلیل با خطا مواجه شد",
            "error": True
        }
    
    def get_token_usage(self) -> Dict[str, int]:
        """دریافت آمار مصرف توکن"""
        return {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}


# ═══════════════════════════════════════════════════════════════
# 🧪 تست ماژول
# ═══════════════════════════════════════════════════════════════

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    print("=" * 60)
    print("🤖 تست ماژول تحلیل چارت")
    print("=" * 60)
    
    # بررسی تنظیمات
    print(f"\n📋 تنظیمات فعلی:")
    print(f"   AI Provider: {AI_PROVIDER}")
    print(f"   OpenAI Key: {'✅ تنظیم شده' if OPENAI_API_KEY else '❌ تنظیم نشده'}")
    print(f"   Gemini Key: {'✅ تنظیم شده' if GEMINI_API_KEY else '❌ تنظیم نشده'}")
    
    try:
        analyzer = ChartAnalyzer()
        print("\n✅ تحلیلگر با موفقیت راه‌اندازی شد!")
        print(f"   Provider: {analyzer.provider}")
        print(f"   Model: {analyzer.model}")
        
        # تست ساختار پیش‌فرض
        result = analyzer._create_default_result("تست خطا")
        print(f"\n📊 ساختار نتیجه:")
        print(json.dumps(result, indent=2, ensure_ascii=False))
        
    except ValueError as e:
        print(f"\n❌ خطا: {e}")
        print("\n💡 برای استفاده رایگان:")
        print("   1. به https://aistudio.google.com بروید")
        print("   2. API Key بسازید")
        print("   3. GEMINI_API_KEY را تنظیم کنید")
