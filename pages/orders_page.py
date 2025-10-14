# pages/orders_page.py

import sys
import os
if os.path.dirname(os.path.dirname(os.path.abspath(__file__))) not in sys.path:
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import streamlit as st
import pandas as pd
import time
import numpy as np
from datetime import datetime, timedelta
from utils.data_manager import save_database, load_database, to_excel
from utils.api_core import get_all_orders, orders_to_dataframe
from utils.constants import UNIQUE_KEY_COLS
from utils.helpers import normalize_id, persian_to_gregorian

st.set_page_config(layout="wide", page_title="دریافت و آرشیو سفارشات")

if 'orders_df' not in st.session_state:
    st.session_state.orders_df = load_database()

st.header("دریافت و آرشیو سفارشات")
st.metric("تعداد کل رکوردها", f"{len(st.session_state.orders_df):,} رکورد")

# بخش فیلتر پیشرفته
st.markdown("---")
st.subheader("فیلتر پیشرفته")

df = st.session_state.orders_df.copy()

if not df.empty:
    with st.expander("تنظیمات فیلتر", expanded=True):
        col1, col2, col3 = st.columns(3)
        
        with col1:
            search_term = st.text_input(
                "جستجو (کد سفارش، نام مشتری، عنوان محصول):",
                placeholder="حداقل 2 حرف..."
            )
            all_statuses = ['همه'] + sorted(df['وضعیت'].dropna().unique().tolist())
            selected_status = st.selectbox("وضعیت سفارش:", all_statuses)
        
        with col2:
            all_cities = ['همه'] + sorted(df['شهر'].dropna().unique().tolist())
            selected_city = st.selectbox("شهر:", all_cities)
            all_provinces = ['همه'] + sorted(df['استان'].dropna().unique().tolist())
            selected_province = st.selectbox("استان:", all_provinces)
        
        with col3:
            tracking_filter = st.selectbox(
                "وضعیت کد رهگیری:",
                ["همه", "دارای کد رهگیری", "بدون کد رهگیری"]
            )
            address_filter = st.selectbox(
                "وضعیت آدرس:",
                ["همه", "دارای آدرس کامل", "بدون آدرس کامل"]
            )
    
    filtered_df = df.copy()
    
    if search_term and len(search_term) >= 2:
        search_cols = ['کد سفارش', 'شناسه محموله', 'نام مشتری', 'عنوان سفارش']
        mask = filtered_df[search_cols].fillna('').astype(str).apply(
            lambda row: row.str.contains(search_term, case=False, na=False).any(),
            axis=1
        )
        filtered_df = filtered_df[mask]
    
    if selected_status != 'همه':
        filtered_df = filtered_df[filtered_df['وضعیت'] == selected_status]
    
    if selected_city != 'همه':
        filtered_df = filtered_df[filtered_df['شهر'] == selected_city]
    
    if selected_province != 'همه':
        filtered_df = filtered_df[filtered_df['استان'] == selected_province]
    
    if tracking_filter == "دارای کد رهگیری":
        filtered_df = filtered_df[filtered_df['کد رهگیری'].notna() & (filtered_df['کد رهگیری'] != '') & (filtered_df['کد رهگیری'] != 'نامشخص')]
    elif tracking_filter == "بدون کد رهگیری":
        filtered_df = filtered_df[filtered_df['کد رهگیری'].isna() | (filtered_df['کد رهگیری'] == '') | (filtered_df['کد رهگیری'] == 'نامشخص')]
    
    if address_filter == "دارای آدرس کامل":
        filtered_df = filtered_df[filtered_df['آدرس کامل'].notna() & (filtered_df['آدرس کامل'] != '') & (filtered_df['آدرس کامل'] != 'نامشخص')]
    elif address_filter == "بدون آدرس کامل":
        filtered_df = filtered_df[filtered_df['آدرس کامل'].isna() | (filtered_df['آدرس کامل'] == '') | (filtered_df['آدرس کامل'] == 'نامشخص')]
    
    st.success(f"تعداد رکوردهای فیلتر شده: **{len(filtered_df):,}** از **{len(df):,}**")
    
    if len(filtered_df) > 0:
        excel_data = to_excel(filtered_df)
        st.download_button(
            label=f"دانلود اکسل ({len(filtered_df):,} ردیف)",
            data=excel_data,
            file_name=f'orders_filtered_{len(filtered_df)}.xlsx',
            mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            type="secondary"
        )
    
    st.markdown("---")
    st.subheader("نمایش داده‌ها")
    
    display_columns = [
        "کد سفارش", "شناسه محموله", "تصویر محصول", "عنوان سفارش", 
        "تعداد", "وضعیت", "نام مشتری", "مبلغ", "استان", "شهر", 
        "آدرس کامل", "کد پستی", "شماره تلفن", "کد رهگیری", "تاریخ ثبت"
    ]
    existing_columns = [col for col in display_columns if col in filtered_df.columns]
    
    st.dataframe(
        filtered_df[existing_columns],
        column_config={
            "تصویر محصول": st.column_config.ImageColumn("تصویر", width="small"),
            "مبلغ": st.column_config.NumberColumn("مبلغ", format="%d تومان"),
            "آدرس کامل": st.column_config.TextColumn("آدرس", width="large")
        },
        use_container_width=True,
        height=500,
        hide_index=True
    )

else:
    st.info("پایگاه داده خالی است.")

st.markdown("---")
st.subheader("همگام‌سازی با API")

fetch_full_details = st.checkbox("دریافت اطلاعات کامل مشتری (آدرس، تلفن و...)", value=False)

if st.button("دریافت و همگام‌سازی سفارش‌ها", type="primary"):
    orders_sbs = get_all_orders(True)
    orders_mp = get_all_orders(False)

    all_orders_dict = {o['shipmentId']: o for o in orders_sbs}
    all_orders_dict.update({o['shipmentId']: o for o in orders_mp})

    fresh_df = orders_to_dataframe(list(all_orders_dict.values()), fetch_full_details)

    if not fresh_df.empty:
        for col in UNIQUE_KEY_COLS:
            if col in fresh_df.columns:
                fresh_df[col] = fresh_df[col].apply(normalize_id)

        db_df = st.session_state.orders_df.copy()
        cols_to_preserve = ['کد رهگیری', 'آدرس کامل', 'کد پستی', 'شماره تلفن', 'نام مشتری']
        
        if not db_df.empty:
            for col in UNIQUE_KEY_COLS:
                if col in db_df.columns:
                    db_df[col] = db_df[col].apply(normalize_id)
            
            preserved_data = db_df[UNIQUE_KEY_COLS + cols_to_preserve].copy()
            
            def is_valid_value(val):
                if pd.isna(val): return False
                val_str = str(val).strip()
                return val_str and val_str not in ['', 'نامشخص', 'ناشناخته', 'nan', 'None']
            
            mask = preserved_data[cols_to_preserve].apply(lambda row: any(is_valid_value(v) for v in row), axis=1)
            preserved_data = preserved_data[mask]
            
            if not preserved_data.empty:
                fresh_df = pd.merge(fresh_df, preserved_data, on=UNIQUE_KEY_COLS, how='left', suffixes=('_new', '_old'))
                
                for col in cols_to_preserve:
                    if f'{col}_old' in fresh_df.columns:
                        fresh_df[col] = fresh_df.apply(
                            lambda row: row[f'{col}_old'] if is_valid_value(row[f'{col}_old']) and not is_valid_value(row[f'{col}_new']) else row[f'{col}_new'],
                            axis=1
                        )
                        fresh_df.drop(columns=[f'{col}_old', f'{col}_new'], inplace=True)
        
        fresh_df = fresh_df.drop_duplicates(subset=UNIQUE_KEY_COLS, keep='first')
        
        if not db_df.empty:
            fresh_df['_temp_key'] = fresh_df[UNIQUE_KEY_COLS].apply(lambda x: '|||'.join(x.astype(str)), axis=1)
            db_df['_temp_key'] = db_df[UNIQUE_KEY_COLS].apply(lambda x: '|||'.join(x.astype(str)), axis=1)
            
            existing_keys = set(db_df['_temp_key'])
            to_update = fresh_df[fresh_df['_temp_key'].isin(existing_keys)].copy()
            to_add = fresh_df[~fresh_df['_temp_key'].isin(existing_keys)].copy()
            
            db_df = db_df[~db_df['_temp_key'].isin(to_update['_temp_key'])]
            final_df = pd.concat([db_df, to_update, to_add], ignore_index=True)
            final_df.drop(columns=['_temp_key'], inplace=True, errors='ignore')
            
            new_count = len(to_add)
            updated_count = len(to_update)
        else:
            final_df = fresh_df
            new_count = len(fresh_df)
            updated_count = 0

        final_df['تاریخ ثبت میلادی'] = pd.to_datetime(final_df['تاریخ ثبت'].apply(persian_to_gregorian), errors='coerce')
        final_df = final_df.sort_values(by='تاریخ ثبت میلادی', ascending=False, na_position='last').drop(columns=['تاریخ ثبت میلادی'])

        save_database(final_df)
        st.session_state.orders_df = final_df
        
        st.success("همگام‌سازی موفق")
        col1, col2, col3 = st.columns(3)
        col1.metric("مجموع", f"{len(final_df):,}")
        col2.metric("جدید", f"{new_count:,}")
        col3.metric("به‌روزرسانی", f"{updated_count:,}")
        
        time.sleep(2)
        st.rerun()

st.markdown("---")
with st.expander("ابزارهای پایگاه داده"):
    st.warning("این عملیات فایل را مستقیماً تغییر می‌دهد.")
    if st.button("پاکسازی رکوردهای تکراری", type="primary"):
        df_to_clean = st.session_state.orders_df.copy()
        if not df_to_clean.empty:
            initial_count = len(df_to_clean)
            
            for col in UNIQUE_KEY_COLS:
                if col in df_to_clean.columns:
                    df_to_clean[col] = df_to_clean[col].apply(normalize_id)
            
            df_to_clean['priority'] = np.where(
                (df_to_clean['آدرس کامل'].notna()) & (df_to_clean['آدرس کامل'] != 'نامشخص') & (df_to_clean['آدرس کامل'] != ''), 1, 2
            )
            df_to_clean.sort_values(by=UNIQUE_KEY_COLS + ['priority'], ascending=True, inplace=True)
            cleaned_df = df_to_clean.drop_duplicates(subset=UNIQUE_KEY_COLS, keep='first').drop(columns=['priority'])
            
            final_count = len(cleaned_df)
            removed_count = initial_count - final_count
            
            save_database(cleaned_df)
            st.session_state.orders_df = cleaned_df
            st.success(f"پاکسازی کامل شد! {removed_count:,} رکورد حذف شد.")
            time.sleep(2)
            st.rerun()