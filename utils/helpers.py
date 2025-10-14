import pandas as pd
import jdatetime
import arabic_reshaper
from bidi.algorithm import get_display

def normalize_id(value):
    """نرمال‌سازی شناسه، تبدیل فارسی به لاتین و حذف اعشار."""
    if pd.isna(value):
        return ""
    s_val = str(value).strip()
    persian_to_latin_map = str.maketrans('۰۱۲۳۴۵۶۷۸۹', '0123456789')
    s_val = s_val.translate(persian_to_latin_map)
    if s_val.endswith('.0'):
        return s_val[:-2]
    return s_val

def persian_to_gregorian(persian_date: str) -> str:
    """تبدیل تاریخ شمسی به میلادی."""
    try:
        year, month, day = map(int, persian_date.split("/"))
        gregorian_date = jdatetime.date(year, month, day).togregorian()
        return f"{gregorian_date.year}-{gregorian_date.month:02d}-{gregorian_date.day:02d}"
    except (ValueError, AttributeError, TypeError):
        return ""

def convert_persian_to_latin(persian_number):
    """تبدیل ارقام فارسی در یک رشته به ارقام لاتین."""
    persian_digits = '۰۱۲۳۴۵۶۷۸۹'
    latin_digits = '0123456789'
    trans = str.maketrans(persian_digits, latin_digits)
    return str(persian_number).translate(trans)

def process_persian(text):
    """آماده‌سازی متن فارسی برای نمایش صحیح در محیط‌های گرافیکی."""
    return get_display(arabic_reshaper.reshape(str(text)))