import os
import sys
from database.models import get_session, init_database, Order, OrderItem

print("=== بررسی و اصلاح تعداد اقلام ===\n")

db_path = os.path.join('..', 'data', 'digikala_sales.db')
engine = init_database(db_path)
session = get_session(engine)

# بررسی چند مورد
print("نمونه‌هایی از سفارشات:\n")
orders = session.query(Order).limit(10).all()

for order in orders:
    items = session.query(OrderItem).filter(OrderItem.order_id == order.id).all()
    total_quantity = sum(item.quantity for item in items)
    
    print(f"سفارش {order.order_code}:")
    print(f"  - تعداد OrderItem ها: {len(items)}")
    print(f"  - مجموع quantity: {total_quantity}")
    for item in items:
        print(f"    • {item.product_title[:50]}... (qty: {item.quantity})")
    print()

session.close()

print("\n✓ برای مشاهده تعداد دقیق، به جدول نگاه کنید.")
print("اگر همه سفارشات فقط 1 OrderItem دارند، مشکل از migration است.")