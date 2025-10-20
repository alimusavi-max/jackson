# database/warehouse_models.py
"""
مدل‌های انبارداری - نسخه یکپارچه با warehouse_models_extended
"""
from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, ForeignKey, Text, JSON
from sqlalchemy.orm import relationship
from datetime import datetime
from .models import Base


class Warehouse(Base):
    """مدل انبار - چندین انبار قابل تعریف"""
    __tablename__ = 'warehouses'
    
    id = Column(Integer, primary_key=True)
    code = Column(String(50), unique=True, nullable=False, index=True)  # 🔥 اضافه شد
    name = Column(String(200), nullable=False)
    address = Column(Text)
    city = Column(String(100))
    province = Column(String(100))
    postal_code = Column(String(20))
    phone = Column(String(20))
    warehouse_type = Column(String(50), default="main")
    manager_name = Column(String(100))
    manager_phone = Column(String(20))
    is_active = Column(Boolean, default=True)
    is_default = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relations
    inventory_items = relationship("InventoryItem", back_populates="warehouse")
    stock_movements = relationship("StockMovement", back_populates="warehouse")
    
    def __repr__(self):
        return f"<Warehouse {self.code}: {self.name}>"


class ProductCategory(Base):
    """دسته‌بندی محصولات"""
    __tablename__ = 'product_categories'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    code = Column(String(50), unique=True)
    parent_id = Column(Integer, ForeignKey('product_categories.id'))
    description = Column(Text)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    parent = relationship("ProductCategory", remote_side=[id], backref="children")
    products = relationship("ProductMaster", back_populates="category")


class ProductMaster(Base):
    """محصول اصلی"""
    __tablename__ = 'product_master'
    
    id = Column(Integer, primary_key=True)
    internal_sku = Column(String(100), unique=True, nullable=False, index=True)
    name = Column(String(300), nullable=False)
    name_en = Column(String(300))
    description = Column(Text)
    category_id = Column(Integer, ForeignKey('product_categories.id'))
    
    # مشخصات فیزیکی
    barcode = Column(String(100), unique=True)
    weight = Column(Float)
    length = Column(Float)
    width = Column(Float)
    height = Column(Float)
    
    # قیمت‌گذاری
    cost_price = Column(Float, default=0)
    sell_price = Column(Float, default=0)
    wholesale_price = Column(Float)
    
    # موجودی
    total_stock = Column(Integer, default=0)
    reserved_stock = Column(Integer, default=0)
    available_stock = Column(Integer, default=0)
    min_stock_level = Column(Integer, default=0)
    max_stock_level = Column(Integer, default=1000)
    reorder_point = Column(Integer, default=10)
    reorder_quantity = Column(Integer, default=50)
    
    primary_image = Column(String(500))
    images = Column(JSON)
    
    is_active = Column(Boolean, default=True)
    is_serialized = Column(Boolean, default=False)
    brand = Column(String(100))
    manufacturer = Column(String(200))
    warranty_months = Column(Integer, default=0)
    
    tags = Column(JSON)
    attributes = Column(JSON)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = Column(Integer)
    
    category = relationship("ProductCategory", back_populates="products")
    platform_mappings = relationship("ProductPlatformMapping", back_populates="product")
    inventory_items = relationship("InventoryItem", back_populates="product")
    stock_movements = relationship("StockMovement", back_populates="product")
    
    @property
    def is_low_stock(self):
        return self.available_stock <= self.min_stock_level
    
    @property
    def profit_margin(self):
        if self.cost_price > 0:
            return ((self.sell_price - self.cost_price) / self.cost_price) * 100
        return 0


class ProductPlatformMapping(Base):
    """نگاشت شناسه‌های پلتفرم‌ها"""
    __tablename__ = 'product_platform_mappings'
    
    id = Column(Integer, primary_key=True)
    product_id = Column(Integer, ForeignKey('product_master.id'), nullable=False)
    platform = Column(String(50), nullable=False)
    platform_display_name = Column(String(100))
    platform_sku = Column(String(200), nullable=False)
    platform_product_id = Column(String(200))
    platform_url = Column(String(500))
    platform_price = Column(Float)
    commission_rate = Column(Float)
    is_active = Column(Boolean, default=True)
    is_synced = Column(Boolean, default=False)
    last_sync = Column(DateTime)
    notes = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    product = relationship("ProductMaster", back_populates="platform_mappings")


class InventoryItem(Base):
    """موجودی محصول در انبار"""
    __tablename__ = 'inventory_items'
    
    id = Column(Integer, primary_key=True)
    product_id = Column(Integer, ForeignKey('product_master.id'), nullable=False)
    warehouse_id = Column(Integer, ForeignKey('warehouses.id'), nullable=False)
    
    quantity = Column(Integer, default=0)
    reserved = Column(Integer, default=0)
    available = Column(Integer, default=0)
    damaged = Column(Integer, default=0)
    
    location = Column(String(100))
    zone = Column(String(50))
    cost_price_override = Column(Float)
    last_counted = Column(DateTime)
    notes = Column(Text)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    product = relationship("ProductMaster", back_populates="inventory_items")
    warehouse = relationship("Warehouse", back_populates="inventory_items")


class StockMovement(Base):
    """تراکنش‌های انبار"""
    __tablename__ = 'stock_movements'
    
    id = Column(Integer, primary_key=True)
    movement_type = Column(String(50), nullable=False)
    product_id = Column(Integer, ForeignKey('product_master.id'), nullable=False)
    warehouse_id = Column(Integer, ForeignKey('warehouses.id'), nullable=False)
    to_warehouse_id = Column(Integer, ForeignKey('warehouses.id'))
    
    quantity = Column(Integer, nullable=False)
    reference_type = Column(String(50))
    reference_id = Column(String(100))
    reference_number = Column(String(100))
    
    unit_cost = Column(Float)
    total_cost = Column(Float)
    status = Column(String(50), default='PENDING')
    
    scheduled_date = Column(DateTime)
    completed_date = Column(DateTime)
    
    created_by = Column(Integer)
    completed_by = Column(Integer)
    notes = Column(Text)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    product = relationship("ProductMaster", back_populates="stock_movements")
    warehouse = relationship("Warehouse", back_populates="stock_movements", foreign_keys=[warehouse_id])


class StockCount(Base):
    """موجودی‌گیری فیزیکی"""
    __tablename__ = 'stock_counts'
    
    id = Column(Integer, primary_key=True)
    count_number = Column(String(50), unique=True, nullable=False)
    warehouse_id = Column(Integer, ForeignKey('warehouses.id'), nullable=False)
    
    scheduled_date = Column(DateTime)
    started_at = Column(DateTime)
    completed_at = Column(DateTime)
    
    status = Column(String(50), default='DRAFT')
    created_by = Column(Integer)
    completed_by = Column(Integer)
    
    total_items_counted = Column(Integer, default=0)
    total_discrepancies = Column(Integer, default=0)
    
    notes = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    count_items = relationship("StockCountItem", back_populates="stock_count")


class StockCountItem(Base):
    """آیتم‌های موجودی‌گیری"""
    __tablename__ = 'stock_count_items'
    
    id = Column(Integer, primary_key=True)
    stock_count_id = Column(Integer, ForeignKey('stock_counts.id'), nullable=False)
    product_id = Column(Integer, ForeignKey('product_master.id'), nullable=False)
    
    system_quantity = Column(Integer)
    counted_quantity = Column(Integer)
    difference = Column(Integer)
    is_reconciled = Column(Boolean, default=False)
    
    notes = Column(Text)
    counted_by = Column(Integer)
    counted_at = Column(DateTime)
    
    stock_count = relationship("StockCount", back_populates="count_items")


class Supplier(Base):
    """تامین‌کننده"""
    __tablename__ = 'suppliers'
    
    id = Column(Integer, primary_key=True)
    code = Column(String(50), unique=True, nullable=False)
    name = Column(String(200), nullable=False)
    name_en = Column(String(200))
    
    contact_person = Column(String(100))
    phone = Column(String(20))
    mobile = Column(String(20))
    email = Column(String(100))
    website = Column(String(200))
    
    address = Column(Text)
    city = Column(String(100))
    province = Column(String(100))
    postal_code = Column(String(20))
    country = Column(String(100), default='ایران')
    
    bank_account = Column(String(50))
    bank_name = Column(String(100))
    tax_id = Column(String(50))
    
    payment_terms = Column(String(200))
    lead_time_days = Column(Integer)
    min_order_value = Column(Float)
    rating = Column(Float)
    
    is_active = Column(Boolean, default=True)
    notes = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)