# backend/test_orders_df.py
"""
اسکریپت تست برای بررسی DataFrame سفارشات
"""

import sys
import os

# اضافه کردن مسیر backend به path
sys.path.insert(0, os.path.dirname(__file__))

from utils.api_core import get_all_orders, orders_to_dataframe, load_session_cookies, format_cookies_for_requests

print("=" * 60)
print("🧪 تست DataFrame سفارشات")
print("=" * 60)

# دریافت سفارشات
print("\n1️⃣ دریافت سفارشات از API...")
orders_sbs = get_all_orders(use_ship_by_seller=True)
orders_mp = get_all_orders(use_ship_by_seller=False)

# ترکیب
all_orders_dict = {o['shipmentId']: o for o in orders_sbs}
all_orders_dict.update({o['shipmentId']: o for o in orders_mp})

print(f"✅ تعداد سفارشات منحصر به فرد: {len(all_orders_dict)}")

# تبدیل به DataFrame
print("\n2️⃣ تبدیل به DataFrame...")
cookies_list = load_session_cookies()
cookies_dict = format_cookies_for_requests(cookies_list) if cookies_list else None

df = orders_to_dataframe(
    list(all_orders_dict.values()),
    fetch_details=False,
    cookies_dict=cookies_dict
)

print(f"✅ تعداد ردیف‌های DataFrame: {len(df)}")
print(f"✅ ستون‌ها: {list(df.columns)}")

# بررسی سفارشات چندقلمی
print("\n3️⃣ بررسی سفارشات چندقلمی...")
grouped = df.groupby('شناسه محموله')

multi_item_orders = []
for shipment_id, group in grouped:
    if len(group) > 1:
        multi_item_orders.append({
            'shipment_id': shipment_id,
            'items_count': len(group),
            'customer': group.iloc[0]['نام مشتری'],
            'products': group['عنوان سفارش'].tolist()
        })

print(f"\n📦 تعداد سفارشات چندقلمی: {len(multi_item_orders)}")

if multi_item_orders:
    print("\n🔍 نمونه سفارشات چندقلمی:")
    for i, order in enumerate(multi_item_orders[:5], 1):  # نمایش 5 مورد اول
        print(f"\n  {i}. شناسه: {order['shipment_id']}")
        print(f"     مشتری: {order['customer']}")
        print(f"     تعداد اقلام: {order['items_count']}")
        print(f"     محصولات:")
        for j, product in enumerate(order['products'], 1):
            print(f"       {j}. {product[:50]}...")

# نمایش یک نمونه کامل
if multi_item_orders:
    print("\n" + "=" * 60)
    print("📋 جزئیات کامل یک سفارش چندقلمی:")
    print("=" * 60)
    
    sample_shipment = multi_item_orders[0]['shipment_id']
    sample_group = grouped.get_group(sample_shipment)
    
    print(f"\nشناسه محموله: {sample_shipment}")
    print(f"تعداد اقلام: {len(sample_group)}\n")
    
    for idx, (_, row) in enumerate(sample_group.iterrows(), 1):
        print(f"آیتم {idx}:")
        print(f"  - عنوان: {row['عنوان سفارش']}")
        print(f"  - کد محصول: {row.get('کد محصول (DKP)', 'N/A')}")
        print(f"  - تعداد: {row.get('تعداد', 'N/A')}")
        print(f"  - مبلغ: {row.get('مبلغ', 'N/A')}")
        print()

print("\n" + "=" * 60)
print("✅ تست تمام شد!")
print("=" * 60)