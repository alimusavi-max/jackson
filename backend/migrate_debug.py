import sys
import os
import pandas as pd
from database.models import init_database, get_session, Order, OrderItem

print("=== شروع Migration با Debug ===\n")

# چک CSV
csv_path = os.path.join('..', 'data', 'orders_database_complete.csv')
print(f"1. مسیر CSV: {os.path.abspath(csv_path)}")
print(f"   وجود دارد: {os.path.exists(csv_path)}")

if not os.path.exists(csv_path):
    print("\n❌ فایل CSV یافت نشد!")
    print("لطفاً مطمئن شوید فایل orders_database_complete.csv در پوشه data است")
    sys.exit(1)

# خواندن CSV
print("\n2. در حال خواندن CSV...")
try:
    df = pd.read_csv(csv_path, encoding='utf-8-sig', dtype=str)
    print(f"   ✓ تعداد ردیف‌ها: {len(df)}")
    print(f"   ✓ ستون‌ها: {', '.join(df.columns[:5])}...")
except Exception as e:
    print(f"   ❌ خطا در خواندن CSV: {e}")
    sys.exit(1)

# ایجاد دیتابیس
print("\n3. ایجاد/اتصال به دیتابیس...")
db_path = os.path.join('..', 'data', 'digikala_sales.db')
print(f"   مسیر DB: {os.path.abspath(db_path)}")

try:
    engine = init_database(db_path)
    session = get_session(engine)
    print("   ✓ اتصال برقرار شد")
except Exception as e:
    print(f"   ❌ خطا در اتصال: {e}")
    sys.exit(1)

# گروه‌بندی
print("\n4. پردازش داده‌ها...")
grouped = df.groupby('شناسه محموله')
print(f"   تعداد محموله‌های منحصر به فرد: {len(grouped)}")

# ذخیره
orders_created = 0
items_created = 0
errors = []

print("\n5. ذخیره در دیتابیس...")
for idx, (shipment_id, group) in enumerate(grouped):
    if idx < 3:  # نمایش 3 مورد اول برای debug
        print(f"   [{idx+1}] محموله {shipment_id}: {len(group)} آیتم")
    
    try:
        first_row = group.iloc[0]
        
        # چک وجود
        existing = session.query(Order).filter_by(shipment_id=str(shipment_id)).first()
        
        if existing:
            order = existing
        else:
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
        
        # آیتم‌ها
        for _, row in group.iterrows():
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
            
    except Exception as e:
        errors.append(f"خطا در ردیف {idx}: {str(e)}")
        if len(errors) <= 3:  # نمایش 3 خطای اول
            print(f"   ⚠ {errors[-1]}")

# Commit
print("\n6. ذخیره نهایی...")
try:
    session.commit()
    print("   ✓ Commit موفق")
except Exception as e:
    print(f"   ❌ خطا در commit: {e}")
    session.rollback()
    sys.exit(1)

# نتیجه
print("\n" + "="*50)
print(f"✅ Migration کامل شد!")
print(f"   📦 سفارشات ایجاد شده: {orders_created}")
print(f"   📋 اقلام ایجاد شده: {items_created}")
if errors:
    print(f"   ⚠ تعداد خطاها: {len(errors)}")
print("="*50)

# تست نهایی
final_count = session.query(Order).count()
print(f"\n✓ تست: {final_count} سفارش در دیتابیس")

session.close()