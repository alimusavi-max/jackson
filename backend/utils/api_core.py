# utils/api_core.py

import requests
import json
import time
import pandas as pd
from typing import List, Dict, Any, Optional
import streamlit as st

from utils.constants import (
    BASE_URL_SHIP_BY_SELLER, BASE_URL_ONGOING, DEFAULT_PAGE_SIZE,
    MAX_PAGES
)
from utils.helpers import convert_persian_to_latin
from utils.data_manager import create_empty_dataframe
from utils.api_handler import api_request_with_relogin # <<-- وارد کردن تابع جدید

# --- توابع اصلی داده ---
def get_customer_info(shipment_id) -> Optional[Dict[str, Any]]:
    """اطلاعات کامل مشتری را با استفاده از مکانیزم مقاوم و لاگین خودکار دریافت می‌کند."""
    shipment_id = convert_persian_to_latin(str(shipment_id))
    try:
        shipment_id_clean = str(int(float(shipment_id)))
    except ValueError:
        shipment_id_clean = shipment_id

    url = f"https://seller.digikala.com/api/v2/ship-by-seller-orders/customer/{shipment_id_clean}"

    # استفاده از تابع جدید به جای ارسال مستقیم درخواست
    response = api_request_with_relogin("GET", url)
    
    if response and response.status_code == 200:
        try:
            data = response.json()
            return data.get('data', {})
        except json.JSONDecodeError:
            st.error(f"پاسخ دریافت شده از سرور برای شناسه {shipment_id_clean} فرمت JSON معتبر ندارد.")
            return None
    return None

def get_all_orders(use_ship_by_seller: bool) -> List[Dict[str, Any]]:
    """دریافت لیست سفارشات از API و بازگرداندن به صورت لیست دیکشنری."""
    all_orders = []
    base_url = BASE_URL_SHIP_BY_SELLER if use_ship_by_seller else BASE_URL_ONGOING
    
    with st.spinner(f"در حال دریافت سفارش‌ها از API دیجی‌کالا ({'SBS' if use_ship_by_seller else 'Marketplace'})..."):
        for page in range(1, MAX_PAGES + 1):
            st.info(f"در حال خواندن صفحه {page}...")
            params = {'page': page, 'size': DEFAULT_PAGE_SIZE}
            
            # استفاده از تابع جدید
            response = api_request_with_relogin("GET", base_url, params=params)
            
            if not response or response.status_code != 200:
                st.error(f"دریافت اطلاعات از صفحه {page} ناموفق بود.")
                break
            
            try:
                data = response.json()
                orders = data.get('data', {}).get('items', [])
                if not orders:
                    st.info(f"صفحه {page} فاقد سفارش جدید بود. پایان دریافت.")
                    break
                all_orders.extend(orders)
                time.sleep(0.5)
            except (json.JSONDecodeError, AttributeError) as e:
                st.error(f"خطا در پردازش پاسخ JSON: {e}")
                break
                
    return all_orders

def orders_to_dataframe(orders: List[Dict[str, Any]], fetch_details: bool = False) -> pd.DataFrame:
    """تبدیل لیست دیکشنری سفارشات به DataFrame و دریافت اختیاری جزئیات مشتری."""
    if not orders:
        return create_empty_dataframe()
    
    order_list = []
    total = len(orders)
    progress_bar = None
    status_text = None
    
    if fetch_details:
        progress_bar = st.progress(0)
        status_text = st.empty()
        
    for idx, order in enumerate(orders):
        shipment_id = order.get('shipmentId', 'شناسه محموله موجود نیست')
        customer_details = None
        
        if fetch_details and shipment_id != 'شناسه محموله موجود نیست':
            if progress_bar and status_text:
                status_text.text(f"در حال دریافت جزئیات سفارش {idx + 1}/{total}")
                progress_bar.progress((idx + 1) / total)
            
            # فراخوانی تابع اصلاح شده
            customer_details = get_customer_info(shipment_id) 
            time.sleep(0.3)
            
        address_info = order.get('address', {})
        
        for variant in order.get("variants", []):
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
                "کد رهگیری": "" # مقدار اولیه
            }
            
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

    if progress_bar:
        progress_bar.empty()
    if status_text:
        status_text.empty()
        
    return pd.DataFrame(order_list)