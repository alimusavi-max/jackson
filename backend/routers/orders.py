# backend/routers/orders.py
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session, joinedload
from datetime import datetime
import pandas as pd
from typing import Optional, List
import requests

# Import از ماژول‌های پروژه
from database.models import Order, OrderItem, Base, init_database, get_session
from utils.helpers import normalize_id
from pydantic import BaseModel

router = APIRouter()

# ========== Pydantic Models ==========
class SyncOrdersRequest(BaseModel):
    fetch_full_details: bool = False

class ConfirmOrdersRequest(BaseModel):
    shipment_ids: Optional[List[int]] = None

class OrderItemResponse(BaseModel):
    id: int
    product_title: str
    product_code: Optional[str]
    product_image: Optional[str]
    quantity: int
    price: float

    class Config:
        from_attributes = True

class OrderResponse(BaseModel):
    id: int
    order_code: str
    shipment_id: str
    customer_name: Optional[str]
    customer_phone: Optional[str]
    status: Optional[str]
    province: Optional[str]
    city: Optional[str]
    full_address: Optional[str]
    postal_code: Optional[str]
    tracking_code: Optional[str]
    order_date_persian: Optional[str]
    created_at: datetime
    updated_at: datetime
    items: List[OrderItemResponse]
    
    # 🔥 فیلدهای محاسباتی که فرانت نیاز داره
    items_count: int
    total_quantity: int
    total_amount: float

    class Config:
        from_attributes = True

# ========== Dependency ==========
def get_db():
    """دریافت session دیتابیس"""
    import os
    db_path = os.path.join(os.path.dirname(__file__), '..', '..', 'data', 'digikala_sales.db')
    engine = init_database(db_path)
    db = get_session(engine)
    try:
        yield db
    finally:
        db.close()

# ========== تابع کمکی برای ارسال درخواست تایید ==========
def send_confirm_request(shipment_id: int, cookies_dict: dict) -> tuple[bool, str]:
    """ارسال درخواست تایید به API دیجی‌کالا"""
    url = "https://seller.digikala.com/api/v2/ship-by-seller-orders/update-status"
    
    headers = {
        "accept": "application/json, text/plain, */*",
        "accept-language": "en-GB,en;q=0.9,fa-IR;q=0.8,fa;q=0.7,en-US;q=0.6",
        "content-type": "application/json",
        "origin": "https://seller.digikala.com",
        "referer": "https://seller.digikala.com/pwa/orders/ship-by-seller",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    }
    
    payload = {
        "order_shipment_id": int(shipment_id),
        "new_status": "processing"
    }
    
    try:
        response = requests.put(
            url,
            json=payload,
            headers=headers,
            cookies=cookies_dict,
            timeout=10
        )
        
        if response.status_code == 200:
            return True, "تایید شد"
        else:
            return False, f"خطای {response.status_code}"
    
    except Exception as e:
        return False, str(e)

# ========== تابع کمکی برای محاسبه فیلدها ==========
def enrich_order_data(order: Order) -> dict:
    """اضافه کردن فیلدهای محاسباتی به سفارش"""
    items_count = len(order.items) if order.items else 0
    total_quantity = sum(item.quantity for item in order.items) if order.items else 0
    total_amount = sum(item.price * item.quantity for item in order.items) if order.items else 0
    
    return {
        "id": order.id,
        "order_code": order.order_code,
        "shipment_id": order.shipment_id,
        "customer_name": order.customer_name,
        "customer_phone": order.customer_phone,
        "status": order.status,
        "province": order.province,
        "city": order.city,
        "full_address": order.full_address,
        "postal_code": order.postal_code,
        "tracking_code": order.tracking_code,
        "order_date_persian": order.order_date_persian,
        "created_at": order.created_at,
        "updated_at": order.updated_at,
        "items": [
            {
                "id": item.id,
                "product_title": item.product_title,
                "product_code": item.product_code,
                "product_image": item.product_image,
                "quantity": item.quantity,
                "price": item.price
            }
            for item in (order.items or [])
        ],
        "items_count": items_count,
        "total_quantity": total_quantity,
        "total_amount": total_amount
    }

# ========== Endpoints ==========

@router.get("/orders")
async def get_orders(
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    status: Optional[str] = None,
    has_tracking: Optional[bool] = None,
    search: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    دریافت لیست سفارشات با فیلترهای مختلف
    
    - **limit**: تعداد سفارشات (پیش‌فرض: 100)
    - **offset**: شروع از کدام سفارش (برای صفحه‌بندی)
    - **status**: فیلتر بر اساس وضعیت
    - **has_tracking**: فیلتر سفارشات با/بدون کد رهگیری
    - **search**: جستجو در کد سفارش، نام مشتری یا شماره تلفن
    """
    try:
        # 🔥 CRITICAL: استفاده از joinedload برای بارگذاری items
        query = db.query(Order).options(joinedload(Order.items))
        
        # فیلتر وضعیت
        if status:
            query = query.filter(Order.status == status)
        
        # فیلتر کد رهگیری
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
            search_term = f"%{search}%"
            query = query.filter(
                (Order.order_code.like(search_term)) |
                (Order.customer_name.like(search_term)) |
                (Order.customer_phone.like(search_term)) |
                (Order.shipment_id.like(search_term))
            )
        
        # مرتب‌سازی و صفحه‌بندی
        orders = query.order_by(Order.created_at.desc()).offset(offset).limit(limit).all()
        
        print(f"✅ {len(orders)} سفارش دریافت شد (offset: {offset}, limit: {limit})")
        
        # 🔥 تبدیل به format مورد نیاز فرانت
        enriched_orders = [enrich_order_data(order) for order in orders]
        
        return enriched_orders
    
    except Exception as e:
        print(f"❌ خطا در دریافت سفارشات: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/orders/{order_id}")
async def get_order(
    order_id: int,
    db: Session = Depends(get_db)
):
    """دریافت جزئیات یک سفارش خاص"""
    try:
        # 🔥 با joinedload
        order = db.query(Order).options(joinedload(Order.items)).filter(Order.id == order_id).first()
        
        if not order:
            raise HTTPException(status_code=404, detail="سفارش یافت نشد")
        
        return enrich_order_data(order)
    
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ خطا: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/orders/stats/summary")
async def get_orders_summary(db: Session = Depends(get_db)):
    """آمار خلاصه سفارشات"""
    try:
        from sqlalchemy import func
        
        total = db.query(Order).count()
        
        with_tracking = db.query(Order).filter(
            Order.tracking_code.isnot(None),
            Order.tracking_code != '',
            Order.tracking_code != 'نامشخص'
        ).count()
        
        without_tracking = total - with_tracking
        
        # گروه‌بندی بر اساس وضعیت
        status_counts = db.query(
            Order.status,
            func.count(Order.id)
        ).group_by(Order.status).all()
        
        status_breakdown = {status: count for status, count in status_counts if status}
        
        return {
            "total_orders": total,
            "with_tracking": with_tracking,
            "without_tracking": without_tracking,
            "status_breakdown": status_breakdown
        }
    
    except Exception as e:
        print(f"❌ خطا در دریافت آمار: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/orders/sync")
async def sync_orders_from_api(
    request: SyncOrdersRequest,
    db: Session = Depends(get_db)
):
    """همگام‌سازی سفارشات از API دیجی‌کالا"""
    try:
        from utils.api_core import get_all_orders, orders_to_dataframe, load_session_cookies, format_cookies_for_requests
        
        print("\n🔄 شروع همگام‌سازی...")
        
        orders_sbs = get_all_orders(use_ship_by_seller=True)
        print("📡 دریافت از Marketplace...")
        orders_mp = get_all_orders(use_ship_by_seller=False)
        
        all_orders_dict = {o['shipmentId']: o for o in orders_sbs}
        all_orders_dict.update({o['shipmentId']: o for o in orders_mp})
        
        total_fetched = len(all_orders_dict)
        print(f"✅ مجموع: {total_fetched} سفارش منحصر به فرد")
        
        if total_fetched == 0:
            return {
                "success": False,
                "message": "هیچ سفارش جدیدی از API دریافت نشد",
                "new_orders": 0,
                "updated_orders": 0,
                "total": 0
            }
        
        print("🔄 پردازش داده‌ها...")
        
        cookies_list = load_session_cookies()
        cookies_dict = format_cookies_for_requests(cookies_list) if cookies_list else None
        
        fresh_df = orders_to_dataframe(
            list(all_orders_dict.values()),
            fetch_details=request.fetch_full_details,
            cookies_dict=cookies_dict
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
        
        print("💾 ذخیره در دیتابیس...")
        
        grouped = fresh_df.groupby('شناسه محموله')
        
        for shipment_id_raw, group in grouped:
            shipment_id = normalize_id(shipment_id_raw)
            
            if not shipment_id:
                continue
            
            existing_order = db.query(Order).filter_by(shipment_id=shipment_id).first()
            
            if existing_order:
                first_row = group.iloc[0]
                existing_order.status = first_row.get('وضعیت', existing_order.status)
                if first_row.get('کد رهگیری') and first_row.get('کد رهگیری') != 'نامشخص':
                    existing_order.tracking_code = first_row.get('کد رهگیری')
                existing_order.updated_at = datetime.utcnow()
                updated_count += 1
                
                for _, row in group.iterrows():
                    product_code = normalize_id(row.get('کد محصول (DKP)', ''))
                    
                    existing_item = db.query(OrderItem).filter_by(
                        order_id=existing_order.id,
                        product_code=product_code
                    ).first()
                    
                    if existing_item:
                        existing_item.quantity = int(row.get('تعداد', 1)) if pd.notna(row.get('تعداد')) else 1
                        existing_item.price = float(row.get('مبلغ', 0)) if pd.notna(row.get('مبلغ')) else 0
                    else:
                        new_item = OrderItem(
                            order_id=existing_order.id,
                            product_title=row.get('عنوان سفارش', ''),
                            product_code=product_code,
                            product_image=row.get('تصویر محصول'),
                            quantity=int(row.get('تعداد', 1)) if pd.notna(row.get('تعداد')) else 1,
                            price=float(row.get('مبلغ', 0)) if pd.notna(row.get('مبلغ')) else 0
                        )
                        db.add(new_item)
            else:
                first_row = group.iloc[0]
                
                order = Order(
                    order_code=normalize_id(first_row.get('کد سفارش', '')),
                    shipment_id=shipment_id,
                    customer_name=first_row.get('نام مشتری', ''),
                    customer_phone=first_row.get('شماره تلفن', ''),
                    status=first_row.get('وضعیت', ''),
                    province=first_row.get('استان', ''),
                    city=first_row.get('شهر', ''),
                    full_address=first_row.get('آدرس کامل', ''),
                    postal_code=first_row.get('کد پستی', ''),
                    tracking_code=first_row.get('کد رهگیری') if pd.notna(first_row.get('کد رهگیری')) and first_row.get('کد رهگیری') != 'نامشخص' else None,
                    order_date_persian=first_row.get('تاریخ ثبت', '')
                )
                db.add(order)
                db.flush()
                
                for _, row in group.iterrows():
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
                
                if len(group) > 1:
                    print(f"   📦 سفارش چندقلمی: {shipment_id} ({len(group)} قلم)")
        
        db.commit()
        
        print(f"✅ همگام‌سازی کامل: {new_count} جدید، {updated_count} به‌روزرسانی")
        
        return {
            "success": True,
            "message": f"همگام‌سازی موفق: {new_count} سفارش جدید، {updated_count} سفارش به‌روزرسانی شد",
            "new_orders": new_count,
            "updated_orders": updated_count,
            "total": new_count + updated_count
        }
    
    except ImportError as e:
        print(f"❌ خطای Import: {e}")
        import traceback
        traceback.print_exc()
        return {
            "success": False,
            "message": f"خطا: ماژول utils یافت نشد - {str(e)}",
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
            "new_orders": 0,
            "updated_orders": 0,
            "total": 0
        }


@router.post("/orders/confirm-new")
async def confirm_new_orders(
    request: ConfirmOrdersRequest = ConfirmOrdersRequest(),
    db: Session = Depends(get_db)
):
    """
    تایید سفارشات جدید (تغییر وضعیت به processing)
    اگر shipment_ids خالی باشد، همه سفارشات با وضعیت "سفارش جدید" تایید می‌شوند
    """
    try:
        from utils.api_core import load_session_cookies, format_cookies_for_requests
        
        print("\n✅ شروع تایید سفارشات جدید...")
        
        # بارگذاری کوکی‌ها
        cookies_list = load_session_cookies()
        if not cookies_list:
            return {
                "success": False,
                "message": "کوکی‌ها یافت نشد. لطفاً ابتدا وارد سیستم شوید.",
                "confirmed": 0,
                "failed": 0,
                "total": 0
            }
        
        cookies_dict = format_cookies_for_requests(cookies_list)
        
        # پیدا کردن سفارشات
        if request.shipment_ids:
            # تایید سفارشات خاص
            orders = db.query(Order).filter(
                Order.shipment_id.in_([str(sid) for sid in request.shipment_ids])
            ).all()
        else:
            # تایید همه سفارشات جدید
            orders = db.query(Order).filter(
                Order.status.in_(['سفارش جدید', 'new', 'New Order'])
            ).all()
        
        if not orders:
            return {
                "success": True,
                "message": "هیچ سفارش جدیدی برای تایید یافت نشد",
                "confirmed": 0,
                "failed": 0,
                "total": 0
            }
        
        print(f"📦 تعداد سفارشات برای تایید: {len(orders)}")
        
        confirmed_count = 0
        failed_count = 0
        results = []
        
        for order in orders:
            print(f"   🔄 تایید {order.shipment_id}...", end=" ")
            
            success, message = send_confirm_request(
                int(order.shipment_id),
                cookies_dict
            )
            
            if success:
                # به‌روزرسانی وضعیت در دیتابیس
                order.status = "در حال پردازش"
                order.updated_at = datetime.utcnow()
                confirmed_count += 1
                print("✅")
                
                results.append({
                    "shipment_id": order.shipment_id,
                    "order_code": order.order_code,
                    "success": True,
                    "message": "تایید شد"
                })
            else:
                failed_count += 1
                print(f"❌ {message}")
                
                results.append({
                    "shipment_id": order.shipment_id,
                    "order_code": order.order_code,
                    "success": False,
                    "message": message
                })
        
        db.commit()
        
        print(f"\n✅ تایید کامل: {confirmed_count} موفق، {failed_count} ناموفق")
        
        return {
            "success": True,
            "message": f"{confirmed_count} سفارش تایید شد، {failed_count} ناموفق",
            "confirmed": confirmed_count,
            "failed": failed_count,
            "total": len(orders),
            "results": results
        }
    
    except Exception as e:
        print(f"❌ خطا در تایید: {e}")
        import traceback
        traceback.print_exc()
        db.rollback()
        return {
            "success": False,
            "message": f"خطا در تایید سفارشات: {str(e)}",
            "confirmed": 0,
            "failed": 0,
            "total": 0
        }