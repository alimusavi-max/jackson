#!/usr/bin/env python3
# backend/setup_warehouse.py
"""
اسکریپت راه‌اندازی کامل سیستم انبارداری
- ایجاد جداول
- داده‌های پیش‌فرض
- چند انبار نمونه
- مارکت‌های اصلی
"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from database.models import Base, init_database, get_session
from database.warehouse_models_extended import (
    Warehouse, ProductCategory, Marketplace,
    WarehouseProduct, ProductMarketplace,
    initialize_default_data
)


def main():
    print("\n" + "="*70)
    print("🏭 راه‌اندازی سیستم انبارداری")
    print("="*70 + "\n")
    
    # مسیر دیتابیس
    db_path = os.path.join(
        os.path.dirname(__file__), 
        '..', 
        'data', 
        'digikala_sales.db'
    )
    db_path = os.path.abspath(db_path)
    
    print(f"📁 مسیر دیتابیس: {db_path}")
    
    # ایجاد/اتصال به دیتابیس
    engine = init_database(db_path)
    session = get_session(engine)
    
    try:
        # 1. ایجاد جداول
        print("\n🔨 ایجاد جداول...")
        Base.metadata.create_all(engine)
        print("✅ جداول ایجاد شدند")
        
        # 2. داده‌های پیش‌فرض
        print("\n📦 ایجاد داده‌های پیش‌فرض...")
        initialize_default_data(session)
        
        # 3. انبارهای نمونه اضافی
        print("\n🏭 ایجاد انبارهای نمونه...")
        
        warehouses_sample = [
            {
                "code": "WH-002",
                "name": "انبار فرعی شمال",
                "city": "رشت",
                "province": "گیلان",
                "warehouse_type": "secondary",
                "is_active": True
            },
            {
                "code": "WH-003",
                "name": "انبار فرعی جنوب",
                "city": "شیراز",
                "province": "فارس",
                "warehouse_type": "secondary",
                "is_active": True
            }
        ]
        
        for wh_data in warehouses_sample:
            if not session.query(Warehouse).filter_by(code=wh_data["code"]).first():
                warehouse = Warehouse(**wh_data)
                session.add(warehouse)
                print(f"   ✓ {wh_data['name']}")
        
        # 4. محصولات نمونه
        print("\n📦 ایجاد محصولات نمونه...")
        
        main_warehouse = session.query(Warehouse).filter_by(code="WH-001").first()
        electronics_cat = session.query(ProductCategory).filter_by(slug="electronics").first()
        
        if main_warehouse and electronics_cat:
            products_sample = [
                {
                    "sku": "PROD-001",
                    "title": "گوشی موبایل سامسونگ Galaxy A54",
                    "description": "گوشی هوشمند سامسونگ مدل Galaxy A54 با حافظه 128GB",
                    "brand": "Samsung",
                    "category_id": electronics_cat.id,
                    "warehouse_id": main_warehouse.id,
                    "cost_price": 12000000,
                    "sell_price": 14500000,
                    "stock_quantity": 15,
                    "min_stock_alert": 5,
                    "reorder_point": 10,
                    "barcode": "8801643941307"
                },
                {
                    "sku": "PROD-002",
                    "title": "هندزفری بلوتوثی شیائومی Redmi Buds 3 Pro",
                    "description": "هندزفری بی‌سیم شیائومی با قابلیت حذف نویز",
                    "brand": "Xiaomi",
                    "category_id": electronics_cat.id,
                    "warehouse_id": main_warehouse.id,
                    "cost_price": 2500000,
                    "sell_price": 3200000,
                    "stock_quantity": 30,
                    "min_stock_alert": 10,
                    "reorder_point": 15
                },
                {
                    "sku": "PROD-003",
                    "title": "پاوربانک انکر مدل PowerCore 20000mAh",
                    "description": "شارژر همراه انکر با ظرفیت 20000 میلی آمپر ساعت",
                    "brand": "Anker",
                    "category_id": electronics_cat.id,
                    "warehouse_id": main_warehouse.id,
                    "cost_price": 1800000,
                    "sell_price": 2400000,
                    "stock_quantity": 2,  # موجودی کم
                    "min_stock_alert": 5,
                    "reorder_point": 8
                }
            ]
            
            for prod_data in products_sample:
                if not session.query(WarehouseProduct).filter_by(sku=prod_data["sku"]).first():
                    product = WarehouseProduct(**prod_data)
                    product.update_available_quantity()
                    session.add(product)
                    print(f"   ✓ {prod_data['title'][:50]}...")
        
        # 5. نقشه‌گذاری SKU نمونه
        print("\n🌐 ایجاد نقشه‌گذاری SKU پلتفرم‌ها...")
        
        digikala = session.query(Marketplace).filter_by(code="DK").first()
        basalam = session.query(Marketplace).filter_by(code="BS").first()
        
        product_1 = session.query(WarehouseProduct).filter_by(sku="PROD-001").first()
        
        if product_1 and digikala:
            # SKU دیجی‌کالا
            if not session.query(ProductMarketplace).filter_by(
                product_id=product_1.id,
                marketplace_id=digikala.id
            ).first():
                mapping = ProductMarketplace(
                    product_id=product_1.id,
                    marketplace_id=digikala.id,
                    marketplace_sku="DKP-123456",
                    marketplace_url="https://www.digikala.com/product/dkp-123456",
                    price_in_marketplace=15000000,
                    is_active=True
                )
                session.add(mapping)
                print(f"   ✓ {product_1.title[:40]}... → دیجی‌کالا")
        
        if product_1 and basalam:
            # SKU باسلام
            if not session.query(ProductMarketplace).filter_by(
                product_id=product_1.id,
                marketplace_id=basalam.id
            ).first():
                mapping = ProductMarketplace(
                    product_id=product_1.id,
                    marketplace_id=basalam.id,
                    marketplace_sku="BS-789012",
                    marketplace_url="https://www.basalam.com/product/BS-789012",
                    price_in_marketplace=14800000,
                    is_active=True
                )
                session.add(mapping)
                print(f"   ✓ {product_1.title[:40]}... → باسلام")
        
        # Commit
        session.commit()
        
        print("\n" + "="*70)
        print("✅ راه‌اندازی کامل شد!")
        print("="*70)
        
        # آمار نهایی
        print("\n📊 آمار سیستم:")
        print(f"   🏭 انبارها: {session.query(Warehouse).count()}")
        print(f"   📦 محصولات: {session.query(WarehouseProduct).count()}")
        print(f"   🌐 مارکت‌ها: {session.query(Marketplace).count()}")
        print(f"   🗂️ دسته‌بندی‌ها: {session.query(ProductCategory).count()}")
        print(f"   🔗 نقشه‌گذاری SKU: {session.query(ProductMarketplace).count()}")
        
        print("\n🎯 مراحل بعدی:")
        print("   1. Backend را ری‌استارت کنید")
        print("   2. از Frontend به /warehouse/inventory بروید")
        print("   3. محصولات و انبارها را مشاهده کنید")
        print("   4. محصول جدید با SKU چند پلتفرمی اضافه کنید")
        print("="*70 + "\n")
        
    except Exception as e:
        print(f"\n❌ خطا: {e}")
        import traceback
        traceback.print_exc()
        session.rollback()
    finally:
        session.close()


if __name__ == "__main__":
    main()