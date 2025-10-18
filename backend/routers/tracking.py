# backend/routers/tracking.py
from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Depends
from sqlalchemy.orm import Session
import pdfplumber
import re
import io
import json
import pandas as pd
from collections import defaultdict
from pydantic import BaseModel
from typing import List

from database.models import Order, init_database, get_session

router = APIRouter(prefix="/tracking", tags=["tracking"])

def get_db():
    import os
    db_path = os.path.join(os.path.dirname(__file__), '..', '..', 'data', 'digikala_sales.db')
    engine = init_database(db_path)
    db = get_session(engine)
    try:
        yield db
    finally:
        db.close()

class TrackingItem(BaseModel):
    order_code: str
    tracking_code: str

class MatchRequest(BaseModel):
    tracking_data: List[TrackingItem]

@router.get("/test")
async def test():
    return {"status": "ok", "message": "Tracking API works!"}

@router.post("/extract-pdf")
async def extract_pdf(file: UploadFile = File(...)):
    """استخراج کدهای رهگیری از PDF - دقیقاً مثل Streamlit"""
    
    try:
        print(f"\n📄 دریافت PDF: {file.filename}")
        contents = await file.read()
        pdf_file = io.BytesIO(contents)
        
        records = defaultdict(dict)
        
        tracking_pattern = re.compile(r'^\d{24}$')
        order_pattern = re.compile(r'\b(\d{9})\b')
        row_num_pattern = re.compile(r'^\d{1,2}$')
        
        last_row_num = None
        
        with pdfplumber.open(pdf_file) as pdf:
            print(f"📑 تعداد صفحات: {len(pdf.pages)}")
            
            for page_num, page in enumerate(pdf.pages, 1):
                print(f"🔍 صفحه {page_num}...")
                tables = page.extract_tables()
                
                if tables:
                    print(f"   {len(tables)} جدول یافت شد")
                    for table in tables:
                        if not table:
                            continue
                        
                        for row in table:
                            if not row:
                                continue
                            
                            cleaned_row = [cell.strip() if cell else "" for cell in row]
                            
                            # شناسایی شماره ردیف
                            if cleaned_row and row_num_pattern.match(cleaned_row[-1]):
                                last_row_num = cleaned_row[-1]
                            
                            # جستجو برای کدها
                            if last_row_num:
                                for cell in cleaned_row:
                                    if tracking_pattern.match(cell):
                                        records[last_row_num]['کد رهگیری'] = cell
                                    
                                    order_match = order_pattern.search(cell)
                                    if order_match:
                                        records[last_row_num]['شماره سفارش'] = order_match.group(1)
        
        # تبدیل به لیست
        results = []
        for row_num, data in sorted(records.items()):
            if 'کد رهگیری' in data and 'شماره سفارش' in data:
                results.append({
                    "order_code": data['شماره سفارش'],
                    "tracking_code": data['کد رهگیری']
                })
                print(f"   ✓ {data['شماره سفارش']} -> {data['کد رهگیری'][:12]}...")
        
        # حذف تکراری
        unique_results = []
        seen = set()
        for item in results:
            key = (item["order_code"], item["tracking_code"])
            if key not in seen:
                seen.add(key)
                unique_results.append(item)
        
        print(f"\n✅ استخراج شد: {len(unique_results)} سفارش\n")
        
        return unique_results
    
    except Exception as e:
        print(f"❌ خطا: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"خطا در پردازش PDF: {str(e)}")


@router.post("/match-database")
async def match_database(request: MatchRequest, db: Session = Depends(get_db)):
    """تطبیق با دیتابیس - دقیقاً مثل Streamlit"""
    
    try:
        print(f"\n🔍 تطبیق {len(request.tracking_data)} سفارش با دیتابیس...")
        
        results = []
        
        for item in request.tracking_data:
            # جستجوی دقیق در دیتابیس
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
                print(f"   ✓ {item.order_code} -> {order.customer_name}")
            else:
                results.append({
                    "order_code": item.order_code,
                    "tracking_code": item.tracking_code,
                    "shipment_id": None,
                    "customer_name": None,
                    "city": None,
                    "status": None,
                    "matched": False
                })
                print(f"   ✗ {item.order_code} -> یافت نشد")
        
        matched_count = sum(1 for r in results if r.get("matched"))
        unmatched_count = len(results) - matched_count
        
        print(f"\n✅ تطبیق کامل:")
        print(f"   تطبیق یافت: {matched_count}")
        print(f"   یافت نشد: {unmatched_count}\n")
        
        return {
            "success": True,
            "total": len(results),
            "matched": matched_count,
            "unmatched": unmatched_count,
            "results": results
        }
    
    except Exception as e:
        print(f"❌ خطا در تطبیق: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"خطا: {str(e)}")


@router.post("/match-excel")
async def match_excel(
    excel: UploadFile = File(...),
    tracking_data: str = Form(...),
    db: Session = Depends(get_db)
):
    """تطبیق با Excel - دقیقاً مثل Streamlit (روش قدیمی)"""
    
    try:
        print(f"\n📊 تطبیق با Excel...")
        
        # 1. خواندن Excel
        excel_contents = await excel.read()
        df_excel = pd.read_excel(io.BytesIO(excel_contents), dtype=str)
        
        # فقط دو ستون اول
        df_excel = df_excel.iloc[:, [0, 1]]
        df_excel.columns = ['کد سفارش', 'شناسه محموله']
        
        print(f"   📄 Excel: {len(df_excel)} ردیف")
        
        # 2. پارس tracking data
        tracking_list = json.loads(tracking_data)
        df_tracking = pd.DataFrame(tracking_list)
        
        # اطمینان از نام ستون‌ها
        if len(df_tracking.columns) == 2:
            df_tracking.columns = ['order_code', 'tracking_code']
        
        print(f"   📄 Tracking: {len(df_tracking)} ردیف")
        
        # 3. تطبیق - دقیقاً مثل Streamlit
        df_tracking['merge_key'] = df_tracking['order_code']
        
        # استخراج 9 رقم از Excel - دقیقاً مثل قبل
        df_excel['merge_key'] = df_excel['کد سفارش'].str.extract(r'(\d{9})', expand=False)
        
        # حذف NaN
        df_excel = df_excel.dropna(subset=['merge_key'])
        
        print(f"   📄 Excel پاکسازی شده: {len(df_excel)} ردیف")
        
        # Merge
        merged = pd.merge(df_tracking, df_excel, on='merge_key', how='inner')
        
        print(f"   ✓ تطبیق یافته: {len(merged)} ردیف")
        
        # 4. جستجو در دیتابیس
        results = []
        
        for _, row in merged.iterrows():
            shipment_id = str(row['شناسه محموله'])
            order_code = str(row['order_code'])
            tracking_code = str(row['tracking_code'])
            
            # جستجو با shipment_id
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
                    "status": order.status,
                    "matched": True
                })
                print(f"   ✓ {order_code} -> {order.customer_name}")
            else:
                results.append({
                    "order_code": order_code,
                    "tracking_code": tracking_code,
                    "shipment_id": shipment_id,
                    "customer_name": None,
                    "city": None,
                    "status": None,
                    "matched": False
                })
                print(f"   ✗ {order_code} -> یافت نشد در DB")
        
        # 5. پیدا کردن سفارشاتی که در Excel نبودند
        excel_order_codes = set(df_excel['merge_key'].dropna())
        tracking_order_codes = set(df_tracking['order_code'])
        
        not_in_excel = tracking_order_codes - excel_order_codes
        
        if not_in_excel:
            print(f"\n⚠️  {len(not_in_excel)} سفارش در Excel یافت نشد:")
            for order_code in not_in_excel:
                tracking_row = df_tracking[df_tracking['order_code'] == order_code].iloc[0]
                results.append({
                    "order_code": order_code,
                    "tracking_code": tracking_row['tracking_code'],
                    "shipment_id": None,
                    "customer_name": None,
                    "city": None,
                    "status": None,
                    "matched": False,
                    "reason": "not_in_excel"
                })
                print(f"   - {order_code}")
        
        matched_count = sum(1 for r in results if r.get("matched"))
        unmatched_count = len(results) - matched_count
        
        print(f"\n✅ تطبیق Excel کامل:")
        print(f"   تطبیق یافت: {matched_count}")
        print(f"   یافت نشد: {unmatched_count}\n")
        
        return {
            "success": True,
            "total": len(results),
            "matched": matched_count,
            "unmatched": unmatched_count,
            "results": results
        }
    
    except Exception as e:
        print(f"❌ خطا در تطبیق Excel: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"خطا: {str(e)}")


@router.post("/submit")
async def submit_tracking(
    order_id: int = Form(...),
    tracking_code: str = Form(...),
    db: Session = Depends(get_db)
):
    """ثبت کد رهگیری در دیتابیس"""
    
    try:
        order = db.query(Order).filter(Order.id == order_id).first()
        
        if not order:
            raise HTTPException(status_code=404, detail="سفارش یافت نشد")
        
        order.tracking_code = tracking_code
        db.commit()
        
        print(f"✅ کد رهگیری {tracking_code} برای سفارش {order.order_code} ثبت شد")
        
        return {
            "success": True,
            "message": "کد رهگیری با موفقیت ثبت شد",
            "order_code": order.order_code,
            "tracking_code": tracking_code
        }
    
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        print(f"❌ خطا: {e}")
        raise HTTPException(status_code=500, detail=f"خطا: {str(e)}")