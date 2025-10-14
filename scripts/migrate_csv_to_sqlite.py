# scripts/migrate_csv_to_sqlite.py
import sys
import os

# اضافه کردن مسیر backend به Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
backend_dir = os.path.join(os.path.dirname(current_dir), 'backend')
sys.path.insert(0, backend_dir)

import pandas as pd
from database.models import init_database, get_session, Order, OrderItem, SenderProfile
from datetime import datetime
import json

def migrate_orders_from_csv(csv_path="../data/orders_database_complete.csv"):
    """انتقال سفارشات از CSV به SQLite"""
    print("📂 در حال خواندن فایل CSV...")
    
    # تصحیح مسیر نسبی
    if not os.path.isabs(csv_path):
        csv_path = os.path.join(os.path.dirname(current_dir), csv_path.replace('../', ''))
    
    if not os.path.exists(csv_path):
        print(f"❌ فایل CSV در مسیر {csv_path} یافت نشد!")
        return
    
    df = pd.read_csv(csv_path, encoding='utf-8-sig', dtype=str)
    
    # ایجاد دیتابیس
    db_path = os.path.join(os.path.dirname(current_dir), 'data', 'digikala_sales.db')
    engine = init_database(db_path)
    session = get_session(engine)
    
    print(f"📊 تعداد رکوردهای CSV: {len(df)}")
    
    # گروه‌بندی بر اساس شناسه محموله
    grouped = df.groupby('شناسه محموله')
    
    orders_created = 0
    items_created = 0
    
    for shipment_id, group in grouped:
        first_row = group.iloc[0]
        
        # بررسی وجود سفارش
        existing_order = session.query(Order).filter_by(shipment_id=str(shipment_id)).first()
        
        if existing_order:
            order = existing_order
        else:
            # ایجاد سفارش جدید
            order = Order(
                order_code=str(first_row['کد سفارش']),
                shipment_id=str(shipment_id),
                customer_name=str(first_row.get('نام مشتری', '')),
                customer_phone=str(first_row.get('شماره تلفن', '')),
                status=str(first_row.get('وضعیت', '')),
                province=str(first_row.get('استان', '')),
                city=str(first_row.get('شهر', '')),
                full_address=str(first_row.get('آدرس کامل', '')),
                postal_code=str(first_row.get('کد پستی', '')),
                tracking_code=str(first_row.get('کد رهگیری', '')) if pd.notna(first_row.get('کد رهگیری')) else None,
                order_date_persian=str(first_row.get('تاریخ ثبت', ''))
            )
            session.add(order)
            session.flush()
            orders_created += 1
        
        # اضافه کردن اقلام
        for _, row in group.iterrows():
            existing_item = session.query(OrderItem).filter_by(
                order_id=order.id,
                product_code=str(row.get('کد محصول (DKP)', ''))
            ).first()
            
            if not existing_item:
                item = OrderItem(
                    order_id=order.id,
                    product_title=str(row.get('عنوان سفارش', '')),
                    product_code=str(row.get('کد محصول (DKP)', '')),
                    product_image=str(row.get('تصویر محصول', '')) if pd.notna(row.get('تصویر محصول')) else None,
                    quantity=int(float(row.get('تعداد', 1))) if pd.notna(row.get('تعداد')) else 1,
                    price=float(row.get('مبلغ', 0)) if pd.notna(row.get('مبلغ')) else 0
                )
                session.add(item)
                items_created += 1
    
    session.commit()
    
    print(f"✅ انتقال داده‌ها کامل شد!")
    print(f"   📦 سفارشات ایجاد شده: {orders_created}")
    print(f"   📋 اقلام ایجاد شده: {items_created}")
    
    session.close()


def migrate_sender_profiles(json_path="../data/sender_profiles.json"):
    """انتقال پروفایل‌های فرستنده"""
    print("\n📂 در حال خواندن پروفایل‌های فرستنده...")
    
    # تصحیح مسیر
    if not os.path.isabs(json_path):
        json_path = os.path.join(os.path.dirname(current_dir), json_path.replace('../', ''))
    
    if not os.path.exists(json_path):
        print(f"⚠️ فایل {json_path} یافت نشد. رد می‌شود.")
        return
    
    with open(json_path, 'r', encoding='utf-8') as f:
        profiles_data = json.load(f)
    
    db_path = os.path.join(os.path.dirname(current_dir), 'data', 'digikala_sales.db')
    engine = init_database(db_path)
    session = get_session(engine)
    
    profiles_created = 0
    
    for profile_name, profile_info in profiles_data.items():
        existing = session.query(SenderProfile).filter_by(profile_name=profile_name).first()
        
        if not existing:
            profile = SenderProfile(
                profile_name=profile_name,
                sender_name=profile_info.get('name', ''),
                address=profile_info.get('address', ''),
                postal_code=profile_info.get('postal_code', ''),
                phone=profile_info.get('phone', ''),
                is_default=(profile_name == list(profiles_data.keys())[0])
            )
            session.add(profile)
            profiles_created += 1
    
    session.commit()
    print(f"✅ {profiles_created} پروفایل فرستنده ایجاد شد")
    session.close()


if __name__ == "__main__":
    print("🚀 شروع فرآیند انتقال داده‌ها...\n")
    
    try:
        migrate_orders_from_csv()
        migrate_sender_profiles()
        print("\n🎉 تمام داده‌ها با موفقیت منتقل شدند!")
    except Exception as e:
        print(f"\n❌ خطا: {e}")
        import traceback
        traceback.print_exc()