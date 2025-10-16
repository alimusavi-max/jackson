# backend/routers/reports.py
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from datetime import datetime, timedelta
from typing import Optional

from database.models import Order, OrderItem, get_session, init_database

router = APIRouter(prefix="/reports", tags=["گزارشات"])

def get_db():
    engine = init_database("digikala_sales.db")
    db = get_session(engine)
    try:
        yield db
    finally:
        db.close()


@router.get("/stats")
async def get_reports_stats(
    days: int = Query(30, ge=1, le=365),
    db: Session = Depends(get_db)
):
    """آمار و گزارشات جامع"""
    
    # محاسبه تاریخ شروع
    start_date = datetime.utcnow() - timedelta(days=days)
    
    # کل سفارشات
    total_orders = db.query(Order).filter(
        Order.created_at >= start_date
    ).count()
    
    # مجموع فروش
    total_revenue_query = db.query(
        func.sum(OrderItem.price * OrderItem.quantity)
    ).join(Order).filter(
        Order.created_at >= start_date
    ).scalar()
    total_revenue = float(total_revenue_query) if total_revenue_query else 0
    
    # مشتریان منحصر به فرد
    unique_customers = db.query(
        func.count(func.distinct(Order.customer_name))
    ).filter(
        Order.created_at >= start_date
    ).scalar() or 0
    
    # محصولات منحصر به فرد
    unique_products = db.query(
        func.count(func.distinct(OrderItem.product_code))
    ).join(Order).filter(
        Order.created_at >= start_date
    ).scalar() or 0
    
    # توزیع وضعیت‌ها
    status_distribution = db.query(
        Order.status,
        func.count(Order.id).label('count')
    ).filter(
        Order.created_at >= start_date
    ).group_by(Order.status).all()
    
    status_dist = [
        {"name": status or "نامشخص", "value": count}
        for status, count in status_distribution
    ]
    
    # شهرهای برتر
    top_cities = db.query(
        Order.city,
        func.count(Order.id).label('count')
    ).filter(
        Order.created_at >= start_date,
        Order.city.isnot(None),
        Order.city != ''
    ).group_by(Order.city).order_by(desc('count')).limit(10).all()
    
    top_cities_data = [
        {"name": city, "count": count}
        for city, count in top_cities
    ]
    
    # محصولات پرفروش
    top_products = db.query(
        OrderItem.product_title,
        func.sum(OrderItem.quantity).label('total_qty'),
        func.sum(OrderItem.price * OrderItem.quantity).label('total_revenue')
    ).join(Order).filter(
        Order.created_at >= start_date
    ).group_by(OrderItem.product_title).order_by(
        desc('total_qty')
    ).limit(10).all()
    
    top_products_data = [
        {
            "name": title[:50] + "..." if len(title) > 50 else title,
            "quantity": int(qty),
            "revenue": float(revenue)
        }
        for title, qty, revenue in top_products
    ]
    
    # فروش روزانه (7 روز اخیر)
    daily_sales = []
    for i in range(min(days, 30)):
        day_start = datetime.utcnow() - timedelta(days=i)
        day_end = day_start + timedelta(days=1)
        
        day_orders = db.query(Order).filter(
            Order.created_at >= day_start,
            Order.created_at < day_end
        ).count()
        
        day_revenue = db.query(
            func.sum(OrderItem.price * OrderItem.quantity)
        ).join(Order).filter(
            Order.created_at >= day_start,
            Order.created_at < day_end
        ).scalar() or 0
        
        daily_sales.append({
            "date": day_start.strftime("%Y-%m-%d"),
            "orders": day_orders,
            "amount": float(day_revenue)
        })
    
    daily_sales.reverse()
    
    return {
        "totalOrders": total_orders,
        "totalRevenue": total_revenue,
        "uniqueCustomers": unique_customers,
        "uniqueProducts": unique_products,
        "statusDistribution": status_dist,
        "topCities": top_cities_data,
        "topProducts": top_products_data,
        "dailySales": daily_sales
    }


@router.get("/export")
async def export_report(
    format: str = Query("excel", regex="^(excel|pdf|csv)$"),
    days: int = Query(30, ge=1, le=365),
    db: Session = Depends(get_db)
):
    """دانلود گزارش به صورت فایل"""
    # این endpoint را بعداً پیاده‌سازی می‌کنیم
    return {"message": "به زودی..."}


@router.get("/comparison")
async def get_comparison_stats(db: Session = Depends(get_db)):
    """مقایسه دوره‌های زمانی"""
    
    # 30 روز اخیر
    last_30_start = datetime.utcnow() - timedelta(days=30)
    last_30_orders = db.query(Order).filter(
        Order.created_at >= last_30_start
    ).count()
    
    # 30 روز قبل از آن
    prev_30_start = datetime.utcnow() - timedelta(days=60)
    prev_30_end = datetime.utcnow() - timedelta(days=30)
    prev_30_orders = db.query(Order).filter(
        Order.created_at >= prev_30_start,
        Order.created_at < prev_30_end
    ).count()
    
    # درصد تغییر
    if prev_30_orders > 0:
        change_percent = ((last_30_orders - prev_30_orders) / prev_30_orders) * 100
    else:
        change_percent = 0
    
    return {
        "current_period": last_30_orders,
        "previous_period": prev_30_orders,
        "change_percent": round(change_percent, 2),
        "trend": "up" if change_percent > 0 else "down" if change_percent < 0 else "stable"
    }