# backend/routers/warehouse.py
"""
API کامل انبارداری با قابلیت چند انبار و چند پلتفرم
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func, or_
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime

from database.models import init_database, get_session
from database.warehouse_models_extended import (
    Warehouse, WarehouseProduct, ProductCategory, 
    Marketplace, ProductMarketplace, InventoryTransaction,
    StockTake, StockTakeItem, TransactionType, StockTakeStatus,
    generate_transaction_number, generate_stock_take_number
)
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

# Warehouse
class WarehouseCreate(BaseModel):
    code: str
    name: str
    address: Optional[str] = None
    city: Optional[str] = None
    province: Optional[str] = None
    postal_code: Optional[str] = None
    phone: Optional[str] = None
    warehouse_type: str = "main"
    manager_name: Optional[str] = None
    manager_phone: Optional[str] = None

class WarehouseResponse(BaseModel):
    id: int
    code: str
    name: str
    address: Optional[str]
    city: Optional[str]
    province: Optional[str]
    warehouse_type: str
    manager_name: Optional[str]
    is_active: bool
    is_default: bool
    product_count: int = 0
    
    class Config:
        from_attributes = True

# Product
class MarketplaceSKUCreate(BaseModel):
    marketplace_id: int
    marketplace_sku: str
    marketplace_url: Optional[str] = None
    price_in_marketplace: Optional[float] = None
    sync_stock: bool = False

class MarketplaceSKUResponse(BaseModel):
    id: int
    marketplace_id: int
    marketplace_name: str
    marketplace_code: str
    marketplace_sku: str
    marketplace_url: Optional[str]
    price_in_marketplace: Optional[float]
    is_active: bool
    
    class Config:
        from_attributes = True

class ProductCreate(BaseModel):
    sku: str
    title: str
    description: Optional[str] = None
    category_id: Optional[int] = None
    brand: Optional[str] = None
    warehouse_id: int
    cost_price: float = 0
    sell_price: float = 0
    min_stock_alert: int = 5
    reorder_point: int = 10
    barcode: Optional[str] = None
    weight: Optional[float] = None
    marketplace_skus: List[MarketplaceSKUCreate] = []

class ProductUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    category_id: Optional[int] = None
    brand: Optional[str] = None
    cost_price: Optional[float] = None
    sell_price: Optional[float] = None
    min_stock_alert: Optional[int] = None
    is_active: Optional[bool] = None

class ProductResponse(BaseModel):
    id: int
    sku: str
    title: str
    description: Optional[str]
    category_id: Optional[int]
    category_name: Optional[str]
    brand: Optional[str]
    stock_quantity: int
    available_quantity: int
    reserved_quantity: int
    min_stock_alert: int
    reorder_point: int
    cost_price: float
    sell_price: float
    warehouse_id: int
    warehouse_name: str
    is_active: bool
    is_low_stock: bool
    needs_reorder: bool
    marketplace_skus: List[MarketplaceSKUResponse] = []
    
    class Config:
        from_attributes = True

# Transaction
class TransactionCreate(BaseModel):
    product_id: int
    warehouse_id: int
    type: TransactionType
    quantity: int
    unit_cost: Optional[float] = None
    reference_type: Optional[str] = None
    reference_id: Optional[str] = None
    notes: Optional[str] = None
    reason: Optional[str] = None

class TransactionResponse(BaseModel):
    id: int
    transaction_number: str
    type: str
    product_id: int
    product_sku: str
    product_title: str
    warehouse_id: int
    warehouse_name: str
    quantity: int
    quantity_before: Optional[int]
    quantity_after: Optional[int]
    unit_cost: Optional[float]
    total_cost: Optional[float]
    transaction_date: datetime
    notes: Optional[str]
    
    class Config:
        from_attributes = True

# Marketplace
class MarketplaceResponse(BaseModel):
    id: int
    name: str
    code: str
    website: Optional[str]
    is_active: bool
    
    class Config:
        from_attributes = True

# Stats
class WarehouseStats(BaseModel):
    total_products: int
    total_stock: int
    low_stock_items: int
    out_of_stock_items: int
    total_inventory_value: float
    today_transactions: int


# ==================== Warehouses ====================

@router.get("/warehouses", response_model=List[WarehouseResponse])
async def list_warehouses(
    active_only: bool = True,
    db: Session = Depends(get_db)
):
    """لیست انبارها"""
    query = db.query(Warehouse)
    
    if active_only:
        query = query.filter(Warehouse.is_active == True)
    
    warehouses = query.order_by(Warehouse.is_default.desc(), Warehouse.name).all()
    
    # شمارش محصولات هر انبار
    result = []
    for wh in warehouses:
        product_count = db.query(WarehouseProduct).filter(
            WarehouseProduct.warehouse_id == wh.id
        ).count()
        
        result.append(WarehouseResponse(
            id=wh.id,
            code=wh.code,
            name=wh.name,
            address=wh.address,
            city=wh.city,
            province=wh.province,
            warehouse_type=wh.warehouse_type,
            manager_name=wh.manager_name,
            is_active=wh.is_active,
            is_default=wh.is_default,
            product_count=product_count
        ))
    
    return result


@router.post("/warehouses", response_model=WarehouseResponse)
async def create_warehouse(
    warehouse: WarehouseCreate,
    db: Session = Depends(get_db)
):
    """ایجاد انبار جدید"""
    # چک تکراری
    if db.query(Warehouse).filter(Warehouse.code == warehouse.code).first():
        raise HTTPException(status_code=400, detail="کد انبار تکراری است")
    
    new_warehouse = Warehouse(**warehouse.dict())
    db.add(new_warehouse)
    db.commit()
    db.refresh(new_warehouse)
    
    return WarehouseResponse(
        id=new_warehouse.id,
        code=new_warehouse.code,
        name=new_warehouse.name,
        address=new_warehouse.address,
        city=new_warehouse.city,
        province=new_warehouse.province,
        warehouse_type=new_warehouse.warehouse_type,
        manager_name=new_warehouse.manager_name,
        is_active=new_warehouse.is_active,
        is_default=new_warehouse.is_default,
        product_count=0
    )


@router.put("/warehouses/{warehouse_id}")
async def update_warehouse(
    warehouse_id: int,
    updates: dict,
    db: Session = Depends(get_db)
):
    """به‌روزرسانی انبار"""
    warehouse = db.query(Warehouse).filter(Warehouse.id == warehouse_id).first()
    if not warehouse:
        raise HTTPException(status_code=404, detail="انبار یافت نشد")
    
    for key, value in updates.items():
        if hasattr(warehouse, key):
            setattr(warehouse, key, value)
    
    warehouse.updated_at = datetime.utcnow()
    db.commit()
    
    return {"success": True, "message": "انبار به‌روزرسانی شد"}


@router.delete("/warehouses/{warehouse_id}")
async def delete_warehouse(
    warehouse_id: int,
    db: Session = Depends(get_db)
):
    """حذف انبار"""
    warehouse = db.query(Warehouse).filter(Warehouse.id == warehouse_id).first()
    if not warehouse:
        raise HTTPException(status_code=404, detail="انبار یافت نشد")
    
    # چک کردن محصولات
    product_count = db.query(WarehouseProduct).filter(
        WarehouseProduct.warehouse_id == warehouse_id
    ).count()
    
    if product_count > 0:
        raise HTTPException(
            status_code=400, 
            detail=f"این انبار {product_count} محصول دارد. ابتدا محصولات را منتقل کنید"
        )
    
    db.delete(warehouse)
    db.commit()
    
    return {"success": True, "message": "انبار حذف شد"}


@router.post("/warehouses/{warehouse_id}/set-default")
async def set_default_warehouse(
    warehouse_id: int,
    db: Session = Depends(get_db)
):
    """تنظیم انبار پیش‌فرض"""
    warehouse = db.query(Warehouse).filter(Warehouse.id == warehouse_id).first()
    if not warehouse:
        raise HTTPException(status_code=404, detail="انبار یافت نشد")
    
    # حذف پیش‌فرض قبلی
    db.query(Warehouse).update({"is_default": False})
    
    warehouse.is_default = True
    db.commit()
    
    return {"success": True, "message": f"انبار '{warehouse.name}' به عنوان پیش‌فرض تنظیم شد"}


# ==================== Products ====================

@router.get("/products", response_model=List[ProductResponse])
async def list_products(
    warehouse_id: Optional[int] = None,
    category_id: Optional[int] = None,
    search: Optional[str] = None,
    low_stock_only: bool = False,
    active_only: bool = True,
    limit: int = Query(100, le=1000),
    offset: int = 0,
    db: Session = Depends(get_db)
):
    """لیست محصولات با فیلتر پیشرفته"""
    query = db.query(WarehouseProduct).options(
        joinedload(WarehouseProduct.warehouse),
        joinedload(WarehouseProduct.category),
        joinedload(WarehouseProduct.marketplace_skus).joinedload(ProductMarketplace.marketplace)
    )
    
    if warehouse_id:
        query = query.filter(WarehouseProduct.warehouse_id == warehouse_id)
    
    if category_id:
        query = query.filter(WarehouseProduct.category_id == category_id)
    
    if active_only:
        query = query.filter(WarehouseProduct.is_active == True)
    
    if search:
        search_term = f"%{search}%"
        query = query.filter(
            or_(
                WarehouseProduct.sku.like(search_term),
                WarehouseProduct.title.like(search_term),
                WarehouseProduct.barcode.like(search_term)
            )
        )
    
    if low_stock_only:
        query = query.filter(
            WarehouseProduct.available_quantity <= WarehouseProduct.min_stock_alert
        )
    
    products = query.order_by(WarehouseProduct.created_at.desc()).offset(offset).limit(limit).all()
    
    result = []
    for p in products:
        marketplace_skus = []
        for mp_sku in p.marketplace_skus:
            marketplace_skus.append(MarketplaceSKUResponse(
                id=mp_sku.id,
                marketplace_id=mp_sku.marketplace_id,
                marketplace_name=mp_sku.marketplace.name,
                marketplace_code=mp_sku.marketplace.code,
                marketplace_sku=mp_sku.marketplace_sku,
                marketplace_url=mp_sku.marketplace_url,
                price_in_marketplace=mp_sku.price_in_marketplace,
                is_active=mp_sku.is_active
            ))
        
        result.append(ProductResponse(
            id=p.id,
            sku=p.sku,
            title=p.title,
            description=p.description,
            category_id=p.category_id,
            category_name=p.category.name if p.category else None,
            brand=p.brand,
            stock_quantity=p.stock_quantity,
            available_quantity=p.available_quantity,
            reserved_quantity=p.reserved_quantity,
            min_stock_alert=p.min_stock_alert,
            reorder_point=p.reorder_point,
            cost_price=p.cost_price,
            sell_price=p.sell_price,
            warehouse_id=p.warehouse_id,
            warehouse_name=p.warehouse.name,
            is_active=p.is_active,
            is_low_stock=p.is_low_stock,
            needs_reorder=p.needs_reorder,
            marketplace_skus=marketplace_skus
        ))
    
    return result


@router.get("/products/{product_id}", response_model=ProductResponse)
async def get_product(
    product_id: int,
    db: Session = Depends(get_db)
):
    """جزئیات محصول"""
    product = db.query(WarehouseProduct).options(
        joinedload(WarehouseProduct.warehouse),
        joinedload(WarehouseProduct.category),
        joinedload(WarehouseProduct.marketplace_skus).joinedload(ProductMarketplace.marketplace)
    ).filter(WarehouseProduct.id == product_id).first()
    
    if not product:
        raise HTTPException(status_code=404, detail="محصول یافت نشد")
    
    marketplace_skus = [
        MarketplaceSKUResponse(
            id=mp_sku.id,
            marketplace_id=mp_sku.marketplace_id,
            marketplace_name=mp_sku.marketplace.name,
            marketplace_code=mp_sku.marketplace.code,
            marketplace_sku=mp_sku.marketplace_sku,
            marketplace_url=mp_sku.marketplace_url,
            price_in_marketplace=mp_sku.price_in_marketplace,
            is_active=mp_sku.is_active
        )
        for mp_sku in product.marketplace_skus
    ]
    
    return ProductResponse(
        id=product.id,
        sku=product.sku,
        title=product.title,
        description=product.description,
        category_id=product.category_id,
        category_name=product.category.name if product.category else None,
        brand=product.brand,
        stock_quantity=product.stock_quantity,
        available_quantity=product.available_quantity,
        reserved_quantity=product.reserved_quantity,
        min_stock_alert=product.min_stock_alert,
        reorder_point=product.reorder_point,
        cost_price=product.cost_price,
        sell_price=product.sell_price,
        warehouse_id=product.warehouse_id,
        warehouse_name=product.warehouse.name,
        is_active=product.is_active,
        is_low_stock=product.is_low_stock,
        needs_reorder=product.needs_reorder,
        marketplace_skus=marketplace_skus
    )


@router.post("/products", response_model=ProductResponse)
async def create_product(
    product: ProductCreate,
    db: Session = Depends(get_db)
):
    """ایجاد محصول جدید"""
    # چک تکراری
    if db.query(WarehouseProduct).filter(WarehouseProduct.sku == product.sku).first():
        raise HTTPException(status_code=400, detail="SKU تکراری است")
    
    # ایجاد محصول
    new_product = WarehouseProduct(
        sku=product.sku,
        title=product.title,
        description=product.description,
        category_id=product.category_id,
        brand=product.brand,
        warehouse_id=product.warehouse_id,
        cost_price=product.cost_price,
        sell_price=product.sell_price,
        min_stock_alert=product.min_stock_alert,
        reorder_point=product.reorder_point,
        barcode=product.barcode,
        weight=product.weight,
        is_active=True
    )
    
    db.add(new_product)
    db.flush()
    
    # اضافه کردن SKU های مارکت‌ها
    for mp_sku in product.marketplace_skus:
        marketplace_mapping = ProductMarketplace(
            product_id=new_product.id,
            marketplace_id=mp_sku.marketplace_id,
            marketplace_sku=mp_sku.marketplace_sku,
            marketplace_url=mp_sku.marketplace_url,
            price_in_marketplace=mp_sku.price_in_marketplace,
            sync_stock=mp_sku.sync_stock,
            is_active=True
        )
        db.add(marketplace_mapping)
    
    db.commit()
    db.refresh(new_product)
    
    return await get_product(new_product.id, db)


@router.put("/products/{product_id}")
async def update_product(
    product_id: int,
    updates: ProductUpdate,
    db: Session = Depends(get_db)
):
    """به‌روزرسانی محصول"""
    product = db.query(WarehouseProduct).filter(WarehouseProduct.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="محصول یافت نشد")
    
    update_data = updates.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(product, key, value)
    
    product.updated_at = datetime.utcnow()
    db.commit()
    
    return {"success": True, "message": "محصول به‌روزرسانی شد"}


@router.delete("/products/{product_id}")
async def delete_product(
    product_id: int,
    db: Session = Depends(get_db)
):
    """حذف محصول"""
    product = db.query(WarehouseProduct).filter(WarehouseProduct.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="محصول یافت نشد")
    
    db.delete(product)
    db.commit()
    
    return {"success": True, "message": "محصول حذف شد"}


# ==================== Marketplace SKUs ====================

@router.post("/products/{product_id}/marketplace-skus")
async def add_marketplace_sku(
    product_id: int,
    sku_data: MarketplaceSKUCreate,
    db: Session = Depends(get_db)
):
    """افزودن SKU مارکت به محصول"""
    product = db.query(WarehouseProduct).filter(WarehouseProduct.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="محصول یافت نشد")
    
    # چک تکراری
    existing = db.query(ProductMarketplace).filter(
        ProductMarketplace.product_id == product_id,
        ProductMarketplace.marketplace_id == sku_data.marketplace_id
    ).first()
    
    if existing:
        raise HTTPException(status_code=400, detail="این مارکت قبلاً برای این محصول ثبت شده")
    
    mapping = ProductMarketplace(
        product_id=product_id,
        marketplace_id=sku_data.marketplace_id,
        marketplace_sku=sku_data.marketplace_sku,
        marketplace_url=sku_data.marketplace_url,
        price_in_marketplace=sku_data.price_in_marketplace,
        sync_stock=sku_data.sync_stock,
        is_active=True
    )
    
    db.add(mapping)
    db.commit()
    
    return {"success": True, "message": "SKU مارکت اضافه شد"}


@router.delete("/marketplace-skus/{mapping_id}")
async def delete_marketplace_sku(
    mapping_id: int,
    db: Session = Depends(get_db)
):
    """حذف SKU مارکت"""
    mapping = db.query(ProductMarketplace).filter(ProductMarketplace.id == mapping_id).first()
    if not mapping:
        raise HTTPException(status_code=404, detail="SKU یافت نشد")
    
    db.delete(mapping)
    db.commit()
    
    return {"success": True, "message": "SKU مارکت حذف شد"}


# ==================== Marketplaces ====================

@router.get("/marketplaces", response_model=List[MarketplaceResponse])
async def list_marketplaces(
    active_only: bool = True,
    db: Session = Depends(get_db)
):
    """لیست مارکت‌ها"""
    query = db.query(Marketplace)
    
    if active_only:
        query = query.filter(Marketplace.is_active == True)
    
    marketplaces = query.order_by(Marketplace.name).all()
    
    return [
        MarketplaceResponse(
            id=m.id,
            name=m.name,
            code=m.code,
            website=m.website,
            is_active=m.is_active
        )
        for m in marketplaces
    ]


# ==================== Transactions ====================

@router.post("/transactions")
async def create_transaction(
    transaction: TransactionCreate,
    db: Session = Depends(get_db)
):
    """ایجاد تراکنش انبار"""
    product = db.query(WarehouseProduct).filter(WarehouseProduct.id == transaction.product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="محصول یافت نشد")
    
    quantity_before = product.stock_quantity
    
    # محاسبه موجودی جدید
    if transaction.type in [TransactionType.RECEIVE, TransactionType.RETURN]:
        quantity_after = quantity_before + transaction.quantity
    elif transaction.type in [TransactionType.DISPATCH, TransactionType.DAMAGE]:
        quantity_after = quantity_before - transaction.quantity
        if quantity_after < 0:
            raise HTTPException(status_code=400, detail="موجودی کافی نیست")
    else:
        quantity_after = quantity_before
    
    # ایجاد تراکنش
    new_transaction = InventoryTransaction(
        transaction_number=generate_transaction_number(),
        type=transaction.type,
        product_id=transaction.product_id,
        warehouse_id=transaction.warehouse_id,
        quantity=abs(transaction.quantity),
        quantity_before=quantity_before,
        quantity_after=quantity_after,
        unit_cost=transaction.unit_cost or product.cost_price,
        total_cost=(transaction.unit_cost or product.cost_price) * abs(transaction.quantity),
        reference_type=transaction.reference_type,
        reference_id=transaction.reference_id,
        notes=transaction.notes,
        reason=transaction.reason,
        is_approved=True
    )
    
    # به‌روزرسانی موجودی
    product.stock_quantity = quantity_after
    product.last_stock_update = datetime.utcnow()
    product.update_available_quantity()
    
    db.add(new_transaction)
    db.commit()
    
    return {
        "success": True,
        "message": "تراکنش ثبت شد",
        "transaction_number": new_transaction.transaction_number,
        "quantity_before": quantity_before,
        "quantity_after": quantity_after
    }


@router.get("/transactions", response_model=List[TransactionResponse])
async def list_transactions(
    warehouse_id: Optional[int] = None,
    product_id: Optional[int] = None,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """لیست تراکنش‌ها"""
    query = db.query(InventoryTransaction).options(
        joinedload(InventoryTransaction.product),
        joinedload(InventoryTransaction.warehouse)
    )
    
    if warehouse_id:
        query = query.filter(InventoryTransaction.warehouse_id == warehouse_id)
    
    if product_id:
        query = query.filter(InventoryTransaction.product_id == product_id)
    
    transactions = query.order_by(InventoryTransaction.created_at.desc()).limit(limit).all()
    
    return [
        TransactionResponse(
            id=t.id,
            transaction_number=t.transaction_number,
            type=t.type.value,
            product_id=t.product_id,
            product_sku=t.product.sku,
            product_title=t.product.title,
            warehouse_id=t.warehouse_id,
            warehouse_name=t.warehouse.name,
            quantity=t.quantity,
            quantity_before=t.quantity_before,
            quantity_after=t.quantity_after,
            unit_cost=t.unit_cost,
            total_cost=t.total_cost,
            transaction_date=t.transaction_date,
            notes=t.notes
        )
        for t in transactions
    ]


# ==================== Stats ====================

@router.get("/stats", response_model=WarehouseStats)
async def get_warehouse_stats(
    warehouse_id: Optional[int] = None,
    db: Session = Depends(get_db)
):
    """آمار انبار"""
    query = db.query(WarehouseProduct)
    
    if warehouse_id:
        query = query.filter(WarehouseProduct.warehouse_id == warehouse_id)
    
    total_products = query.count()
    
    low_stock = query.filter(
        WarehouseProduct.available_quantity <= WarehouseProduct.min_stock_alert
    ).count()
    
    out_of_stock = query.filter(WarehouseProduct.available_quantity == 0).count()
    
    products = query.all()
    total_stock = sum(p.stock_quantity for p in products)
    total_value = sum(p.cost_price * p.stock_quantity for p in products)
    
    # تراکنش‌های امروز
    today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    today_transactions = db.query(InventoryTransaction).filter(
        InventoryTransaction.created_at >= today_start
    ).count()
    
    return WarehouseStats(
        total_products=total_products,
        total_stock=total_stock,
        low_stock_items=low_stock,
        out_of_stock_items=out_of_stock,
        total_inventory_value=total_value,
        today_transactions=today_transactions
    )