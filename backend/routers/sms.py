# backend/routers/sms.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List
from datetime import datetime
import subprocess
import os

from database.models import Order, SMSLog, get_session, init_database

router = APIRouter(prefix="/sms", tags=["مدیریت پیامک"])

# تنظیمات KDE Connect
DEVICE_ID = os.getenv("DEVICE_ID", "8840ef7242ad4049afc617c52ecb5f57")
KDECONNECT_CLI_PATH = r"C:\Program Files\KDE Connect\bin\kdeconnect-cli.exe"
COMPANY_NAME = "تجارت دریای آرام"

def get_db():
    engine = init_database("digikala_sales.db")
    db = get_session(engine)
    try:
        yield db
    finally:
        db.close()


class SendSMSRequest(BaseModel):
    order_ids: List[int]
    dry_run: bool = True


def check_kde_connect():
    """بررسی وضعیت اتصال KDE Connect"""
    if not os.path.exists(KDECONNECT_CLI_PATH):
        return False, "KDE Connect نصب نیست"
    
    try:
        result = subprocess.run(
            [KDECONNECT_CLI_PATH, "--device", DEVICE_ID, "--ping"],
            capture_output=True,
            timeout=5
        )
        if result.returncode == 0:
            return True, "متصل"
        else:
            return False, "دستگاه آفلاین است"
    except Exception as e:
        return False, str(e)


def send_sms_via_kde(phone: str, message: str, dry_run: bool = False):
    """ارسال پیامک از طریق KDE Connect"""
    if dry_run:
        return True, "حالت تست - پیامک ارسال نشد"
    
    try:
        command = [
            KDECONNECT_CLI_PATH,
            "--device", DEVICE_ID,
            "--send-sms", message,
            "--destination", phone
        ]
        
        result = subprocess.run(
            command,
            capture_output=True,
            timeout=15
        )
        
        if result.returncode == 0:
            return True, "پیامک ارسال شد"
        else:
            return False, result.stderr.decode('utf-8', errors='ignore')
    
    except Exception as e:
        return False, str(e)


def get_sms_template(customer_name: str, tracking_code: str) -> str:
    """تولید متن پیامک"""
    greeting = f"سلام {customer_name} عزیز،" if customer_name else "سلام دوست عزیز،"
    
    message = (
        f"{greeting}\n"
        f"بسته شما از طرف «{COMPANY_NAME}» ارسال شد. 📦\n\n"
        f"برای پیگیری لحظه‌ای مرسوله، کد رهگیری زیر را در سایت پست وارد نمایید:\n"
        f"🔢 {tracking_code}\n\n"
        f"tracking.post.ir"
    )
    
    return message


@router.get("/status")
async def get_sms_status():
    """وضعیت سرویس پیامک"""
    is_connected, message = check_kde_connect()
    
    return {
        "kde_connect_installed": os.path.exists(KDECONNECT_CLI_PATH),
        "device_connected": is_connected,
        "status_message": message,
        "device_id": DEVICE_ID
    }


@router.get("/ready-orders")
async def get_ready_orders(db: Session = Depends(get_db)):
    """سفارشات آماده برای ارسال پیامک"""
    
    # سفارشاتی که کد رهگیری دارند و پیامک ارسال نشده
    orders = db.query(Order).filter(
        Order.tracking_code.isnot(None),
        Order.tracking_code != '',
        Order.tracking_code != 'نامشخص',
        Order.customer_phone.isnot(None),
        Order.customer_phone != ''
    ).all()
    
    # فیلتر سفارشاتی که قبلاً پیامک ارسال شده
    result = []
    for order in orders:
        # بررسی لاگ ارسال
        existing_log = db.query(SMSLog).filter(
            SMSLog.order_id == order.id,
            SMSLog.is_successful == True
        ).first()
        
        if not existing_log:
            result.append({
                "orderId": order.order_code,
                "customerName": order.customer_name,
                "trackingCode": order.tracking_code,
                "phoneNumber": order.customer_phone,
                "status": order.status,
                "shipmentId": order.shipment_id,
                "id": order.id
            })
    
    return result


@router.post("/send")
async def send_sms_bulk(
    request: SendSMSRequest,
    db: Session = Depends(get_db)
):
    """ارسال پیامک برای چند سفارش"""
    
    # بررسی اتصال
    is_connected, status_msg = check_kde_connect()
    if not is_connected and not request.dry_run:
        raise HTTPException(status_code=503, detail=f"KDE Connect متصل نیست: {status_msg}")
    
    results = []
    success_count = 0
    
    for order_id in request.order_ids:
        order = db.query(Order).filter(Order.id == order_id).first()
        
        if not order:
            results.append({
                "order_id": order_id,
                "success": False,
                "message": "سفارش یافت نشد"
            })
            continue
        
        if not order.tracking_code or order.tracking_code == 'نامشخص':
            results.append({
                "order_id": order_id,
                "order_code": order.order_code,
                "success": False,
                "message": "کد رهگیری ندارد"
            })
            continue
        
        if not order.customer_phone:
            results.append({
                "order_id": order_id,
                "order_code": order.order_code,
                "success": False,
                "message": "شماره تلفن ندارد"
            })
            continue
        
        # تولید متن پیامک
        message = get_sms_template(order.customer_name, order.tracking_code)
        
        # ارسال
        success, send_message = send_sms_via_kde(
            order.customer_phone,
            message,
            request.dry_run
        )
        
        # ثبت لاگ
        sms_log = SMSLog(
            order_id=order.id,
            tracking_code=order.tracking_code,
            phone_number=order.customer_phone,
            message=message,
            is_successful=success,
            error_message=None if success else send_message
        )
        db.add(sms_log)
        
        if success:
            success_count += 1
        
        results.append({
            "order_id": order_id,
            "order_code": order.order_code,
            "customer_name": order.customer_name,
            "phone": order.customer_phone,
            "success": success,
            "message": send_message
        })
    
    db.commit()
    
    return {
        "total": len(request.order_ids),
        "success": success_count,
        "failed": len(request.order_ids) - success_count,
        "dry_run": request.dry_run,
        "results": results
    }


@router.get("/logs")
async def get_sms_logs(
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """تاریخچه ارسال پیامک‌ها"""
    
    logs = db.query(SMSLog).order_by(
        SMSLog.sent_at.desc()
    ).limit(limit).all()
    
    return [{
        "id": log.id,
        "order_id": log.order_id,
        "tracking_code": log.tracking_code,
        "phone_number": log.phone_number,
        "sent_at": log.sent_at.isoformat() if log.sent_at else None,
        "is_successful": log.is_successful,
        "error_message": log.error_message
    } for log in logs]


@router.post("/test")
async def test_sms(
    phone: str,
    message: str
):
    """تست ارسال یک پیامک"""
    
    is_connected, status_msg = check_kde_connect()
    if not is_connected:
        raise HTTPException(status_code=503, detail=f"KDE Connect متصل نیست: {status_msg}")
    
    success, result = send_sms_via_kde(phone, message, dry_run=False)
    
    return {
        "success": success,
        "message": result
    }