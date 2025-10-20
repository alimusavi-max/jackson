# backend/main.py
from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from sqlalchemy import func, create_engine
from sqlalchemy.orm import sessionmaker
from typing import List, Optional
import os
import sys

# اضافه کردن backend به path
sys.path.insert(0, os.path.dirname(__file__))

# ==================== Import همه Models ====================
from database.models import Order, OrderItem, Base
from database.auth_models import User

# 🔥 CRITICAL: Import کردن تمام مدل‌های warehouse برای register شدن در Base
from database.warehouse_models_extended import (
    Warehouse, WarehouseProduct, ProductCategory,
    Marketplace, ProductMarketplace, InventoryTransaction,
    StockTake, StockTakeItem
)

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

# 🔥 ایجاد تمام جداول (شامل warehouse)
print("🔨 ایجاد جداول...")
Base.metadata.create_all(bind=engine)
print("✅ تمام جداول ایجاد شدند\n")

def test_db():
    db = SessionLocal()
    try:
        count = db.query(Order).count()
        warehouse_count = db.query(Warehouse).count()
        print(f"✅ تست دیتابیس: {count} سفارش، {warehouse_count} انبار")
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

# 🔐 Auth Router
try:
    from routers import auth
    app.include_router(auth.router, prefix="/api")
    print("✅ auth router loaded")
except Exception as e:
    print(f"❌ auth router: {e}")

# 📦 Warehouse Router
try:
    from routers import warehouse
    app.include_router(warehouse.router, prefix="/api")
    print("✅ warehouse router loaded")
except Exception as e:
    print(f"❌ warehouse router: {e}")
    import traceback
    traceback.print_exc()

# 🛍️ Orders Router
try:
    from routers import orders
    app.include_router(orders.router, prefix="/api", tags=["orders"])
    print("✅ orders router loaded")
except Exception as e:
    print(f"❌ orders router: {e}")

# 📋 Labels Router
try:
    from routers import labels
    app.include_router(labels.router, prefix="/api", tags=["labels"])
    print("✅ labels router loaded")
except Exception as e:
    print(f"❌ labels router: {e}")

# 📮 Tracking Router
try:
    from routers import tracking
    app.include_router(tracking.router, prefix="/api", tags=["tracking"])
    print("✅ tracking router loaded")
except Exception as e:
    print(f"❌ tracking router: {e}")

# 📤 Sender Profiles Router
try:
    from routers import sender_profiles
    app.include_router(sender_profiles.router, prefix="/api", tags=["sender-profiles"])
    print("✅ sender_profiles router loaded")
except Exception as e:
    print(f"❌ sender_profiles router: {e}")

print("✅ تمام routers بارگذاری شدند\n")

# ==================== Routes ====================
@app.get("/")
def root():
    db = SessionLocal()
    try:
        orders_count = db.query(Order).count()
        warehouses_count = db.query(Warehouse).count()
        products_count = db.query(WarehouseProduct).count()
    except:
        orders_count = 0
        warehouses_count = 0
        products_count = 0
    finally:
        db.close()
    
    return {
        "message": "Digikala Management API v2.0 🚀",
        "status": "running",
        "db_path": DB_PATH_ABS,
        "db_exists": os.path.exists(DB_PATH_ABS),
        "stats": {
            "orders": orders_count,
            "warehouses": warehouses_count,
            "products": products_count
        },
        "features": {
            "auth": "✓ کاربران و نقش‌ها",
            "sales": "✓ مدیریت فروش",
            "warehouse": "✓ انبارداری چند انباره",
            "labels": "✓ برچسب پستی",
            "tracking": "✓ کد رهگیری",
            "sms": "✓ پیامک"
        },
        "endpoints": {
            "auth": "/api/auth/login",
            "orders": "/api/orders",
            "warehouse": "/api/warehouse/products",
            "warehouses": "/api/warehouse/warehouses",
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
        
        # آمار انبار
        total_warehouses = db.query(Warehouse).filter(Warehouse.is_active == True).count()
        total_products = db.query(WarehouseProduct).filter(WarehouseProduct.is_active == True).count()
        total_stock = db.query(func.sum(WarehouseProduct.stock_quantity)).scalar() or 0
        
        return {
            "sales": {
                "total_orders": total_orders,
                "orders_with_tracking": orders_with_tracking,
                "orders_without_tracking": total_orders - orders_with_tracking,
                "total_sales": total_sales,
                "unique_cities": unique_cities,
                "completion_rate": round((orders_with_tracking / total_orders * 100), 2) if total_orders > 0 else 0
            },
            "warehouse": {
                "total_warehouses": total_warehouses,
                "total_products": total_products,
                "total_stock": total_stock
            }
        }
    except Exception as e:
        print(f"❌ خطا در آمار: {e}")
        import traceback
        traceback.print_exc()
        return {
            "error": str(e),
            "sales": {"total_orders": 0},
            "warehouse": {"total_warehouses": 0}
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
    print("   - http://localhost:8000/api/warehouse/warehouses")
    print()
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=False)