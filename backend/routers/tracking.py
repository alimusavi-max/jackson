# backend/routers/tracking.py
from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException
from sqlalchemy.orm import Session
from typing import List
import pandas as pd
import pdfplumber
import re
import io
import json

from database.models import Order, get_session, init_database

router = APIRouter(prefix="/tracking", tags=["کدهای رهگیری"])

def get_db():
    engine = init_database("digikala_sales.db")
    db = get_session(engine)
    try:
        yield db
    finally:
        db.close()

@router.post("/extract-pdf")
async def extract_pdf(file: UploadFile = File(...)):
    """استخراج کدهای رهگیری از PDF"""
    try:
        contents = await file.read()
        pdf_file = io.BytesIO(contents)
        
        results = []
        tracking_pattern = re.compile(r'^\d{24}$')
        order_pattern = re.compile(r'\b(\d{9})\b')
        
        with pdfplumber.open(pdf_file) as pdf:
            for page in pdf.pages:
                tables = page.extract_tables()
                
                for table in tables:
                    if not table:
                        continue
                    
                    for row in table:
                        order_code = None
                        tracking_code = None
                        
                        for cell in row:
                            if not cell:
                                continue
                            
                            cell = str(cell).strip()
                            
                            # جستجوی کد رهگیری (24 رقمی)
                            if tracking_pattern.match(cell):
                                tracking_code = cell
                            
                            # جستجوی کد سفارش (9 رقمی)
                            match = order_pattern.search(cell)
                            if match:
                                order_code = match.group(1)
                        
                        if order_code and tracking_code:
                            results.append({
                                "orderCode": order_code,
                                "trackingCode": tracking_code,
                                "shipmentId": ""
                            })
        
        # حذف تکراری‌ها
        unique_results = []
        seen = set()
        for item in results:
            key = (item["orderCode"], item["trackingCode"])
            if key not in seen:
                seen.add(key)
                unique_results.append(item)
        
        return unique_results
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"خطا در پردازش PDF: {str(e)}")


@router.post("/submit")
async def submit_tracking_codes(
    excel: UploadFile = File(...),
    tracking_data: str = Form(...),
    db: Session = Depends(get_db)
):
    """ارسال کدهای رهگیری به API دیجی‌کالا"""
    try:
        # خواندن فایل اکسل
        excel_contents = await excel.read()
        df_excel = pd.read_excel(io.BytesIO(excel_contents), dtype=str)
        df_excel = df_excel.iloc[:, [0, 1]]  # فقط دو ستون اول
        df_excel.columns = ['order_code', 'shipment_id']
        
        # پارس کردن tracking_data
        tracking_list = json.loads(tracking_data)
        df_tracking = pd.DataFrame(tracking_list)
        
        # تطبیق داده‌ها
        df_merged = pd.merge(
            df_tracking,
            df_excel,
            left_on='orderCode',
            right_on='order_code',
            how='inner'
        )
        
        results = []
        
        for _, row in df_merged.iterrows():
            try:
                # به‌روزرسانی در دیتابیس محلی
                order = db.query(Order).filter(
                    Order.order_code == row['orderCode']
                ).first()
                
                if order:
                    order.tracking_code = row['trackingCode']
                    db.commit()
                    
                    results.append({
                        "orderCode": row['orderCode'],
                        "trackingCode": row['trackingCode'],
                        "status": "success",
                        "message": "کد رهگیری با موفقیت ثبت شد"
                    })
                else:
                    results.append({
                        "orderCode": row['orderCode'],
                        "trackingCode": row['trackingCode'],
                        "status": "error",
                        "message": "سفارش در دیتابیس یافت نشد"
                    })
            
            except Exception as e:
                results.append({
                    "orderCode": row['orderCode'],
                    "trackingCode": row['trackingCode'],
                    "status": "error",
                    "message": str(e)
                })
        
        return {"results": results}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"خطا در پردازش: {str(e)}")


@router.get("/pending-orders")
async def get_pending_orders(db: Session = Depends(get_db)):
    """سفارشات بدون کد رهگیری"""
    orders = db.query(Order).filter(
        (Order.tracking_code.is_(None)) | 
        (Order.tracking_code == '') |
        (Order.tracking_code == 'نامشخص')
    ).limit(100).all()
    
    return [{
        "id": order.id,
        "order_code": order.order_code,
        "shipment_id": order.shipment_id,
        "customer_name": order.customer_name,
        "city": order.city
    } for order in orders]