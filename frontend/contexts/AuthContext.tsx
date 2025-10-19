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
    """آیتم‌های موجودی‌گیری"""
    __tablename__ = 'stock_take_items'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    stock_take_id = Column(Integer, ForeignKey('stock_takes.id'), nullable=False)
    product_id = Column(Integer, ForeignKey('warehouse_products.id'), nullable=False)
    
    # موجودی
    system_quantity = Column(Integer)  # موجودی در سیستم
    counted_quantity = Column(Integer)  # موجودی شمارش شده
    difference = Column(Integer)  # اختلاف
    
    notes = Column(Text)
    counted_at = Column(DateTime)
    counted_by = Column(Integer, ForeignKey('users.id'))
    
    # Relations
    stock_take = relationship("StockTake", back_populates="items")
    product = relationship("WarehouseProduct")
    counter = relationship("User")


class Supplier(Base):
    """تامین‌کنندگان"""
    __tablename__ = 'suppliers'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    code = Column(String(50), unique=True, nullable=False)
    name = Column(String(200), nullable=False)
    
    # اطلاعات تماس
    contact_person = Column(String(200))
    phone = Column(String(20))
    email = Column(String(100))
    website = Column(String(200))
    
    # آدرس
    address = Column(Text)
    city = Column(String(100))
    province = Column(String(100))
    postal_code = Column(String(20))
    
    # مالی
    tax_id = Column(String(50))
    account_number = Column(String(100))
    payment_terms = Column(String(200))  # شرایط پرداخت
    credit_limit = Column(Float)
    
    # وضعیت
    rating = Column(Integer, default=5)  # از 1 تا 5
    is_active = Column(Boolean, default=True)
    
    notes = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relations
    purchase_orders = relationship("PurchaseOrder", back_populates="supplier")


class PurchaseOrder(Base):
    """سفارش خرید"""
    __tablename__ = 'purchase_orders'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    po_number = Column(String(50), unique=True, nullable=False, index=True)
    
    supplier_id = Column(Integer, ForeignKey('suppliers.id'), nullable=False)
    warehouse_id = Column(Integer, ForeignKey('warehouses.id'), nullable=False)
    
    # تاریخ
    order_date = Column(DateTime, default=datetime.utcnow)
    expected_delivery_date = Column(DateTime)
    actual_delivery_date = Column(DateTime)
    
    # وضعیت
    status = Column(String(50), default="draft")  # draft, sent, partial, received, cancelled
    
    # مالی
    subtotal = Column(Float, default=0)
    tax = Column(Float, default=0)
    discount = Column(Float, default=0)
    shipping_cost = Column(Float, default=0)
    total = Column(Float, default=0)
    
    # کاربر
    created_by = Column(Integer, ForeignKey('users.id'))
    approved_by = Column(Integer, ForeignKey('users.id'))
    
    notes = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relations
    supplier = relationship("Supplier", back_populates="purchase_orders")
    warehouse = relationship("Warehouse")
    items = relationship("PurchaseOrderItem", back_populates="purchase_order")
    creator = relationship("User", foreign_keys=[created_by])
    approver = relationship("User", foreign_keys=[approved_by])


class PurchaseOrderItem(Base):
    """آیتم‌های سفارش خرید"""
    __tablename__ = 'purchase_order_items'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    purchase_order_id = Column(Integer, ForeignKey('purchase_orders.id'), nullable=False)
    product_id = Column(Integer, ForeignKey('warehouse_products.id'), nullable=False)
    
    quantity_ordered = Column(Integer, nullable=False)
    quantity_received = Column(Integer, default=0)
    
    unit_price = Column(Float, nullable=False)
    tax_rate = Column(Float, default=0)
    discount = Column(Float, default=0)
    total = Column(Float)
    
    notes = Column(Text)
    
    # Relations
    purchase_order = relationship("PurchaseOrder", back_populates="items")
    product = relationship("WarehouseProduct")


# ==================== به‌روزرسانی Order برای ارتباط با انبار ====================
from database.models import Order

# اضافه کردن ستون‌های جدید به Order
Order.created_by = Column(Integer, ForeignKey('users.id'))
Order.warehouse_id = Column(Integer, ForeignKey('warehouses.id'))
Order.is_warehouse_dispatched = Column(Boolean, default=False)
Order.dispatch_date = Column(DateTime)

# Relations
Order.creator = relationship("User", foreign_keys="Order.created_by", back_populates="created_orders")
Order.warehouse = relationship("Warehouse")


# ==================== توابع کمکی ====================

def generate_transaction_number() -> str:
    """تولید شماره تراکنش"""
    from datetime import datetime
    import random
    timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
    random_suffix = random.randint(1000, 9999)
    return f"TRX-{timestamp}-{random_suffix}"


def generate_po_number() -> str:
    """تولید شماره سفارش خرید"""
    from datetime import datetime
    import random
    timestamp = datetime.now().strftime('%Y%m%d')
    random_suffix = random.randint(100, 999)
    return f"PO-{timestamp}-{random_suffix}"


def generate_stock_take_number() -> str:
    """تولید شماره موجودی‌گیری"""
    from datetime import datetime
    timestamp = datetime.now().strftime('%Y%m%d')
    return f"ST-{timestamp}"


def create_inventory_transaction(
    session,
    product_id: int,
    warehouse_id: int,
    transaction_type: TransactionType,
    quantity: int,
    user_id: int,
    reference_type: str = None,
    reference_id: str = None,
    notes: str = None,
    unit_cost: float = None
):
    """ایجاد تراکنش انبار و به‌روزرسانی موجودی"""
    
    product = session.query(WarehouseProduct).get(product_id)
    if not product:
        raise ValueError("محصول یافت نشد")
    
    quantity_before = product.stock_quantity
    
    # محاسبه موجودی جدید
    if transaction_type in [TransactionType.RECEIVE, TransactionType.RETURN]:
        quantity_after = quantity_before + quantity
    elif transaction_type in [TransactionType.DISPATCH, TransactionType.DAMAGE]:
        quantity_after = quantity_before - quantity
        if quantity_after < 0:
            raise ValueError("موجودی کافی نیست")
    elif transaction_type == TransactionType.ADJUSTMENT:
        quantity_after = quantity  # در تعدیل، quantity همان موجودی جدید است
    else:
        quantity_after = quantity_before
    
    # ایجاد تراکنش
    transaction = InventoryTransaction(
        transaction_number=generate_transaction_number(),
        type=transaction_type,
        product_id=product_id,
        warehouse_id=warehouse_id,
        quantity=abs(quantity),
        quantity_before=quantity_before,
        quantity_after=quantity_after,
        unit_cost=unit_cost or product.cost_price,
        total_cost=(unit_cost or product.cost_price) * abs(quantity),
        reference_type=reference_type,
        reference_id=reference_id,
        notes=notes,
        created_by=user_id,
        is_approved=True  # می‌تونه workflow تایید داشته باشه
    )
    
    # به‌روزرسانی موجودی
    product.stock_quantity = quantity_after
    product.last_stock_update = datetime.utcnow()
    product.update_available_quantity()
    
    session.add(transaction)
    session.commit()
    
    return transaction


def initialize_warehouse_data(session):
    """ایجاد داده‌های اولیه انبار"""
    
    # انبار اصلی
    main_warehouse = session.query(Warehouse).filter_by(code="WH-001").first()
    if not main_warehouse:
        main_warehouse = Warehouse(
            code="WH-001",
            name="انبار مرکزی",
            address="تهران، خیابان ولیعصر",
            city="تهران",
            province="تهران",
            type="main",
            is_active=True
        )
        session.add(main_warehouse)
        session.commit()
        print("✅ انبار مرکزی ایجاد شد")
    
    # دسته‌بندی‌های نمونه
    categories_data = [
        ("electronics", "الکترونیک", None),
        ("mobile", "موبایل", "electronics"),
        ("laptop", "لپ‌تاپ", "electronics"),
        ("accessories", "لوازم جانبی", None),
    ]
    
    for slug, name, parent_slug in categories_data:
        cat = session.query(ProductCategory).filter_by(slug=slug).first()
        if not cat:
            parent_id = None
            if parent_slug:
                parent = session.query(ProductCategory).filter_by(slug=parent_slug).first()
                if parent:
                    parent_id = parent.id
            
            cat = ProductCategory(
                name=name,
                slug=slug,
                parent_id=parent_id,
                is_active=True
            )
            session.add(cat)
    
    session.commit()
    print("✅ دسته‌بندی‌ها ایجاد شدند")


if __name__ == "__main__":
    from database.models import init_database, get_session
    
    engine = init_database("../data/digikala_sales.db")
    session = get_session(engine)
    
    print("🔧 در حال ایجاد جداول انبارداری...")
    Base.metadata.create_all(engine)
    
    print("\n📦 ایجاد داده‌های اولیه...")
    initialize_warehouse_data(session)
    
    print("\n✅ جداول انبارداری ایجاد شدند!")
    session.close()