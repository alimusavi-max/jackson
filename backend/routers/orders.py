from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime
import pandas as pd
from typing import Optional

# Import از ماژول‌های پروژه
from database.models import Order, OrderItem, Base, init_database, get_session
from utils.helpers import normalize_id
from pydantic import BaseModel

router = APIRouter()

# ========== Pydantic Models ==========
class SyncOrdersRequest(BaseModel):
    fetch_full_details: bool = False

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

# ========== Endpoints ==========
@router.post("/orders/sync")
async def sync_orders_from_api(
    request: SyncOrdersRequest,
    db: Session = Depends(get_db)
):
    """
    همگام‌سازی سفارشات از API دیجی‌کالا
    """
    try:
        # Import توابع utils
        from utils.api_core import get_all_orders, orders_to_dataframe, load_session_cookies, format_cookies_for_requests
        
        print("\n🔄 شروع همگام‌سازی...")
        
        # دریافت سفارشات از Ship-by-Seller
        print("📡 دریافت از Ship-by-Seller...")
        orders_sbs = get_all_orders(use_ship_by_seller=True)
        
        # دریافت از Marketplace
        print("📡 دریافت از Marketplace...")
        orders_mp = get_all_orders(use_ship_by_seller=False)
        
        # ترکیب و حذف تکراری
        all_orders_dict = {o['shipmentId']: o for o in orders_sbs}
        all_orders_dict.update({o['shipmentId']: o for o in orders_mp})
        
        total_fetched = len(all_orders_dict)
        print(f"✅ مجموع: {total_fetched} سفارش منحصر به فرد")
        
        if total_fetched == 0:
            return {
                "success": False,
                "message": "هیچ سفارش جدیدی از API دریافت نشد. لطفاً کوکی‌ها را بررسی کنید.",
                "new_orders": 0,
                "updated_orders": 0,
                "total": 0
            }
        
        # تبدیل به DataFrame
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
        
        # گروه‌بندی بر اساس شناسه محموله (سفارشات چندقلمی)
        grouped = fresh_df.groupby('شناسه محموله')
        
        for shipment_id_raw, group in grouped:
            shipment_id = normalize_id(shipment_id_raw)
            
            if not shipment_id:
                continue
            
            # بررسی وجود سفارش
            existing_order = db.query(Order).filter_by(shipment_id=shipment_id).first()
            
            if existing_order:
                # به‌روزرسانی سفارش موجود
                first_row = group.iloc[0]
                existing_order.status = first_row.get('وضعیت', existing_order.status)
                if first_row.get('کد رهگیری') and first_row.get('کد رهگیری') != 'نامشخص':
                    existing_order.tracking_code = first_row.get('کد رهگیری')
                existing_order.updated_at = datetime.utcnow()
                updated_count += 1
                
                # به‌روزرسانی آیتم‌های موجود یا افزودن جدید
                for _, row in group.iterrows():
                    product_code = normalize_id(row.get('کد محصول (DKP)', ''))
                    
                    # چک کردن آیتم موجود
                    existing_item = db.query(OrderItem).filter_by(
                        order_id=existing_order.id,
                        product_code=product_code
                    ).first()
                    
                    if existing_item:
                        # به‌روزرسانی آیتم
                        existing_item.quantity = int(row.get('تعداد', 1)) if pd.notna(row.get('تعداد')) else 1
                        existing_item.price = float(row.get('مبلغ', 0)) if pd.notna(row.get('مبلغ')) else 0
                    else:
                        # افزودن آیتم جدید
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
                # ایجاد سفارش جدید
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
                
                # افزودن تمام آیتم‌های سفارش (چندقلمی)
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
                
                # نمایش اطلاعات سفارش چندقلمی
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