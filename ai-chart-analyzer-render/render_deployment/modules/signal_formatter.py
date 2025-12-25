"""
ماژول فرمت‌بندی و ارسال سیگنال‌های معاملاتی
شامل قالب‌های مختلف پیام و دکمه‌های تعاملی
"""

from typing import Dict, Any, List
from datetime import datetime
from config import SIGNAL_EMOJIS


class SignalFormatter:
    """کلاس فرمت‌بندی سیگنال‌های معاملاتی"""
    
    @staticmethod
    def format_signal(data: Dict[str, Any]) -> str:
        """
        فرمت‌بندی سیگنال اسکالپ به صورت پیام کوتاه و سریع برای تلگرام (با قابلیت اهرم)
        
        Args:
            data: دیکشنری اطلاعات تحلیل با ساختار جدید اسکالپینگ
            
        Returns:
            رشته پیام فرمت‌شده
        """
        bias = data.get('bias', 'نامشخص')
        setup = data.get('setup', 'تشخیص داده نشد')
        entry = data.get('entry', '0')
        sl = data.get('sl', '0')
        tp = data.get('tp', '0')
        confidence = data.get('confidence', '0')
        
        # انتخاب ایموجی و جهت بر اساس bias
        bias_lower = bias.lower().strip()
        
        if bias_lower == 'short':
            direction_emoji = '📉'
            direction_text = 'SHORT'
            direction_full = 'فروش'
            color_emoji = '🔴'
        elif bias_lower == 'long':
            direction_emoji = '📈'
            direction_text = 'LONG'
            direction_full = 'خرید'
            color_emoji = '🟢'
        else:
            direction_emoji = '⚖️'
            direction_text = 'RANGE'
            direction_full = 'خنثی'
            color_emoji = '🟡'
        
        # فرمت قیمت‌ها - نمایش دقیق بدون گرد کردن
        def format_price(price: str) -> str:
            try:
                # تبدیل به رشته بدون تغییر
                price_str = str(price).strip()
                # اگر عدد است، فقط تضمین می‌کنیم که رشته باقی بماند
                if price_str.replace('.', '').replace('-', '').isdigit():
                    return price_str
                return price_str
            except (ValueError, TypeError):
                return str(price)
        
        entry_fmt = format_price(entry)
        sl_fmt = format_price(sl)
        tp_fmt = format_price(tp)
        key_level = data.get('key_level', 'نامشخص')
        reasoning = data.get('reasoning', '')
        
        # اطلاعات اهرم
        leverage_recommendation = data.get('leverage_recommendation')
        leverage_reasoning = data.get('leverage_reasoning', '')
        risk_warning = data.get('risk_warning', '')
        
        # محاسبه RR
        try:
            entry_val = float(entry)
            sl_val = float(sl)
            tp_val = float(tp)
            
            if bias_lower == 'long':
                risk = entry_val - sl_val
                reward = tp_val - entry_val
            elif bias_lower == 'short':
                risk = sl_val - entry_val
                reward = entry_val - tp_val
            else:
                risk = 0
                reward = 0
            
            if risk > 0:
                rr = round(reward / risk, 2)
                rr_text = f"⚡ RR 1:{rr}"
            else:
                rr_text = "⚡ RR -"
        except:
            rr_text = "⚡ RR -"
        
        # ساخت بخش اهرم
        leverage_section = ""
        if leverage_recommendation:
            leverage_section = f"""
🎚️ **اهرم پیشنهادی:** `{leverage_recommendation}x`
💡 **دلیل اهرم:**
{leverage_reasoning}

━━━━━━━━━━━━━━━━━━━
"""
            if risk_warning:
                leverage_section += f"⚠️ {risk_warning}\n\n"
        
        # ساخت پیام حرفه‌ای با جزئیات کامل و اهرم
        message = f"""{direction_emoji} **{direction_text}** | {confidence}%
{color_emoji} {setup}

🎯 **ورود:** `{entry_fmt}`
❌ **حد ضرر:** `{sl_fmt}`
💰 **هدف:** `{tp_fmt}`

━━━━━━━━━━━━━━━━━━━
📍 **سطح کلیدی:**
`{key_level}`
━━━━━━━━━━━━━━━━━━━
💡 **دلیل تحلیل:**
{reasoning}
━━━━━━━━━━━━━━━━━━━
{rr_text} | اسکالپ ۱-۵ دقیقه
━━━━━━━━━━━━━━━━━━━
{leverage_section}⚠️ *مدیریت ریسک فراموش نشه!*
        """.strip()
        
        return message
    
    @staticmethod
    def create_keyboard(signal_id: str = None) -> dict:
        """
        ایجاد کیبورد شیشه‌ای برای تعامل (با قابلیت اهرم)
        
        Args:
            signal_id: شناسه منحصر به فرد سیگنال
            
        Returns:
            دیکشنری کیبورد تلگرام
        """
        from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(text="🔄 تحلیل مجدد", callback_data="retry_analysis"),
                InlineKeyboardButton(text="📊 آمار", callback_data="show_stats")
            ],
            [
                InlineKeyboardButton(text="🎚️ محاسبه اهرم", callback_data="calculate_leverage"),
                InlineKeyboardButton(text="💾 ذخیره", callback_data="save_signal")
            ],
            [
                InlineKeyboardButton(text="🔗 اشتراک‌گذاری", callback_data="share_signal"),
                InlineKeyboardButton(text="⚠️ مدیریت ریسک", callback_data="risk_management")
            ]
        ])
        
        return keyboard
    
    @staticmethod
    def format_error_message(error_text: str) -> str:
        """
        فرمت‌بندی پیام خطا
        
        Args:
            error_text: متن خطا
            
        Returns:
            پیام خطای فرمت‌شده
        """
        return f"""
{SIGNAL_EMOJIS['error']} **خطا در پردازش**

متأسفانه در تحلیل چارت خطایی رخ داد:

`{error_text}`

لطفاً موارد زیر را بررسی کنید:
• تصویر واضح و با کیفیت باشد
• چارت قیمت در تصویر مشخص باشد
• مجدداً تلاش کنید

@{'AI_Chart_Bot'}
        """.strip()
    
    @staticmethod
    def format_analyzing_message() -> str:
        """
        فرمت‌بندی پیام در حال تحلیل
        
        Returns:
            پیام وضعیت تحلیل
        """
        return f"""
{SIGNAL_EMOJIS['analyzing']} **در حال تحلیل چارت...**

لطفاً صبر کنید تا چارت شما توسط هوش مصنوعی بررسی شود.

⏱️ معمولاً این فرآیند 10-20 ثانیه طول می‌کشد...
        """.strip()
    
    @staticmethod
    def format_welcome_message() -> str:
        """
        فرمت‌بندی پیام خوشامدگویی
        
        Returns:
            پیام خوشامدگویی
        """
        return f"""
👋 **سلام دوست عزیز!**

به ربات *تحلیل گر هوشمند چارت* خوش آمدید! 🎉

با ارسال عکس چارت قیمت، تحلیل حرفه‌ای دریافت کنید:

✅ تشخیص خودکار نماد و تایم‌فریم
✅ شناسایی روند و الگوهای قیمتی
✅ تعیین نقاط ورود، حد ضرر و حد سود
✅ محاسبه نسبت ریسک به ریوارد

📸 **همین حالا عکس چارت خود را ارسال کنید!**

⚠️ *توجه: این ربات فقط جنبه کمکی دارد و تصمیم نهایی با شماست.*
        """.strip()
    
    @staticmethod
    def format_help_message() -> str:
        """
        فرمت‌بندی راهنمای استفاده
        
        Returns:
            پیام راهنما
        """
        return f"""
📖 **راهنمای استفاده**

**ارسال چارت:**
عکس چارت قیمت را از صرافی یا پلتفرم معاملاتی بگیرید و ارسال کنید.

**نکات مهم:**
• تصویر باید واضح باشد
• محورهای قیمت و زمان مشخص باشند
• بهتر است کندل‌ها واضح باشند

**خروجی تحلیل:**
• نماد معاملاتی
• جهت روند (صعودی/نزولی)
• نقاط ورود و خروج
• حد ضرر و حد سود
• توضیح تحلیل

برای شروع، عکس چارت ارسال کنید! 📸
        """.strip()
