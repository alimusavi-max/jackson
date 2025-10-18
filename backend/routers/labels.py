# backend/routers/labels.py
from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import StreamingResponse
from typing import List, Optional
from pydantic import BaseModel
from sqlalchemy.orm import Session
import io
from datetime import datetime
import sys
import os

# اضافه کردن مسیر backend به sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import توابع label generation
try:
    from utils.label_core import (
        generate_label_portrait,
        generate_label_landscape,
        create_pdf_two_labels,
        get_font_path
    )
    from reportlab.lib.pagesizes import A5
    LABEL_CORE_AVAILABLE = True
    print("✅ utils.label_core imported successfully")
except ImportError as e:
    LABEL_CORE_AVAILABLE = False
    print(f"❌ خطا در import utils.label_core: {e}")
    import traceback
    traceback.print_exc()

# Import API core برای دریافت اطلاعات
try:
    from utils.api_core import get_customer_info, format_cookies_for_requests, load_session_cookies
    API_CORE_AVAILABLE = True
    print("✅ utils.api_core imported successfully")
except ImportError as e:
    API_CORE_AVAILABLE = False
    print(f"❌ خطا در import utils.api_core: {e}")

# Import database models
from database.models import Order, OrderItem, init_database, get_session

router = APIRouter(prefix="/labels", tags=["Labels"])

# ========== Pydantic Models ==========
class ProductItem(BaseModel):
    name: Optional[str] = None
    qty: Optional[int] = 1
    product_title: Optional[str] = None
    quantity: Optional[int] = None

class OrderData(BaseModel):
    id: int
    order_code: str
    shipment_id: str
    customer_name: str
    customer_phone: str
    city: str
    province: str
    full_address: str
    postal_code: str
    items: List[ProductItem]

class SenderInfo(BaseModel):
    name: str
    address: str
    postal_code: str
    phone: str

class LabelSettings(BaseModel):
    orientation: str = "portrait"
    include_datamatrix: bool = True
    include_qrcode: bool = True
    fetch_from_api: bool = False
    update_database: bool = False

class GenerateLabelsRequest(BaseModel):
    orders: List[OrderData]
    sender: SenderInfo
    settings: LabelSettings

# ========== Database Dependency ==========
def get_db():
    """دریافت session دیتابیس"""
    db_path = os.path.join(os.path.dirname(__file__), '..', '..', 'data', 'digikala_sales.db')
    engine = init_database(db_path)
    db = get_session(engine)
    try:
        yield db
    finally:
        db.close()

# ========== Endpoints ==========
@router.get("/test")
async def test_labels_api():
    """تست اتصال به API برچسب‌ها"""
    return {
        "status": "ok",
        "message": "Labels API is working!",
        "label_core_available": LABEL_CORE_AVAILABLE,
        "api_core_available": API_CORE_AVAILABLE
    }


@router.get("/test-font")
async def test_font():
    """تست فونت برای دیباگ"""
    if not LABEL_CORE_AVAILABLE:
        return {
            "status": "error",
            "message": "label_core not imported"
        }
    
    font_path = get_font_path()
    
    if font_path:
        import os
        exists = os.path.exists(font_path)
        size = os.path.getsize(font_path) if exists else 0
        
        return {
            "status": "found",
            "path": font_path,
            "exists": exists,
            "size_kb": round(size / 1024, 2)
        }
    else:
        return {
            "status": "not_found",
            "message": "فونت Vazir.ttf پیدا نشد"
        }


@router.get("/sample")
async def generate_sample_label():
    """تولید یک برچسب نمونه برای تست"""
    
    if not LABEL_CORE_AVAILABLE:
        raise HTTPException(status_code=500, detail="label_core not available")
    
    sender_info = {
        'name': 'فروشگاه تجارت دریای آرام',
        'address': 'تهران، خیابان ولیعصر، پلاک ۱۲۳',
        'postal_code': '1234567890',
        'phone': '021-12345678'
    }
    
    receiver_info = {
        'نام مشتری': 'علی احمدی',
        'شهر': 'تهران',
        'استان': 'تهران',
        'آدرس کامل': 'تهران، خیابان آزادی، کوچه شهید رضایی، پلاک ۴۵',
        'کد پستی': '9876543210',
        'شماره تلفن': '09123456789',
        'products': [
            {'name': 'گوشی موبایل سامسونگ Galaxy A54', 'qty': 1},
            {'name': 'کاور محافظ سیلیکونی', 'qty': 2},
        ]
    }
    
    try:
        print("🎨 در حال تولید برچسب نمونه...")
        
        # تولید برچسب
        label_img = generate_label_portrait(
            order_id='123456789',
            sender_info=sender_info,
            receiver_info=receiver_info,
            include_datamatrix=True
        )
        
        print("✅ برچسب تولید شد، در حال تبدیل به PNG...")
        
        # تبدیل به PNG
        img_buffer = io.BytesIO()
        label_img.save(img_buffer, format='PNG')
        img_buffer.seek(0)
        
        print("✅ PNG آماده است")
        
        return StreamingResponse(
            img_buffer,
            media_type="image/png",
            headers={
                "Content-Disposition": "inline; filename=sample_label.png"
            }
        )
        
    except Exception as e:
        print(f"❌ خطا در تولید برچسب نمونه: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"خطا: {str(e)}")


@router.post("/generate")
async def generate_labels(request: GenerateLabelsRequest, db: Session = Depends(get_db)):
    """تولید برچسب‌های پستی به صورت PDF با قابلیت دریافت از API و به‌روزرسانی دیتابیس"""
    
    if not LABEL_CORE_AVAILABLE:
        raise HTTPException(status_code=500, detail="label_core not available")
    
    if not request.orders:
        raise HTTPException(status_code=400, detail="لیست سفارشات خالی است")
    
    print(f"\n{'='*60}")
    print(f"🏷️  شروع تولید {len(request.orders)} برچسب")
    print(f"🔄 دریافت از API: {request.settings.fetch_from_api}")
    print(f"💾 به‌روزرسانی DB: {request.settings.update_database}")
    print(f"{'='*60}\n")
    
    # بررسی فونت
    font_path = get_font_path()
    if not font_path:
        raise HTTPException(
            status_code=500,
            detail="❌ فونت Vazir.ttf پیدا نشد! لطفاً فایل فونت را در روت پروژه قرار دهید."
        )
    
    print(f"✅ فونت پیدا شد: {font_path}\n")
    
    # آماده‌سازی کوکی‌ها برای API (اگر نیاز باشد)
    cookies_dict = None
    if request.settings.fetch_from_api and API_CORE_AVAILABLE:
        cookies_list = load_session_cookies()
        if cookies_list:
            cookies_dict = format_cookies_for_requests(cookies_list)
            print("✅ کوکی‌ها برای API آماده شد")
        else:
            print("⚠️ کوکی یافت نشد - دریافت از API ممکن نیست")
    
    # تبدیل اطلاعات فرستنده
    sender_info = {
        'name': request.sender.name,
        'address': request.sender.address,
        'postal_code': request.sender.postal_code,
        'phone': request.sender.phone
    }
    
    # تولید برچسب‌ها
    label_images = []
    updated_orders = []  # برای ذخیره سفارشاتی که باید در DB به‌روزرسانی شوند
    
    for idx, order in enumerate(request.orders, 1):
        try:
            print(f"📦 [{idx}/{len(request.orders)}] پردازش {order.order_code}...")
            
            # تبدیل اطلاعات گیرنده
            receiver_info = {
                'نام مشتری': order.customer_name,
                'شهر': order.city,
                'استان': order.province,
                'آدرس کامل': order.full_address,
                'کد پستی': order.postal_code,
                'شماره تلفن': order.customer_phone,
                'products': []
            }
            
            # 🔥 دریافت اطلاعات از API (اگر فعال باشد)
            api_data = None
            if request.settings.fetch_from_api and cookies_dict:
                print(f"   🔄 دریافت اطلاعات از API برای {order.shipment_id}...")
                try:
                    api_data = get_customer_info(order.shipment_id, cookies_dict)
                    if api_data:
                        print(f"   ✅ اطلاعات از API دریافت شد")
                        
                        # به‌روزرسانی receiver_info با داده‌های API
                        if api_data.get('address'):
                            receiver_info['آدرس کامل'] = api_data['address']
                        if api_data.get('postalCode'):
                            receiver_info['کد پستی'] = api_data['postalCode']
                        if api_data.get('phoneNumber'):
                            receiver_info['شماره تلفن'] = api_data['phoneNumber']
                        if api_data.get('city'):
                            receiver_info['شهر'] = api_data['city']
                        if api_data.get('state'):
                            receiver_info['استان'] = api_data['state']
                        
                        # ذخیره برای به‌روزرسانی دیتابیس
                        if request.settings.update_database:
                            updated_orders.append({
                                'order_code': order.order_code,
                                'api_data': api_data,
                                'order_db_id': order.id
                            })
                    else:
                        print(f"   ⚠️ اطلاعات از API دریافت نشد")
                except Exception as e:
                    print(f"   ⚠️ خطا در دریافت از API: {e}")
            
            # تبدیل اطلاعات محصولات
            for item in order.items:
                product_name = item.name or item.product_title or 'نامشخص'
                product_qty = item.qty or item.quantity or 1
                
                receiver_info['products'].append({
                    'name': product_name,
                    'qty': product_qty
                })
            
            # تولید برچسب
            if request.settings.orientation == "portrait":
                label_img = generate_label_portrait(
                    order_id=order.order_code,
                    sender_info=sender_info,
                    receiver_info=receiver_info,
                    include_datamatrix=request.settings.include_datamatrix
                )
            else:
                label_img = generate_label_landscape(
                    order_id=order.order_code,
                    sender_info=sender_info,
                    receiver_info=receiver_info
                )
            
            # ذخیره تصویر در BytesIO
            img_buffer = io.BytesIO()
            label_img.save(img_buffer, format='PNG')
            img_buffer.seek(0)
            label_images.append(img_buffer)
            
            print(f"   ✅ برچسب {order.order_code} تولید شد")
            
        except Exception as e:
            print(f"   ❌ خطا در تولید برچسب {order.order_code}: {e}")
            import traceback
            traceback.print_exc()
            continue
    
    if not label_images:
        raise HTTPException(status_code=500, detail="❌ هیچ برچسبی تولید نشد")
    
    # 🔥 به‌روزرسانی دیتابیس (اگر فعال باشد)
    updated_count = 0
    if request.settings.update_database and updated_orders:
        print(f"\n💾 به‌روزرسانی {len(updated_orders)} سفارش در دیتابیس...")
        
        for update_info in updated_orders:
            try:
                # پیدا کردن سفارش در DB
                db_order = db.query(Order).filter(
                    Order.id == update_info['order_db_id']
                ).first()
                
                if db_order:
                    api_data = update_info['api_data']
                    needs_update = False
                    
                    # به‌روزرسانی فقط فیلدهای خالی یا نامشخص
                    if api_data.get('address') and (not db_order.full_address or db_order.full_address == 'نامشخص'):
                        db_order.full_address = api_data['address']
                        needs_update = True
                    
                    if api_data.get('postalCode') and (not db_order.postal_code or db_order.postal_code == 'نامشخص'):
                        db_order.postal_code = api_data['postalCode']
                        needs_update = True
                    
                    if api_data.get('phoneNumber') and (not db_order.customer_phone or db_order.customer_phone == 'نامشخص'):
                        db_order.customer_phone = api_data['phoneNumber']
                        needs_update = True
                    
                    if api_data.get('city') and (not db_order.city or db_order.city == 'نامشخص'):
                        db_order.city = api_data['city']
                        needs_update = True
                    
                    if api_data.get('state') and (not db_order.province or db_order.province == 'نامشخص'):
                        db_order.province = api_data['state']
                        needs_update = True
                    
                    if needs_update:
                        db_order.updated_at = datetime.utcnow()
                        updated_count += 1
                        print(f"   ✅ سفارش {update_info['order_code']} به‌روزرسانی شد")
                
            except Exception as e:
                print(f"   ⚠️ خطا در به‌روزرسانی {update_info['order_code']}: {e}")
        
        try:
            db.commit()
            print(f"\n✅ {updated_count} سفارش در دیتابیس به‌روزرسانی شد")
        except Exception as e:
            db.rollback()
            print(f"❌ خطا در commit: {e}")
    
    print(f"\n✅ {len(label_images)} برچسب تولید شد")
    print(f"📄 در حال ایجاد PDF...\n")
    
    # ایجاد PDF با تابع از utils
    try:
        # ایجاد فایل موقت برای PDF
        import tempfile
        temp_pdf = tempfile.NamedTemporaryFile(delete=False, suffix='.pdf')
        temp_path = temp_pdf.name
        temp_pdf.close()
        
        # تولید PDF
        create_pdf_two_labels(
            label_images=label_images,
            output_path=temp_path,
            page_size=A5
        )
        
        # خواندن PDF
        with open(temp_path, 'rb') as f:
            pdf_data = f.read()
        
        # حذف فایل موقت
        os.unlink(temp_path)
        
        pdf_buffer = io.BytesIO(pdf_data)
        
        # نام فایل
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"labels_{timestamp}.pdf"
        
        print(f"✅ PDF ایجاد شد: {filename}")
        if updated_count > 0:
            print(f"💾 {updated_count} سفارش در دیتابیس به‌روزرسانی شد")
        print(f"{'='*60}\n")
        
        return StreamingResponse(
            pdf_buffer,
            media_type="application/pdf",
            headers={
                "Content-Disposition": f"attachment; filename={filename}"
            }
        )
        
    except Exception as e:
        print(f"❌ خطا در ایجاد PDF: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"خطا در ایجاد PDF: {str(e)}")