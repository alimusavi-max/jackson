# backend/routers/labels.py
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Dict, Optional
import io
import time
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
    تولید PDF برچسب‌های پستی
    """
    try:
        labels = []
        
        for order_data in request.orders:
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
                    'qty': item.get('quantity', 1)
                })
            
            # اطلاعات فرستنده
            sender_info = {
                'name': request.sender.name,
                'address': request.sender.address,
                'postal_code': request.sender.postal_code,
                'phone': request.sender.phone
            }
            
            # تولید برچسب
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
            labels.append(io.BytesIO(buf.getvalue()))
        
        # ساخت PDF
        pdf_buffer = io.BytesIO()
        
        if request.settings.orientation == "portrait":
            page_size = portrait(A5)
        else:
            page_size = landscape(A5)
        
        # تولید PDF موقت
        temp_path = f"temp_labels_{int(time.time())}.pdf"
        create_pdf_two_labels(labels, temp_path, page_size)
        
        # خواندن PDF و پاک کردن فایل موقت
        with open(temp_path, "rb") as f:
            pdf_data = f.read()
        
        import os
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
        print(f"خطا در تولید برچسب: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"خطا در تولید برچسب: {str(e)}")


@router.get("/test")
async def test_labels():
    """تست اتصال"""
    return {"message": "Labels endpoint is working!"}