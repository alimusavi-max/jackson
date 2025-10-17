# backend/routers/labels.py
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse, JSONResponse
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Dict, Optional
import io
import time
import json
from datetime import datetime

from database.models import Order, OrderItem, get_session, init_database
from utils.label_core import generate_label_portrait, generate_label_landscape, create_pdf_two_labels
from reportlab.lib.pagesizes import A5, portrait, landscape

router = APIRouter(prefix="/labels", tags=["برچسب‌های پستی"])

def get_db():
    engine = init_database("digikala_sales.db")
    db = get_session(engine)
    try:
        yield db
    finally:
        db.close()

# Pydantic Models
class SenderInfo(BaseModel):
    name: str
    address: str
    postal_code: str
    phone: str

class OrderForLabel(BaseModel):
    id: int
    order_code: str
    shipment_id: str
    customer_name: str
    customer_phone: str
    city: str
    province: str
    full_address: str
    postal_code: str
    items: List[Dict]

class LabelSettings(BaseModel):
    orientation: str  # "portrait" or "landscape"
    include_datamatrix: bool = True
    include_qrcode: bool = True
    fetch_from_api: bool = False

class GenerateLabelRequest(BaseModel):
    orders: List[OrderForLabel]
    sender: SenderInfo
    settings: LabelSettings


@router.post("/generate")
async def generate_labels(
    request: GenerateLabelRequest,
    db: Session = Depends(get_db)
):
    """
    تولید PDF برچسب‌های پستی با نمایش پیشرفت
    """
    try:
        print(f"\n{'='*60}")
        print(f"🏷️  شروع تولید {len(request.orders)} برچسب")
        print(f"{'='*60}\n")
        
        labels = []
        total = len(request.orders)
        
        for idx, order_data in enumerate(request.orders, 1):
            print(f"[{idx}/{total}] پردازش سفارش {order_data.order_code}...")
            
            # آماده‌سازی اطلاعات گیرنده
            receiver_info = {
                'نام مشتری': order_data.customer_name,
                'city': order_data.city,
                'شهر': order_data.city,
                'استان': order_data.province,
                'state': order_data.province,
                'address': order_data.full_address,
                'آدرس کامل': order_data.full_address,
                'postalCode': order_data.postal_code,
                'کد پستی': order_data.postal_code,
                'phoneNumber': order_data.customer_phone,
                'شماره تلفن': order_data.customer_phone,
                'products': []
            }
            
            # تبدیل items به فرمت مورد نیاز
            for item in order_data.items:
                receiver_info['products'].append({
                    'name': item.get('product_title', 'نامشخص'),
                    'qty': item.get('quantity', 1),
                    'product_title': item.get('product_title', 'نامشخص'),
                    'quantity': item.get('quantity', 1)
                })
            
            print(f"   📦 محصولات: {len(receiver_info['products'])} قلم")
            if len(receiver_info['products']) > 1:
                print(f"   🎁 سفارش چندقلمی!")
            
            # اطلاعات فرستنده
            sender_info = {
                'name': request.sender.name,
                'address': request.sender.address,
                'postal_code': request.sender.postal_code,
                'phone': request.sender.phone
            }
            
            # تولید برچسب
            try:
                if request.settings.orientation == "portrait":
                    img = generate_label_portrait(
                        order_data.order_code,
                        sender_info,
                        receiver_info,
                        include_datamatrix=request.settings.include_datamatrix
                    )
                else:
                    img = generate_label_landscape(
                        order_data.order_code,
                        sender_info,
                        receiver_info
                    )
                
                # تبدیل به BytesIO
                buf = io.BytesIO()
                img.save(buf, format="PNG")
                buf.seek(0)
                labels.append(buf)
                
                print(f"   ✅ برچسب ایجاد شد")
                
            except Exception as e:
                print(f"   ❌ خطا در تولید برچسب: {e}")
                import traceback
                traceback.print_exc()
                raise
        
        print(f"\n{'='*60}")
        print(f"📄 ساخت PDF...")
        print(f"{'='*60}\n")
        
        # ساخت PDF
        pdf_buffer = io.BytesIO()
        
        if request.settings.orientation == "portrait":
            page_size = portrait(A5)
        else:
            page_size = landscape(A5)
        
        # تولید PDF موقت
        import tempfile
        import os
        
        with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as temp_file:
            temp_path = temp_file.name
        
        try:
            create_pdf_two_labels(labels, temp_path, page_size)
            
            # خواندن PDF
            with open(temp_path, "rb") as f:
                pdf_data = f.read()
            
            print(f"✅ PDF ایجاد شد: {len(pdf_data)} bytes")
            
        finally:
            # پاک کردن فایل موقت
            if os.path.exists(temp_path):
                os.remove(temp_path)
        
        # بازگرداندن PDF
        return StreamingResponse(
            io.BytesIO(pdf_data),
            media_type="application/pdf",
            headers={
                "Content-Disposition": f"attachment; filename=labels_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
            }
        )
        
    except Exception as e:
        print(f"\n{'='*60}")
        print(f"❌ خطای کلی:")
        print(f"{'='*60}")
        import traceback
        traceback.print_exc()
        
        raise HTTPException(
            status_code=500,
            detail=f"خطا در تولید برچسب: {str(e)}"
        )


@router.post("/generate-stream")
async def generate_labels_stream(request: GenerateLabelRequest):
    """
    تولید برچسب‌ها با Server-Sent Events برای نمایش پیشرفت
    """
    async def event_generator():
        try:
            total = len(request.orders)
            yield f"data: {json.dumps({'type': 'start', 'total': total})}\n\n"
            
            labels = []
            
            for idx, order_data in enumerate(request.orders, 1):
                # ارسال پیشرفت
                progress = {
                    'type': 'progress',
                    'current': idx,
                    'total': total,
                    'order_code': order_data.order_code,
                    'percentage': int((idx / total) * 100)
                }
                yield f"data: {json.dumps(progress)}\n\n"
                
                # پردازش برچسب (مشابه تابع قبلی)
                receiver_info = {
                    'نام مشتری': order_data.customer_name,
                    'city': order_data.city,
                    'شهر': order_data.city,
                    'استان': order_data.province,
                    'state': order_data.province,
                    'address': order_data.full_address,
                    'آدرس کامل': order_data.full_address,
                    'postalCode': order_data.postal_code,
                    'کد پستی': order_data.postal_code,
                    'phoneNumber': order_data.customer_phone,
                    'شماره تلفن': order_data.customer_phone,
                    'products': [
                        {
                            'name': item.get('product_title', 'نامشخص'),
                            'qty': item.get('quantity', 1)
                        }
                        for item in order_data.items
                    ]
                }
                
                sender_info = {
                    'name': request.sender.name,
                    'address': request.sender.address,
                    'postal_code': request.sender.postal_code,
                    'phone': request.sender.phone
                }
                
                if request.settings.orientation == "portrait":
                    img = generate_label_portrait(
                        order_data.order_code,
                        sender_info,
                        receiver_info,
                        include_datamatrix=request.settings.include_datamatrix
                    )
                else:
                    img = generate_label_landscape(
                        order_data.order_code,
                        sender_info,
                        receiver_info
                    )
                
                buf = io.BytesIO()
                img.save(buf, format="PNG")
                buf.seek(0)
                labels.append(buf)
            
            # اتمام
            yield f"data: {json.dumps({'type': 'complete', 'message': 'PDF در حال ساخت...'})}\n\n"
            
        except Exception as e:
            error_data = {'type': 'error', 'message': str(e)}
            yield f"data: {json.dumps(error_data)}\n\n"
    
    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream"
    )


@router.get("/test")
async def test_labels():
    """تست اتصال و فونت"""
    from utils.label_core import get_font_path, load_fonts
    
    font_path = get_font_path()
    fonts_loaded = load_fonts()
    
    return {
        "message": "Labels endpoint is working!",
        "font_path": font_path,
        "font_found": font_path is not None,
        "fonts_loaded": len(fonts_loaded) > 0
    }