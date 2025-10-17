# backend/test_font.py
"""
اسکریپت تست برای بررسی فونت و تولید برچسب نمونه
"""

import os
import sys

# اضافه کردن مسیر backend به path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from utils.label_core import get_font_path, load_fonts, generate_label_portrait
from PIL import Image

print("="*60)
print("🧪 تست سیستم تولید برچسب")
print("="*60)

# 1. بررسی فونت
print("\n1️⃣ بررسی فونت Vazir...")
font_path = get_font_path()

if font_path:
    print(f"✅ فونت پیدا شد: {font_path}")
    print(f"   حجم فایل: {os.path.getsize(font_path) / 1024:.1f} KB")
else:
    print("⚠️  فونت Vazir.ttf پیدا نشد!")
    print("   لطفاً فایل Vazir.ttf را در یکی از این مسیرها قرار دهید:")
    print("   - روت پروژه")
    print("   - پوشه backend")
    print("   - پوشه backend/utils")

# 2. تست بارگذاری فونت‌ها
print("\n2️⃣ تست بارگذاری فونت‌ها...")
fonts = load_fonts()
print(f"✅ {len(fonts)} فونت بارگذاری شد:")
for name, font in fonts.items():
    print(f"   - {name}: {font}")

# 3. تولید برچسب نمونه
print("\n3️⃣ تولید برچسب نمونه...")

try:
    # داده‌های نمونه
    sender_info = {
        'name': 'فروشگاه تجارت دریای آرام',
        'address': 'تهران، خیابان ولیعصر، پلاک ۱۲۳',
        'postal_code': '1234567890',
        'phone': '021-12345678'
    }
    
    receiver_info = {
        'نام مشتری': 'علی احمدی',
        'شهر': 'تهران',
        'استان': 'تهران',
        'آدرس کامل': 'تهران، خیابان آزادی، کوچه شهید رضایی، پلاک ۴۵',
        'کد پستی': '9876543210',
        'شماره تلفن': '09123456789',
        'products': [
            {'name': 'گوشی موبایل سامسونگ Galaxy A54', 'qty': 1},
            {'name': 'کاور محافظ', 'qty': 2},
            {'name': 'محافظ صفحه نمایش شیشه‌ای', 'qty': 1}
        ]
    }
    
    # تولید برچسب
    label_img = generate_label_portrait(
        order_id='123456789',
        sender_info=sender_info,
        receiver_info=receiver_info,
        include_datamatrix=True
    )
    
    # ذخیره تصویر
    output_path = 'test_label.png'
    label_img.save(output_path)
    
    print(f"✅ برچسب نمونه ایجاد شد: {output_path}")
    print(f"   اندازه تصویر: {label_img.size}")
    print(f"   حجم فایل: {os.path.getsize(output_path) / 1024:.1f} KB")
    
    # نمایش تصویر (اختیاری)
    try:
        label_img.show()
        print("   🖼️  تصویر نمایش داده شد")
    except:
        print("   (نمایش تصویر در محیط فعلی امکان‌پذیر نیست)")
    
    print("\n✅ تمام تست‌ها موفق بودند!")
    
except Exception as e:
    print(f"\n❌ خطا در تولید برچسب:")
    print(f"   {str(e)}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("\n" + "="*60)
print("🎉 تست به پایان رسید")
print("="*60)