#!/usr/bin/env python3
# backend/rebuilddatabase.py
"""
اسکریپت بازسازی کامل دیتابیس
⚠️ هشدار: این اسکریپت تمام داده‌های موجود را پاک می‌کند!
"""
import sys
import os
import shutil
from datetime import datetime

# اضافه کردن مسیر backend به sys.path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# 🔥 Import همه مدل‌ها برای ایجاد جداول
from database.models import Base, init_database, get_session
from database.auth_models import (
    User, Role, Permission, AuditLog,
    create_default_permissions,
    create_default_roles,
    create_superuser
)

# 🔥 Import مدل‌های warehouse
from database.warehouse_models import (
    Warehouse, ProductCategory, ProductMaster,
    ProductPlatformMapping, InventoryItem,
    StockMovement, StockCount, StockCountItem, Supplier
)

# 🔥 Import مدل‌های warehouse_models_extended
from database.warehouse_models_extended import (
    WarehouseProduct, Marketplace, ProductMarketplace,
    InventoryTransaction, StockTake, StockTakeItem
)


def print_header(text):
    """چاپ هدر زیبا"""
    print("\n" + "="*70)
    print(f"  {text}")
    print("="*70)


def print_section(text):
    """چاپ بخش"""
    print(f"\n📌 {text}")


def print_success(text):
    """چاپ موفقیت"""
    print(f"   ✅ {text}")


def print_error(text):
    """چاپ خطا"""
    print(f"   ❌ {text}")


def print_warning(text):
    """چاپ هشدار"""
    print(f"   ⚠️  {text}")


def list_all_tables():
    """لیست تمام جداولی که ایجاد می‌شوند"""
    print_section("جداول قابل ایجاد:")
    
    tables = sorted(Base.metadata.tables.keys())
    
    # دسته‌بندی جداول
    auth_tables = [t for t in tables if t in ['users', 'roles', 'permissions', 'user_roles', 'role_permissions', 'audit_logs']]
    warehouse_tables = [t for t in tables if 'warehouse' in t or 'product' in t or 'inventory' in t or 'stock' in t or 'supplier' in t]
    marketplace_tables = [t for t in tables if 'marketplace' in t]
    order_tables = [t for t in tables if 'order' in t or 'sms' in t or 'sender' in t]
    other_tables = [t for t in tables if t not in auth_tables + warehouse_tables + marketplace_tables + order_tables]
    
    if auth_tables:
        print("\n   🔐 احراز هویت و دسترسی:")
        for table in auth_tables:
            print(f"      - {table}")
    
    if warehouse_tables:
        print("\n   📦 انبارداری:")
        for table in warehouse_tables:
            print(f"      - {table}")
    
    if marketplace_tables:
        print("\n   🌐 مارکت‌پلیس:")
        for table in marketplace_tables:
            print(f"      - {table}")
    
    if order_tables:
        print("\n   🛒 سفارشات:")
        for table in order_tables:
            print(f"      - {table}")
    
    if other_tables:
        print("\n   📋 سایر:")
        for table in other_tables:
            print(f"      - {table}")
    
    print(f"\n   📊 مجموع: {len(tables)} جدول")


def main():
    print_header("🔥 بازسازی کامل دیتابیس")
    
    # مسیر دیتابیس
    db_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'digikala_sales.db')
    db_path = os.path.abspath(db_path)
    
    print(f"\n📁 مسیر دیتابیس: {db_path}")
    print(f"📂 وجود دارد: {'✅ بله' if os.path.exists(db_path) else '❌ خیر'}")
    
    # نمایش جداول
    list_all_tables()
    
    # تایید کاربر
    print("\n" + "⚠️ "*35)
    print("⚠️  هشدار: این عملیات تمام داده‌های موجود را پاک می‌کند!")
    print("⚠️ "*35)
    
    response = input("\n❓ آیا مطمئن هستید؟ (برای تایید 'yes' تایپ کنید): ").strip().lower()
    
    if response != 'yes':
        print("\n❌ عملیات لغو شد.")
        print("💡 نکته: برای تایید باید دقیقاً 'yes' تایپ کنید (حروف کوچک)")
        return
    
    try:
        # 1. پشتیبان‌گیری
        if os.path.exists(db_path):
            print_section("پشتیبان‌گیری از دیتابیس قدیمی")
            
            backup_path = db_path + f".backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            
            try:
                shutil.copy2(db_path, backup_path)
                print_success(f"فایل backup: {os.path.basename(backup_path)}")
                
                # نمایش اندازه
                size_mb = os.path.getsize(backup_path) / (1024 * 1024)
                print(f"      حجم: {size_mb:.2f} MB")
            except Exception as e:
                print_error(f"خطا در backup: {e}")
                print_warning("ادامه می‌دهیم بدون backup...")
        
        # 2. حذف دیتابیس قدیمی
        if os.path.exists(db_path):
            print_section("حذف دیتابیس قدیمی")
            
            try:
                os.remove(db_path)
                print_success("دیتابیس قدیمی حذف شد")
            except Exception as e:
                print_error(f"خطا در حذف: {e}")
                print_error("نمی‌توان ادامه داد!")
                return
        
        # 3. ایجاد دیتابیس جدید
        print_section("ایجاد دیتابیس جدید")
        
        engine = init_database(db_path)
        print_success("اتصال به دیتابیس برقرار شد")
        
        # 4. ایجاد تمام جداول
        print_section("ایجاد جداول")
        
        Base.metadata.create_all(engine)
        print_success("تمام جداول ایجاد شدند")
        
        # نمایش جداول ایجاد شده
        print("\n   📋 جداول ایجاد شده:")
        for table_name in sorted(Base.metadata.tables.keys()):
            print(f"      ✓ {table_name}")
        
        # 5. ایجاد داده‌های اولیه
        session = get_session(engine)
        
        try:
            print_section("ایجاد مجوزها و نقش‌ها")
            create_default_permissions(session)
            create_default_roles(session)
            
            print_section("ایجاد کاربر ادمین")
            create_superuser(
                session,
                username="admin",
                email="admin@company.com",
                password="admin123",
                full_name="مدیر سیستم"
            )
            
            # 6. ایجاد داده‌های warehouse
            print_section("ایجاد داده‌های پیش‌فرض انبارداری")
            
            # انبار پیش‌فرض
            default_warehouse = Warehouse(
                code="WH-MAIN",
                name="انبار اصلی",
                address="تهران، میدان ونک",
                city="تهران",
                province="تهران",
                warehouse_type="main",
                is_active=True,
                is_default=True
            )
            session.add(default_warehouse)
            print_success("انبار اصلی ایجاد شد")
            
            # مارکت‌پلیس‌ها
            marketplaces_data = [
                {"name": "دیجی‌کالا", "code": "digikala", "website": "https://www.digikala.com"},
                {"name": "باسلام", "code": "basalam", "website": "https://www.basalam.com"},
                {"name": "دیوار", "code": "divar", "website": "https://divar.ir"},
                {"name": "ترب", "code": "torob", "website": "https://torob.com"}
            ]
            
            for mp_data in marketplaces_data:
                mp = Marketplace(**mp_data, is_active=True)
                session.add(mp)
            print_success(f"{len(marketplaces_data)} مارکت‌پلیس اضافه شد")
            
            # دسته‌بندی‌ها
            categories_data = [
                {"name": "الکترونیک", "slug": "electronics"},
                {"name": "پوشاک", "slug": "clothing"},
                {"name": "کتاب", "slug": "books"},
                {"name": "لوازم خانگی", "slug": "home"},
                {"name": "آرایشی", "slug": "beauty"},
                {"name": "ورزش", "slug": "sports"},
                {"name": "غیره", "slug": "other"}
            ]
            
            for cat_data in categories_data:
                cat = ProductCategory(**cat_data, is_active=True)
                session.add(cat)
            print_success(f"{len(categories_data)} دسته‌بندی اضافه شد")
            
            session.commit()
            
            print_header("✅ بازسازی با موفقیت کامل شد!")
            
            print("\n🔑 اطلاعات ورود:")
            print("   نام کاربری: admin")
            print("   رمز عبور: admin123")
            print("   ایمیل: admin@company.com")
            
            print("\n⚠️  نکات امنیتی:")
            print("   1. حتماً رمز عبور را از پنل تغییر دهید")
            print("   2. ایمیل واقعی خود را وارد کنید")
            
            print("\n📍 مراحل بعدی:")
            print("   1. Backend را ری‌استارت کنید:")
            print("      cd backend")
            print("      python main.py")
            print("\n   2. از Frontend لاگین کنید")
            print("\n   3. همگام‌سازی سفارشات را اجرا کنید")
            
            print("\n💾 Backup:")
            if 'backup_path' in locals():
                print(f"   فایل backup: {backup_path}")
                print(f"   برای بازگردانی: فایل backup را rename کنید به digikala_sales.db")
            
            print("="*70 + "\n")
            
        except Exception as e:
            print_error(f"خطا در ایجاد داده‌ها: {e}")
            import traceback
            traceback.print_exc()
        finally:
            session.close()
            
    except Exception as e:
        print_error(f"خطای کلی: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()