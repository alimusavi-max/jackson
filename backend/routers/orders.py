# backend/routers/orders.py
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, or_
from typing import List, Optional
from datetime import datetime, timedelta
import pandas as pd

from database.models import Order, OrderItem, get_session, init_database
from utils.api_core import get_all_orders, orders_to_dataframe
from utils.helpers import normalize_id, persian_to_gregorian
from pydantic import BaseModel

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from database.models import Order, OrderItem, get_session, init_database

router = APIRouter(prefix="/orders", tags=["سفارشات"])


# ============= Pydantic Models =============

class OrderItemResponse(BaseModel):
    id: int
    product_title: str
    product_code: str
    quantity: int
    price: float
    product_image: Optional[str]

    class Config:
        from_attributes = True


class OrderResponse(BaseModel):
    id: int
    order_code: str
    shipment_id: str
    customer_name: Optional[str]
    customer_phone: Optional[str]
    status: Optional[str]
    city: Optional[str]
    province: Optional[str]
    tracking_code: Optional[str]
    order_date_persian: Optional[str]
    items_count: int
    total_amount: float

    class Config:
        from_attributes = True


class OrderDetailResponse(OrderResponse):
    full_address: Optional[str]
    postal_code: Optional[str]
    items: List[OrderItemResponse]


class SyncOrdersRequest(BaseModel):
    fetch_full_details: bool = False


class UpdateOrderRequest(BaseModel):
    tracking_code: Optional[str] = None
    status: Optional[str] = None
    customer_phone: Optional[str] = None
    full_address: Optional[str] = None
    postal_code: Optional[str] = None


class BulkUpdateRequest(BaseModel):
    order_ids: List[int]
    updates: UpdateOrderRequest


# ============= Dependency =============

def get_db():
    engine = init_database("digikala_sales.db")
    db = get_session(engine)
    try:
        yield db
    finally:
        db.close()


# ============= Endpoints =============

@router.get("/", response_model=List[OrderResponse])
async def get_orders(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    status: Optional[str] = None,
    city: Optional[str] = None,
    province: Optional[str] = None,
    has_tracking: Optional[bool] = None,
    search: Optional[str] = None,
    order_by: str = Query("created_at", regex="^(created_at|order_date_gregorian|total_amount)$"),
    order_dir: str = Query("desc", regex="^(asc|desc)$"),
    db: Session = Depends(get_db)
):
    """
    دریافت لیست سفارشات با فیلترهای پیشرفته
    
    **فیلترها:**
    - status: فیلتر بر اساس وضعیت
    - city: فیلتر بر اساس شهر
    - province: فیلتر بر اساس استان
    - has_tracking: True/False برای داشتن/نداشتن کد رهگیری
    - search: جستجو در کد سفارش، نام مشتری، کد رهگیری
    - order_by: مرتب‌سازی (created_at, order_date_gregorian, total_amount)
    - order_dir: جهت مرتب‌سازی (asc, desc)
    """
    query = db.query(Order)

    # اعمال فیلترها
    if status:
        query = query.filter(Order.status == status)
    if city:
        query = query.filter(Order.city == city)
    if province:
        query = query.filter(Order.province == province)
    if has_tracking is not None:
        if has_tracking:
            query = query.filter(Order.tracking_code.isnot(None), Order.tracking_code != '')
        else:
            query = query.filter(or_(Order.tracking_code.is_(None), Order.tracking_code == ''))
    
    # جستجو
    if search:
        search_pattern = f"%{search}%"
        query = query.filter(
            or_(
                Order.order_code.like(search_pattern),
                Order.customer_name.like(search_pattern),
                Order.tracking_code.like(search_pattern),
                Order.shipment_id.like(search_pattern)
            )
        )

    # مرتب‌سازی
    order_column = getattr(Order, order_by)
    if order_dir == "desc":
        query = query.order_by(order_column.desc())
    else:
        query = query.order_by(order_column.asc())

    # صفحه‌بندی
    orders = query.offset(skip).limit(limit).all()

    # محاسبه اطلاعات اضافی
    result = []
    for order in orders:
        items_count = len(order.items)
        total_amount = sum(item.price * item.quantity for item in order.items)
        
        result.append({
            **order.__dict__,
            "items_count": items_count,
            "total_amount": total_amount
        })

    return result


@router.get("/stats")
async def get_orders_stats(db: Session = Depends(get_db)):
    """آمار کلی سفارشات"""
    total_orders = db.query(Order).count()
    
    orders_with_tracking = db.query(Order).filter(
        Order.tracking_code.isnot(None),
        Order.tracking_code != ''
    ).count()
    
    # محاسبه مجموع فروش
    total_sales = db.query(
        func.sum(OrderItem.price * OrderItem.quantity)
    ).scalar() or 0
    
    # تعداد شهرهای منحصر به فرد
    unique_cities = db.query(func.count(func.distinct(Order.city))).scalar()
    
    # سفارشات 7 روز اخیر
    seven_days_ago = datetime.utcnow() - timedelta(days=7)
    recent_orders = db.query(Order).filter(
        Order.created_at >= seven_days_ago
    ).count()

    return {
        "total_orders": total_orders,
        "orders_with_tracking": orders_with_tracking,
        "orders_without_tracking": total_orders - orders_with_tracking,
        "total_sales": total_sales,
        "unique_cities": unique_cities,
        "recent_orders_7d": recent_orders,
        "completion_rate": round((orders_with_tracking / total_orders * 100), 2) if total_orders > 0 else 0
    }


@router.get("/{order_id}", response_model=OrderDetailResponse)
async def get_order_detail(order_id: int, db: Session = Depends(get_db)):
    """دریافت جزئیات کامل یک سفارش"""
    order = db.query(Order).filter(Order.id == order_id).first()
    
    if not order:
        raise HTTPException(status_code=404, detail="سفارش یافت نشد")

    items_count = len(order.items)
    total_amount = sum(item.price * item.quantity for item in order.items)

    return {
        **order.__dict__,
        "items_count": items_count,
        "total_amount": total_amount,
        "items": [item.__dict__ for item in order.items]
    }


@router.post("/sync")
async def sync_orders_from_api(
    request: SyncOrdersRequest,
    db: Session = Depends(get_db)
):
    """
    همگام‌سازی سفارشات از API دیجی‌کالا
    
    **پارامترها:**
    - fetch_full_details: اگر True باشد، اطلاعات کامل مشتری (آدرس، تلفن) دریافت می‌شود
    """
    try:
        # دریافت سفارشات از API
        orders_sbs = get_all_orders(use_ship_by_seller=True)
        orders_mp = get_all_orders(use_ship_by_seller=False)
        
        # ترکیب و حذف تکراری
        all_orders_dict = {o['shipmentId']: o for o in orders_sbs}
        all_orders_dict.update({o['shipmentId']: o for o in orders_mp})
        
        # تبدیل به DataFrame
        fresh_df = orders_to_dataframe(
            list(all_orders_dict.values()),
            fetch_details=request.fetch_full_details
        )
        
        if fresh_df.empty:
            return {
                "success": False,
                "message": "هیچ سفارش جدیدی یافت نشد",
                "new_orders": 0,
                "updated_orders": 0
            }

        new_count = 0
        updated_count = 0
        
        # ذخیره در دیتابیس
        for _, row in fresh_df.iterrows():
            shipment_id = normalize_id(row['شناسه محموله'])
            existing_order = db.query(Order).filter_by(shipment_id=shipment_id).first()
            
            if existing_order:
                # به‌روزرسانی سفارش موجود
                existing_order.status = row.get('وضعیت', existing_order.status)
                existing_order.tracking_code = row.get('کد رهگیری', existing_order.tracking_code)
                existing_order.updated_at = datetime.utcnow()
                updated_count += 1
            else:
                # ایجاد سفارش جدید
                order = Order(
                    order_code=normalize_id(row['کد سفارش']),
                    shipment_id=shipment_id,
                    customer_name=row.get('نام مشتری', ''),
                    customer_phone=row.get('شماره تلفن', ''),
                    status=row.get('وضعیت', ''),
                    province=row.get('استان', ''),
                    city=row.get('شهر', ''),
                    full_address=row.get('آدرس کامل', ''),
                    postal_code=row.get('کد پستی', ''),
                    tracking_code=row.get('کد رهگیری') if pd.notna(row.get('کد رهگیری')) else None,
                    order_date_persian=row.get('تاریخ ثبت', ''),
                    order_date_gregorian=persian_to_gregorian(row.get('تاریخ ثبت', ''))
                )
                db.add(order)
                db.flush()
                
                # افزودن آیتم سفارش
                item = OrderItem(
                    order_id=order.id,
                    product_title=row.get('عنوان سفارش', ''),
                    product_code=normalize_id(row.get('کد محصول (DKP)', '')),
                    product_image=row.get('تصویر محصول'),
                    quantity=int(row.get('تعداد', 1)) if pd.notna(row.get('تعداد')) else 1,
                    price=float(row.get('مبلغ', 0)) if pd.notna(row.get('مبلغ')) else 0
                )
                db.add(item)
                new_count += 1
        
        db.commit()
        
        return {
            "success": True,
            "message": f"همگام‌سازی موفق: {new_count} جدید، {updated_count} به‌روزرسانی",
            "new_orders": new_count,
            "updated_orders": updated_count,
            "total": new_count + updated_count
        }
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"خطا در همگام‌سازی: {str(e)}")


@router.put("/{order_id}")
async def update_order(
    order_id: int,
    request: UpdateOrderRequest,
    db: Session = Depends(get_db)
):
    """به‌روزرسانی اطلاعات یک سفارش"""
    order = db.query(Order).filter(Order.id == order_id).first()
    
    if not order:
        raise HTTPException(status_code=404, detail="سفارش یافت نشد")
    
    # به‌روزرسانی فیلدها
    update_data = request.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(order, field, value)
    
    order.updated_at = datetime.utcnow()
    db.commit()
    
    return {"success": True, "message": "سفارش به‌روزرسانی شد"}


@router.post("/bulk-update")
async def bulk_update_orders(
    request: BulkUpdateRequest,
    db: Session = Depends(get_db)
):
    """به‌روزرسانی گروهی چند سفارش"""
    updated_count = 0
    
    for order_id in request.order_ids:
        order = db.query(Order).filter(Order.id == order_id).first()
        if order:
            update_data = request.updates.dict(exclude_unset=True)
            for field, value in update_data.items():
                setattr(order, field, value)
            order.updated_at = datetime.utcnow()
            updated_count += 1
    
    db.commit()
    
    return {
        "success": True,
        "updated_count": updated_count,
        "message": f"{updated_count} سفارش به‌روزرسانی شد"
    }


@router.delete("/{order_id}")
async def delete_order(order_id: int, db: Session = Depends(get_db)):
    """حذف یک سفارش (با احتیاط استفاده شود)"""
    order = db.query(Order).filter(Order.id == order_id).first()
    
    if not order:
        raise HTTPException(status_code=404, detail="سفارش یافت نشد")
    
    db.delete(order)
    db.commit()
    
    return {"success": True, "message": "سفارش حذف شد"}


@router.get("/filters/options")
async def get_filter_options(db: Session = Depends(get_db)):
    """دریافت گزینه‌های موجود برای فیلترها"""
    statuses = db.query(Order.status).distinct().all()
    cities = db.query(Order.city).distinct().all()
    provinces = db.query(Order.province).distinct().all()
    
    return {
        "statuses": [s[0] for s in statuses if s[0]],
        "cities": sorted([c[0] for c in cities if c[0]]),
        "provinces": sorted([p[0] for p in provinces if p[0]])
    }