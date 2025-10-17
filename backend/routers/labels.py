# backend/routers/labels.py
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from typing import List, Optional
from pydantic import BaseModel
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

class GenerateLabelsRequest(BaseModel):
    orders: List[OrderData]
    sender: SenderInfo
    settings: LabelSettings

# ========== Endpoints ==========
@router.get("/test")
async def test_labels_api():
    """تست اتصال به API برچسب‌ها"""
    return {
        "status": "ok",
        "message": "Labels API is working!",
        "label_core_available": LABEL_CORE_AVAILABLE
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
async def generate_labels(request: GenerateLabelsRequest):
    """تولید برچسب‌های پستی به صورت PDF"""
    
    if not LABEL_CORE_AVAILABLE:
        raise HTTPException(status_code=500, detail="label_core not available")
    
    if not request.orders:
        raise HTTPException(status_code=400, detail="لیست سفارشات خالی است")
    
    print(f"\n{'='*60}")
    print(f"🏷️  شروع تولید {len(request.orders)} برچسب")
    print(f"{'='*60}\n")
    
    # بررسی فونت
    font_path = get_font_path()
    if not font_path:
        raise HTTPException(
            status_code=500,
            detail="❌ فونت Vazir.ttf پیدا نشد! لطفاً فایل فونت را در روت پروژه قرار دهید."
        )
    
    print(f"✅ فونت پیدا شد: {font_path}\n")
    
    # تبدیل اطلاعات فرستنده
    sender_info = {
        'name': request.sender.name,
        'address': request.sender.address,
        'postal_code': request.sender.postal_code,
        'phone': request.sender.phone
    }
    
    # تولید برچسب‌ها
    label_images = []
    
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