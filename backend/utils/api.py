import json
import time
from typing import List, Dict, Any, Optional
import requests
import streamlit as st
import os

# ثابت User Agent
USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/91.0.4472.124 Safari/537.36"
)

# مسیر پیش‌فرض کوکی
BASE_DIR = os.getcwd()
DEFAULT_COOKIE_FILE = os.path.join(BASE_DIR, "sessions", "digikala_cookies.json")


def convert_persian_to_latin(persian_number: str) -> str:
    """تبدیل اعداد فارسی به انگلیسی"""
    persian_digits = '۰۱۲۳۴۵۶۷۸۹'
    latin_digits = '0123456789'
    trans = str.maketrans(persian_digits, latin_digits)
    return str(persian_number).translate(trans)


def send_request_with_rate_limit_handling(
    url: str, headers: Dict, params: Dict = None, timeout: int = 30
) -> Optional[requests.Response]:
    """مدیریت ریکوئست با هندل کردن خطای 429 (rate limit)"""
    attempt = 0
    while True:
        try:
            response = requests.get(url, headers=headers, params=params, timeout=timeout)

            if response.status_code == 429:
                retry_after = response.headers.get("Retry-After")
                wait_time = 2 ** attempt
                if retry_after and retry_after.isdigit():
                    wait_time = int(retry_after)
                    st.warning(f"⏳ سرور درخواست توقف به مدت {wait_time} ثانیه دارد. در حال انتظار...")
                else:
                    st.warning(f"⏳ با محدودیت سرعت مواجه شدیم. تلاش مجدد تا {wait_time} ثانیه دیگر...")

                time.sleep(wait_time)
                attempt += 1
                continue

            response.raise_for_status()
            return response

        except requests.exceptions.HTTPError as e:
            st.error(f"خطای پایدار HTTP: {e.response.status_code} برای {url}.")
            if e.response.status_code == 401:
                st.error("خطای 401: دسترسی نامعتبر. فایل کوکی را بررسی کنید.")
            return None

        except requests.exceptions.RequestException as e:
            wait_time = min(2 ** attempt, 60)
            st.warning(f"خطا در اتصال: {e}. تلاش مجدد تا {wait_time} ثانیه دیگر...")
            time.sleep(wait_time)
            attempt += 1


def load_session_cookies(cookie_file: str = DEFAULT_COOKIE_FILE) -> Optional[List[Dict[str, Any]]]:
    """خواندن فایل کوکی (فرمت JSON)"""
    try:
        with open(cookie_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        st.error(f"فایل کوکی در مسیر '{cookie_file}' یافت نشد.")
        return None
    except json.JSONDecodeError:
        st.error("فایل کوکی فرمت JSON معتبری ندارد.")
        return None


def get_customer_info(shipment_id, headers):
    """گرفتن اطلاعات مشتری از API دیجی‌کالا"""
    shipment_id = convert_persian_to_latin(str(shipment_id))
    try:
        shipment_id_clean = str(int(float(shipment_id)))
    except ValueError:
        shipment_id_clean = shipment_id

    url = f"https://seller.digikala.com/api/v2/ship-by-seller-orders/customer/{shipment_id_clean}"

    response = send_request_with_rate_limit_handling(url, headers=headers)
    if response:
        try:
            data = response.json()
            return data.get('data', {})
        except json.JSONDecodeError:
            st.error(f"پاسخ دریافتی برای شناسه {shipment_id_clean} JSON معتبر نیست.")
            return None
    return None
