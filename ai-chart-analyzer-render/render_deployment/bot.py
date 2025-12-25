"""
ربات تلگرام تحلیل هوشمند چارت
پیاده‌سازی کامل با استفاده از aiogram و OpenAI

Author: MiniMax Agent
"""

import os
import sys
import asyncio
import logging
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv

# بارگذاری تنظیمات از فایل .env
load_dotenv(Path(__file__).parent / ".env")

# اضافه کردن مسیر ماژول‌ها به path
MODULES_DIR = Path(__file__).parent / "modules"
sys.path.insert(0, str(MODULES_DIR))

from aiogram import Bot, Dispatcher, F, types
from aiogram.filters import Command, CommandStart
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties
from aiogram.methods.send_message import SendMessage

from config import TELEGRAM_TOKEN, LOG_LEVEL, LOG_FILE
from modules.image_processor import preprocess_image, validate_image, get_unique_filename, cleanup_old_images
from modules.ai_analyzer import ChartAnalyzer
from modules.signal_formatter import SignalFormatter
from modules.chart_annotator import annotate_chart_with_analysis
from modules.leverage_calculator import LeverageCalculator, RiskLevel, VolatilityLevel

# تنظیم لاگینگ
logging.basicConfig(
    level=getattr(logging, LOG_LEVEL.upper()),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE, encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# راه‌اندازی ربات و دپاچر
bot = Bot(
    token=TELEGRAM_TOKEN,
    default=DefaultBotProperties(parse_mode=ParseMode.MARKDOWN)
)
dp = Dispatcher()

# راه‌اندازی ماژول‌ها
analyzer = ChartAnalyzer()
formatter = SignalFormatter()
leverage_calculator = LeverageCalculator()


# ==================== هندلرهای دستورات ====================

@dp.message(CommandStart())
async def cmd_start(message: Message):
    """پاسخ به دستور /start"""
    try:
        user_name = message.from_user.full_name
        logger.info(f"کاربر جدید: {user_name} (ID: {message.from_user.id})")
        
        welcome_text = formatter.format_welcome_message()
        
        # ایجاد کیبورد شروع
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(text="📊 شروع تحلیل", callback_data="start_analysis"),
                InlineKeyboardButton(text="📖 راهنما", callback_data="show_help")
            ]
        ])
        
        await message.answer(welcome_text, reply_markup=keyboard)
        
    except Exception as e:
        logger.error(f"خطا در cmd_start: {e}")
        await message.answer("خطایی رخ داد. لطفاً مجدداً تلاش کنید.")


@dp.message(Command("help"))
async def cmd_help(message: Message):
    """پاسخ به دستور /help"""
    help_text = formatter.format_help_message()
    await message.answer(help_text)


@dp.message(Command("stats"))
async def cmd_stats(message: Message):
    """پاسخ به دستور /stats - نمایش آمار (برای توسعه آینده)"""
    await message.answer("📊 این قابلیت به زودی اضافه می‌شود!")


@dp.message(Command("cleanup"))
async def cmd_cleanup(message: Message):
    """پاکسازی تصاویر قدیمی - فقط برای مدیر"""
    # بررسی اینکه کاربر مدیر است (در صورت نیاز)
    cleanup_old_images(max_age_hours=0)  # حذف همه تصاویر
    await message.answer("✅ تصاویر موقت پاکسازی شدند")


@dp.message(Command("leverage"))
async def cmd_leverage(message: Message):
    """دستور محاسبه اهرم"""
    leverage_help = """
🎚️ **دستور محاسبه اهرم**

📝 **نحوه استفاده:**
`/leverage [مبلغ] [ورود] [ضرر] [ریسک%] [اهرم]`

📊 **مثال:**
`/leverage 1000 1.0850 1.0820 2 10`

💡 **توضیح پارامترها:**
• مبلغ: موجودی حساب ($)
• ورود: قیمت ورود
• ضرر: قیمت حد ضرر
• ریسک%: درصد ریسک (1-5)
• اهرم: سطح اهرم (اختیاری، پیش‌فرض: 1x)

🔔 **یا عکس چارت ارسال کنید تا AI اهرم مناسب را پیشنهاد دهد!**
    """
    await message.answer(leverage_help)


# ==================== هندلر تصاویر ====================

@dp.message(F.photo)
async def handle_chart(message: Message):
    """پردازش تصویر چارت ارسالی"""
    user_id = message.from_user.id
    user_name = message.from_user.full_name
    
    logger.info(f"دریافت تصویر از کاربر {user_name} (ID: {user_id})")
    
    try:
        # 1. دریافت تصویر با بالاترین کیفیت
        photo = message.photo[-1]
        
        # 2. ذخیره موقت تصویر
        file_path = get_unique_filename(user_id)
        await bot.download(photo, destination=file_path)
        
        logger.info(f"تصویر ذخیره شد: {file_path}")
        
        # 3. اعتبارسنجی تصویر
        is_valid, validation_msg = validate_image(str(file_path))
        if not is_valid:
            logger.warning(f"اعتبارسنجی ناموفق: {validation_msg}")
            await message.answer(formatter.format_error_message(validation_msg))
            if os.path.exists(file_path):
                os.remove(file_path)
            return
        
        # 4. ارسال پیام "در حال تحلیل"
        analyzing_msg = await message.answer(formatter.format_analyzing_message())
        
        # 5. پیش‌پردازش تصویر
        base64_image = preprocess_image(str(file_path))
        
        # 6. تحلیل با هوش مصنوعی
        analysis_result = analyzer.analyze(base64_image)
        
        # 7. رسم علامت‌ها روی چارت (اگر خطا نباشد)
        annotated_chart_path = None
        if not analysis_result.get('error'):
            try:
                annotated_chart_path = annotate_chart_with_analysis(str(file_path), analysis_result)
                logger.info(f"چارت علامت‌گذاری شد: {annotated_chart_path}")
            except Exception as e:
                logger.warning(f"خطا در علامت‌گذاری چارت: {e}")
        
        # 8. فرمت‌بندی و ارسال سیگنال
        signal_text = formatter.format_signal(analysis_result)
        keyboard = formatter.create_keyboard()
        
        await analyzing_msg.delete()
        
        # ارسال پیام متنی سیگنال کامل
        await message.answer(signal_text, reply_markup=keyboard)
        logger.info("پیام سیگنال ارسال شد")
        
        # ارسال چارت علامت‌گذاری شده (اگر موجود باشد)
        if annotated_chart_path and os.path.exists(annotated_chart_path):
            try:
                await message.answer_photo(
                    photo=types.FSInputFile(annotated_chart_path),
                    caption="📊 چارت تحلیل شده با نقاط ورود/حد ضرر/حد سود",
                )
                logger.info("چارت علامت‌گذاری شده ارسال شد")
            except Exception as e:
                logger.warning(f"خطا در ارسال چارت علامت‌گذاری شده: {e}")
        else:
            logger.info("چارت علامت‌گذاری شده موجود نیست")
        
        logger.info(f"تحلیل تکمیل شد برای کاربر {user_name}")
        
    except Exception as e:
        logger.error(f"خطا در پردازش تصویر: {e}")
        error_msg = await message.answer(formatter.format_error_message(str(e)))
        # امکان حذف خودکار پیام خطا بعد از مدتی
    
    finally:
        # 9. حذف فایل‌های موقت
        try:
            if 'file_path' in locals() and os.path.exists(file_path):
                os.remove(file_path)
                logger.info(f"فایل موقت حذف شد: {file_path}")
            # حذف چارت علامت‌گذاری شده
            if 'annotated_chart_path' in locals() and annotated_chart_path and os.path.exists(annotated_chart_path):
                os.remove(annotated_chart_path)
                logger.info(f"چارت علامت‌گذاری شده حذف شد: {annotated_chart_path}")
        except Exception as e:
            logger.warning(f"خطا در حذف فایل‌های موقت: {e}")


# ==================== هندلرهای Callback ====================

@dp.callback_query()
async def handle_callback(callback: CallbackQuery):
    """پردازش کلیک‌های دکمه‌های شیشه‌ای"""
    try:
        action = callback.data
        user_name = callback.from_user.full_name
        
        logger.info(f"Callback دریافت شد از {user_name}: {action}")
        
        if action == "retry_analysis":
            await callback.message.answer("📸 لطفاً عکس چارت را مجدداً ارسال کنید")
            
        elif action == "show_help":
            help_text = formatter.format_help_message()
            await callback.message.edit_text(help_text, reply_markup=None)
            
        elif action == "start_analysis":
            await callback.message.answer("📸 عکس چارت خود را ارسال کنید")
            
        elif action == "save_signal":
            await callback.message.answer("💾 سیگنال در پروفایل شما ذخیره شد (قابلیت آینده)")
            
        elif action == "share_signal":
            # اشتراک‌گذاری سیگنال
            share_text = callback.message.text
            await bot.copy_message(
                chat_id=callback.from_user.id,
                from_chat_id=callback.message.chat.id,
                message_id=callback.message.message_id
            )
            
        elif action == "show_stats":
            await callback.message.answer("📊 آمار استفاده (به زودی)")
            
        elif action == "calculate_leverage":
            leverage_help = """
🎚️ **ماشین حساب اهرم**

برای محاسبه اهرم مناسب، اطلاعات زیر را ارسال کنید:

📝 **فرمت پیام:**
`محاسبه اهرم [مبلغ موجودی] [قیمت ورود] [حد ضرر] [درصد ریسک] [اهرم دلخواه]`

📊 **مثال:**
`محاسبه اهرم 1000 1.0850 1.0820 2 10`

💡 **توضیحات:**
- مبلغ موجودی: موجودی حساب شما
- قیمت ورود: قیمت ورود به معامله
- حد ضرر: قیمت حد ضرر
- درصد ریسک: درصد ریسک از موجودی (1-5%)
- اهرم دلخواه: سطح اهرم مورد نظر (اختیاری)

🔔 **یا می‌توانید فقط عکس چارت ارسال کنید تا AI اهرم مناسب را پیشنهاد دهد!**
            """
            await callback.message.answer(leverage_help)
            
        elif action == "risk_management":
            risk_help = """
⚠️ **راهنمای مدیریت ریسک با اهرم**

🎯 **قوانین طلایی:**
• هرگز بیش از 2% از موجودی را ریسک نکنید
• اهرم بالا = ریسک بالا
• در نوسان زیاد اهرم کمتری استفاده کنید

📊 **سطوح اهرم پیشنهادی:**
🟢 اعتماد بالا (80%+) → 10-15x
🟡 اعتماد متوسط (60-79%) → 5-10x  
🔴 اعتماد پایین (<60%) → 1-5x

💰 **مدیریت سرمایه:**
• حساب کوچک (زیر $500): اهرم کمتر
• حساب متوسط ($500-2000): اهرم متوسط
• حساب بزرگ (بالای $2000): اهرم بالاتر

⚠️ **هشدار مهم:**
اهرم می‌تواند سود و زیان را چند برابر کند!
همیشه حد ضرر را رعایت کنید.
            """
            await callback.message.answer(risk_help)
        
        # تأیید دریافت callback
        await callback.answer()
        
    except Exception as e:
        logger.error(f"خطا در پردازش callback: {e}")
        await callback.answer("خطایی رخ داد", show_alert=True)


# ==================== هندلر پیام‌های متنی ====================

@dp.message()
async def handle_text(message: Message):
    """پردازش پیام‌های متنی (با قابلیت محاسبه اهرم)"""
    text = message.text.lower().strip()
    
    if text in ['سلام', 'hi', 'hello', 'hey']:
        await message.answer(f"👋 سلام {message.from_user.first_name}! عکس چارت ارسال کنید 📊")
    
    elif text in ['راهنما', 'help', '؟', '?']:
        help_text = formatter.format_help_message()
        await message.answer(help_text)
    
    elif text in ['شروع', 'start', 'شروع تحلیل']:
        await message.answer("📸 عکس چارت خود را برای تحلیل ارسال کنید")
    
    elif text.startswith('محاسبه اهرم'):
        await handle_leverage_calculation(message)
    
    else:
        # پیام نامفهوم
        await message.answer(
            "🤔 متوجه نشدم! لطفاً عکس چارت ارسال کنید یا از دستور /help استفاده کنید."
        )


async def handle_leverage_calculation(message: Message):
    """هندلر محاسبه اهرم از پیام متنی"""
    try:
        # پارس کردن ورودی
        parts = message.text.split()
        if len(parts) < 5:
            await message.answer(
                "❌ فرمت نامعتبر!\n\n"
                "📝 فرمت صحیح:\n"
                "`محاسبه اهرم [مبلغ] [ورود] [ضرر] [ریسک%] [اهرم]`\n\n"
                "📊 مثال:\n"
                "`محاسبه اهرم 1000 1.0850 1.0820 2 10`"
            )
            return
        
        # استخراج مقادیر
        account_balance = float(parts[1])
        entry_price = float(parts[2])
        stop_loss = float(parts[3])
        risk_percent = float(parts[4])
        leverage = float(parts[5]) if len(parts) > 5 else 1.0
        
        # محاسبه پوزیشن
        calc = leverage_calculator.calculate_position_size(
            entry_price=entry_price,
            stop_loss=stop_loss,
            account_balance=account_balance,
            risk_percent=risk_percent,
            leverage=leverage
        )
        
        # فرمت و ارسال نتیجه
        result_text = leverage_calculator.format_position_calculation(calc)
        await message.answer(result_text)
        
    except ValueError:
        await message.answer("❌ لطفاً اعداد معتبر وارد کنید!")
    except Exception as e:
        await message.answer(f"❌ خطا در محاسبه: {str(e)}")


# ==================== تابع اصلی ====================

async def main():
    """اجرای اصلی ربات"""
    try:
        logger.info("🚀 ربات در حال راه‌اندازی...")
        
        # بررسی اتصال به تلگرام
        bot_info = await bot.get_me()
        logger.info(f"✅ ربات متصل شد: @{bot_info.username}")
        
        # شروع دریافت پیام‌ها
        logger.info("📡 شروع به دریافت پیام‌ها...")
        await dp.start_polling(bot)
        
    except KeyboardInterrupt:
        logger.info("⚠️ ربات متوقف شد (Ctrl+C)")
    except Exception as e:
        logger.error(f"❌ خطای بحرانی: {e}")
    finally:
        logger.info("👋 خداحافظ!")


# نقطه شروع برنامه
if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.info("⚠️ برنامه متوقف شد")
