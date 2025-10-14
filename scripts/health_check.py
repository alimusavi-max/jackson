# scripts/health_check.py
"""
اسکریپت بررسی سلامت سیستم
این اسکریپت تمام بخش‌های سیستم را چک می‌کند
"""

import os
import sys
import sqlite3
import requests
import json
from pathlib import Path
from datetime import datetime

# رنگ‌ها برای خروجی
class Colors:
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BLUE = '\033[94m'
    END = '\033[0m'
    BOLD = '\033[1m'

def print_header(text):
    print(f"\n{Colors.BOLD}{Colors.BLUE}{'='*60}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.BLUE}{text:^60}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.BLUE}{'='*60}{Colors.END}\n")

def print_success(text):
    print(f"{Colors.GREEN}✓{Colors.END} {text}")

def print_warning(text):
    print(f"{Colors.YELLOW}⚠{Colors.END} {text}")

def print_error(text):
    print(f"{Colors.RED}✗{Colors.END} {text}")

def print_info(text):
    print(f"{Colors.BLUE}ℹ{Colors.END} {text}")


def check_files():
    """بررسی وجود فایل‌های ضروری"""
    print_header("بررسی فایل‌های ضروری")
    
    required_files = {
        "دیتابیس": "data/digikala_sales.db",
        "کوکی‌ها": "sessions/digikala_cookies.json",
        "تنظیمات محیط": ".env",
        "فونت فارسی": "Vazir.ttf",
    }
    
    all_exist = True
    for name, path in required_files.items():
        if os.path.exists(path):
            size = os.path.getsize(path)
            print_success(f"{name}: {path} ({size:,} bytes)")
        else:
            print_error(f"{name}: {path} - فایل یافت نشد!")
            all_exist = False
    
    return all_exist


def check_database():
    """بررسی سلامت دیتابیس"""
    print_header("بررسی دیتابیس")
    
    db_path = "data/digikala_sales.db"
    
    if not os.path.exists(db_path):
        print_error(f"دیتابیس در {db_path} یافت نشد!")
        return False
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # بررسی جداول
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row[0] for row in cursor.fetchall()]
        
        print_info(f"جداول موجود: {', '.join(tables)}")
        
        # شمارش رکوردها
        stats = {}
        for table in ['orders', 'order_items', 'sms_logs', 'sender_profiles']:
            if table in tables:
                cursor.execute(f"SELECT COUNT(*) FROM {table}")
                count = cursor.fetchone()[0]
                stats[table] = count
                print_success(f"{table}: {count:,} رکورد")
            else:
                print_warning(f"جدول {table} وجود ندارد")
        
        conn.close()
        
        if stats.get('orders', 0) == 0:
            print_warning("هیچ سفارشی در دیتابیس وجود ندارد. آیا migration را اجرا کرده‌اید؟")
        
        return True
        
    except Exception as e:
        print_error(f"خطا در بررسی دیتابیس: {e}")
        return False


def check_backend_api():
    """بررسی Backend API"""
    print_header("بررسی Backend API")
    
    api_url = "http://localhost:8000"
    
    try:
        # بررسی root endpoint
        response = requests.get(f"{api_url}/", timeout=5)
        if response.status_code == 200:
            print_success(f"Backend در حال اجرا است: {api_url}")
            data = response.json()
            print_info(f"پیام: {data.get('message', 'N/A')}")
        else:
            print_error(f"Backend پاسخ غیرعادی داد: {response.status_code}")
            return False
        
        # بررسی Swagger docs
        try:
            docs_response = requests.get(f"{api_url}/docs", timeout=5)
            if docs_response.status_code == 200:
                print_success(f"مستندات API در دسترس است: {api_url}/docs")
        except:
            pass
        
        # بررسی stats endpoint
        try:
            stats_response = requests.get(f"{api_url}/api/stats", timeout=5)
            if stats_response.status_code == 200:
                stats = stats_response.json()
                print_success(f"آمار سیستم:")
                print_info(f"  - کل سفارشات: {stats.get('total_orders', 0):,}")
                print_info(f"  - با کد رهگیری: {stats.get('orders_with_tracking', 0):,}")
                print_info(f"  - مجموع فروش: {stats.get('total_sales', 0):,} تومان")
        except Exception as e:
            print_warning(f"خطا در دریافت آمار: {e}")
        
        return True
        
    except requests.exceptions.ConnectionError:
        print_error("Backend در حال اجرا نیست!")
        print_info("برای اجرای Backend: cd backend && uvicorn main:app --reload")
        return False
    except Exception as e:
        print_error(f"خطا در اتصال به Backend: {e}")
        return False


def check_frontend():
    """بررسی Frontend"""
    print_header("بررسی Frontend")
    
    frontend_url = "http://localhost:3000"
    
    try:
        response = requests.get(frontend_url, timeout=5)
        if response.status_code == 200:
            print_success(f"Frontend در حال اجرا است: {frontend_url}")
            return True
        else:
            print_warning(f"Frontend پاسخ غیرعادی داد: {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print_error("Frontend در حال اجرا نیست!")
        print_info("برای اجرای Frontend: cd frontend && npm run dev")
        return False
    except Exception as e:
        print_error(f"خطا در اتصال به Frontend: {e}")
        return False


def check_environment():
    """بررسی متغیرهای محیطی"""
    print_header("بررسی تنظیمات محیط")
    
    if not os.path.exists('.env'):
        print_error("فایل .env وجود ندارد!")
        print_info("لطفاً .env.example را کپی کنید: cp .env.example .env")
        return False
    
    required_vars = ['GMAIL_USERNAME', 'GMAIL_PASSWORD', 'DEVICE_ID']
    
    from dotenv import load_dotenv
    load_dotenv()
    
    all_set = True
    for var in required_vars:
        value = os.getenv(var)
        if value:
            masked = '*' * 8 if 'PASSWORD' in var else value[:20]
            print_success(f"{var}: {masked}...")
        else:
            print_warning(f"{var}: تنظیم نشده")
            all_set = False
    
    return all_set


def check_dependencies():
    """بررسی وابستگی‌های Python"""
    print_header("بررسی وابستگی‌های Python")
    
    required_packages = [
        'fastapi', 'uvicorn', 'sqlalchemy', 'pandas',
        'requests', 'selenium', 'pdfplumber', 'pillow'
    ]
    
    all_installed = True
    for package in required_packages:
        try:
            __import__(package)
            print_success(f"{package}")
        except ImportError:
            print_error(f"{package} - نصب نشده!")
            all_installed = False
    
    if not all_installed:
        print_info("\nبرای نصب: pip install -r backend/requirements.txt")
    
    return all_installed


def check_kde_connect():
    """بررسی KDE Connect"""
    print_header("بررسی KDE Connect")
    
    kde_path = r"C:\Program Files\KDE Connect\bin\kdeconnect-cli.exe"
    
    if not os.path.exists(kde_path):
        print_warning("KDE Connect یافت نشد!")
        print_info("برای ارسال پیامک، KDE Connect را نصب کنید")
        return False
    
    print_success(f"KDE Connect یافت شد: {kde_path}")
    
    # تست اتصال
    device_id = os.getenv('DEVICE_ID')
    if device_id:
        try:
            import subprocess
            result = subprocess.run(
                [kde_path, "--device", device_id, "--ping"],
                capture_output=True,
                timeout=5
            )
            if result.returncode == 0:
                print_success(f"اتصال با دستگاه {device_id} برقرار است")
                return True
            else:
                print_warning("دستگاه در دسترس نیست (آفلاین)")
                return False
        except Exception as e:
            print_warning(f"خطا در تست اتصال: {e}")
            return False
    else:
        print_warning("DEVICE_ID تنظیم نشده است")
        return False


def generate_report():
    """تولید گزارش نهایی"""
    print_header("گزارش نهایی")
    
    checks = {
        "فایل‌ها": check_files(),
        "دیتابیس": check_database(),
        "تنظیمات محیط": check_environment(),
        "وابستگی‌ها": check_dependencies(),
        "Backend API": check_backend_api(),
        "Frontend": check_frontend(),
        "KDE Connect": check_kde_connect(),
    }
    
    passed = sum(checks.values())
    total = len(checks)
    
    print(f"\n{'='*60}")
    print(f"نتیجه کلی: {passed}/{total} بررسی موفق")
    print(f"{'='*60}\n")
    
    if passed == total:
        print_success("✓ تمام بخش‌های سیستم سالم هستند!")
        print_info("سیستم آماده استفاده است 🎉")
    elif passed >= total * 0.7:
        print_warning("⚠ برخی بخش‌ها نیاز به توجه دارند")
        print_info("سیستم قابل استفاده است اما بهتر است مشکلات را برطرف کنید")
    else:
        print_error("✗ سیستم دارای مشکلات جدی است")
        print_info("لطفاً ابتدا مشکلات را برطرف کنید")
    
    # ذخیره گزارش
    report = {
        "timestamp": datetime.now().isoformat(),
        "checks": checks,
        "score": f"{passed}/{total}"
    }
    
    report_path = "logs/health_check_report.json"
    os.makedirs("logs", exist_ok=True)
    with open(report_path, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    
    print(f"\nگزارش کامل در {report_path} ذخیره شد")


if __name__ == "__main__":
    print(f"\n{Colors.BOLD}🏥 بررسی سلامت سیستم مدیریت دیجی‌کالا{Colors.END}")
    print(f"{Colors.BOLD}تاریخ: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}{Colors.END}\n")
    
    try:
        generate_report()
    except KeyboardInterrupt:
        print(f"\n\n{Colors.YELLOW}بررسی توسط کاربر متوقف شد{Colors.END}")
        sys.exit(1)
    except Exception as e:
        print(f"\n{Colors.RED}خطای غیرمنتظره: {e}{Colors.END}")
        sys.exit(1)