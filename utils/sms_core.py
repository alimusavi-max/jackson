# utils/sms_core.py

import subprocess
import streamlit as st
import os
from typing import Tuple, Set
from utils.constants import DEVICE_ID, KDECONNECT_CLI_PATH, SENT_ORDERS_FILE, COMPANY_NAME

# --- توابع مدیریت سوابق ارسال ---
def load_sent_orders() -> Set[str]:
    if not os.path.exists(SENT_ORDERS_FILE):
        return set()
    try:
        with open(SENT_ORDERS_FILE, "r", encoding="utf-8") as f:
            return {line.strip() for line in f if line.strip()}
    except Exception as e:
        st.error(f"خطا در خواندن فایل سوابق ارسال: {e}")
        return set()

def save_sent_order(tracking_code: str):
    with open(SENT_ORDERS_FILE, "a", encoding="utf-8") as f:
        f.write(str(tracking_code) + "\n")

def overwrite_sent_orders(sent_codes: Set[str]):
    try:
        with open(SENT_ORDERS_FILE, "w", encoding="utf-8") as f:
            for code in sorted(list(sent_codes)):
                f.write(code + "\n")
    except Exception as e:
        st.error(f"خطا در ذخیره‌سازی فایل سوابق ارسال: {e}")

# --- توابع KDE Connect (با منطق تست اتصال کاملاً جدید) ---
def check_kde_connect_cli() -> Tuple[bool, str]:
    """
    ارتباط با KDE Connect را با بررسی exit-code دستور پینگ چک می‌کند (روش قابل اطمینان‌تر).
    """
    if not os.path.exists(KDECONNECT_CLI_PATH):
        return False, f"❌ فایل اجرایی KDE Connect در مسیر '{KDECONNECT_CLI_PATH}' پیدا نشد."

    try:
        # اجرای دستور پینگ. check=True باعث می‌شود در صورت عدم موفقیت، خطا ایجاد شود.
        subprocess.run(
            [KDECONNECT_CLI_PATH, "--device", DEVICE_ID, "--ping"],
            check=True,
            capture_output=True, # خروجی را می‌گیریم تا نمایش داده نشود
            timeout=7 # کمی زمان بیشتر برای پاسخ‌دهی
        )
        # اگر دستور بالا بدون خطا اجرا شود، یعنی اتصال برقرار است
        return True, f"✅ اتصال با دستگاه '{DEVICE_ID}' برقرار است."

    except subprocess.CalledProcessError as e:
        # این خطا معمولا وقتی رخ می‌دهد که دستگاه آفلاین یا غیرقابل دسترس باشد
        error_output = e.stderr.decode('utf-8', errors='ignore').strip()
        if "not reachable" in error_output.lower():
            return False, f"❌ دستگاه '{DEVICE_ID}' در دسترس نیست (آفلاین). لطفاً KDE Connect را روی گوشی خود باز کنید."
        return False, f"❌ خطا در اجرای دستور KDE Connect: {error_output}"
    except subprocess.TimeoutExpired:
        return False, "❌ زمان پاسخگویی KDE Connect تمام شد. ممکن است برنامه روی گوشی یا کامپیوتر هنگ کرده باشد."
    except Exception as e:
        return False, f"❌ خطایی نامشخص رخ داد: {e}"

def send_sms(phone_number: str, message: str, dry_run: bool = False) -> Tuple[bool, str]:
    if dry_run:
        return True, f" (آزمایشی) پیامک برای {phone_number} شبیه‌سازی شد."
    is_connected, status_message = check_kde_connect_cli()
    if not is_connected:
        return False, f"خطا در ارسال: {status_message}"
    try:
        command = [
            KDECONNECT_CLI_PATH, "--device", DEVICE_ID,
            "--send-sms", message, "--destination", str(phone_number)
        ]
        subprocess.run(command, check=True, capture_output=True, timeout=15)
        return True, f"پیامک برای {phone_number} با موفقیت ارسال شد."
    except subprocess.CalledProcessError as e:
        return False, f"خطا در اجرای دستور ارسال: {e.stderr.decode('utf-8', errors='ignore').strip()}"
    except Exception as e:
        return False, f"خطایی ناشناخته در زمان ارسال: {e}"

def get_sms_template(customer_name: str, tracking_code: str) -> str:
    greeting = f"سلام {customer_name} عزیز،" if customer_name else "سلام دوست عزیز،"
    message = (
        f"{greeting}\n"
        f"بسته شما از طرف «{COMPANY_NAME}» ارسال شد. 📦\n\n"
        f"برای پیگیری لحظه‌ای مرسوله، کد رهگیری زیر را در سایت پست (tracking.post.ir) وارد نمایید:\n"
        f"کد رهگیری: {tracking_code}"
    )
    return message