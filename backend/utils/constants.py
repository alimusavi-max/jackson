# utils/constants.py

# --- مسیر فایل‌ها ---
COOKIES_FILE_PATH = "sessions/digikala_cookies.json" 
DB_FILE = "orders_database_complete.csv" 
SENDER_PROFILES_FILE = "sender_profiles.json" 
FONT_PATH = "Vazir.ttf" 
LABELS_DIR = "generated_labels" 
# --- ثوابت مدیریت داده ---
UNIQUE_KEY_COLS = ['کد سفارش', 'کد محصول (DKP)', 'شناسه محموله'] 

# --- ثوابت API و شبکه ---
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"

BASE_URL_SHIP_BY_SELLER = "https://seller.digikala.com/api/v2/ship-by-seller-orders"
BASE_URL_ONGOING = "https://seller.digikala.com/api/v2/orders/ongoing"
URL_CUSTOMER_INFO = "https://seller.digikala.com/api/v2/ship-by-seller-orders/customer/{shipment_id}"
URL_UPDATE_TRACKING_CODE = "https://seller.digikala.com/api/v2/ship-by-seller-orders/update-tracking-code"
URL_UPDATE_STATUS = "https://seller.digikala.com/api/v2/ship-by-seller-orders/update-status"

# --- تنظیمات عمومی API ---
DEFAULT_PAGE_SIZE = 30
MAX_PAGES = 20

# --- ثوابت ارسال پیامک ---
DEVICE_ID = "8840ef7242ad4049afc617c52ecb5f57"
COMPANY_NAME = "تجارت دریای آرام"
SENT_ORDERS_FILE = "sent_orders.txt"
UNKNOWN_TRACKING_CODE = "نامشخص"
KDECONNECT_CLI_PATH = r"C:\Program Files\KDE Connect\bin\kdeconnect-cli.exe"