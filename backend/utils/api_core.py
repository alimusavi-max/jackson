# backend/utils/api_core.py
"""
توابع اصلی برای ارتباط با API دیجی‌کالا
"""

import requests
import json
import time
import pandas as pd
from typing import List, Dict, Any, Optional
import os

# ثوابت
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
BASE_URL_SHIP_BY_SELLER = "https://seller.digikala.com/api/v2/ship-by-seller-orders"
BASE_URL_ONGOING = "https://seller.digikala.com/api/v2/orders/ongoing"
DEFAULT_PAGE_SIZE = 30
MAX_PAGES = 20
COOKIES_FILE_PATH = "sessions/digikala_cookies.json"


def load_session_cookies() -> List[Dict[str, Any]]:
    """بارگذاری کوکی‌ها از فایل"""
    try:
        current_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.abspath(os.path.join(current_dir, os.pardir, os.pardir))
        full_path = os.path.join(project_root, COOKIES_FILE_PATH)
        
        print(f"🔍 در حال بارگذاری کوکی از: {full_path}")
        
        if not os.path.exists(full_path):
            print(f"❌ فایل کوکی یافت نشد: {full_path}")
            return []
        
        with open(full_path, 'r', encoding='utf-8') as f:
            cookies = json.load(f)
            print(f"✅ {len(cookies)} کوکی بارگذاری شد")
            return cookies
    
    except Exception as e:
        print(f"❌ خطا در بارگذاری کوکی: {e}")
        return []


def format_cookies_for_requests(cookie_list: List[Dict]) -> Dict[str, str]:
    """تبدیل لیست کوکی‌ها به دیکشنری"""
    if not cookie_list:
        return {}
    return {cookie['name']: cookie['value'] for cookie in cookie_list}


def api_request_with_retry(
    method: str,
    url: str,
    cookies_dict: Dict[str, str],
    **kwargs
) -> Optional[requests.Response]:
    """ارسال درخواست با retry"""
    
    headers = kwargs.get('headers', {})
    headers['User-Agent'] = USER_AGENT
    kwargs['headers'] = headers
    kwargs['cookies'] = cookies_dict
    
    max_retries = 3
    retry_count = 0
    
    while retry_count < max_retries:
        try:
            response = requests.request(method, url, timeout=30, **kwargs)
            
            if response.status_code == 401:
                print(f"⚠️ خطای 401: کوکی‌ها منقضی شده‌اند")
                return None
            
            if response.status_code == 429:
                wait_time = int(response.headers.get("Retry-After", "15"))
                print(f"⏳ Rate limit: صبر کنید {wait_time} ثانیه...")
                time.sleep(wait_time)
                retry_count += 1
                continue
            
            response.raise_for_status()
            return response
        
        except requests.exceptions.RequestException as e:
            print(f"❌ خطا در درخواست: {e}")
            retry_count += 1
            if retry_count < max_retries:
                time.sleep(2 ** retry_count)
            continue
    
    return None


def get_customer_info(shipment_id: str, cookies_dict: Dict[str, str]) -> Optional[Dict[str, Any]]:
    """دریافت اطلاعات کامل مشتری"""
    try:
        persian_digits = '۰۱۲۳۴۵۶۷۸۹'
        latin_digits = '0123456789'
        trans = str.maketrans(persian_digits, latin_digits)
        shipment_id = str(shipment_id).translate(trans)
        
        shipment_id_clean = str(int(float(shipment_id)))
        
        url = f"https://seller.digikala.com/api/v2/ship-by-seller-orders/customer/{shipment_id_clean}"
        
        response = api_request_with_retry("GET", url, cookies_dict)
        
        if response and response.status_code == 200:
            data = response.json()
            return data.get('data', {})
        
        return None
    
    except Exception as e:
        print(f"❌ خطا در دریافت اطلاعات مشتری: {e}")
        return None


def get_all_orders(use_ship_by_seller: bool = True) -> List[Dict[str, Any]]:
    """دریافت تمام سفارشات از API"""
    
    print(f"\n{'='*60}")
    print(f"📡 دریافت سفارشات از {'Ship-by-Seller' if use_ship_by_seller else 'Marketplace'}")
    print(f"{'='*60}\n")
    
    cookies_list = load_session_cookies()
    if not cookies_list:
        print("❌ کوکی یافت نشد!")
        return []
    
    cookies_dict = format_cookies_for_requests(cookies_list)
    
    base_url = BASE_URL_SHIP_BY_SELLER if use_ship_by_seller else BASE_URL_ONGOING
    all_orders = []
    
    for page in range(1, MAX_PAGES + 1):
        print(f"📄 صفحه {page}...", end=" ")
        
        params = {'page': page, 'size': DEFAULT_PAGE_SIZE}
        
        response = api_request_with_retry("GET", base_url, cookies_dict, params=params)
        
        if not response:
            print("❌ خطا")
            break
        
        try:
            data = response.json()
            orders = data.get('data', {}).get('items', [])
            
            if not orders:
                print("✅ پایان")
                break
            
            all_orders.extend(orders)
            print(f"✅ {len(orders)} سفارش")
            time.sleep(0.5)
        
        except Exception as e:
            print(f"❌ خطا: {e}")
            break
    
    print(f"\n{'='*60}")
    print(f"✅ مجموع: {len(all_orders)} سفارش دریافت شد")
    print(f"{'='*60}\n")
    
    return all_orders


def orders_to_dataframe(
    orders: List[Dict[str, Any]],
    fetch_details: bool = False,
    cookies_dict: Optional[Dict[str, str]] = None
) -> pd.DataFrame:
    """
    تبدیل لیست سفارشات به DataFrame
    
    ⚠️ نکته مهم: این تابع برای هر variant یک ردیف جداگانه ایجاد می‌کند
    """
    
    if not orders:
        return pd.DataFrame()
    
    print(f"\n📊 تبدیل {len(orders)} سفارش به DataFrame...")
    
    order_list = []
    
    for idx, order in enumerate(orders):
        shipment_id = order.get('shipmentId', '')
        customer_details = None
        
        # دریافت جزئیات مشتری (اختیاری)
        if fetch_details and shipment_id and cookies_dict:
            if idx % 10 == 0:
                print(f"   📥 دریافت جزئیات: {idx + 1}/{len(orders)}")
            customer_details = get_customer_info(shipment_id, cookies_dict)
            time.sleep(0.3)
        
        address_info = order.get('address', {})
        
        # 🔴 نکته کلیدی: برای هر variant یک ردیف جداگانه ایجاد می‌شود
        variants = order.get("variants", [])
        
        if not variants:
            print(f"⚠️ سفارش {shipment_id} هیچ variant ندارد!")
            continue
        
        # 🎯 اینجا مهمه: حلقه روی تمام variants
        for variant_idx, variant in enumerate(variants):
            order_dict = {
                "کد سفارش": order.get('orderId'),
                "شناسه محموله": shipment_id,
                "تصویر محصول": variant.get("image_url"),
                "عنوان سفارش": variant.get('title', 'نامشخص'),
                "تعداد": variant.get('count', 0),
                "وضعیت": order.get('status', {}).get('text_fa', 'نامشخص'),
                "نام مشتری": order.get('customer_name', 'ناشناخته'),
                "مبلغ": variant.get('price', 0),
                "کد محصول (DKP)": variant.get('productId', 'نامشخص'),
                "تاریخ ثبت": order.get('orderDate', 'نامشخص'),
                "کد رهگیری": ""
            }
            
            # اطلاعات آدرس
            if customer_details:
                order_dict.update({
                    "استان": customer_details.get('state', address_info.get('state', 'نامشخص')),
                    "شهر": customer_details.get('city', address_info.get('city', 'نامشخص')),
                    "آدرس کامل": customer_details.get('address', address_info.get('address', 'نامشخص')),
                    "کد پستی": customer_details.get('postalCode', address_info.get('postal_code', 'نامشخص')),
                    "شماره تلفن": customer_details.get('phoneNumber', order.get('customer_phone', 'نامشخص')),
                })
            else:
                order_dict.update({
                    "استان": address_info.get('state', 'نامشخص'),
                    "شهر": address_info.get('city', 'نامشخص'),
                    "آدرس کامل": address_info.get('address', 'نامشخص'),
                    "کد پستی": address_info.get('postal_code', 'نامشخص'),
                    "شماره تلفن": order.get('customer_phone', 'نامشخص'),
                })
            
            order_list.append(order_dict)
            
            # لاگ برای دیباگ
            if len(variants) > 1 and variant_idx == 0:
                print(f"   📦 سفارش چندقلمی: {shipment_id} ({len(variants)} قلم)")
    
    df = pd.DataFrame(order_list)
    print(f"✅ DataFrame ایجاد شد: {len(df)} ردیف (شامل تمام اقلام)\n")
    
    # نمایش تعداد سفارشات منحصر به فرد
    if not df.empty:
        unique_orders = df['شناسه محموله'].nunique()
        print(f"📊 تعداد سفارشات منحصر به فرد: {unique_orders}")
        print(f"📊 تعداد کل اقلام: {len(df)}\n")
    
    return df


# تست
if __name__ == "__main__":
    print("🧪 تست API...")
    orders = get_all_orders(use_ship_by_seller=True)
    print(f"نتیجه: {len(orders)} سفارش")
    
    if orders:
        df = orders_to_dataframe(orders[:10])  # فقط 10 سفارش اول برای تست
        print("\nنمونه DataFrame:")
        print(df[['شناسه محموله', 'عنوان سفارش', 'تعداد']].head(20))