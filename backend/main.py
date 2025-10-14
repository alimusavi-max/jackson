from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from sqlalchemy import func, create_engine
from sqlalchemy.orm import sessionmaker
from typing import List, Optional
import os
import sys

# اضافه کردن backend به path
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

# ایجاد engine با echo
engine = create_engine(f'sqlite:///{DB_PATH_ABS}', echo=False)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# ایجاد جداول (در صورت نیاز)
Base.metadata.create_all(bind=engine)

# تست اولیه
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

# اجرای تست
initial_count = test_db()

# ==================== FastAPI App ====================
app = FastAPI(
    title="Digikala Management API",
    version="2.0",
    description=f"Database: {DB_PATH_ABS} | Orders: {initial_count}"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

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
        "message": "Digikala Management API v2.0",
        "status": "running",
        "db_path": DB_PATH_ABS,
        "db_exists": os.path.exists(DB_PATH_ABS),
        "orders_count": count
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
        
        # مجموع فروش
        total_sales_query = db.query(
            func.sum(OrderItem.price * OrderItem.quantity)
        ).scalar()
        
        total_sales = float(total_sales_query) if total_sales_query else 0
        
        return {
            "total_orders": total_orders,
            "orders_with_tracking": orders_with_tracking,
            "orders_without_tracking": total_orders - orders_with_tracking,
            "total_sales": total_sales,
            "db_path": DB_PATH_ABS
        }
    except Exception as e:
        return {
            "error": str(e),
            "total_orders": 0,
            "orders_with_tracking": 0,
            "orders_without_tracking": 0,
            "total_sales": 0
        }

@app.get("/api/orders")
def get_orders(
    limit: int = 1000,
    skip: int = 0,
    has_tracking: Optional[bool] = None,
    search: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """دریافت لیست سفارشات با محاسبه دقیق تعداد اقلام"""
    try:
        query = db.query(Order)
        
        # فیلتر tracking
        if has_tracking is not None:
            if has_tracking:
                query = query.filter(
                    Order.tracking_code.isnot(None),
                    Order.tracking_code != '',
                    Order.tracking_code != 'نامشخص'
                )
            else:
                query = query.filter(
                    (Order.tracking_code.is_(None)) | 
                    (Order.tracking_code == '') | 
                    (Order.tracking_code == 'نامشخص')
                )
        
        # جستجو
        if search:
            search_filter = f"%{search}%"
            query = query.filter(
                (Order.order_code.like(search_filter)) |
                (Order.customer_name.like(search_filter)) |
                (Order.tracking_code.like(search_filter))
            )
        
        # مرتب‌سازی و صفحه‌بندی
        orders = query.order_by(Order.id.desc()).offset(skip).limit(limit).all()
        
        result = []
        for order in orders:
            # محاسبه دقیق تعداد اقلام
            items = db.query(OrderItem).filter(OrderItem.order_id == order.id).all()
            items_count = sum(item.quantity for item in items)  # جمع quantity ها
            total_amount = sum(item.price * item.quantity for item in items)
            
            result.append({
                "id": order.id,
                "order_code": order.order_code,
                "shipment_id": order.shipment_id,
                "customer_name": order.customer_name or "نامشخص",
                "customer_phone": order.customer_phone or "",
                "status": order.status or "نامشخص",
                "city": order.city or "",
                "province": order.province or "",
                "full_address": order.full_address or "",
                "postal_code": order.postal_code or "",
                "tracking_code": order.tracking_code,
                "order_date_persian": order.order_date_persian or "",
                "items_count": items_count,  # تعداد واقعی
                "total_amount": total_amount
            })
        
        return result
    
    except Exception as e:
        print(f"خطا در get_orders: {e}")
        import traceback
        traceback.print_exc()
        return []
    
@app.get("/api/orders/{order_id}")
def get_order_detail(order_id: int, db: Session = Depends(get_db)):
    """جزئیات یک سفارش"""
    order = db.query(Order).filter(Order.id == order_id).first()
    
    if not order:
        raise HTTPException(status_code=404, detail="سفارش یافت نشد")
    
    items = [
        {
            "id": item.id,
            "product_title": item.product_title,
            "product_code": item.product_code,
            "quantity": item.quantity,
            "price": item.price,
            "product_image": item.product_image
        }
        for item in order.items
    ]
    
    return {
        "id": order.id,
        "order_code": order.order_code,
        "shipment_id": order.shipment_id,
        "customer_name": order.customer_name,
        "customer_phone": order.customer_phone,
        "status": order.status,
        "city": order.city,
        "province": order.province,
        "full_address": order.full_address,
        "postal_code": order.postal_code,
        "tracking_code": order.tracking_code,
        "order_date_persian": order.order_date_persian,
        "items": items,
        "items_count": len(items),
        "total_amount": sum(item["price"] * item["quantity"] for item in items)
    }

@app.post("/api/orders/sync")
def sync_orders(db: Session = Depends(get_db)):
    """همگام‌سازی با API دیجی‌کالا - غیرفعال فعلاً"""
    return {
        "success": False,
        "message": "همگام‌سازی در نسخه بعدی فعال می‌شود",
        "new_orders": 0,
        "updated_orders": 0
    }

@app.post("/api/orders/sync")
async def sync_orders(
    fetch_full_details: bool = False,
    db: Session = Depends(get_db)
):
    """
    همگام‌سازی سفارشات از API دیجی‌کالا
    """
    try:
        # Import توابع از utils
        import sys
        sys.path.insert(0, os.path.join(BASE_DIR, 'utils'))
        
        from api_core import get_all_orders, orders_to_dataframe
        from helpers import normalize_id
        
        print("🔄 شروع همگام‌سازی...")
        
        # دریافت سفارشات از API دیجی‌کالا
        print("📡 در حال دریافت از Ship-by-Seller...")
        orders_sbs = get_all_orders(use_ship_by_seller=True)
        
        print("📡 در حال دریافت از Marketplace...")
        orders_mp = get_all_orders(use_ship_by_seller=False)
        
        # ترکیب و حذف تکراری
        all_orders_dict = {o['shipmentId']: o for o in orders_sbs}
        all_orders_dict.update({o['shipmentId']: o for o in orders_mp})
        
        total_fetched = len(all_orders_dict)
        print(f"✓ {total_fetched} سفارش از API دریافت شد")
        
        if total_fetched == 0:
            return {
                "success": False,
                "message": "هیچ سفارش جدیدی از API دریافت نشد",
                "new_orders": 0,
                "updated_orders": 0,
                "total": 0
            }
        
        # تبدیل به DataFrame
        print("🔄 در حال پردازش داده‌ها...")
        fresh_df = orders_to_dataframe(
            list(all_orders_dict.values()),
            fetch_details=fetch_full_details
        )
        
        if fresh_df.empty:
            return {
                "success": False,
                "message": "خطا در پردازش داده‌ها",
                "new_orders": 0,
                "updated_orders": 0,
                "total": 0
            }
        
        new_count = 0
        updated_count = 0
        
        print("💾 در حال ذخیره در دیتابیس...")
        
        # ذخیره در دیتابیس
        for _, row in fresh_df.iterrows():
            shipment_id = normalize_id(row.get('شناسه محموله', ''))
            
            if not shipment_id:
                continue
            
            # بررسی وجود سفارش
            existing_order = db.query(Order).filter_by(shipment_id=shipment_id).first()
            
            if existing_order:
                # به‌روزرسانی سفارش موجود
                existing_order.status = row.get('وضعیت', existing_order.status)
                if row.get('کد رهگیری') and row.get('کد رهگیری') != 'نامشخص':
                    existing_order.tracking_code = row.get('کد رهگیری')
                updated_count += 1
            else:
                # ایجاد سفارش جدید
                order = Order(
                    order_code=normalize_id(row.get('کد سفارش', '')),
                    shipment_id=shipment_id,
                    customer_name=row.get('نام مشتری', ''),
                    customer_phone=row.get('شماره تلفن', ''),
                    status=row.get('وضعیت', ''),
                    province=row.get('استان', ''),
                    city=row.get('شهر', ''),
                    full_address=row.get('آدرس کامل', ''),
                    postal_code=row.get('کد پستی', ''),
                    tracking_code=row.get('کد رهگیری') if row.get('کد رهگیری') != 'نامشخص' else None,
                    order_date_persian=row.get('تاریخ ثبت', '')
                )
                db.add(order)
                db.flush()
                
                # افزودن آیتم سفارش
                item = OrderItem(
                    order_id=order.id,
                    product_title=row.get('عنوان سفارش', ''),
                    product_code=normalize_id(row.get('کد محصول (DKP)', '')),
                    product_image=row.get('تصویر محصول'),
                    quantity=int(row.get('تعداد', 1)) if row.get('تعداد') else 1,
                    price=float(row.get('مبلغ', 0)) if row.get('مبلغ') else 0
                )
                db.add(item)
                new_count += 1
        
        db.commit()
        
        print(f"✅ همگام‌سازی کامل شد: {new_count} جدید، {updated_count} به‌روزرسانی")
        
        return {
            "success": True,
            "message": f"همگام‌سازی موفق: {new_count} سفارش جدید، {updated_count} سفارش به‌روزرسانی شد",
            "new_orders": new_count,
            "updated_orders": updated_count,
            "total": new_count + updated_count
        }
        
    except ImportError as e:
        print(f"❌ خطای Import: {e}")
        return {
            "success": False,
            "message": f"خطا: ماژول‌های utils یافت نشد. مطمئن شوید پوشه utils در backend کپی شده است.",
            "error": str(e),
            "new_orders": 0,
            "updated_orders": 0,
            "total": 0
        }
    except Exception as e:
        print(f"❌ خطا در همگام‌سازی: {e}")
        import traceback
        traceback.print_exc()
        db.rollback()
        return {
            "success": False,
            "message": f"خطا در همگام‌سازی: {str(e)}",
            "error": str(e),
            "new_orders": 0,
            "updated_orders": 0,
            "total": 0
        }

# ==================== اجرا ====================
if __name__ == "__main__":
    import uvicorn
    print("\n🚀 در حال اجرای Backend API...\n")
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=False)