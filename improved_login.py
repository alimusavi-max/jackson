import os
import time
import json
import imaplib
import email
from email.header import decode_header
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from dotenv import load_dotenv
from pathlib import Path
from bs4 import BeautifulSoup
import re
import sys
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

print("شروع برنامه...")

# بارگذاری متغیرهای محیطی
load_dotenv()
EMAIL = os.getenv("GMAIL_USERNAME")
PASSWORD = os.getenv("GMAIL_PASSWORD")
DK_KEEP_BROWSER = os.getenv("DK_KEEP_BROWSER_ON_ERROR", "0") == "1"

print(f"EMAIL = {EMAIL}")
print(f"PASSWORD = {'***' if PASSWORD else None}")
print(f"DK_KEEP_BROWSER = {DK_KEEP_BROWSER}")

BASE_DIR = Path(__file__).resolve().parent
SESSIONS_DIR = BASE_DIR / "sessions"
SESSIONS_DIR.mkdir(exist_ok=True)
LOG_DIR = BASE_DIR / "logs"
LOG_DIR.mkdir(exist_ok=True)

def fetch_latest_digikala_otp():
    print("دریافت OTP از جیمیل...")
    mail = imaplib.IMAP4_SSL("imap.gmail.com")
    mail.login(EMAIL, PASSWORD)
    mail.select("inbox")
    status, messages = mail.search(None, 'ALL')
    if status != "OK":
        raise Exception("جستجوی ایمیل شکست خورد")
    message_ids = messages[0].split()
    print("آخرین subject ایمیل‌های دریافتی:")
    for num in reversed(message_ids[-10:]):
        res, msg_data = mail.fetch(num, "(RFC822)")
        if res != "OK":
            continue
        msg = email.message_from_bytes(msg_data[0][1])
        subject, _ = decode_header(msg["Subject"])[0]
        if isinstance(subject, bytes):
            subject = subject.decode()
        print(subject)
        if ("اعتبارسنجی" in subject) or ("مرکز فروشندگان" in subject):
            body = ""
            if msg.is_multipart():
                for part in msg.walk():
                    if part.get_content_type() == "text/html":
                        body = part.get_payload(decode=True).decode()
                        break
            else:
                body = msg.get_payload(decode=True).decode()
            soup = BeautifulSoup(body, "html.parser")
            for s in soup.find_all("span"):
                t = s.get_text(strip=True)
                if re.fullmatch(r"\d{5,6}", t):
                    print("OTP (دقیق):", t)
                    return t
            code_match = re.search(r"\b\d{5,6}\b", body)
            if code_match:
                print("OTP (Fallback):", code_match.group(0))
                return code_match.group(0)
    raise Exception("کد تایید یافت نشد")

def save_cookies(driver, path):
    print(f"در حال ذخیره کوکی‌ها در {path}")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(driver.get_cookies(), f, indent=2, ensure_ascii=False)

def main():
    log_file = LOG_DIR / "improved_login.log"
    print(f"Log file: {log_file}")
    with open(log_file, "w", encoding="utf-8") as log:
        def logprint(*args):
            print(*args)
            print(*args, file=log)

        logprint("🟢 شروع ورود به دیجی‌کالا...")

        chrome_options = Options()
        chrome_options.add_argument("--start-maximized")
        service = Service()

        print("در حال ساخت ChromeDriver...")
        try:
            driver = webdriver.Chrome(service=service, options=chrome_options)
        except Exception as e:
            print("⛔️ خطا در ساخت ChromeDriver:", e)
            logprint("⛔️ خطا در ساخت ChromeDriver:", e)
            return

        try:
            print("در حال باز کردن سایت...")
            driver.get("https://seller.digikala.com/")

            print("منتظر نمایش فیلد ایمیل/موبایل...")
            email_input = WebDriverWait(driver, 20).until(
                EC.presence_of_element_located((By.NAME, "userName"))
            )
            print("فیلد ایمیل پیدا شد.")
            email_input.clear()
            email_input.send_keys(EMAIL)
            print("ایمیل یا موبایل وارد شد.")

            print("در حال یافتن دکمه تایید...")
            time.sleep(1.5)

            buttons = driver.find_elements(By.TAG_NAME, "button")
            found = False
            for idx, btn in enumerate(buttons):
                try:
                    btn_text = btn.text.strip()
                    btn_class = btn.get_attribute('class')
                    print(f"Button {idx}: text={btn_text!r}  class={btn_class!r}")
                    if btn.is_enabled() and btn.is_displayed():
                        if any(word in btn_text for word in ["تایید", "بعدی", "ادامه"]):
                            btn.click()
                            print(f"روی دکمه کلیک شد: {btn_text}")
                            found = True
                            break
                except Exception as ex:
                    print("خطا در چک کردن دکمه:", ex)
            if not found:
                print("هیچ دکمه تاییدی پیدا و کلیک نشد!")
                raise Exception("دکمه تایید پیدا نشد یا کلیک نشد.")

            logprint("⏳ منتظر دریافت کد تایید از ایمیل...")

            time.sleep(10)
            code = fetch_latest_digikala_otp()
            logprint(f"📩 کد دریافت‌شده: {code}")

            print("منتظر نمایش فیلد OTP...")
            try:
                otp_inputs = WebDriverWait(driver, 20).until(
                    lambda d: [i for i in d.find_elements(By.XPATH, '//input[@type="tel" and @autocomplete="off"]') if i.is_displayed() and i.is_enabled() and not i.get_attribute("value")]
                )
                if len(otp_inputs) != 6:
                    print("⛔️ تعداد فیلدهای OTP نامعتبر است:", len(otp_inputs))
                    raise Exception("OTP inputs not found (count != 6)")
                print("OTP inputs پیدا شدند:", len(otp_inputs))
            except Exception as ex:
                print("⛔️ فیلدهای OTP پیدا نشدند! همه اینپوت‌ها:")
                inputs = driver.find_elements(By.TAG_NAME, "input")
                for idx, inp in enumerate(inputs):
                    print(f"Input {idx}: name={inp.get_attribute('name')}, type={inp.get_attribute('type')}, autocomplete={inp.get_attribute('autocomplete')}, value={inp.get_attribute('value')}")
                raise Exception("OTP input fields not found.")

            # وارد کردن کد OTP رقم به رقم
            for i, ch in enumerate(code[:6]):
                otp_inputs[i].send_keys(ch)
            print("OTP وارد شد.")

            print("منتظر کلیک نهایی ورود...")
            WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, '//button'))
            ).click()
            print("ورود نهایی کلیک شد.")

            logprint("✅ ورود انجام شد. در حال ذخیره‌سازی سشن...")
            
            print("چند ثانیه منتظر می‌مانیم تا سشن کامل لود شود...")
            time.sleep(10)
            cookies_path = SESSIONS_DIR / "digikala_cookies.json"
            save_cookies(driver, cookies_path)
            logprint(f"✅ کوکی‌ها ذخیره شدند: {cookies_path}")

        except Exception as e:
            print("⛔️ خطا در اجرای عملیات:", e)
            logprint("⛔️ خطا:", e)
            try:
                page_path = LOG_DIR / "selenium_error.html"
                screen_path = LOG_DIR / "selenium_error.png"
                with open(page_path, "w", encoding="utf-8") as f:
                    f.write(driver.page_source)
                driver.save_screenshot(screen_path)
                logprint(f"📄 صفحه ذخیره شد: {page_path}")
                logprint(f"📸 اسکرین‌شات گرفته شد: {screen_path}")
            except Exception as ex2:
                print("خطا در ذخیره صفحه یا اسکرین‌شات:", ex2)
            raise
        finally:
            if DK_KEEP_BROWSER:
                print("🔁 مرورگر به‌صورت دستی بسته شود...")
                input("برای خروج ENTER بزنید...")
            driver.quit()
            print("مرورگر بسته شد.")

if __name__ == "__main__":
    main()
