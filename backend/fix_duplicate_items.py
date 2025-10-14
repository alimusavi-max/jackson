import os
from database.models import get_session, init_database, Order, OrderItem

print("=== حذف اقلام تکراری ===\n")

db_path = os.path.join('..', 'data', 'digikala_sales.db')
engine = init_database(db_path)
session = get_session(engine)

print("🔍 در حال شمارش اقلام تکراری...")

# شمارش کل
total_items_before = session.query(OrderItem).count()
print(f"تعداد کل OrderItem قبل: {total_items_before}")

# حذف تکراری‌ها
orders = session.query(Order).all()
removed_count = 0

for order in orders:
    items = session.query(OrderItem).filter(OrderItem.order_id == order.id).all()
    
    if len(items) > 1:
        # گروه‌بندی بر اساس product_code
        seen = {}
        for item in items:
            key = item.product_code
            if key in seen:
                # تکراری است - حذف کن
                session.delete(item)
                removed_count += 1
            else:
                seen[key] = item

session.commit()

total_items_after = session.query(OrderItem).count()

print(f"\n✅ پاکسازی کامل شد!")
print(f"   تعداد OrderItem قبل: {total_items_before}")
print(f"   تعداد OrderItem بعد: {total_items_after}")
print(f"   تعداد حذف شده: {removed_count}")

# نمونه چند سفارش بعد از پاکسازی
print("\n📊 نمونه سفارشات بعد از پاکسازی:\n")
for order in session.query(Order).limit(5).all():
    items = session.query(OrderItem).filter(OrderItem.order_id == order.id).all()
    total_qty = sum(item.quantity for item in items)
    print(f"سفارش {order.order_code}:")
    print(f"  - تعداد OrderItem: {len(items)}")
    print(f"  - مجموع quantity: {total_qty}")

session.close()