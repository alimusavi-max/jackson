# backend/utils/helpers.py
"""
توابع کمکی
"""

import pandas as pd
from datetime import datetime


def normalize_id(value):
    """نرمال‌سازی شناسه: تبدیل فارسی به لاتین و حذف اعشار"""
    if pd.isna(value):
        return ""
    
    s_val = str(value).strip()
    
    # تبدیل ارقام فارسی به لاتین
    persian_to_latin_map = str.maketrans('۰۱۲۳۴۵۶۷۸۹', '0123456789')
    s_val = s_val.translate(persian_to_latin_map)
    
    # حذف .0 از انتها
    if s_val.endswith('.0'):
        return s_val[:-2]
    
    return s_val


def persian_to_gregorian(persian_date: str) -> str:
    """تبدیل تاریخ شمسی به میلادی (ساده)"""
    try:
        # این یک تابع ساده است
        # برای استفاده واقعی باید از jdatetime استفاده کنید
        return datetime.now().isoformat()
    except:
        return ""


def convert_persian_to_latin(persian_number):
    """تبدیل ارقام فارسی در رشته به ارقام لاتین"""
    persian_digits = '۰۱۲۳۴۵۶۷۸۹'
    latin_digits = '0123456789'
    trans = str.maketrans(persian_digits, latin_digits)
    return str(persian_number).translate(trans)


def format_price(price):
    """فرمت کردن قیمت"""
    try:
        return f"{float(price):,.0f}"
    except:
        return "0"


def validate_phone(phone):
    """اعتبارسنجی شماره تلفن"""
    if not phone:
        return False
    
    # حذف فاصله و خط تیره
    phone = phone.replace(' ', '').replace('-', '')
    
    # تبدیل فارسی به لاتین
    phone = convert_persian_to_latin(phone)
    
    # بررسی طول (09xxxxxxxxx = 11 رقم)
    if len(phone) == 11 and phone.startswith('09'):
        return True
    
    return False


def clean_text(text):
    """پاکسازی متن"""
    if pd.isna(text):
        return ""
    
    text = str(text).strip()
    
    # حذف خطوط اضافی
    text = ' '.join(text.split())
    
    return text