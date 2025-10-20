# database/warehouse_models.py
from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, ForeignKey, Text, JSON
from sqlalchemy.orm import relationship
from datetime import datetime
from .models import Base

class Warehouse(Base):
    """مدل انبار - چندین انبار قابل تعریف"""
    __tablename__ = 'warehouses'
    
    id = Column(Integer, primary_key=True)
    code = Column(String(50), unique=True, nullable=False)  # کد انبار (مثلاً: WH-001)
    name = Column(String(200), nullable=False)
    address = Column(Text)
    city = Column(String(100))
    province = Column(String(100))
    postal_code = Column(String(20))
    manager_name = Column(String(100))
    manager_phone = Column(String(20))
    is_active = Column(Boolean, default=True)
    is_default = Column(Boolean, default=False)  # انبار پیش‌فرض
    capacity = Column(Float)  # ظرفیت کل (مترمربع یا تعداد)
    description = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # روابط
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
    
    # روابط
    parent = relationship("ProductCategory", remote_side=[id], backref="children")
    products = relationship("ProductMaster", back_populates="category")


class ProductMaster(Base):
    """محصول اصلی - با شناسه‌های چندگانه"""
    __tablename__ = 'product_master'
    
    id = Column(Integer, primary_key=True)
    
    # شناسه داخلی سیستم
    internal_sku = Column(String(100), unique=True, nullable=False, index=True)
    
    # اطلاعات پایه
    name = Column(String(300), nullable=False)
    name_en = Column(String(300))
    description = Column(Text)
    category_id = Column(Integer, ForeignKey('product_categories.id'))
    
    # مشخصات فیزیکی
    barcode = Column(String(100), unique=True)
    weight = Column(Float)  # گرم
    length = Column(Float)  # سانتی‌متر
    width = Column(Float)
    height = Column(Float)
    
    # قیمت‌گذاری
    cost_price = Column(Float, default=0)  # قیمت خرید
    sell_price = Column(Float, default=0)  # قیمت فروش
    wholesale_price = Column(Float)  # قیمت عمده
    
    # موجودی
    total_stock = Column(Integer, default=0)  # موجودی کل در همه انبارها
    reserved_stock = Column(Integer, default=0)  # موجودی رزرو شده
    available_stock = Column(Integer, default=0)  # موجودی قابل فروش
    min_stock_level = Column(Integer, default=0)  # حداقل موجودی
    max_stock_level = Column(Integer, default=1000)  # حداکثر موجودی
    reorder_point = Column(Integer, default=10)  # نقطه سفارش مجدد
    reorder_quantity = Column(Integer, default=50)  # مقدار سفارش مجدد
    
    # تصاویر و رسانه
    primary_image = Column(String(500))
    images = Column(JSON)  # لیست تصاویر اضافی
    
    # متا
    is_active = Column(Boolean, default=True)
    is_serialized = Column(Boolean, default=False)  # آیا نیاز به شماره سریال دارد
    brand = Column(String(100))
    manufacturer = Column(String(200))
    warranty_months = Column(Integer, default=0)
    
    tags = Column(JSON)  # تگ‌ها
    attributes = Column(JSON)  # مشخصات تکمیلی (رنگ، سایز و...)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = Column(Integer)
    
    # روابط
    category = relationship("ProductCategory", back_populates="products")
    platform_mappings = relationship("ProductPlatformMapping", back_populates="product")
    inventory_items = relationship("InventoryItem", back_populates="product")
    stock_movements = relationship("StockMovement", back_populates="product")
    
    @property
    def is_low_stock(self):
        """آیا موجودی کم است؟"""
        return self.available_stock <= self.min_stock_level
    
    @property
    def profit_margin(self):
        """حاشیه سود (درصد)"""
        if self.cost_price > 0:
            return ((self.sell_price - self.cost_price) / self.cost_price) * 100
        return 0
    
    def __repr__(self):
        return f"<Product {self.internal_sku}: {self.name}>"


class ProductPlatformMapping(Base):
    """نگاشت شناسه‌های پلتفرم‌های مختلف به محصول"""
    __tablename__ = 'product_platform_mappings'
    
    id = Column(Integer, primary_key=True)
    product_id = Column(Integer, ForeignKey('product_master.id'), nullable=False)
    
    # پلتفرم
    platform = Column(String(50), nullable=False)  # digikala, torob, snappfood, etc.
    platform_display_name = Column(String(100))
    
    # شناسه در پلتفرم
    platform_sku = Column(String(200), nullable=False)
    platform_product_id = Column(String(200))  # ID داخلی پلتفرم
    platform_url = Column(String(500))
    
    # قیمت در پلتفرم (ممکن است متفاوت باشد)
    platform_price = Column(Float)
    commission_rate = Column(Float)  # درصد کمیسیون
    
    # وضعیت
    is_active = Column(Boolean, default=True)
    is_synced = Column(Boolean, default=False)
    last_sync = Column(DateTime)
    
    # متا
    notes = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # روابط
    product = relationship("ProductMaster", back_populates="platform_mappings")
    
    def __repr__(self):
        return f"<Mapping {self.platform}: {self.platform_sku}>"


class InventoryItem(Base):
    """موجودی محصول در انبار خاص"""
    __tablename__ = 'inventory_items'
    
    id = Column(Integer, primary_key=True)
    product_id = Column(Integer, ForeignKey('product_master.id'), nullable=False)
    warehouse_id = Column(Integer, ForeignKey('warehouses.id'), nullable=False)
    
    # موجودی
    quantity = Column(Integer, default=0)
    reserved = Column(Integer, default=0)
    available = Column(Integer, default=0)
    damaged = Column(Integer, default=0)  # معیوب
    
    # محل نگهداری
    location = Column(String(100))  # مثلاً: A-12-3 (ردیف-قفسه-طبقه)
    zone = Column(String(50))  # منطقه انبار
    
    # قیمت‌گذاری برای این انبار (در صورت نیاز)
    cost_price_override = Column(Float)
    
    # متا
    last_counted = Column(DateTime)  # آخرین موجودی‌گیری فیزیکی
    notes = Column(Text)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # روابط
    product = relationship("ProductMaster", back_populates="inventory_items")
    warehouse = relationship("Warehouse", back_populates="inventory_items")
    
    def __repr__(self):
        return f"<Inventory P:{self.product_id} W:{self.warehouse_id} Q:{self.quantity}>"


class StockMovement(Base):
    """تراکنش‌های انبار - ورود/خروج/انتقال"""
    __tablename__ = 'stock_movements'
    
    id = Column(Integer, primary_key=True)
    
    # نوع حرکت
    movement_type = Column(String(50), nullable=False)  # RECEIVE, DISPATCH, TRANSFER, ADJUSTMENT, DAMAGE, RETURN
    
    # محصول و انبار
    product_id = Column(Integer, ForeignKey('product_master.id'), nullable=False)
    warehouse_id = Column(Integer, ForeignKey('warehouses.id'), nullable=False)
    
    # انبار مقصد (در صورت انتقال)
    to_warehouse_id = Column(Integer, ForeignKey('warehouses.id'))
    
    # مقدار
    quantity = Column(Integer, nullable=False)
    
    # مرجع
    reference_type = Column(String(50))  # ORDER, PURCHASE, MANUAL, etc.
    reference_id = Column(String(100))
    reference_number = Column(String(100))  # شماره فاکتور، سفارش و...
    
    # قیمت واحد (در زمان تراکنش)
    unit_cost = Column(Float)
    total_cost = Column(Float)
    
    # وضعیت
    status = Column(String(50), default='PENDING')  # PENDING, COMPLETED, CANCELLED
    
    # زمان‌بندی
    scheduled_date = Column(DateTime)
    completed_date = Column(DateTime)
    
    # کاربر و توضیحات
    created_by = Column(Integer)  # user_id
    completed_by = Column(Integer)
    notes = Column(Text)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # روابط
    product = relationship("ProductMaster", back_populates="stock_movements")
    warehouse = relationship("Warehouse", back_populates="stock_movements", foreign_keys=[warehouse_id])
    
    def __repr__(self):
        return f"<Movement {self.movement_type}: {self.quantity}x P:{self.product_id}>"


class StockCount(Base):
    """موجودی‌گیری فیزیکی"""
    __tablename__ = 'stock_counts'
    
    id = Column(Integer, primary_key=True)
    
    # شناسایی
    count_number = Column(String(50), unique=True, nullable=False)
    warehouse_id = Column(Integer, ForeignKey('warehouses.id'), nullable=False)
    
    # زمان‌بندی
    scheduled_date = Column(DateTime)
    started_at = Column(DateTime)
    completed_at = Column(DateTime)
    
    # وضعیت
    status = Column(String(50), default='DRAFT')  # DRAFT, IN_PROGRESS, COMPLETED, CANCELLED
    
    # کاربران
    created_by = Column(Integer)
    completed_by = Column(Integer)
    
    # نتایج
    total_items_counted = Column(Integer, default=0)
    total_discrepancies = Column(Integer, default=0)
    
    notes = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # روابط
    count_items = relationship("StockCountItem", back_populates="stock_count")


class StockCountItem(Base):
    """آیتم‌های موجودی‌گیری"""
    __tablename__ = 'stock_count_items'
    
    id = Column(Integer, primary_key=True)
    stock_count_id = Column(Integer, ForeignKey('stock_counts.id'), nullable=False)
    product_id = Column(Integer, ForeignKey('product_master.id'), nullable=False)
    
    # موجودی
    system_quantity = Column(Integer)  # موجودی در سیستم
    counted_quantity = Column(Integer)  # موجودی شمارش شده
    difference = Column(Integer)  # اختلاف
    
    # وضعیت
    is_reconciled = Column(Boolean, default=False)
    
    notes = Column(Text)
    counted_by = Column(Integer)
    counted_at = Column(DateTime)
    
    # روابط
    stock_count = relationship("StockCount", back_populates="count_items")


class Supplier(Base):
    """تامین‌کننده"""
    __tablename__ = 'suppliers'
    
    id = Column(Integer, primary_key=True)
    
    # شناسایی
    code = Column(String(50), unique=True, nullable=False)
    name = Column(String(200), nullable=False)
    name_en = Column(String(200))
    
    # اطلاعات تماس
    contact_person = Column(String(100))
    phone = Column(String(20))
    mobile = Column(String(20))
    email = Column(String(100))
    website = Column(String(200))
    
    # آدرس
    address = Column(Text)
    city = Column(String(100))
    province = Column(String(100))
    postal_code = Column(String(20))
    country = Column(String(100), default='ایران')
    
    # مالی
    bank_account = Column(String(50))
    bank_name = Column(String(100))
    tax_id = Column(String(50))
    
    # شرایط
    payment_terms = Column(String(200))  # شرایط پرداخت
    lead_time_days = Column(Integer)  # زمان تحویل
    min_order_value = Column(Float)  # حداقل مبلغ سفارش
    
    # رتبه‌بندی
    rating = Column(Float)  # از 1 تا 5
    
    # وضعیت
    is_active = Column(Boolean, default=True)
    
    notes = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f"<Supplier {self.code}: {self.name}>"