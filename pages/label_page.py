# pages/label_page.py

import sys
import os
if os.path.dirname(os.path.dirname(os.path.abspath(__file__))) not in sys.path:
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import streamlit as st
import pandas as pd
import io
import time
from datetime import datetime
import treepoem
from PIL import Image

# Make sure these paths are correct for your project structure
from utils.constants import LABELS_DIR
from utils.label_core import generate_label_portrait, generate_label_landscape, create_pdf_two_labels
from utils.api_core import get_customer_info
from utils.data_manager import load_database, load_sender_profiles, save_sender_profiles, save_database
from reportlab.lib.pagesizes import A5, landscape, portrait

st.set_page_config(layout="wide", page_title="ساخت برچسب پستی")

def process_labels(df_selected, sender_info, fetch_from_api, update_db, orientation, include_dm):
    labels = []
    progress_bar = st.progress(0)
    status_text = st.empty()
    updated_count = 0

    if df_selected.empty:
        st.warning("هیچ سفارشی برای پردازش انتخاب نشده است.")
        return

    total_rows = len(df_selected)

    for i, (_, row_selected) in enumerate(df_selected.iterrows()):
        shipment_id = row_selected['شناسه محموله']
        customer_name = row_selected.get('نام مشتری', row_selected.get('کد سفارش', ''))

        status_text.text(f"پردازش {i+1}/{total_rows}: {customer_name}")

        label_data = row_selected.to_dict()

        if fetch_from_api:
            api_data = get_customer_info(shipment_id)
            if api_data:
                label_data.update(api_data)
                if update_db and 'orders_df' in st.session_state:
                    db_mask = st.session_state.orders_df['شناسه محموله'] == shipment_id
                    if db_mask.any():
                        db_row_index = st.session_state.orders_df.index[db_mask].tolist()[0]
                        needs_update = False
                        for field, api_key in [('آدرس کامل', 'address'), ('کد پستی', 'postalCode'), ('شماره تلفن', 'phoneNumber')]:
                            db_value = st.session_state.orders_df.loc[db_row_index, field]
                            api_value = api_data.get(api_key)
                            if (pd.isna(db_value) or str(db_value).strip() in ['', 'نامشخص']) and (api_value and str(api_value).strip()):
                                st.session_state.orders_df.loc[db_row_index, field] = api_value
                                needs_update = True
                        if needs_update:
                            updated_count += 1
            else:
                st.warning(f"دریافت اطلاعات از API برای محموله {shipment_id} ناموفق بود.")

        if orientation == "عمودی (Portrait)":
            img = generate_label_portrait(row_selected['کد سفارش'], sender_info, label_data, include_datamatrix=include_dm)
        # The landscape function in the original file didn't include the improved product details,
        # so it's adjusted here to accept the full label_data like the portrait function.
        elif orientation == "افقی (Landscape)":
            img = generate_label_landscape(row_selected['کد سفارش'], sender_info, label_data)
        else: # This handles the case for Tab 3 where orientation is an empty string
            continue

        buf = io.BytesIO()
        img.save(buf, format="PNG")
        labels.append(io.BytesIO(buf.getvalue()))

        progress_bar.progress((i + 1) / total_rows)
        time.sleep(0.1)

    if updated_count > 0:
        save_database(st.session_state.orders_df)
        st.success(f"✅ پایگاه داده با اطلاعات جدید {updated_count} سفارش به‌روزرسانی و ذخیره شد.")

    if orientation:
        create_and_download_pdf(labels, orientation)

def create_and_download_pdf(labels, orientation):
    if not labels:
        st.warning("هیچ برچسبی برای ساخت PDF وجود ندارد.")
        return

    os.makedirs(LABELS_DIR, exist_ok=True)
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M")

    if orientation == "عمودی (Portrait)":
        file_name, page_size, button_label = f"labels_portrait_{timestamp}.pdf", portrait(A5), "📥 دانلود PDF عمودی"
    else:
        file_name, page_size, button_label = f"labels_landscape_{timestamp}.pdf", landscape(A5), "📥 دانلود PDF افقی"

    full_path = os.path.join(LABELS_DIR, file_name)
    create_pdf_two_labels(labels, full_path, page_size)

    with open(full_path, "rb") as f:
        st.download_button(button_label, f, file_name, "application/pdf")

    st.success(f"✅ {len(labels)} برچسب در پوشه '{LABELS_DIR}' ساخته شد!")

# --- UI and Main Logic ---
if 'orders_df' not in st.session_state: st.session_state.orders_df = load_database()
if 'sender_info' not in st.session_state: st.session_state.sender_info = {}

st.header("🏷️ ساخت برچسب پستی")

# Sender Profile Management... (No changes here)
st.subheader("مدیریت پروفایل‌های فرستنده")
profiles = load_sender_profiles()
col1, col2 = st.columns([2, 1])
with col1:
    profile_keys = ["جدید"] + list(profiles.keys())
    selected_profile = st.selectbox("انتخاب پروفایل:", profile_keys, key="profile_selector")
with col2:
    st.write("")
    st.write("")
    if selected_profile != "جدید" and st.button("🗑️ حذف این پروفایل", type="secondary"):
        del profiles[selected_profile]
        save_sender_profiles(profiles)
        st.success(f"پروفایل '{selected_profile}' حذف شد.")
        st.rerun()

if selected_profile != "جدید": st.session_state.sender_info = profiles[selected_profile].copy()

with st.expander("اطلاعات فرستنده", expanded=True):
    # Sender Info Inputs... (No changes here)
    c1, c2 = st.columns(2)
    with c1:
        sender_name = st.text_input("نام فرستنده", value=st.session_state.sender_info.get('name', ''), key="sender_name")
        sender_address = st.text_area("آدرس فرستنده", value=st.session_state.sender_info.get('address', ''), height=100, key="sender_address")
    with c2:
        sender_postal = st.text_input("کد پستی فرستنده", value=st.session_state.sender_info.get('postal_code', ''), key="sender_postal")
        sender_phone = st.text_input("شماره تلفن فرستنده", value=st.session_state.sender_info.get('phone', ''), key="sender_phone")

    st.session_state.sender_info = {'name': sender_name, 'address': sender_address, 'postal_code': sender_postal, 'phone': sender_phone}

    sc1, sc2, sc3 = st.columns([2, 1, 1])
    with sc1:
        profile_name = st.text_input("نام پروفایل برای ذخیره:", value=selected_profile if selected_profile != "جدید" else "", placeholder="مثال: فروشگاه تهران")
    with sc2:
        st.write("")
        st.write("")
        if st.button("💾 ذخیره پروفایل", type="primary"):
            if profile_name:
                profiles[profile_name] = st.session_state.sender_info.copy()
                save_sender_profiles(profiles)
                st.success(f"✅ پروفایل '{profile_name}' ذخیره شد.")
                time.sleep(1)
                st.rerun()
            else:
                st.error("لطفاً نام پروفایل را وارد کنید.")
    with sc3:
        # Sender Barcode... (No changes here)
        st.write("")
        st.write("")
        if st.button("📊 ساخت بارکد"):
            if all(st.session_state.sender_info.values()):
                sender_dm_string = f"{sender_name}\t3530217018\t{sender_postal}\t\t{sender_phone}"
                try:
                    sender_dm_image = treepoem.generate_barcode(barcode_type='datamatrix', data=sender_dm_string)
                    st.image(sender_dm_image, caption="بارکد اطلاعات فرستنده", width=150)
                except Exception as e:
                    st.error(f"خطا در ساخت بارکد: {e}")
            else:
                st.warning("لطفاً تمام اطلاعات فرستنده را تکمیل کنید.")

st.markdown("---")
st.subheader("انتخاب سفارش‌ها برای چاپ برچسب")
tab1, tab2, tab3 = st.tabs(["از دیتابیس", "از فایل اکسل", "به‌روزرسانی اطلاعات"])

# --- Helper Functions for Data Aggregation ---
def aggregate_products_as_list(group):
    group['تعداد'] = pd.to_numeric(group['تعداد'], errors='coerce').fillna(1).astype(int)
    # Ensure 'عنوان سفارش' exists, provide a default if not.
    group['عنوان سفارش'] = group.get('عنوان سفارش', 'نامشخص')
    return group[['عنوان سفارش', 'تعداد']].rename(columns={'عنوان سفارش': 'name', 'تعداد': 'qty'}).to_dict('records')

def aggregate_products_for_display(group):
    final_strings = []
    for _, row in group.iterrows():
        quantity_val = pd.to_numeric(row['تعداد'], errors='coerce')
        quantity = 1 if pd.isna(quantity_val) else int(quantity_val)
        product_name = row.get('عنوان سفارش', 'نامشخص')
        final_strings.append(f"{product_name} ({quantity} عدد)")
    return '\n'.join(final_strings)

with tab1:
    if st.session_state.orders_df.empty:
        st.warning("دیتابیس خالی است.")
    else:
        df = st.session_state.orders_df.copy()
        # Filter UI... (No changes)
        with st.expander("🔍 فیلتر سفارش‌ها", expanded=True):
            f_col1, f_col2, f_col3 = st.columns(3)
            with f_col1:
                search_term = st.text_input("جستجو (کد سفارش، نام، محصول):", key="db_search_label")
                all_statuses = ['همه'] + sorted(df['وضعیت'].dropna().unique().tolist())
                selected_status = st.selectbox("وضعیت:", all_statuses, key="db_status_label")
            with f_col2:
                all_cities = ['همه'] + sorted(df['شهر'].dropna().unique().tolist())
                selected_city = st.selectbox("شهر:", all_cities, key="db_city_label")
                all_provinces = ['همه'] + sorted(df['استان'].dropna().unique().tolist())
                selected_province = st.selectbox("استان:", all_provinces, key="db_province_label")
            with f_col3:
                tracking_filter = st.selectbox("کد رهگیری:", ["همه", "دارای کد", "بدون کد"], key="db_tracking_label")
                address_filter = st.selectbox("آدرس کامل:", ["همه", "دارای آدرس", "بدون آدرس"], key="db_address_label")

        # Filtering Logic... (No changes)
        filtered_df = df.copy()
        if search_term: filtered_df = filtered_df[filtered_df.apply(lambda row: search_term in str(row.to_list()), axis=1)]
        if selected_status != 'همه': filtered_df = filtered_df[filtered_df['وضعیت'] == selected_status]
        if selected_city != 'همه': filtered_df = filtered_df[filtered_df['شهر'] == selected_city]
        if selected_province != 'همه': filtered_df = filtered_df[filtered_df['استان'] == selected_province]
        if tracking_filter == "دارای کد": filtered_df = filtered_df[filtered_df['کد رهگیری'].str.strip().astype(bool)]
        elif tracking_filter == "بدون کد": filtered_df = filtered_df[~filtered_df['کد رهگیری'].str.strip().astype(bool)]
        if address_filter == "دارای آدرس": filtered_df = filtered_df[filtered_df['آدرس کامل'].str.strip().astype(bool)]
        elif address_filter == "بدون آدرس": filtered_df = filtered_df[~filtered_df['آدرس کامل'].str.strip().astype(bool)]

        st.info(f"📊 {len(filtered_df):,} سفارش از {len(df):,} یافت شد")

        if not filtered_df.empty:
            product_details_list = filtered_df.groupby('شناسه محموله').apply(aggregate_products_as_list).rename('products').reset_index()
            product_descriptions = filtered_df.groupby('شناسه محموله').apply(aggregate_products_for_display).rename('شرح کامل محصولات').reset_index()

            grouped_df = filtered_df.groupby('شناسه محموله').agg({'کد سفارش': 'first', 'نام مشتری': 'first', 'شهر': 'first', 'آدرس کامل': 'first', 'کد پستی': 'first', 'شماره تلفن': 'first'}).reset_index()
            grouped_df = pd.merge(grouped_df, product_descriptions, on='شناسه محموله')
            grouped_df = pd.merge(grouped_df, product_details_list, on='شناسه محموله')

            display_options = [f"{row['کد سفارش']} - {row['نام مشتری']} ({row.get('شهر', '؟')})" for _, row in grouped_df.iterrows()]
            selected_indices = st.multiselect("انتخاب سفارشات:", options=range(len(grouped_df)), format_func=lambda i: display_options[i], default=list(range(len(grouped_df))))

            if selected_indices:
                selected_df = grouped_df.iloc[selected_indices]
                st.dataframe(selected_df[['کد سفارش', 'نام مشتری', 'شهر', 'شرح کامل محصولات']], use_container_width=True, height=300, hide_index=True)

                opt_col1, opt_col2 = st.columns(2)
                with opt_col1:
                    orientation_db = st.radio("حالت چاپ:", ["عمودی (Portrait)", "افقی (Landscape)"], key="orientation_db")
                    fetch_api_db = st.checkbox("🔄 دریافت اطلاعات از API", value=True, key="fetch_api_db")
                with opt_col2:
                    include_dm_db = st.checkbox("افزودن بارکد Data Matrix گیرنده", value=True, key="include_dm_db")

                if st.button("🖨️ چاپ برچسب برای سفارشات انتخابی", type="primary", key="print_from_db"):
                    process_labels(selected_df, st.session_state.sender_info, fetch_from_api=fetch_api_db, update_db=True, orientation=orientation_db, include_dm=include_dm_db)

with tab2:
    st.info("💡 اطلاعات مشتری (آدرس، کد پستی،...) از API دریافت و سپس برچسب ساخته می‌شود.")
    excel_file = st.file_uploader("فایل اکسل سفارش‌ها", type=["xlsx"], key="excel_upload")

    opt_col3, opt_col4 = st.columns(2)
    with opt_col3:
        orientation_excel = st.radio("حالت چاپ:", ["عمودی (Portrait)", "افقی (Landscape)"], key="orientation_excel")
        update_db_excel = st.checkbox("💾 ذخیره اطلاعات دریافتی در دیتابیس", value=True, key="update_db_excel")
    with opt_col4:
        include_dm_excel = st.checkbox("افزودن بارکد Data Matrix گیرنده", value=True, key="include_dm_excel")

    if st.button("🖨️ شروع پردازش از اکسل", type="primary", key="print_from_excel") and excel_file:
        excel_df = pd.read_excel(excel_file, dtype=str)
        product_list_excel = excel_df.groupby('شناسه محموله').apply(aggregate_products_as_list).rename('products').reset_index()
        excel_grouped = excel_df.groupby('شناسه محموله').first().reset_index()
        excel_final = pd.merge(excel_grouped, product_list_excel, on='شناسه محموله')
        process_labels(excel_final, st.session_state.sender_info, fetch_from_api=True, update_db=update_db_excel, orientation=orientation_excel, include_dm=include_dm_excel)

with tab3:
    st.markdown("### 🔄 به‌روزرسانی اطلاعات مشتریان از API")
    st.info("این بخش برای سفارشاتی که آدرس یا اطلاعات تماس ناقص دارند مفید است.")

    col1, col2 = st.columns(2)
    with col1:
        update_option = st.radio("چه سفارشاتی به‌روزرسانی شوند؟", ["فقط سفارشات بدون آدرس", "فقط سفارشات بدون کد پستی", "فقط سفارشات بدون شماره تلفن"], key="update_option")
    with col2:
        max_updates = st.number_input("حداکثر تعداد برای به‌روزرسانی:", min_value=1, max_value=1000, value=50, step=10, key="max_updates")

    if st.button("🔄 شروع به‌روزرسانی", type="primary", key="start_update"):
        df_update = st.session_state.orders_df.copy()
        if update_option == "فقط سفارشات بدون آدرس": target_df = df_update[df_update['آدرس کامل'].isna() | (df_update['آدرس کامل'] == '') | (df_update['آدرس کامل'] == 'نامشخص')]
        elif update_option == "فقط سفارشات بدون کد پستی": target_df = df_update[df_update['کد پستی'].isna() | (df_update['کد پستی'] == '') | (df_update['کد پستی'] == 'نامشخص')]
        else: target_df = df_update[df_update['شماره تلفن'].isna() | (df_update['شماره تلفن'] == '') | (df_update['شماره تلفن'] == 'نامشخص')]

        target_df = target_df.head(max_updates)

        if target_df.empty:
            st.warning("هیچ سفارشی برای به‌روزرسانی یافت نشد.")
        else:
            st.info(f"🔍 {len(target_df)} سفارش برای به‌روزرسانی یافت شد. شروع عملیات...")
            prods_list = target_df.groupby('شناسه محموله').apply(aggregate_products_as_list).rename('products').reset_index()
            grouped_target = target_df.groupby('شناسه محموله').first().reset_index()
            final_target = pd.merge(grouped_target, prods_list, on='شناسه محموله')

            # Pass orientation="" so no PDF is generated
            process_labels(final_target, st.session_state.sender_info, fetch_from_api=True, update_db=True, orientation="", include_dm=False)
            st.success("عملیات به‌روزرسانی دیتابیس تکمیل شد.")