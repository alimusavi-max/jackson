# pages/pdf_tracking_page.py

import sys
import os

current_file = os.path.abspath(__file__)
project_root = os.path.dirname(os.path.dirname(current_file))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

import streamlit as st
import pandas as pd
import requests
import time
import re

st.set_page_config(layout="wide", page_title="ثبت رهگیری")

try:
    from utils.tracking_core import extract_shipping_data_robust, send_tracking_code_to_api
    from utils.data_manager import save_database, load_database
except ImportError as e:
    st.error(f"خطا در import: {e}")
    st.stop()

if 'orders_df' not in st.session_state:
    st.session_state.orders_df = load_database()
if 'pdf_data' not in st.session_state:
    st.session_state.pdf_data = None
if 'merged_data' not in st.session_state:
    st.session_state.merged_data = None

st.header("ثبت کدهای رهگیری پستی")

# مرحله ۱: آپلود PDF
st.subheader("مرحله ۱: آپلود PDF")
uploaded_pdf = st.file_uploader("فایل PDF رسید", type="pdf")

if uploaded_pdf:
    with st.spinner('استخراج...'):
        extracted = extract_shipping_data_robust(uploaded_pdf)
        if not extracted.empty:
            st.session_state.pdf_data = extracted
            st.success(f"{len(extracted)} سفارش استخراج شد")
            st.dataframe(extracted, use_container_width=True)
        else:
            st.warning("داده‌ای یافت نشد")

# مرحله ۲: آپلود اکسل
if st.session_state.pdf_data is not None:
    st.subheader("مرحله ۲: آپلود اکسل")
    st.info("ستون A = کد سفارش، ستون B = شناسه محموله")
    
    uploaded_excel = st.file_uploader("فایل اکسل", type=["xlsx", "xls"])
    
    if uploaded_excel:
        excel_df = pd.read_excel(uploaded_excel, dtype=str)
        excel_df = excel_df.iloc[:, [0, 1]]
        excel_df.columns = ['کد سفارش', 'شناسه محموله']
        
        pdf_df = st.session_state.pdf_data.copy()
        pdf_df['merge_key'] = pdf_df['شماره سفارش']
        excel_df['merge_key'] = excel_df['کد سفارش'].str.extract(r'(\d{9})', expand=False)
        
        merged = pd.merge(pdf_df, excel_df, on='merge_key', how='inner')
        
        if not merged.empty:
            final = merged[['کد سفارش', 'کد رهگیری', 'شناسه محموله']].copy()
            final.columns = ['شماره سفارش', 'کد رهگیری', 'شناسه محموله']
            st.session_state.merged_data = final
            st.success(f"{len(final)} سفارش تطبیق یافت")
            st.dataframe(final, use_container_width=True)
        else:
            st.error("تطبیقی یافت نشد")

# مرحله ۳: ارسال به API
if st.session_state.merged_data is not None and not st.session_state.merged_data.empty:
    st.subheader("مرحله ۳: ارسال به API")
    
    if st.button("ارسال به دیجی‌کالا و ذخیره در دیتابیس", type="primary"):
        results = []
        updated_in_db = 0
        total = len(st.session_state.merged_data)
        
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        for i, row in st.session_state.merged_data.iterrows():
            order_id_match = re.search(r'(\d{9})', str(row['شماره سفارش']))
            if not order_id_match:
                continue
            
            order_id = order_id_match.group(1)
            status_text.text(f"ارسال {i+1}/{total}: سفارش {order_id}")
            progress_bar.progress((i + 1) / total)
            
            try:
                shipment_clean = str(row['شناسه محموله']).translate(str.maketrans('۰۱۲۳۴۵۶۷۸۹', '0123456789'))
                shipment_id = int(float(shipment_clean))
            except:
                results.append({"سفارش": order_id, "وضعیت": "خطا", "پیام": "شناسه نامعتبر"})
                continue
            
            response = send_tracking_code_to_api(shipment_id, row['کد رهگیری'])
            
            if isinstance(response, requests.Response) and response.status_code in [200, 201]:
                status = "موفق"
                msg = "ثبت شد"
                mask = st.session_state.orders_df['کد سفارش'].astype(str) == order_id
                if mask.any():
                    st.session_state.orders_df.loc[mask, 'کد رهگیری'] = row['کد رهگیری']
                    updated_in_db += 1
            else:
                status = "ناموفق"
                msg = str(response)[:100]
            
            results.append({"سفارش": order_id, "کد": row['کد رهگیری'], "وضعیت": status, "پیام": msg})
            time.sleep(0.5)
    
        progress_bar.empty()
        status_text.empty()
        
        if updated_in_db > 0:
            save_database(st.session_state.orders_df)
            st.success(f"{updated_in_db} کد رهگیری در دیتابیس ذخیره شد")
        
        st.subheader("گزارش:")
        results_df = pd.DataFrame(results)
        success = len(results_df[results_df['وضعیت'] == 'موفق'])
        
        col1, col2 = st.columns(2)
        col1.metric("موفق", success)
        col2.metric("ناموفق", len(results_df) - success)
        
        st.dataframe(results_df, use_container_width=True)