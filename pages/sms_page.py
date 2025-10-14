# pages/sms_page.py

import sys
import os
if os.path.dirname(os.path.dirname(os.path.abspath(__file__))) not in sys.path:
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import streamlit as st
import pandas as pd
from datetime import datetime
from utils.sms_core import (
    load_sent_orders, save_sent_order, check_kde_connect_cli, 
    send_sms, overwrite_sent_orders, get_sms_template
)
from utils.constants import UNKNOWN_TRACKING_CODE
from utils.data_manager import load_database
from utils.helpers import persian_to_gregorian

st.set_page_config(layout="wide", page_title="مدیریت پیامک")

if 'orders_df' not in st.session_state:
    st.session_state.orders_df = load_database()

st.header("📱 مدیریت ارسال پیامک سفارشات")

is_connected, status_message = check_kde_connect_cli()
if is_connected:
    st.success(status_message, icon="✅")
else:
    st.error(status_message, icon="❌")

tab1, tab2, tab3 = st.tabs(["🚀 ارسال خودکار", "✉️ ارسال دستی", "🗂️ مدیریت لیست ارسال"])

# --- تب ۱: ارسال خودکار (کد کامل بازیابی شد) ---
with tab1:
    st.subheader("ارسال خودکار پیامک برای محموله‌های جدید")
    
    if st.session_state.orders_df.empty:
        st.warning("ابتدا سفارشات را از صفحه مربوطه دریافت کنید.")
    else:
        sent_codes = load_sent_orders()
        df = st.session_state.orders_df.copy()
        
        df_trackable = df[
            df['کد رهگیری'].notna() &
            (df['کد رهگیری'] != '') &
            (df['کد رهگیری'] != UNKNOWN_TRACKING_CODE)
        ].copy()

        df_new = df_trackable[~df_trackable['کد رهگیری'].isin(sent_codes)]
        
        st.info(f"{len(df_trackable)} محموله دارای کد رهگیری | {len(df_new)} محموله جدید برای ارسال پیامک")
        
        if not df_new.empty:
            df_display = df_new[['نام مشتری', 'شناسه محموله', 'کد رهگیری', 'وضعیت', 'شماره تلفن']].drop_duplicates()
            st.dataframe(df_display, use_container_width=True)
            
            is_dry_run = st.checkbox("✅ فقط شبیه‌سازی کن (Dry Run)", value=True)
            
            if st.button("شروع ارسال پیامک به محموله‌های جدید", type="primary", disabled=not is_connected):
                progress_bar = st.progress(0, "در حال ارسال...")
                log_placeholder = st.empty()
                log_messages = []
                
                total = len(df_display)
                for i, (_, row) in enumerate(df_display.iterrows()):
                    message = get_sms_template(row['نام مشتری'], row['کد رهگیری'])
                    success, msg = send_sms(row['شماره تلفن'], message, is_dry_run)
                    
                    if success:
                        log_messages.append(f"✅ {msg}")
                        if not is_dry_run:
                            save_sent_order(row['کد رهگیری'])
                    else:
                        log_messages.append(f"❌ {msg}")
                    
                    progress_bar.progress((i + 1) / total)
                    log_placeholder.markdown("\n\n".join(log_messages))
                
                st.success("عملیات ارسال تمام شد.")

# --- تب ۲: ارسال دستی (کد کامل بازیابی شد) ---
with tab2:
    st.subheader("ارسال دستی یک پیامک")
    sent_codes = load_sent_orders()
    with st.form("manual_sms_form"):
        name = st.text_input("نام مشتری")
        phone = st.text_input("شماره تلفن")
        tracking = st.text_input("کد رهگیری")
        submitted = st.form_submit_button("ارسال پیامک", disabled=not is_connected)
        if submitted:
            if not all([name, phone, tracking]):
                st.error("لطفاً تمام فیلدها را پر کنید.")
            elif tracking in sent_codes:
                st.warning("این کد رهگیری قبلاً در لیست ارسال شده‌ها بوده است.")
            else:
                message = get_sms_template(name, tracking)
                success, msg = send_sms(phone, message)
                if success:
                    save_sent_order(tracking)
                    st.success(msg)
                else:
                    st.error(msg)

# --- تب ۳: مدیریت لیست ارسال (نسخه اصلاح شده قبلی) ---
with tab3:
    st.subheader("مدیریت لیست ارسال (Exclusion List)")
    st.info("سفارشات را بین دو لیست جابجا کنید. سفارشاتی که در لیست 'ارسال شده‌ها' باشند، در تب 'ارسال خودکار' نمایش داده نخواهند شد.")

    sent_codes = load_sent_orders()
    df = st.session_state.orders_df.copy()
    
    df_trackable = df[df['کد رهگیری'].notna() & (df['کد رهگیری'] != '') & (df['کد رهگیری'] != UNKNOWN_TRACKING_CODE)].copy()
    df_trackable['تاریخ میلادی'] = pd.to_datetime(df_trackable['تاریخ ثبت'].apply(persian_to_gregorian), errors='coerce')

    df_excluded = df_trackable[df_trackable['کد رهگیری'].isin(sent_codes)]
    df_sendable = df_trackable[~df_trackable['کد رهگیری'].isin(sent_codes)]

    col1, col2, col3 = st.columns([5, 1, 5])

    with col1:
        st.markdown("##### 📬 سفارشات آماده ارسال")
        
        f_col1, f_col2 = st.columns(2)
        with f_col1:
            status_filter = st.multiselect("فیلتر وضعیت:", df_sendable['وضعیت'].unique())
        with f_col2:
            min_date, max_date = df_sendable['تاریخ میلادی'].min(), df_sendable['تاریخ میلادی'].max()
            if pd.isna(min_date) or pd.isna(max_date): min_date, max_date = datetime.now(), datetime.now()
            date_range = st.date_input("فیلتر تاریخ:", value=(min_date, max_date), min_value=min_date, max_value=max_date)

        df_sendable_filtered = df_sendable.copy()
        if status_filter: df_sendable_filtered = df_sendable_filtered[df_sendable_filtered['وضعیت'].isin(status_filter)]
        if len(date_range) == 2:
            start_date, end_date = pd.to_datetime(date_range[0]), pd.to_datetime(date_range[1])
            df_sendable_filtered = df_sendable_filtered[df_sendable_filtered['تاریخ میلادی'].between(start_date, end_date, inclusive='both')]
        
        options_sendable = {f"{idx}: {row['کد سفارش']} - {row['نام مشتری']}": idx for idx, row in df_sendable_filtered.iterrows()}
        if st.checkbox("انتخاب همه آماده ارسال‌ها", key="select_all_sendable"):
             selected_indices_sendable = list(options_sendable.values())
        else:
             selected_indices_sendable = []
        
        selected_sendable = st.multiselect(
            "انتخاب برای افزودن به لیست ارسال شده‌ها:",
            options=options_sendable.keys(),
            default=[k for k,v in options_sendable.items() if v in selected_indices_sendable]
        )

    with col2:
        st.write("")
        st.write("")
        if st.button("⬅️ افزودن", use_container_width=True, help="سفارشات انتخاب شده را به لیست ارسال شده‌ها منتقل کن"):
            if selected_sendable:
                indices_to_move = [options_sendable[key] for key in selected_sendable]
                codes_to_add = set(df_sendable_filtered.loc[indices_to_move]['کد رهگیری'].unique())
                new_sent_codes = sent_codes.union(codes_to_add)
                overwrite_sent_orders(new_sent_codes)
                st.success(f"{len(codes_to_add)} سفارش به لیست ارسال شده‌ها اضافه شد.")
                st.rerun()
        
        if st.button("حذف ➡️", use_container_width=True, help="سفارشات انتخاب شده را از لیست ارسال شده‌ها حذف کن"):
            if 'selected_excluded' in st.session_state and st.session_state.selected_excluded:
                indices_to_move = [st.session_state.options_excluded[key] for key in st.session_state.selected_excluded]
                codes_to_remove = set(df_excluded.loc[indices_to_move]['کد رهگیری'].unique())
                new_sent_codes = sent_codes.difference(codes_to_remove)
                overwrite_sent_orders(new_sent_codes)
                st.success(f"{len(codes_to_remove)} سفارش از لیست ارسال شده‌ها حذف شد.")
                st.rerun()

    with col3:
        st.markdown("##### 📨 سفارشات در لیست ارسال شده‌ها")

        search_excluded = st.text_input("جستجو در ارسال شده‌ها (کد سفارش، نام، رهگیری):")
        df_excluded_filtered = df_excluded.copy()
        if search_excluded:
            df_excluded_filtered = df_excluded[df_excluded.apply(lambda row: search_excluded.lower() in str(row.to_list()).lower(), axis=1)]

        options_excluded = {f"{idx}: {row['کد سفارش']} - {row['نام مشتری']}": idx for idx, row in df_excluded_filtered.iterrows()}
        st.session_state.options_excluded = options_excluded

        if st.checkbox("انتخاب همه ارسال شده‌ها", key="select_all_excluded"):
            selected_indices_excluded = list(options_excluded.values())
        else:
            selected_indices_excluded = []
            
        selected_excluded = st.multiselect(
            "انتخاب برای حذف از لیست ارسال شده‌ها:",
            options=options_excluded.keys(),
            default=[k for k,v in options_excluded.items() if v in selected_indices_excluded],
            key="selected_excluded"
        )