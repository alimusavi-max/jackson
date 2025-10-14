import streamlit as st
import sys
import os

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
if CURRENT_DIR not in sys.path:
    sys.path.insert(0, CURRENT_DIR)

from utils.data_manager import load_database
from utils.sms_core import load_sent_orders

st.set_page_config(layout="wide", page_title="سیستم مدیریت سفارشات دیجی‌کالا")

if 'orders_df' not in st.session_state:
    st.session_state.orders_df = load_database()

if 'sender_info' not in st.session_state:
    st.session_state.sender_info = {
        'name': 'نام فروشگاه شما',
        'address': 'آدرس شما',
        'postal_code': '1234567890',
        'phone': '09123456789'
    }

if 'pdf_data' not in st.session_state:
    st.session_state.pdf_data = None

if 'merged_data' not in st.session_state:
    st.session_state.merged_data = None

st.title("سیستم یکپارچه مدیریت سفارشات دیجی‌کالا")

sent_codes = load_sent_orders()
st.info(f"تاکنون برای {len(sent_codes)} کد رهگیری پیامک ارسال شده است.")

st.markdown("---")
st.subheader("خوش آمدید!")
st.write("از منوی سمت چپ، صفحه مورد نظر خود را انتخاب کنید.")

# نمایش آمار کلی
if not st.session_state.orders_df.empty:
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("تعداد سفارشات", f"{len(st.session_state.orders_df):,}")
    with col2:
        st.metric("مشتریان منحصر به فرد", f"{st.session_state.orders_df['کد سفارش'].nunique():,}")
    with col3:
        # تبدیل مبلغ به عدد قبل از sum
        try:
            total_amount = pd.to_numeric(st.session_state.orders_df['مبلغ'], errors='coerce').sum()
            st.metric("مجموع فروش", f"{total_amount:,.0f} تومان")
        except:
            st.metric("مجموع فروش", "نامشخص")