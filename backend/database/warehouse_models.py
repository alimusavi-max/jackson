# backend/database/warehouse_models.py
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Text, Boolean, Enum as SQLEnum
from sqlalchemy.orm import relationship
from datetime import datetime
from database.models import Base
import enum

class TransactionType(str, enum.Enum):
    """نوع تراکنش انبار"""
    RECEIVE = "receive"  # ورود کالا
    DISPATCH = "dispatch"  # خروج کالا
    RETURN = "return"  # مرجوعی
    ADJUSTMENT = "adjustment"  # تعدیل موجودی
    DAMAGE = "damage"  # خسارت
    TRANSFER = "transfer"  # انتقال بین انبارها


class ProductCategory(Base):
    """دسته‌بندی محصولات"""
    __tablename__ = 'product_categories'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(200), nullable=False)
    slug = Column(String(200), unique=True, index=True)
    parent_id = Column(Integer, ForeignKey('product_categories.id'))
    description = Column(Text)
    image = Column(String(500))
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relations
    parent = relationship("ProductCategory", remote_side=[id], backref="children")
    products = relationship("WarehouseProduct", back_populates="category")


class WarehouseProduct(Base):
    """محصولات انبار (نسخه پیشرفته‌تر Product)"""
    __tablename__ = 'warehouse_products'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # اطلاعات پایه
    sku = Column(String(100), unique=True, index=True, nullable=False)  # کد SKU
    dkp_code = Column(String(100), index=True)  # کد دیجی‌کالا
    barcode = Column(String(100), index=True)  # بارکد
    title = Column(String(500), nullable=False)
    description = Column(Text)
    
    # دسته‌بندی
    category_id = Column(Integer, ForeignKey('product_categories.id'))
    brand = Column(String(200))
    model = Column(String(200))
    
    # موجودی
    stock_quantity = Column(Integer, default=0)
    reserved_quantity = Column(Integer, default=0)  # موجودی رزرو شده
    available_quantity = Column(Integer, default=0)  # موجودی قابل فروش
    
    # هشدار موجودی
    min_stock_alert = Column(Integer, default=5)
    max_stock_capacity = Column(Integer)
    reorder_point = Column(Integer, default=10)  # نقطه سفارش مجدد
    
    # قیمت
    cost_price = Column(Float, default=0)  # قیمت تمام شده
    sell_price = Column(Float, default=0)  # قیمت فروش
    wholesale_price = Column(Float)  # قیمت عمده
    
    # ابعاد و وزن
    weight = Column(Float)  # وزن (گرم)
    length = Column(Float)  # طول (سانتی‌متر)
    width = Column(Float)  # عرض
    height = Column(Float)  # ارتفاع
    
    # تصاویر
    main_image = Column(String(500))
    images = Column(Text)  # JSON array
    
    # موقعیت در انبار
    warehouse_id = Column(Integer, ForeignKey('warehouses.id'))
    location = Column(String(200))  # محل دقیق در انبار (مثلا: قفسه A-3)
    bin_location = Column(String(100))
    
    # وضعیت
    is_active = Column(Boolean, default=True)
    is_serialized = Column(Boolean, default=False)  # آیا سریال دارد؟
    
    # تاریخ‌ها
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_stock_update = Column(DateTime)
    
    # Relations
    category = relationship("ProductCategory", back_populates="products")
    warehouse = relationship("Warehouse", back_populates="products")
    transactions = relationship("InventoryTransaction", back_populates="product")
    serials = relationship("ProductSerial", back_populates="product")
    
    @property
    def is_low_stock(self):
        """آیا موجودی کم است؟"""
        return self.available_quantity <= self.min_stock_alert
    
    @property
    def needs_reorder(self):
        """آیا نیاز به سفارش مجدد دارد؟"""
        return self.available_quantity <= self.reorder_point
    
    def update_available_quantity(self):
        """محاسبه موجودی قابل فروش"""
        self.available_quantity = self.stock_quantity - self.reserved_quantity


class Warehouse(Base):
    """انبارها"""
    __tablename__ = 'warehouses'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    code = Column(String(50), unique=True, nullable=False)
    name = Column(String(200), nullable=False)
    
    # موقعیت
    address = Column(Text)
    city = Column(String(100))
    province = Column(String(100))
    postal_code = Column(String(20))
    phone = Column(String(20))
    
    # مشخصات
    capacity = Column(Float)  # ظرفیت (متر مربع)
    type = Column(String(50))  # main, secondary, transit
    
    # مدیریت
    manager_name = Column(String(200))
    manager_phone = Column(String(20))
    
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relations
    products = relationship("WarehouseProduct", back_populates="warehouse")
    transactions = relationship("InventoryTransaction", back_populates="warehouse")


class InventoryTransaction(Base):
    """تراکنش‌های انبار (ورود/خروج/تعدیل)"""
    __tablename__ = 'inventory_transactions'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    transaction_number = Column(String(50), unique=True, nullable=False, index=True)
    
    # نوع تراکنش
    type = Column(SQLEnum(TransactionType), nullable=False)
    
    # محصول و انبار
    product_id = Column(Integer, ForeignKey('warehouse_products.id'), nullable=False)
    warehouse_id = Column(Integer, ForeignKey('warehouses.id'), nullable=False)
    
    # مقادیر
    quantity = Column(Integer, nullable=False)
    quantity_before = Column(Integer)  # موجودی قبل
    quantity_after = Column(Integer)  # موجودی بعد
    
    unit_cost = Column(Float)  # هزینه واحد
    total_cost = Column(Float)  # هزینه کل
    
    # اطلاعات مرجع
    reference_type = Column(String(50))  # order, purchase, manual
    reference_id = Column(String(100))  # شماره سفارش، فاکتور و ...
    
    # توضیحات
    notes = Column(Text)
    reason = Column(String(500))
    
    # کاربر
    created_by = Column(Integer, ForeignKey('users.id'))
    approved_by = Column(Integer, ForeignKey('users.id'))
    
    # تاریخ
    transaction_date = Column(DateTime, default=datetime.utcnow)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # وضعیت
    is_approved = Column(Boolean, default=False)
    
    # Relations
    product = relationship("WarehouseProduct", back_populates="transactions")
    warehouse = relationship("Warehouse", back_populates="transactions")
    creator = relationship("User", foreign_keys=[created_by])
    approver = relationship("User", foreign_keys=[approved_by])


class ProductSerial(Base):
    """سریال محصولات (برای کالاهای سریال‌دار)"""
    __tablename__ = 'product_serials'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    product_id = Column(Integer, ForeignKey('warehouse_products.id'), nullable=False)
    serial_number = Column(String(200), unique=True, nullable=False, index=True)
    imei = Column(String(100), index=True)  # برای موبایل
    
    status = Column(String(50), default="in_stock")  # in_stock, sold, returned, damaged
    
    purchase_date = Column(DateTime)
    warranty_expire_date = Column(DateTime)
    
    # اگر فروخته شده
    sold_date = Column(DateTime)
    order_id = Column(Integer, ForeignKey('orders.id'))
    
    notes = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relations
    product = relationship("WarehouseProduct", back_populates="serials")
    order = relationship("Order")


class StockTake(Base):
    """موجودی‌گیری انبار"""
    __tablename__ = 'stock_takes'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    stock_take_number = Column(String(50), unique=True, nullable=False)
    
    warehouse_id = Column(Integer, ForeignKey('warehouses.id'), nullable=False)
    
    status = Column(String(50), default="draft")  # draft, in_progress, completed
    
    start_date = Column(DateTime)
    end_date = Column(DateTime)
    
    conducted_by = Column(Integer, ForeignKey('users.id'))
    approved_by = Column(Integer, ForeignKey('users.id'))
    
    total_items_counted = Column(Integer, default=0)
    total_discrepancies = Column(Integer, default=0)
    
    notes = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relations
    warehouse = relationship("Warehouse")
    conductor = relationship("User", foreign_keys=[conducted_by])
    approver = relationship("User", foreign_keys=[approved_by])
    items = relationship("StockTakeItem", back_populates="stock_take")


class StockTakeItem(Base):
    """آیتم‌های مو