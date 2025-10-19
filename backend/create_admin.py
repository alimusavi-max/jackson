# backend/create_admin.py
"""
اسکریپت ایجاد کاربر ادمین اولیه
"""
import sys
import os

# اضافه کردن مسیر backend به sys.path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from database.models import init_database, get_session
from database.auth_models import (
    create_default_permissions,
    create_default_roles,
    create_superuser
)

def main():
    print("\n" + "="*60)
    print("🔧 راه‌اندازی سیستم احراز هویت")
    print("="*60 + "\n")
    
    # مسیر دیتابیس
    db_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'digikala_sales.db')
    db_path = os.path.abspath(db_path)
    
    print(f"📁 مسیر دیتابیس: {db_path}")
    
    # ایجاد/اتصال به دیتابیس
    engine = init_database(db_path)
    session = get_session(engine)
    
    try:
        # 1. ایجاد مجوزها
        print("\n📋 ایجاد مجوزها...")
        create_default_permissions(session)
        
        # 2. ایجاد نقش‌ها
        print("\n👥 ایجاد نقش‌ها...")
        create_default_roles(session)
        
        # 3. ایجاد کاربر ادمین
        print("\n👤 ایجاد کاربر ادمین...")
        create_superuser(
            session,
            username="admin",
            email="admin@company.com",
            password="admin123",
            full_name="مدیر سیستم"
        )
        
        print("\n" + "="*60)
        print("✅ راه‌اندازی با موفقیت کامل شد!")
        print("="*60)
        print("\n🔑 اطلاعات ورود:")
        print("   نام کاربری: admin")
        print("   رمز عبور: admin123")
        print("\n⚠️  توجه: حتماً رمز عبور را تغییر دهید!")
        print("="*60 + "\n")
        
    except Exception as e:
        print(f"\n❌ خطا: {e}")
        import traceback
        traceback.print_exc()
    finally:
        session.close()

if __name__ == "__main__":
    main()