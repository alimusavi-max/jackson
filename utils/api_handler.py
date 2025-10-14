# utils/api_handler.py

import requests
import time
import streamlit as st
import os
from typing import Optional

# این import را به صورت شرطی و داخل تابع انجام می‌دهیم تا از خطای circular import جلوگیری شود
# from improved_login import main as refresh_session_main

from utils.data_manager import load_session_cookies, COOKIES_FILE_PATH

def format_cookies_for_requests(cookie_list):
    """لیست کوکی‌ها را به فرمت دیکشنری برای کتابخانه requests تبدیل می‌کند."""
    if not cookie_list:
        return {}
    return {cookie['name']: cookie['value'] for cookie in cookie_list}

def api_request_with_relogin(method: str, url: str, **kwargs) -> Optional[requests.Response]:
    """
    درخواست API را با مدیریت کامل خطاها (401, 429, ...) و لاگین مجدد خودکار ارسال می‌کند.
    """
    retries = 0
    max_retries = 2 # حداکثر تلاش برای لاگین مجدد

    while retries < max_retries:
        cookies_list = load_session_cookies()
        
        # اگر کوکی وجود ندارد، برای لاگین تلاش می‌کنیم
        if not cookies_list:
            st.warning(f"فایل کوکی در مسیر '{COOKIES_FILE_PATH}' یافت نشد یا خالی است.")
            if retries == 0:
                st.info("تلاش برای اجرای فرآیند ورود برای اولین بار...")
            else:
                st.error("تلاش برای ورود مجدد نیز ناموفق بود.")
                return None
        
        # کوکی‌ها را در هدر kwargs قرار می‌دهیم
        if 'cookies' not in kwargs:
            kwargs['cookies'] = format_cookies_for_requests(cookies_list)

        try:
            # اگر هدرها از قبل تعریف نشده بودند، آن‌ها را اضافه کن
            if 'headers' not in kwargs:
                kwargs['headers'] = {}
            kwargs['headers']['User-Agent'] = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"

            response = requests.request(method, url, timeout=30, **kwargs)

            # --- مدیریت خطای 401 (Unauthorized) ---
            if response.status_code == 401:
                st.warning(f"⚠️ نشست منقضی شد (خطای 401). تلاش برای ورود مجدد... (تلاش {retries + 1})")
                
                try:
                    # وارد کردن دینامیک برای جلوگیری از خطاهای احتمالی
                    from improved_login import main as refresh_session_main
                    with st.spinner("در حال اجرای فرآیند ورود خودکار... این ممکن است کمی طول بکشد."):
                        refresh_session_main()
                    st.success("✅ ورود مجدد با موفقیت انجام شد. در حال ارسال دوباره درخواست...")
                    retries += 1
                    time.sleep(2)
                    kwargs.pop('cookies', None) # کوکی‌های قدیمی را حذف کن تا دوباره لود شوند
                    continue # بازگشت به ابتدای حلقه برای تلاش مجدد
                except ImportError:
                    st.error("❌ فایل improved_login.py در ریشه پروژه یافت نشد.")
                    return None
                except Exception as e:
                    st.error(f"❌ فرآیند ورود خودکار با خطا مواجه شد: {e}")
                    return None

            # --- مدیریت خطای 429 (Rate Limit) ---
            if response.status_code == 429:
                wait_time = int(response.headers.get("Retry-After", "15"))
                st.warning(f"⏳ با محدودیت سرعت مواجه شدیم. در حال انتظار برای {wait_time} ثانیه...")
                time.sleep(wait_time)
                continue

            # بررسی دیگر خطاهای HTTP
            response.raise_for_status()
            
            # اگر همه چیز موفق بود، پاسخ را برگردان
            return response

        except requests.exceptions.HTTPError as e:
            st.error(f"خطای پایدار HTTP: {e.response.status_code} برای {url}.")
            return None # در صورت خطای پایدار، از حلقه خارج شو
        
        except requests.exceptions.RequestException as e:
            wait_time = min(2 ** retries, 60)
            st.warning(f"خطا در اتصال: {e}. تلاش مجدد تا {wait_time} ثانیه دیگر...")
            time.sleep(wait_time)
            retries += 1
            continue
            
    st.error("عملیات پس از چندین تلاش ناموفق بود.")
    return None