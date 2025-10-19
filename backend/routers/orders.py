# backend/routers/orders.py - نسخه کامل اصلاح شده
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func
from datetime import datetime
import pandas as pd
from typing import Optional, List
import requests
import time
import subprocess
import os
import sys
# backend/routers/orders.py - تابع confirm_new_orders با مدیریت کامل خطا

from pathlib import Path
from database.models import Order, OrderItem, Base, init_database, get_session
from utils.helpers import normalize_id
from pydantic import BaseModel

router = APIRouter()

# ========== Pydantic Models ==========
class SyncOrdersRequest(BaseModel):
    fetch_full_details: bool = False

class ConfirmOrdersRequest(BaseModel):
    shipment_ids: Optional[List[str]] = None

class OrderItemResponse(BaseModel):
    id: int
    product_title: str
    product_code: Optional[str]
    quantity: int
    price: float
    product_image: Optional[str] = None

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
    items_count: int
    total_quantity: int
    total_amount: float

    class Config:
        from_attributes = True

class OrdersListResponse(BaseModel):
    data: List[dict]
    total: int
    page: int
    limit: int

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

# ========== تابع کمکی برای محاسبه فیلدها ==========
def enrich_order_data(order: Order) -> dict:
    """اضافه کردن فیلدهای محاسباتی به سفارش"""
    try:
        items = order.items if order.items is not None else []
        
        items_count = len(items)
        total_quantity = sum(item.quantity for item in items) if items else 0
        total_amount = sum(item.price * item.quantity for item in items) if items else 0.0
        
        return {
            "id": order.id,
            "order_code": order.order_code or "",
            "shipment_id": order.shipment_id or "",
            "customer_name": order.customer_name or "نامشخص",
            "customer_phone": order.customer_phone or "نامشخص",
            "status": order.status or "نامشخص",
            "province": order.province or "نامشخص",
            "city": order.city or "نامشخص",
            "full_address": order.full_address or "نامشخص",
            "postal_code": order.postal_code or "نامشخص",
            "tracking_code": order.tracking_code,
            "order_date_persian": order.order_date_persian or "",
            "created_at": order.created_at.isoformat() if order.created_at else "",
            "updated_at": order.created_at.isoformat() if order.created_at else "",
            "items": [
                {
                    "id": item.id,
                    "product_title": item.product_title or "نامشخص",
                    "product_code": item.product_code or "نامشخص",
                    "product_image": item.product_image,
                    "quantity": item.quantity or 0,
                    "price": float(item.price or 0)
                }
                for item in items
            ],
            "items_count": items_count,
            "total_quantity": total_quantity,
            "total_amount": float(total_amount)
        }
    except Exception as e:
        print(f"❌ خطا در enrich_order_data برای سفارش {order.id}: {e}")
        import traceback
        traceback.print_exc()
        
        return {
            "id": order.id,
            "order_code": order.order_code or "",
            "shipment_id": order.shipment_id or "",
            "customer_name": order.customer_name or "نامشخص",
            "customer_phone": order.customer_phone or "نامشخص",
            "status": order.status or "نامشخص",
            "province": order.province or "نامشخص",
            "city": order.city or "نامشخص",
            "full_address": order.full_address or "نامشخص",
            "postal_code": order.postal_code or "نامشخص",
            "tracking_code": order.tracking_code,
            "order_date_persian": order.order_date_persian or "",
            "created_at": order.created_at,
            "updated_at": order.updated_at,
            "items": [],
            "items_count": 0,
            "total_quantity": 0,
            "total_amount": 0.0
        }

# ========== توابع کمکی برای Auto-Login ==========
def run_improved_login():
    """
    اجرای اسکریپت improved_login.py برای رفرش کردن کوکی‌ها
    """
    try:
        # پیدا کردن مسیر پروژه (یک پوشه بالاتر از backend)
        backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        project_root = os.path.dirname(backend_dir)
        login_script = os.path.join(project_root, 'improved_login.py')
        
        if not os.path.exists(login_script):
            print(f"❌ فایل improved_login.py یافت نشد در: {login_script}")
            return False
        
        print(f"\n🔐 در حال اجرای اسکریپت لاگین...")
        print(f"   مسیر: {login_script}")
        
        # اجرای اسکریپت با Python
        result = subprocess.run(
            [sys.executable, login_script],
            cwd=project_root,
            capture_output=True,
            text=True,
            timeout=120  # حداکثر 2 دقیقه
        )
        
        if result.returncode == 0:
            print("✅ لاگین موفقیت‌آمیز - کوکی‌ها به‌روز شدند")
            print(f"   خروجی: {result.stdout[:200]}")
            return True
        else:
            print(f"❌ لاگین ناموفق - کد خروج: {result.returncode}")
            print(f"   خطا: {result.stderr[:500]}")
            return False
            
    except subprocess.TimeoutExpired:
        print("⏱️ Timeout - اسکریپت لاگین بیش از حد طول کشید")
        return False
    except Exception as e:
        print(f"❌ خطا در اجرای improved_login.py: {e}")
        import traceback
        traceback.print_exc()
        return False


def reload_cookies():
    """
    بارگذاری مجدد کوکی‌ها از فایل
    """
    try:
        from utils.api_core import load_session_cookies, format_cookies_for_requests
        cookies_list = load_session_cookies()
        if cookies_list:
            cookies_dict = format_cookies_for_requests(cookies_list)
            print(f"✅ کوکی‌های جدید بارگذاری شد ({len(cookies_list)} کوکی)")
            return cookies_dict
        else:
            print("❌ فایل کوکی خالی است")
            return None
    except Exception as e:
        print(f"❌ خطا در بارگذاری مجدد کوکی‌ها: {e}")
        return None


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
    """دریافت لیست سفارشات با فیلترهای مختلف"""
    try:
        print(f"\n{'='*60}")
        print(f"📥 درخواست سفارشات: limit={limit}, offset={offset}")
        
        query = db.query(Order).options(joinedload(Order.items))
        
        if status:
            query = query.filter(Order.status == status)
            print(f"   فیلتر وضعیت: {status}")
        
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
            print(f"   فیلتر رهگیری: {has_tracking}")
        
        if search:
            search_term = f"%{search}%"
            query = query.filter(
                (Order.order_code.like(search_term)) |
                (Order.customer_name.like(search_term)) |
                (Order.customer_phone.like(search_term)) |
                (Order.shipment_id.like(search_term))
            )
            print(f"   جستجو: {search}")
        
        total_count = query.count()
        print(f"   📊 تعداد کل با فیلتر: {total_count}")
        
        orders = query.order_by(Order.created_at.desc()).offset(offset).limit(limit).all()
        
        print(f"   ✅ {len(orders)} سفارش دریافت شد")
        
        enriched_orders = []
        for order in orders:
            try:
                enriched = enrich_order_data(order)
                enriched_orders.append(enriched)
            except Exception as e:
                print(f"   ⚠️ خطا در پردازش سفارش {order.id}: {e}")
                continue
        
        print(f"   ✅ {len(enriched_orders)} سفارش پردازش شد")
        print(f"{'='*60}\n")
        
        return {
            "data": enriched_orders,
            "total": total_count,
            "page": offset // limit + 1 if limit > 0 else 1,
            "limit": limit
        }
    
    except Exception as e:
        print(f"❌ خطا در دریافت سفارشات: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=500, 
            detail=f"خطا در دریافت سفارشات: {str(e)}"
        )


@router.get("/orders/{order_id}")
async def get_order(
    order_id: int,
    db: Session = Depends(get_db)
):
    """دریافت جزئیات یک سفارش خاص"""
    try:
        print(f"\n📥 درخواست سفارش {order_id}")
        
        order = db.query(Order).options(joinedload(Order.items)).filter(Order.id == order_id).first()
        
        if not order:
            print(f"❌ سفارش {order_id} یافت نشد")
            raise HTTPException(status_code=404, detail="سفارش یافت نشد")
        
        print(f"✅ سفارش {order_id} دریافت شد")
        
        return enrich_order_data(order)
    
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ خطا: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/orders/stats/summary")
async def get_orders_summary(db: Session = Depends(get_db)):
    """آمار خلاصه سفارشات"""
    try:
        print("\n📊 محاسبه آمار سفارشات...")
        
        total = db.query(Order).count()
        
        with_tracking = db.query(Order).filter(
            Order.tracking_code.isnot(None),
            Order.tracking_code != '',
            Order.tracking_code != 'نامشخص'
        ).count()
        
        without_tracking = total - with_tracking
        
        status_counts = db.query(
            Order.status,
            func.count(Order.id)
        ).group_by(Order.status).all()
        
        status_breakdown = {status: count for status, count in status_counts if status}
        
        total_sales_query = db.query(
            func.sum(OrderItem.price * OrderItem.quantity)
        ).scalar()
        
        total_sales = float(total_sales_query) if total_sales_query else 0.0
        
        print(f"✅ آمار: {total} سفارش، {with_tracking} با رهگیری")
        
        return {
            "total_orders": total,
            "with_tracking": with_tracking,
            "without_tracking": without_tracking,
            "total_sales": total_sales,
            "status_breakdown": status_breakdown,
            "completion_rate": round((with_tracking / total * 100), 2) if total > 0 else 0
        }
    
    except Exception as e:
        print(f"❌ خطا در دریافت آمار: {e}")
        import traceback
        traceback.print_exc()
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
                
                new_status = first_row.get('وضعیت', existing_order.status)
                if new_status and new_status != existing_order.status:
                    print(f"   🔄 به‌روزرسانی وضعیت {shipment_id}: {existing_order.status} → {new_status}")
                    existing_order.status = new_status
                
                if first_row.get('کد رهگیری') and first_row.get('کد رهگیری') != 'نامشخص':
                    existing_order.tracking_code = first_row.get('کد رهگیری')
                
                if first_row.get('نام مشتری'):
                    existing_order.customer_name = first_row.get('نام مشتری')
                
                if first_row.get('شماره تلفن'):
                    existing_order.customer_phone = first_row.get('شماره تلفن')
                
                if first_row.get('شهر'):
                    existing_order.city = first_row.get('شهر')
                
                if first_row.get('استان'):
                    existing_order.province = first_row.get('استان')
                
                if first_row.get('آدرس کامل') and first_row.get('آدرس کامل') != 'نامشخص':
                    existing_order.full_address = first_row.get('آدرس کامل')
                
                if first_row.get('کد پستی') and first_row.get('کد پستی') != 'نامشخص':
                    existing_order.postal_code = first_row.get('کد پستی')
                
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
    تایید سفارشات جدید با ارسال به API دیجی‌کالا
    - مدیریت 401: اجرای اتوماتیک improved_login.py
    - مدیریت 429: رعایت Rate Limit با Retry
    """
    try:
        print("\n" + "="*60)
        print("✅ شروع تایید سفارشات جدید...")
        print("="*60)
        
        # بارگذاری کوکی‌ها
        from utils.api_core import load_session_cookies, format_cookies_for_requests
        
        cookies_list = load_session_cookies()
        if not cookies_list:
            return {
                "success": False,
                "message": "❌ کوکی‌های سشن یافت نشد. لطفاً ابتدا لاگین کنید.",
                "confirmed": 0,
                "failed": 0,
                "total": 0
            }
        
        cookies_dict = format_cookies_for_requests(cookies_list)
        
        # انتخاب سفارشات
        if request.shipment_ids and len(request.shipment_ids) > 0:
            print(f"📦 تایید {len(request.shipment_ids)} سفارش مشخص شده...")
            orders = db.query(Order).filter(
                Order.shipment_id.in_(request.shipment_ids)
            ).all()
        else:
            print("🔍 جستجوی سفارشات جدید...")
            orders = db.query(Order).filter(
                Order.status.in_(['سفارش جدید', 'new', 'New Order', 'جدید'])
            ).all()
        
        if not orders:
            print("⚠️ هیچ سفارش جدیدی یافت نشد")
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
        errors = []
        needs_relogin = False
        
        for order in orders:
            try:
                print(f"\n   🔄 پردازش سفارش {order.order_code} (shipment: {order.shipment_id})")
                
                # ارسال درخواست به API
                success, error_msg = await send_confirm_request(
                    order.shipment_id, 
                    cookies_dict
                )
                
                if success:
                    order.status = "در حال آماده‌سازی"
                    order.updated_at = datetime.utcnow()
                    confirmed_count += 1
                    print(f"   ✅ تایید شد")
                else:
                    if "401" in error_msg or "unauthorized" in error_msg.lower():
                        needs_relogin = True
                        print(f"   ⚠️ نیاز به لاگین مجدد")
                        break
                    else:
                        failed_count += 1
                        errors.append(f"سفارش {order.order_code}: {error_msg}")
                        print(f"   ❌ خطا: {error_msg}")
                
            except Exception as e:
                print(f"   ❌ خطا در پردازش: {e}")
                errors.append(f"سفارش {order.order_code}: {str(e)}")
                failed_count += 1
        
        # اگر نیاز به لاگین مجدد بود
        if needs_relogin:
            print("\n🔑 اجرای لاگین مجدد...")
            login_success = await run_improved_login()
            
            if login_success:
                print("✅ لاگین موفق. ادامه تایید سفارشات...")
                # بارگذاری مجدد کوکی‌ها
                cookies_list = load_session_cookies()
                cookies_dict = format_cookies_for_requests(cookies_list)
                
                # ادامه تایید سفارشات باقی‌مانده
                for order in orders[confirmed_count:]:
                    try:
                        print(f"\n   🔄 پردازش سفارش {order.order_code}")
                        
                        success, error_msg = await send_confirm_request(
                            order.shipment_id, 
                            cookies_dict
                        )
                        
                        if success:
                            order.status = "در حال آماده‌سازی"
                            order.updated_at = datetime.utcnow()
                            confirmed_count += 1
                            print(f"   ✅ تایید شد")
                        else:
                            failed_count += 1
                            errors.append(f"سفارش {order.order_code}: {error_msg}")
                            print(f"   ❌ خطا: {error_msg}")
                    
                    except Exception as e:
                        print(f"   ❌ خطا: {e}")
                        errors.append(f"سفارش {order.order_code}: {str(e)}")
                        failed_count += 1
            else:
                print("❌ لاگین مجدد ناموفق بود")
                return {
                    "success": False,
                    "message": "خطا در لاگین مجدد. لطفاً به‌صورت دستی لاگین کنید.",
                    "confirmed": confirmed_count,
                    "failed": len(orders) - confirmed_count,
                    "total": len(orders),
                    "errors": ["لاگین مجدد ناموفق"]
                }
        
        # Commit تغییرات
        try:
            db.commit()
            print(f"\n💾 تغییرات در دیتابیس ذخیره شد")
        except Exception as e:
            print(f"❌ خطا در ذخیره: {e}")
            db.rollback()
            return {
                "success": False,
                "message": f"خطا در ذخیره تغییرات: {str(e)}",
                "confirmed": 0,
                "failed": len(orders),
                "total": len(orders),
                "errors": [str(e)]
            }
        
        print("\n" + "="*60)
        print(f"✅ تایید کامل شد!")
        print(f"   ✓ موفق: {confirmed_count}")
        print(f"   ✗ ناموفق: {failed_count}")
        print("="*60 + "\n")
        
        return {
            "success": True,
            "message": f"{confirmed_count} سفارش تایید شد" + (f" ({failed_count} ناموفق)" if failed_count > 0 else ""),
            "confirmed": confirmed_count,
            "failed": failed_count,
            "total": len(orders),
            "errors": errors if errors else None
        }
    
    except Exception as e:
        print(f"\n❌ خطای کلی: {e}")
        import traceback
        traceback.print_exc()
        db.rollback()
        return {
            "success": False,
            "message": f"خطا: {str(e)}",
            "confirmed": 0,
            "failed": 0,
            "total": 0
        }


async def send_confirm_request(shipment_id: str, cookies_dict: dict, max_retries: int = 5):
    """
    ارسال درخواست تایید سفارش به API دیجی‌کالا
    - مدیریت 429 با Retry و Backoff
    - مدیریت 401 با بازگشت خطا
    
    Returns:
        tuple: (success: bool, error_message: str)
    """
    url = "https://seller.digikala.com/api/v2/ship-by-seller-orders/update-status"
    
    headers = {
        "accept": "application/json, text/plain, */*",
        "accept-language": "en-GB,en;q=0.9,fa-IR;q=0.8,fa;q=0.7,en-US;q=0.6",
        "content-type": "application/json",
        "origin": "https://seller.digikala.com",
        "referer": "https://seller.digikala.com/pwa/orders/ship-by-seller",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36",
        "x-web-optimize-response": "1"
    }
    
    payload = {
        "order_shipment_id": int(shipment_id),
        "new_status": "processing"
    }
    
    retry_count = 0
    base_delay = 2  # ثانیه
    
    while retry_count < max_retries:
        try:
            print(f"      📡 ارسال درخواست (تلاش {retry_count + 1}/{max_retries})...")
            
            response = requests.put(
                url,
                headers=headers,
                cookies=cookies_dict,
                json=payload,
                timeout=30
            )
            
            # ✅ موفقیت
            if response.status_code == 200:
                print(f"      ✅ پاسخ 200: موفق")
                return True, ""
            
            # ⚠️ 401 Unauthorized
            elif response.status_code == 401:
                print(f"      ⚠️ پاسخ 401: نیاز به لاگین مجدد")
                return False, "401 Unauthorized - نیاز به لاگین مجدد"
            
            # ⏳ 429 Rate Limit
            elif response.status_code == 429:
                retry_count += 1
                
                # بررسی Retry-After header
                retry_after = response.headers.get("Retry-After")
                
                if retry_after:
                    try:
                        wait_time = int(retry_after)
                        print(f"      ⏳ 429 - سرور درخواست کرد {wait_time} ثانیه صبر کنید...")
                    except ValueError:
                        # اگر Retry-After یک تاریخ بود (نادر)
                        wait_time = base_delay * (2 ** retry_count)
                        print(f"      ⏳ 429 - Backoff: {wait_time} ثانیه...")
                else:
                    # Exponential Backoff
                    wait_time = base_delay * (2 ** retry_count)
                    print(f"      ⏳ 429 - Exponential Backoff: {wait_time} ثانیه...")
                
                if retry_count < max_retries:
                    print(f"      ⏰ صبر {wait_time} ثانیه قبل از تلاش مجدد...")
                    time.sleep(wait_time)
                    continue
                else:
                    print(f"      ❌ تعداد تلاش به حداکثر رسید")
                    return False, f"429 Rate Limit - پس از {max_retries} تلاش ناموفق"
            
            # ❌ خطاهای دیگر
            else:
                error_text = response.text[:200]
                print(f"      ❌ پاسخ {response.status_code}: {error_text}")
                return False, f"خطای HTTP {response.status_code}: {error_text}"
        
        except requests.exceptions.Timeout:
            retry_count += 1
            print(f"      ⏱️ Timeout - تلاش مجدد...")
            if retry_count < max_retries:
                time.sleep(base_delay)
                continue
            else:
                return False, "Timeout پس از چندین تلاش"
        
        except requests.exceptions.ConnectionError as e:
            retry_count += 1
            print(f"      🔌 خطای اتصال: {e}")
            if retry_count < max_retries:
                time.sleep(base_delay * 2)
                continue
            else:
                return False, f"خطای اتصال: {str(e)}"
        
        except Exception as e:
            print(f"      ❌ خطای غیرمنتظره: {e}")
            return False, f"خطا: {str(e)}"
    
    return False, "ناموفق پس از چندین تلاش"


async def run_improved_login():
    """
    اجرای اسکریپت improved_login.py برای لاگین مجدد
    
    Returns:
        bool: True اگر لاگین موفق بود
    """
    try:
        print("\n" + "="*60)
        print("🔑 اجرای improved_login.py...")
        print("="*60)
        
        # مسیر اسکریپت (همسطح با backend/)
        backend_dir = Path(__file__).resolve().parent.parent
        login_script = backend_dir.parent / "improved_login.py"
        
        if not login_script.exists():
            print(f"❌ فایل {login_script} یافت نشد!")
            return False
        
        print(f"📂 مسیر اسکریپت: {login_script}")
        
        # اجرای اسکریپت
        print("⏳ در حال اجرا... (ممکن است چند دقیقه طول بکشد)")
        
        result = subprocess.run(
            ["python", str(login_script)],
            capture_output=True,
            text=True,
            timeout=300,  # 5 دقیقه timeout
            encoding='utf-8',
            errors='replace'
        )
        
        print("\n📄 خروجی اسکریپت:")
        print(result.stdout)
        
        if result.stderr:
            print("\n⚠️ خطاها:")
            print(result.stderr)
        
        # بررسی موفقیت
        if result.returncode == 0:
            print("\n✅ لاگین با موفقیت انجام شد!")
            
            # بررسی وجود فایل کوکی
            cookies_file = backend_dir / "sessions" / "digikala_cookies.json"
            if cookies_file.exists():
                print(f"✅ فایل کوکی یافت شد: {cookies_file}")
                return True
            else:
                print(f"⚠️ فایل کوکی یافت نشد: {cookies_file}")
                return False
        else:
            print(f"\n❌ لاگین ناموفق - Return code: {result.returncode}")
            return False
    
    except subprocess.TimeoutExpired:
        print("\n❌ Timeout: اسکریپت لاگین بیش از حد طول کشید")
        return False
    
    except Exception as e:
        print(f"\n❌ خطا در اجرای اسکریپت لاگین: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    finally:
        print("="*60 + "\n")