import sys
import os
if os.path.dirname(os.path.dirname(os.path.abspath(__file__))) not in sys.path:
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import streamlit as st
from utils.data_manager import load_database

st.set_page_config(layout="wide", page_title="گزارشات و آمار")

if 'orders_df' not in st.session_state:
    st.session_state.orders_df = load_database()

st.header("📊 گزارشات و آمار")

if st.session_state.orders_df.empty:
    st.warning("⚠️ هیچ داده‌ای وجود ندارد")
else:
    df = st.session_state.orders_df.copy()
    
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("کل سفارشات", f"{len(df):,}")
    c2.metric("مشتریان", f"{df['کد سفارش'].nunique():,}")
    c3.metric("مجموع فروش", f"{df['مبلغ'].sum():,.0f} تومان")
    c4.metric("تنوع محصولات", f"{df['کد محصول (DKP)'].nunique():,}")
    
    st.markdown("---")
    
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("📈 وضعیت سفارشات")
        st.bar_chart(df['وضعیت'].value_counts())
    
    with col2:
        st.subheader("🏙️ توزیع جغرافیایی")
        st.bar_chart(df['شهر'].value_counts().head(10))
    
    st.subheader("🎯 محصولات پرفروش")
    product_stats = df.groupby('عنوان سفارش').agg({
        'تعداد': 'sum',
        'مبلغ': 'sum'
    }).sort_values('تعداد', ascending=False).head(10)
    st.dataframe(product_stats, use_container_width=True)