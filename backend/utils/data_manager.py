# utils/data_manager.py

import pandas as pd
import os
import json
import streamlit as st
import requests
import io
from typing import Dict, Any, List
from utils.constants import DB_FILE, COOKIES_FILE_PATH, UNIQUE_KEY_COLS, SENDER_PROFILES_FILE, USER_AGENT

# --- توابع مدیریت داده اصلی ---
def create_empty_dataframe() -> pd.DataFrame:
    """یک دیتافریم خالی با ساختار صحیح ایجاد می‌کند."""
    return pd.DataFrame(columns=[
        "کد سفارش", "شناسه محموله", "تصویر محصول", "عنوان سفارش", "تعداد",
        "وضعیت", "نام مشتری", "مبلغ", "استان", "شهر", "آدرس کامل",
        "کد پستی", "شماره تلفن", "کد رهگیری", "کد محصول (DKP)", "تاریخ ثبت"
    ])

def load_database():
    """دیتابیس را از فایل CSV بارگذاری کرده و کلیدهای اصلی را نرمال‌سازی می‌کند."""
    if not os.path.exists(DB_FILE):
        return create_empty_dataframe()
    try:
        df = pd.read_csv(DB_FILE, encoding='utf-8-sig', dtype=str)
        # اطمینان از اینکه همه ستون‌های کلیدی پس از بارگذاری نرمال‌سازی می‌شوند
        from utils.helpers import normalize_id
        for col in UNIQUE_KEY_COLS:
            if col in df.columns:
                df[col] = df[col].apply(normalize_id)
        df.fillna('', inplace=True)
        return df
    except pd.errors.EmptyDataError:
        return create_empty_dataframe()

def save_database(df: pd.DataFrame):
    """دیتافریم را در فایل CSV ذخیره می‌کند."""
    df.to_csv(DB_FILE, index=False, encoding='utf-8-sig')

@st.cache_data
def to_excel(df: pd.DataFrame) -> bytes:
    """دیتافریم را به فرمت اکسل برای دانلود آماده می‌کند."""
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Orders')
    processed_data = output.getvalue()
    return processed_data

# --- توابع مدیریت پروفایل فرستنده ---
def load_sender_profiles() -> Dict[str, Dict]:
    """بارگذاری پروفایل‌های فرستنده از فایل JSON"""
    if os.path.exists(SENDER_PROFILES_FILE):
        try:
            with open(SENDER_PROFILES_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return {}
    return {}

def save_sender_profiles(profiles: Dict[str, Dict]):
    """ذخیره پروفایل‌های فرستنده در فایل JSON"""
    with open(SENDER_PROFILES_FILE, 'w', encoding='utf-8') as f:
        json.dump(profiles, f, indent=4, ensure_ascii=False)

# --- تابع مدیریت کوکی ---
def load_session_cookies() -> List[Dict[str, Any]]:
    """کوکی‌ها را با محاسبه مسیر مطلق از ریشه پروژه بارگذاری می‌کند."""
    try:
        current_dir = os.path.dirname(os.path.abspath(__file__))
        PROJECT_ROOT = os.path.abspath(os.path.join(current_dir, os.pardir))
        full_path = os.path.join(PROJECT_ROOT, COOKIES_FILE_PATH) 
        
        if not os.path.exists(full_path):
            st.error(f"❌ فایل کوکی در مسیر: {full_path} یافت نشد. لطفا کوکی معتبر را در پوشه sessions قرار دهید.")
            return []
            
        with open(full_path, 'r', encoding='utf-8') as f:
            return json.load(f)
            
    except Exception as e:
        st.error(f"خطا در بارگذاری کوکی‌ها: {e}")
        return []

# --- تابع ساخت Session ---
def get_api_session() -> requests.Session | None:
    """Session را با هدر و کوکی‌های معتبر می‌سازد."""
    cookies_list = load_session_cookies()
    if not cookies_list:
        return None
        
    session = requests.Session()
    session.headers.update({'User-Agent': USER_AGENT})
    
    for c in cookies_list:
        session.cookies.set(c['name'], c['value'])
        
    return session

# --- تابع برای ارسال کد رهگیری (برای صفحه PDF) ---
def load_cookies_for_requests(cookie_path="sessions/digikala_cookies.json"):
    """بارگذاری کوکی‌ها برای استفاده در requests.Session"""
    current_dir = os.path.dirname(os.path.abspath(__file__))
    PROJECT_ROOT = os.path.abspath(os.path.join(current_dir, os.pardir))
    full_path = os.path.join(PROJECT_ROOT, cookie_path)
    
    if not os.path.exists(full_path):
        st.error(f"فایل کوکی در مسیر '{full_path}' یافت نشد.")
        return None
    
    try:
        with open(full_path, 'r') as f:
            cookies_list = json.load(f)
        return {cookie['name']: cookie['value'] for cookie in cookies_list}
    except Exception as e:
        st.error(f"خطا در خواندن فایل کوکی: {e}")
        return None