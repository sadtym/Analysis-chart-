"""
ماژول پردازش و بهینه‌سازی تصاویر چارت
شامل توابع فشرده‌سازی، تغییر اندازه و آماده‌سازی تصویر برای API
"""

import os
from pathlib import Path
from io import BytesIO
from PIL import Image, ImageEnhance, ImageFilter
import base64
import logging

from config import CHARTS_DIR, IMAGE_MAX_WIDTH, IMAGE_QUALITY, IMAGE_FORMAT

logger = logging.getLogger(__name__)


def preprocess_image(image_path: str) -> str:
    """
    فشرده‌سازی و آماده‌سازی تصویر قبل از ارسال به API هوش مصنوعی
    
    Args:
        image_path: مسیر فایل تصویر
        
    Returns:
        رشته base64 تصویر فشرده شده
    """
    try:
        with Image.open(image_path) as img:
            # تبدیل به RGB اگر حالت RGBA یا دیگر حالتها باشد
            if img.mode in ('RGBA', 'P', 'L'):
                img = img.convert('RGB')
            
            # افزایش کنتراست برای خوانایی بهتر اعداد
            enhancer = ImageEnhance.Contrast(img)
            img = enhancer.enhance(1.2)
            
            # افزایش sharpness
            sharpener = ImageEnhance.Sharpness(img)
            img = sharpener.enhance(1.1)
            
            # کاهش اندازه تا حداکثر عرض مشخص شده
            if img.width > IMAGE_MAX_WIDTH:
                ratio = IMAGE_MAX_WIDTH / img.width
                new_height = int(img.height * ratio)
                img = img.resize((IMAGE_MAX_WIDTH, new_height), Image.Resampling.LANCZOS)
            
            # ذخیره در buffer با کیفیت تنظیم شده
            buffer = BytesIO()
            img.save(buffer, format=IMAGE_FORMAT, quality=IMAGE_QUALITY, optimize=True)
            
            logger.info(f"تصویر پردازش شد: اندازه جدید = {img.size}")
            
            return base64.b64encode(buffer.getvalue()).decode("utf-8")
            
    except Exception as e:
        logger.error(f"خطا در پردازش تصویر: {e}")
        raise


def optimize_for_ocr(image_path: str) -> str:
    """
    بهینه‌سازی تصویر برای تشخیص بهتر اعداد و متون
    
    Args:
        image_path: مسیر فایل تصویر
        
    Returns:
        رشته base64 تصویر بهینه شده
    """
    try:
        with Image.open(image_path) as img:
            if img.mode != 'RGB':
                img = img.convert('RGB')
            
            # اعمال فیلتر افزایش وضوح
            img = img.filter(ImageFilter.SHARPEN)
            
            # کاهش نویز
            img = img.filter(ImageFilter.MedianFilter(size=3))
            
            # ذخیره در buffer
            buffer = BytesIO()
            img.save(buffer, format=IMAGE_FORMAT, quality=IMAGE_QUALITY)
            
            return base64.b64encode(buffer.getvalue()).decode("utf-8")
            
    except Exception as e:
        logger.error(f"خطا در بهینه‌سازی OCR: {e}")
        raise


def validate_image(image_path: str) -> tuple[bool, str]:
    """
    اعتبارسنجی تصویر ارسالی
    
    Args:
        image_path: مسیر فایل تصویر
        
    Returns:
        tuple: (آیا معتبر است, پیام خطا یا موفقیت)
    """
    try:
        if not os.path.exists(image_path):
            return False, "فایل تصویر یافت نشد"
        
        file_size = os.path.getsize(image_path)
        if file_size > 10 * 1024 * 1024:  # 10MB
            return False, "حجم تصویر بیش از 10 مگابایت است"
        
        with Image.open(image_path) as img:
            if img.width < 100 or img.height < 100:
                return False, "ابعاد تصویر بسیار کوچک است"
            
            valid_formats = ('RGB', 'RGBA', 'L', 'P')
            if img.mode not in valid_formats:
                return False, "فرمت تصویر پشتیبانی نمی‌شود"
        
        return True, "تصویر معتبر است"
        
    except Exception as e:
        return False, f"خطا در اعتبارسنجی: {str(e)}"


def get_unique_filename(user_id: int) -> str:
    """
    تولید نام یکتا برای فایل تصویر
    
    Args:
        user_id: شناسه کاربر تلگرام
        
    Returns:
        مسیر کامل فایل با نام یکتا
    """
    import uuid
    filename = f"{user_id}_{uuid.uuid4().hex[:8]}.jpg"
    return CHARTS_DIR / filename


def cleanup_old_images(max_age_hours: int = 24):
    """
    حذف تصاویر قدیمی برای آزادسازی فضا
    
    Args:
        max_age_age: حداکثر سن تصویر به ساعت
    """
    import time
    
    current_time = time.time()
    deleted_count = 0
    
    for image_path in CHARTS_DIR.glob("*.jpg"):
        file_age = current_time - os.path.getmtime(image_path)
        if file_age > max_age_hours * 3600:
            try:
                os.remove(image_path)
                deleted_count += 1
            except Exception as e:
                logger.warning(f"خطا در حذف {image_path}: {e}")
    
    logger.info(f"{deleted_count} تصویر قدیمی حذف شد")
