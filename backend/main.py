# backend/main.py
from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from sqlalchemy import func, create_engine
from sqlalchemy.orm import sessionmaker
from typing import List, Optional
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))

from database.models import Order, OrderItem, SenderProfile, SMSLog, Base

# ==================== تنظیمات دیتابیس ====================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, '..', 'data', 'digikala_sales.db')
DB_PATH_ABS = os.path.abspath(DB_PATH)

print(f"\n{'='*60}")
print(f"🗄️  مسیر دیتابیس: {DB_PATH_ABS}")
print(f"📁 فایل وجود دارد: {os.path.exists(DB_PATH_ABS)}")
print(f"{'='*60}\n")

engine = create_engine(f'sqlite:///{DB_PATH_ABS}', echo=False)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base.metadata.create_all(bind=engine)

def test_db():
    db = SessionLocal()
    try:
        count = db.query(Order).count()
        print(f"✅ تست دیتابیس: {count} سفارش یافت شد")
        return count
    except Exception as e:
        print(f"❌ خطا در تست دیتابیس: {e}")
        return 0
    finally:
        db.close()

initial_count = test_db()

# ==================== FastAPI App ====================
app = FastAPI(
    title="Digikala Management API",
    version="2.0",
    description=f"Database: {DB_PATH_ABS} | Orders: {initial_count}"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# ==================== Include Routers ====================
print("\n🔧 در حال بارگذاری Routers...")

# 🔐 Auth Router (باید اول باشد)
try:
    from routers import auth
    app.include_router(auth.router, prefix="/api")
    print("✅ auth router loaded at /api/auth")
except Exception as e:
    print(f"❌ خطا در بارگذاری auth router: {e}")
    import traceback
    traceback.print_exc()

# 📦 Warehouse Router
try:
    from routers import warehouse
    app.include_router(warehouse.router, prefix="/api")
    print("✅ warehouse router loaded at /api/warehouse")
except Exception as e:
    print(f"❌ خطا در بارگذاری warehouse router: {e}")
    import traceback
    traceback.print_exc()

# 🛍️ Orders Router
try:
    from routers import orders
    app.include_router(orders.router, prefix="/api", tags=["orders"])
    print("✅ orders router loaded at /api/orders")
except Exception as e:
    print(f"❌ خطا در بارگذاری orders router: {e}")
    import traceback
    traceback.print_exc()

# 📋 Labels Router
try:
    from routers import labels
    app.include_router(labels.router, prefix="/api", tags=["labels"])
    print("✅ labels router loaded at /api/labels")
except Exception as e:
    print(f"❌ خطا در بارگذاری labels router: {e}")
    import traceback
    traceback.print_exc()

# 📮 Tracking Router
try:
    from routers import tracking
    app.include_router(tracking.router, prefix="/api", tags=["tracking"])
    print("✅ tracking router loaded at /api/tracking")
except Exception as e:
    print(f"❌ خطا در بارگذاری tracking router: {e}")
    import traceback
    traceback.print_exc()

# 📤 Sender Profiles Router
try:
    from routers import sender_profiles
    app.include_router(sender_profiles.router, prefix="/api", tags=["sender-profiles"])
    print("✅ sender_profiles router loaded at /api/sender-profiles")
except Exception as e:
    print(f"❌ خطا در بارگذاری sender_profiles router: {e}")
    import traceback
    traceback.print_exc()

print("✅ تمام routers بارگذاری شدند\n")

# ==================== Routes ====================
@app.get("/")
def root():
    db = SessionLocal()
    try:
        count = db.query(Order).count()
    except:
        count = 0
    finally:
        db.close()
    
    return {
        "message": "Digikala Management API v2.0 🚀",
        "status": "running",
        "db_path": DB_PATH_ABS,
        "db_exists": os.path.exists(DB_PATH_ABS),
        "orders_count": count,
        "features": {
            "auth": "✓ کاربران و نقش‌ها",
            "sales": "✓ مدیریت فروش",
            "warehouse": "✓ انبارداری",
            "labels": "✓ برچسب پستی",
            "tracking": "✓ کد رهگیری",
            "sms": "✓ پیامک"
        },
        "endpoints": {
            "auth": "/api/auth/login",
            "orders": "/api/orders",
            "warehouse": "/api/warehouse/products",
            "labels": "/api/labels",
            "tracking": "/api/tracking",
            "docs": "/docs"
        }
    }

@app.get("/api/stats")
def get_stats(db: Session = Depends(get_db)):
    """آمار کلی سیستم"""
    try:
        total_orders = db.query(Order).count()
        
        orders_with_tracking = db.query(Order).filter(
            Order.tracking_code.isnot(None),
            Order.tracking_code != '',
            Order.tracking_code != 'نامشخص'
        ).count()
        
        total_sales_query = db.query(
            func.sum(OrderItem.price * OrderItem.quantity)
        ).scalar()
        
        total_sales = float(total_sales_query) if total_sales_query else 0
        
        unique_cities = db.query(func.count(func.distinct(Order.city))).scalar()
        
        return {
            "total_orders": total_orders,
            "orders_with_tracking": orders_with_tracking,
            "orders_without_tracking": total_orders - orders_with_tracking,
            "total_sales": total_sales,
            "unique_cities": unique_cities,
            "completion_rate": round((orders_with_tracking / total_orders * 100), 2) if total_orders > 0 else 0
        }
    except Exception as e:
        return {
            "error": str(e),
            "total_orders": 0,
            "orders_with_tracking": 0,
            "orders_without_tracking": 0,
            "total_sales": 0
        }

# ==================== اجرا ====================
if __name__ == "__main__":
    import uvicorn
    print("\n🚀 در حال اجرای Backend API...\n")
    print("📍 Endpoints:")
    print("   - http://localhost:8000/")
    print("   - http://localhost:8000/docs")
    print("   - http://localhost:8000/api/auth/login")
    print("   - http://localhost:8000/api/orders")
    print("   - http://localhost:8000/api/warehouse/products")
    print("   - http://localhost:8000/api/tracking/test")
    print("   - http://localhost:8000/api/labels/test-font")
    print()
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=False)