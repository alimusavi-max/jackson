# backend/setup_warehouse.py
"""
راه‌اندازی اولیه سیستم انبارداری
"""

import sys
import os

# اضافه کردن مسیر backend به sys.path
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

from sqlalchemy.orm import Session
from database.models import init_database, get_session
from database.warehouse_models_extended import (
    Warehouse, ProductCategory, Marketplace,
    WarehouseProduct, ProductMarketplace
)


def setup_warehouses(db: Session):
    """ایجاد انبارهای پیش‌فرض"""
    print("\n📦 ایجاد انبارهای پیش‌فرض...")
    
    default_warehouse = Warehouse(
        code="WH-MAIN",
        name="انبار اصلی",
        address="تهران، میدان ونک",
        city="تهران",
        province="تهران",
        postal_code="1234567890",
        phone="021-12345678",
        warehouse_type="main",
        is_active=True,
        is_default=True
    )
    
    db.add(default_warehouse)
    db.commit()
    print("   ✅ انبار اصلی ایجاد شد")


def setup_marketplaces(db: Session):
    """ایجاد پلتفرم‌های فروش"""
    print("\n🌐 ایجاد پلتفرم‌های فروش...")
    
    marketplaces = [
        {
            "name": "دیجی‌کالا",
            "code": "digikala",
            "website": "https://www.digikala.com",
            "api_endpoint": "https://seller.digikala.com/api/v2"
        },
        {
            "name": "باسلام",
            "code": "basalam",
            "website": "https://www.basalam.com",
            "api_endpoint": None
        },
        {
            "name": "دیوار",
            "code": "divar",
            "website": "https://divar.ir",
            "api_endpoint": None
        },
        {
            "name": "ترب",
            "code": "torob",
            "website": "https://torob.com",
            "api_endpoint": None
        }
    ]
    
    for mp_data in marketplaces:
        mp = Marketplace(**mp_data, is_active=True)
        db.add(mp)
        print(f"   ✅ {mp_data['name']} اضافه شد")
    
    db.commit()


def setup_categories(db: Session):
    """ایجاد دسته‌بندی‌های پیش‌فرض"""
    print("\n📁 ایجاد دسته‌بندی‌های پیش‌فرض...")
    
    categories = [
        {"name": "الکترونیک", "slug": "electronics"},
        {"name": "پوشاک", "slug": "clothing"},
        {"name": "کتاب و لوازم التحریر", "slug": "books"},
        {"name": "لوازم خانگی", "slug": "home"},
        {"name": "آرایشی و بهداشتی", "slug": "beauty"},
        {"name": "ورزش و سفر", "slug": "sports"},
        {"name": "غیره", "slug": "other"}
    ]
    
    for cat_data in categories:
        cat = ProductCategory(**cat_data, is_active=True)
        db.add(cat)
        print(f"   ✅ دسته‌بندی '{cat_data['name']}' اضافه شد")
    
    db.commit()


def main():
    """راه‌اندازی اصلی"""
    print("="*60)
    print("🚀 راه‌اندازی سیستم انبارداری")
    print("="*60)
    
    try:
        # اتصال به دیتابیس
        db_path = os.path.join(current_dir, '..', 'data', 'digikala_sales.db')
        print(f"\n📊 اتصال به دیتابیس: {db_path}")
        
        engine = init_database(db_path)
        db = get_session(engine)
        
        # ایجاد جداول
        print("\n🔨 ایجاد جداول...")
        from database.models import Base
        from database.warehouse_models_extended import (
            Warehouse, ProductCategory, Marketplace,
            WarehouseProduct, ProductMarketplace,
            InventoryTransaction, StockTake, StockTakeItem
        )
        Base.metadata.create_all(bind=engine)
        print("   ✅ جداول ایجاد شدند")
        
        # بررسی وجود داده
        existing_warehouses = db.query(Warehouse).count()
        
        if existing_warehouses > 0:
            print("\n⚠️  داده‌های قبلی یافت شد")
            response = input("آیا می‌خواهید داده‌های جدید اضافه کنید؟ (y/n): ")
            if response.lower() != 'y':
                print("❌ عملیات لغو شد")
                return
        
        # ایجاد داده‌های پیش‌فرض
        setup_warehouses(db)
        setup_marketplaces(db)
        setup_categories(db)
        
        db.close()
        
        print("\n" + "="*60)
        print("✅ راه‌اندازی با موفقیت انجام شد!")
        print("="*60)
        print("\n📝 مراحل بعدی:")
        print("   1. سرور FastAPI را راه‌اندازی کنید")
        print("   2. به بخش انبارداری در داشبورد بروید")
        print("   3. محصولات خود را اضافه کنید")
        print()
        
    except Exception as e:
        print(f"\n❌ خطا: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()