# backend/routers/tracking.py
from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException
from sqlalchemy.orm import Session
from typing import List
import pandas as pd
import pdfplumber
import re
import io
import json
from pydantic import BaseModel

from database.models import Order, get_session, init_database

router = APIRouter(prefix="/tracking", tags=["کدهای رهگیری"])

def get_db():
    engine = init_database("digikala_sales.db")
    db = get_session(engine)
    try:
        yield db
    finally:
        db.close()

# 🔥 تست endpoint
@router.get("/test")
async def test_tracking_api():
    """تست اتصال به API"""
    return {
        "status": "ok",
        "message": "Tracking API is working!",
        "endpoints": {
            "extract_pdf": "POST /api/tracking/extract-pdf",
            "match_database": "POST /api/tracking/match-database",
            "match_excel": "POST /api/tracking/match-excel",
            "submit": "POST /api/tracking/submit"
        }
    }

# 🔥 مدل جدید برای تطبیق با دیتابیس
class TrackingDataItem(BaseModel):
    order_code: str
    tracking_code: str

class MatchDatabaseRequest(BaseModel):
    tracking_data: List[TrackingDataItem]

class SubmitTrackingRequest(BaseModel):
    order_id: int
    order_code: str
    shipment_id: str
    tracking_code: str

@router.post("/extract-pdf")
async def extract_pdf(file: UploadFile = File(...)):
    """استخراج کدهای رهگیری از PDF"""
    try:
        print(f"\n{'='*60}")
        print(f"📄 دریافت فایل PDF: {file.filename}")
        print(f"{'='*60}\n")
        
        contents = await file.read()
        pdf_file = io.BytesIO(contents)
        
        print(f"📊 حجم فایل: {len(contents)} bytes")
        
        results = []
        tracking_pattern = re.compile(r'^\d{24}


# 🔥 Endpoint جدید: تطبیق با دیتابیس
@router.post("/match-database")
async def match_with_database(
    request: MatchDatabaseRequest,
    db: Session = Depends(get_db)
):
    """تطبیق کدهای رهگیری با سفارشات موجود در دیتابیس"""
    try:
        print(f"🔍 تطبیق {len(request.tracking_data)} کد رهگیری با دیتابیس...")
        
        results = []
        
        for item in request.tracking_data:
            # جستجوی سفارش در دیتابیس
            order = db.query(Order).filter(
                Order.order_code == item.order_code
            ).first()
            
            if order:
                results.append({
                    "id": order.id,
                    "order_code": item.order_code,
                    "tracking_code": item.tracking_code,
                    "shipment_id": order.shipment_id,
                    "customer_name": order.customer_name,
                    "city": order.city,
                    "status": order.status,
                    "matched": True
                })
                print(f"  ✓ {item.order_code} -> {order.customer_name}")
            else:
                results.append({
                    "order_code": item.order_code,
                    "tracking_code": item.tracking_code,
                    "matched": False
                })
                print(f"  ✗ {item.order_code} -> یافت نشد")
        
        matched_count = sum(1 for r in results if r.get("matched"))
        print(f"\n✅ تطبیق کامل: {matched_count}/{len(results)}")
        
        return {
            "success": True,
            "total": len(results),
            "matched": matched_count,
            "results": results
        }
    
    except Exception as e:
        print(f"❌ خطا در تطبیق: {e}")
        raise HTTPException(status_code=500, detail=f"خطا در تطبیق: {str(e)}")


# 🔥 Endpoint جدید: تطبیق با Excel
@router.post("/match-excel")
async def match_with_excel(
    excel: UploadFile = File(...),
    tracking_data: str = Form(...),
    db: Session = Depends(get_db)
):
    """تطبیق با فایل Excel (روش Streamlit)"""
    try:
        print(f"\n📊 تطبیق با Excel...")
        
        # خواندن Excel
        excel_contents = await excel.read()
        df_excel = pd.read_excel(io.BytesIO(excel_contents), dtype=str)
        
        # فقط دو ستون اول
        df_excel = df_excel.iloc[:, [0, 1]]
        df_excel.columns = ['کد سفارش', 'شناسه محموله']
        
        print(f"   Excel: {len(df_excel)} ردیف")
        
        # پارس tracking_data
        tracking_list = json.loads(tracking_data)
        df_tracking = pd.DataFrame(tracking_list)
        df_tracking.columns = ['order_code', 'tracking_code'] if len(df_tracking.columns) == 2 else df_tracking.columns
        
        print(f"   Tracking: {len(df_tracking)} ردیف")
        
        # 🔥 تطبیق مثل Streamlit
        df_tracking['merge_key'] = df_tracking['order_code']
        df_excel['merge_key'] = df_excel['کد سفارش'].str.extract(r'(\d{9})', expand=False)
        
        # حذف NaN ها
        df_excel = df_excel.dropna(subset=['merge_key'])
        
        print(f"   Excel بعد از پاکسازی: {len(df_excel)} ردیف")
        
        # Merge
        merged = pd.merge(df_tracking, df_excel, on='merge_key', how='inner')
        
        print(f"   تطبیق یافته: {len(merged)} ردیف")
        
        results = []
        
        for _, row in merged.iterrows():
            shipment_id = str(row['شناسه محموله'])
            order_code = str(row['order_code'])
            tracking_code = str(row['tracking_code'])
            
            # جستجو در دیتابیس
            order = db.query(Order).filter(
                Order.shipment_id == shipment_id
            ).first()
            
            if order:
                results.append({
                    "id": order.id,
                    "order_code": order_code,
                    "tracking_code": tracking_code,
                    "shipment_id": shipment_id,
                    "customer_name": order.customer_name,
                    "city": order.city,
                    "matched": True
                })
                print(f"   ✓ {order_code} -> {order.customer_name}")
            else:
                results.append({
                    "order_code": order_code,
                    "tracking_code": tracking_code,
                    "shipment_id": shipment_id,
                    "matched": False
                })
                print(f"   ✗ {order_code} -> یافت نشد")
        
        matched_count = sum(1 for r in results if r.get("matched"))
        print(f"\n✅ تطبیق Excel کامل: {matched_count}/{len(results)}\n")
        
        return {"success": True, "results": results}
    
    except Exception as e:
        print(f"❌ خطا در تطبیق Excel: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"خطا: {str(e)}")


@router.post("/submit")
async def submit_tracking_code(
    request: SubmitTrackingRequest,
    db: Session = Depends(get_db)
):
    """ثبت کد رهگیری در دیتابیس و ارسال به API"""
    try:
        # به‌روزرسانی در دیتابیس
        order = db.query(Order).filter(Order.id == request.order_id).first()
        
        if not order:
            raise HTTPException(status_code=404, detail="سفارش یافت نشد")
        
        order.tracking_code = request.tracking_code
        db.commit()
        
        print(f"✅ کد رهگیری {request.tracking_code} برای سفارش {request.order_code} ثبت شد")
        
        # TODO: ارسال به API دیجی‌کالا (اختیاری)
        # از utils.api_core استفاده کنید
        
        return {
            "success": True,
            "message": "کد رهگیری با موفقیت ثبت شد",
            "order_code": request.order_code,
            "tracking_code": request.tracking_code
        }
    
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"خطا: {str(e)}")


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
    } for order in orders])
        order_pattern = re.compile(r'\b(\d{9})\b')
        
        page_count = 0
        with pdfplumber.open(pdf_file) as pdf:
            page_count = len(pdf.pages)
            print(f"📑 تعداد صفحات: {page_count}")
            
            for page_num, page in enumerate(pdf.pages, 1):
                print(f"\n🔍 پردازش صفحه {page_num}/{page_count}...")
                
                # روش 1: استخراج از جداول
                tables = page.extract_tables()
                if tables:
                    print(f"   📊 {len(tables)} جدول یافت شد")
                    
                    for table_idx, table in enumerate(tables):
                        if not table:
                            continue
                        
                        print(f"      جدول {table_idx + 1}: {len(table)} ردیف")
                        
                        for row in table:
                            if not row:
                                continue
                                
                            order_code = None
                            tracking_code = None
                            
                            for cell in row:
                                if not cell:
                                    continue
                                
                                cell_str = str(cell).strip()
                                
                                # جستجوی کد رهگیری (24 رقمی)
                                if tracking_pattern.match(cell_str):
                                    tracking_code = cell_str
                                
                                # جستجوی کد سفارش (9 رقمی)
                                match = order_pattern.search(cell_str)
                                if match:
                                    order_code = match.group(1)
                            
                            if order_code and tracking_code:
                                results.append({
                                    "order_code": order_code,
                                    "tracking_code": tracking_code
                                })
                                print(f"         ✓ {order_code} -> {tracking_code[:12]}...")
                
                # روش 2: استخراج از متن (اگر جدول نداشت)
                if not tables:
                    print(f"   📝 استخراج از متن...")
                    text = page.extract_text()
                    if text:
                        lines = text.split('\n')
                        for line in lines:
                            # جستجوی کد رهگیری
                            tracking_matches = tracking_pattern.findall(line)
                            order_matches = order_pattern.findall(line)
                            
                            if tracking_matches and order_matches:
                                for tracking in tracking_matches:
                                    for order in order_matches:
                                        results.append({
                                            "order_code": order,
                                            "tracking_code": tracking
                                        })
                                        print(f"      ✓ {order} -> {tracking[:12]}...")
        
        # حذف تکراری‌ها
        unique_results = []
        seen = set()
        for item in results:
            key = (item["order_code"], item["tracking_code"])
            if key not in seen:
                seen.add(key)
                unique_results.append(item)
        
        print(f"\n{'='*60}")
        print(f"✅ استخراج کامل شد:")
        print(f"   - کل یافته شده: {len(results)}")
        print(f"   - بعد از حذف تکراری: {len(unique_results)}")
        print(f"{'='*60}\n")
        
        if len(unique_results) == 0:
            print("⚠️ هیچ کد رهگیری در PDF یافت نشد!")
            print("💡 فرمت مورد انتظار:")
            print("   - کد سفارش: 9 رقمی")
            print("   - کد رهگیری: 24 رقمی")
        
        return unique_results
    
    except pdfplumber.pdfminer.pdfparser.PDFSyntaxError as e:
        print(f"❌ خطای فرمت PDF: {e}")
        raise HTTPException(
            status_code=400, 
            detail="فایل آپلود شده یک PDF معتبر نیست. لطفاً یک فایل PDF صحیح انتخاب کنید."
        )
    except Exception as e:
        print(f"❌ خطای غیرمنتظره: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=500, 
            detail=f"خطا در پردازش PDF: {str(e)}. لطفاً فرمت فایل را بررسی کنید."
        )


# 🔥 Endpoint جدید: تطبیق با دیتابیس
@router.post("/match-database")
async def match_with_database(
    request: MatchDatabaseRequest,
    db: Session = Depends(get_db)
):
    """تطبیق کدهای رهگیری با سفارشات موجود در دیتابیس"""
    try:
        print(f"🔍 تطبیق {len(request.tracking_data)} کد رهگیری با دیتابیس...")
        
        results = []
        
        for item in request.tracking_data:
            # جستجوی سفارش در دیتابیس
            order = db.query(Order).filter(
                Order.order_code == item.order_code
            ).first()
            
            if order:
                results.append({
                    "id": order.id,
                    "order_code": item.order_code,
                    "tracking_code": item.tracking_code,
                    "shipment_id": order.shipment_id,
                    "customer_name": order.customer_name,
                    "city": order.city,
                    "status": order.status,
                    "matched": True
                })
                print(f"  ✓ {item.order_code} -> {order.customer_name}")
            else:
                results.append({
                    "order_code": item.order_code,
                    "tracking_code": item.tracking_code,
                    "matched": False
                })
                print(f"  ✗ {item.order_code} -> یافت نشد")
        
        matched_count = sum(1 for r in results if r.get("matched"))
        print(f"\n✅ تطبیق کامل: {matched_count}/{len(results)}")
        
        return {
            "success": True,
            "total": len(results),
            "matched": matched_count,
            "results": results
        }
    
    except Exception as e:
        print(f"❌ خطا در تطبیق: {e}")
        raise HTTPException(status_code=500, detail=f"خطا در تطبیق: {str(e)}")


# 🔥 Endpoint جدید: تطبیق با Excel
@router.post("/match-excel")
async def match_with_excel(
    excel: UploadFile = File(...),
    tracking_data: str = Form(...),
    db: Session = Depends(get_db)
):
    """تطبیق با فایل Excel (روش قدیمی)"""
    try:
        # خواندن Excel
        excel_contents = await excel.read()
        df_excel = pd.read_excel(io.BytesIO(excel_contents), dtype=str)
        df_excel = df_excel.iloc[:, [0, 1]]
        df_excel.columns = ['order_code', 'shipment_id']
        
        # پارس tracking_data
        tracking_list = json.loads(tracking_data)
        
        results = []
        for item in tracking_list:
            # پیدا کردن shipment_id از Excel
            excel_row = df_excel[df_excel['order_code'] == item['order_code']]
            
            if not excel_row.empty:
                shipment_id = excel_row.iloc[0]['shipment_id']
                
                # جستجو در دیتابیس
                order = db.query(Order).filter(
                    Order.shipment_id == shipment_id
                ).first()
                
                if order:
                    results.append({
                        "id": order.id,
                        "order_code": item['order_code'],
                        "tracking_code": item['tracking_code'],
                        "shipment_id": shipment_id,
                        "customer_name": order.customer_name,
                        "city": order.city,
                        "matched": True
                    })
                else:
                    results.append({
                        "order_code": item['order_code'],
                        "tracking_code": item['tracking_code'],
                        "shipment_id": shipment_id,
                        "matched": False
                    })
            else:
                results.append({
                    "order_code": item['order_code'],
                    "tracking_code": item['tracking_code'],
                    "matched": False
                })
        
        return {"success": True, "results": results}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"خطا: {str(e)}")


@router.post("/submit")
async def submit_tracking_code(
    request: SubmitTrackingRequest,
    db: Session = Depends(get_db)
):
    """ثبت کد رهگیری در دیتابیس و ارسال به API"""
    try:
        # به‌روزرسانی در دیتابیس
        order = db.query(Order).filter(Order.id == request.order_id).first()
        
        if not order:
            raise HTTPException(status_code=404, detail="سفارش یافت نشد")
        
        order.tracking_code = request.tracking_code
        db.commit()
        
        print(f"✅ کد رهگیری {request.tracking_code} برای سفارش {request.order_code} ثبت شد")
        
        # TODO: ارسال به API دیجی‌کالا (اختیاری)
        # از utils.api_core استفاده کنید
        
        return {
            "success": True,
            "message": "کد رهگیری با موفقیت ثبت شد",
            "order_code": request.order_code,
            "tracking_code": request.tracking_code
        }
    
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"خطا: {str(e)}")


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