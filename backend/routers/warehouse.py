# backend/routers/warehouse.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel

from database.models import Product, init_database, get_session
import os

router = APIRouter(prefix="/warehouse", tags=["Warehouse"])

# ========== Database Dependency ==========
def get_db():
    db_path = os.path.join(os.path.dirname(__file__), '..', '..', 'data', 'digikala_sales.db')
    engine = init_database(db_path)
    db = get_session(engine)
    try:
        yield db
    finally:
        db.close()


# ========== Pydantic Models ==========
class ProductResponse(BaseModel):
    id: int
    dkp_code: str
    title: str
    stock_quantity: int
    available_quantity: int
    min_stock_alert: int
    cost_price: float
    sell_price: float
    is_low_stock: bool
    
    class Config:
        from_attributes = True


class Stats(BaseModel):
    total_products: int
    low_stock_items: int
    total_inventory_value: float
    today_transactions: int


# ========== Endpoints ==========

@router.get("/test")
async def test_warehouse():
    """تست اتصال"""
    return {"status": "ok", "message": "Warehouse API works!"}


@router.get("/products", response_model=List[ProductResponse])
async def get_products(
    low_stock_only: bool = False,
    db: Session = Depends(get_db)
):
    """دریافت لیست محصولات"""
    try:
        query = db.query(Product)
        
        if low_stock_only:
            query = query.filter(Product.stock_quantity <= Product.min_stock_alert)
        
        products = query.all()
        
        # محاسبه available_quantity و is_low_stock
        result = []
        for p in products:
            result.append({
                "id": p.id,
                "dkp_code": p.dkp_code or "",
                "title": p.title or "",
                "stock_quantity": p.stock_quantity,
                "available_quantity": p.stock_quantity,  # فعلاً ساده
                "min_stock_alert": p.min_stock_alert,
                "cost_price": p.cost_price,
                "sell_price": p.sell_price,
                "is_low_stock": p.stock_quantity <= p.min_stock_alert
            })
        
        return result
    
    except Exception as e:
        print(f"❌ خطا در دریافت محصولات: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stats", response_model=Stats)
async def get_warehouse_stats(db: Session = Depends(get_db)):
    """آمار انبار"""
    try:
        total_products = db.query(Product).count()
        
        low_stock = db.query(Product).filter(
            Product.stock_quantity <= Product.min_stock_alert
        ).count()
        
        # محاسبه ارزش کل موجودی
        products = db.query(Product).all()
        total_value = sum(p.cost_price * p.stock_quantity for p in products)
        
        return {
            "total_products": total_products,
            "low_stock_items": low_stock,
            "total_inventory_value": total_value,
            "today_transactions": 0  # فعلاً صفر
        }
    
    except Exception as e:
        print(f"❌ خطا در دریافت آمار: {e}")
        raise HTTPException(status_code=500, detail=str(e))