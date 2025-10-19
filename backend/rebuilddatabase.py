#!/usr/bin/env python3
# backend/rebuild_database.py
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

from database.models import Base, init_database, get_session
from database.auth_models import (
    create_default_permissions,
    create_default_roles,
    create_superuser
)

def main():
    print("\n" + "="*70)
    print("🔥 بازسازی کامل دیتابیس")
    print("="*70)
    print("\n⚠️  هشدار: این عملیات تمام داده‌های موجود را پاک می‌کند!")
    
    # مسیر دیتابیس
    db_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'digikala_sales.db')
    db_path = os.path.abspath(db_path)
    
    print(f"\n📁 مسیر دیتابیس: {db_path}")
    
    # تایید کاربر
    response = input("\n❓ آیا مطمئن هستید؟ (yes/no): ").strip().lower()
    if response != 'yes':
        print("\n❌ عملیات لغو شد.")
        return
    
    # 1. پشتیبان‌گیری (اگر فایل وجود داشته باشد)
    if os.path.exists(db_path):
        backup_path = db_path + f".backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        print(f"\n💾 پشتیبان‌گیری از دیتابیس قدیمی...")
        print(f"   {backup_path}")
        try:
            shutil.copy2(db_path, backup_path)
            print("   ✅ پشتیبان‌گیری موفق")
        except Exception as e:
            print(f"   ⚠️ خطا در پشتیبان‌گیری: {e}")
        
        # 2. حذف دیتابیس قدیمی
        print("\n🗑️  حذف دیتابیس قدیمی...")
        try:
            os.remove(db_path)
            print("   ✅ حذف موفق")
        except Exception as e:
            print(f"   ❌ خطا در حذف: {e}")
            return
    else:
        print("\n📝 دیتابیس جدید ایجاد می‌شود...")
    
    # 3. ایجاد دیتابیس جدید
    print("\n🔨 ایجاد دیتابیس جدید...")
    try:
        engine = init_database(db_path)
        print("   ✅ دیتابیس ایجاد شد")
        
        # 4. ایجاد تمام جداول
        print("\n📊 ایجاد جداول...")
        Base.metadata.create_all(engine)
        print("   ✅ جداول ایجاد شدند")
        
        # لیست جداول
        print("\n   📋 جداول ایجاد شده:")
        for table in Base.metadata.tables.keys():
            print(f"      - {table}")
        
        # 5. ایجاد داده‌های اولیه
        session = get_session(engine)
        
        try:
            print("\n👥 ایجاد مجوزها و نقش‌ها...")
            create_default_permissions(session)
            create_default_roles(session)
            
            print("\n🔑 ایجاد کاربر ادمین...")
            create_superuser(
                session,
                username="admin",
                email="admin@company.com",
                password="admin123",
                full_name="مدیر سیستم"
            )
            
            print("\n" + "="*70)
            print("✅ بازسازی دیتابیس با موفقیت کامل شد!")
            print("="*70)
            print("\n🔑 اطلاعات ورود:")
            print("   نام کاربری: admin")
            print("   رمز عبور: admin123")
            print("\n⚠️  توجه: حتماً رمز عبور را تغییر دهید!")
            print("\n📍 مراحل بعدی:")
            print("   1. Backend را ری‌استارت کنید")
            print("   2. از Frontend لاگین کنید")
            print("   3. همگام‌سازی سفارشات را اجرا کنید")
            print("="*70 + "\n")
            
        except Exception as e:
            print(f"\n❌ خطا در ایجاد داده‌ها: {e}")
            import traceback
            traceback.print_exc()
        finally:
            session.close()
            
    except Exception as e:
        print(f"\n❌ خطای کلی: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()