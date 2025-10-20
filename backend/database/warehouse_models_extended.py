# backend/database/warehouse_models_extended.py
"""
مدل‌های پیشرفته انبارداری - نسخه کامل با پشتیبانی چند انبار و چند پلتفرم
"""

from sqlalchemy import (
    Column, Integer, String, Float, Boolean, DateTime, Text, 
    ForeignKey, Enum as SQLEnum, CheckConstraint
)
from sqlalchemy.orm import relationship
from datetime import datetime
import enum

from database.models import Base


# ========== Enums ==========

class TransactionType(enum.Enum):
    """انواع تراکنش انبار"""
    RECEIVE = "receive"              # دریافت کالا (ورودی)
    DISPATCH = "dispatch"            # ارسال کالا (خروجی)
    RETURN = "return"                # برگشت از مشتری
    DAMAGE = "damage"                # کالای آسیب‌دیده
    ADJUSTMENT = "adjustment"        # تعدیل موجودی
    TRANSFER = "transfer"            # انتقال بین انبارها
    RESERVE = "reserve"              # رزرو برای سفارش
    UNRESERVE = "unreserve"          # لغو رزرو


class StockTakeStatus(enum.Enum):
    """وضعیت‌های انبارگردانی"""
    PENDING = "pending"              # در انتظار
    IN_PROGRESS = "in_progress"      # در حال انجام
    COMPLETED = "completed"          # تکمیل شده
    CANCELLED = "cancelled"          # لغو شده


# ========== Models ==========

class Warehouse(Base):
    """مدل انبار"""
    __tablename__ = "warehouses"

    id = Column(Integer, primary_key=True, index=True)
    code = Column(String(50), unique=True, nullable=False, index=True)
    name = Column(String(200), nullable=False)
    address = Column(Text, nullable=True)
    city = Column(String(100), nullable=True)
    province = Column(String(100), nullable=True)
    postal_code = Column(String(20), nullable=True)
    phone = Column(String(20), nullable=True)
    warehouse_type = Column(String(50), default="main")  # main, secondary, virtual
    manager_name = Column(String(100), nullable=True)
    manager_phone = Column(String(20), nullable=True)
    is_active = Column(Boolean, default=True)
    is_default = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    products = relationship("WarehouseProduct", back_populates="warehouse", cascade="all, delete-orphan")
    transactions = relationship("InventoryTransaction", back_populates="warehouse")

    def __repr__(self):
        return f"<Warehouse(code='{self.code}', name='{self.name}')>"


class ProductCategory(Base):
    """دسته‌بندی محصولات"""
    __tablename__ = "product_categories"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    slug = Column(String(100), unique=True, nullable=False)
    parent_id = Column(Integer, ForeignKey("product_categories.id"), nullable=True)
    description = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Self-referential relationship
    parent = relationship("ProductCategory", remote_side=[id], backref="children")
    products = relationship("WarehouseProduct", back_populates="category")

    def __repr__(self):
        return f"<Category(name='{self.name}')>"


class WarehouseProduct(Base):
    """محصول در انبار"""
    __tablename__ = "warehouse_products"

    id = Column(Integer, primary_key=True, index=True)
    sku = Column(String(100), unique=True, nullable=False, index=True)
    title = Column(String(500), nullable=False)
    description = Column(Text, nullable=True)
    
    # دسته‌بندی و برند
    category_id = Column(Integer, ForeignKey("product_categories.id"), nullable=True)
    brand = Column(String(100), nullable=True)
    
    # انبار
    warehouse_id = Column(Integer, ForeignKey("warehouses.id"), nullable=False)
    
    # موجودی
    stock_quantity = Column(Integer, default=0)
    available_quantity = Column(Integer, default=0)  # موجودی قابل فروش
    reserved_quantity = Column(Integer, default=0)   # موجودی رزرو شده
    min_stock_alert = Column(Integer, default=5)
    reorder_point = Column(Integer, default=10)
    
    # قیمت‌گذاری
    cost_price = Column(Float, default=0.0)          # قیمت تمام شده
    sell_price = Column(Float, default=0.0)          # قیمت فروش
    
    # اطلاعات فیزیکی
    barcode = Column(String(100), nullable=True, index=True)
    weight = Column(Float, nullable=True)            # وزن به گرم
    
    # وضعیت
    is_active = Column(Boolean, default=True)
    last_stock_update = Column(DateTime, default=datetime.utcnow)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    warehouse = relationship("Warehouse", back_populates="products")
    category = relationship("ProductCategory", back_populates="products")
    transactions = relationship("InventoryTransaction", back_populates="product")
    marketplace_skus = relationship("ProductMarketplace", back_populates="product", cascade="all, delete-orphan")

    # Properties
    @property
    def is_low_stock(self):
        """آیا موجودی کم است؟"""
        return self.available_quantity <= self.min_stock_alert

    @property
    def needs_reorder(self):
        """آیا نیاز به سفارش مجدد دارد؟"""
        return self.available_quantity <= self.reorder_point

    def update_available_quantity(self):
        """به‌روزرسانی موجودی قابل فروش"""
        self.available_quantity = max(0, self.stock_quantity - self.reserved_quantity)

    def __repr__(self):
        return f"<Product(sku='{self.sku}', title='{self.title[:30]}...')>"


class Marketplace(Base):
    """پلتفرم‌های فروش (دیجی‌کالا، باسلام، دیوار و...)"""
    __tablename__ = "marketplaces"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    code = Column(String(50), unique=True, nullable=False)  # digikala, basalam, divar
    website = Column(String(200), nullable=True)
    api_endpoint = Column(String(500), nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    product_mappings = relationship("ProductMarketplace", back_populates="marketplace")

    def __repr__(self):
        return f"<Marketplace(code='{self.code}', name='{self.name}')>"


class ProductMarketplace(Base):
    """ارتباط محصول با پلتفرم‌های فروش"""
    __tablename__ = "product_marketplace"

    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("warehouse_products.id"), nullable=False)
    marketplace_id = Column(Integer, ForeignKey("marketplaces.id"), nullable=False)
    
    marketplace_sku = Column(String(200), nullable=False)  # شماره محصول در آن پلتفرم
    marketplace_url = Column(String(500), nullable=True)
    price_in_marketplace = Column(Float, nullable=True)
    
    sync_stock = Column(Boolean, default=False)  # آیا موجودی همگام‌سازی شود؟
    last_sync = Column(DateTime, nullable=True)
    
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    product = relationship("WarehouseProduct", back_populates="marketplace_skus")
    marketplace = relationship("Marketplace", back_populates="product_mappings")

    def __repr__(self):
        return f"<ProductMarketplace(product_id={self.product_id}, marketplace='{self.marketplace.code}')>"


class InventoryTransaction(Base):
    """تراکنش‌های انبار"""
    __tablename__ = "inventory_transactions"

    id = Column(Integer, primary_key=True, index=True)
    transaction_number = Column(String(50), unique=True, nullable=False, index=True)
    
    type = Column(SQLEnum(TransactionType), nullable=False)
    product_id = Column(Integer, ForeignKey("warehouse_products.id"), nullable=False)
    warehouse_id = Column(Integer, ForeignKey("warehouses.id"), nullable=False)
    
    quantity = Column(Integer, nullable=False)
    quantity_before = Column(Integer, nullable=True)  # موجودی قبل از تراکنش
    quantity_after = Column(Integer, nullable=True)   # موجودی بعد از تراکنش
    
    unit_cost = Column(Float, nullable=True)
    total_cost = Column(Float, nullable=True)
    
    reference_type = Column(String(50), nullable=True)  # order, purchase, etc
    reference_id = Column(String(100), nullable=True)
    
    notes = Column(Text, nullable=True)
    reason = Column(String(200), nullable=True)
    
    transaction_date = Column(DateTime, default=datetime.utcnow)
    is_approved = Column(Boolean, default=True)
    approved_by = Column(Integer, nullable=True)  # User ID
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    product = relationship("WarehouseProduct", back_populates="transactions")
    warehouse = relationship("Warehouse", back_populates="transactions")

    def __repr__(self):
        return f"<Transaction(number='{self.transaction_number}', type='{self.type.value}')>"


class StockTake(Base):
    """انبارگردانی (شمارش فیزیکی موجودی)"""
    __tablename__ = "stock_takes"

    id = Column(Integer, primary_key=True, index=True)
    stock_take_number = Column(String(50), unique=True, nullable=False)
    warehouse_id = Column(Integer, ForeignKey("warehouses.id"), nullable=False)
    
    status = Column(SQLEnum(StockTakeStatus), default=StockTakeStatus.PENDING)
    
    start_date = Column(DateTime, nullable=True)
    end_date = Column(DateTime, nullable=True)
    
    conducted_by = Column(Integer, nullable=True)  # User ID
    notes = Column(Text, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    items = relationship("StockTakeItem", back_populates="stock_take", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<StockTake(number='{self.stock_take_number}', status='{self.status.value}')>"


class StockTakeItem(Base):
    """اقلام انبارگردانی"""
    __tablename__ = "stock_take_items"

    id = Column(Integer, primary_key=True, index=True)
    stock_take_id = Column(Integer, ForeignKey("stock_takes.id"), nullable=False)
    product_id = Column(Integer, ForeignKey("warehouse_products.id"), nullable=False)
    
    system_quantity = Column(Integer, nullable=False)    # موجودی سیستم
    counted_quantity = Column(Integer, nullable=True)    # موجودی شمارش شده
    difference = Column(Integer, nullable=True)          # اختلاف
    
    notes = Column(Text, nullable=True)
    counted_at = Column(DateTime, nullable=True)
    counted_by = Column(Integer, nullable=True)  # User ID

    # Relationships
    stock_take = relationship("StockTake", back_populates="items")

    def __repr__(self):
        return f"<StockTakeItem(product_id={self.product_id}, diff={self.difference})>"


# ========== Helper Functions ==========

def generate_transaction_number():
    """تولید شماره یکتا برای تراکنش"""
    from datetime import datetime
    return f"TRX-{datetime.now().strftime('%Y%m%d%H%M%S')}"


def generate_stock_take_number():
    """تولید شماره یکتا برای انبارگردانی"""
    from datetime import datetime
    return f"ST-{datetime.now().strftime('%Y%m%d%H%M%S')}"