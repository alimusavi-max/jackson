# utils/tracking_core.py

import streamlit as st
import pdfplumber
import re
import pandas as pd
from collections import defaultdict
import requests
from typing import Union

# وارد کردن تابع جدید
from utils.api_handler import api_request_with_relogin
from utils.constants import USER_AGENT

def extract_shipping_data_robust(pdf_file_object) -> pd.DataFrame:
    """استخراج جفت‌های (کد سفارش، کد رهگیری) از فایل PDF رسید پستی"""
    # ... (این تابع بدون تغییر باقی می‌ماند) ...
    records = defaultdict(dict)
    
    tracking_pattern = re.compile(r'^\d{24}$')
    order_pattern = re.compile(r'\b(\d{9})\b')
    row_num_pattern = re.compile(r'^\d{1,2}$')
    
    last_row_num = None
    
    try:
        with pdfplumber.open(pdf_file_object) as pdf:
            for page in pdf.pages:
                tables = page.extract_tables()
                if not tables:
                    continue
                
                for table in tables:
                    if not table or len(table[0]) < 5:
                        continue
                    
                    for row in table:
                        cleaned_row = [cell.strip() if cell else "" for cell in row]
                        
                        if cleaned_row and row_num_pattern.match(cleaned_row[-1]):
                            last_row_num = cleaned_row[-1]
                        
                        if last_row_num:
                            for cell in cleaned_row:
                                if tracking_pattern.match(cell):
                                    records[last_row_num]['کد رهگیری'] = cell
                                elif order_match := order_pattern.search(cell):
                                    records[last_row_num]['شماره سفارش'] = order_match.group(1)
        
        final_list = []
        for row_num, data in sorted(records.items()):
            if 'کد رهگیری' in data and 'شماره سفارش' in data:
                final_list.append({
                    "ردیف": int(row_num),
                    "شماره سفارش": data['شماره سفارش'],
                    "کد رهگیری": data['کد رهگیری']
                })
        
        if not final_list:
            return pd.DataFrame()
        
        return pd.DataFrame(final_list).sort_values(by="ردیف").drop(columns=["ردیف"])
    
    except Exception as e:
        st.error(f"خطا در استخراج PDF: {str(e)}")
        return pd.DataFrame()


def send_tracking_code_to_api(shipment_id: int, tracking_code: str) -> Union[requests.Response, str]:
    """ارسال کد رهگیری به API دیجی‌کالا با استفاده از مکانیزم لاگین خودکار."""
    url = "https://seller.digikala.com/api/v2/ship-by-seller-orders/tracking-code"
    
    payload = {
        "tracking_codes": [{"tracking_code": tracking_code, "id": None}],
        "order_shipment_id": int(shipment_id),
        "infra_type": "post",
        "service_name": ""
    }
    
    headers = {
        "accept": "application/json",
        "content-type": "application/json",
        "origin": "https://seller.digikala.com",
        "referer": "https://seller.digikala.com/pwa/orders/ship-by-seller/",
        "user-agent": USER_AGENT
    }
    
    # استفاده از تابع جدید برای ارسال درخواست POST
    response = api_request_with_relogin("POST", url, headers=headers, json=payload)
    
    if response:
        return response
    else:
        return "ارسال درخواست ناموفق بود. لاگ‌ها را بررسی کنید."

def update_local_tracking_code(df: pd.DataFrame, order_id: str, tracking_code: str) -> pd.DataFrame:
    """به‌روزرسانی کد رهگیری در دیتابیس محلی"""
    df.loc[df['کد سفارش'].astype(str) == str(order_id), 'کد رهگیری'] = tracking_code
    return df