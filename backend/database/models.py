# database/models.py
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, ForeignKey, Text, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker
from datetime import datetime

Base = declarative_base()

# ============= بخش فروش =============

class Order(Base):
    """سفارشات اصلی"""
    __tablename__ = 'orders'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    order_code = Column(String(50), unique=True, nullable=False, index=True)
    shipment_id = Column(String(50), unique=True, nullable=False, index=True)
    customer_name = Column(String(200))
    customer_phone = Column(String(20))
    status = Column(String(100))
    
    # آدرس
    province = Column(String(100))
    city = Column(String(100))
    full_address = Column(Text)
    postal_code = Column(String(20))
    
    # رهگیری
    tracking_code = Column(String(50), index=True)
    
    # تاریخ
    order_date_persian = Column(String(20))
    order_date_gregorian = Column(DateTime, default=datetime.utcnow)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # ارتباط با کاربر و انبار
    created_by = Column(Integer, ForeignKey('users.id'), nullable=True)
    warehouse_id = Column(Integer, ForeignKey('warehouses.id'), nullable=True)
    is_warehouse_dispatched = Column(Boolean, default=False)
    dispatch_date = Column(DateTime, nullable=True)
    
    # Relations
    items = relationship("OrderItem", back_populates="order", cascade="all, delete-orphan")
    sms_logs = relationship("SMSLog", back_populates="order", cascade="all, delete-orphan")
    
    # 🔥 CRITICAL: بدون foreign_keys چون SQLAlchemy خودش تشخیص میده
    # creator = relationship - اینو نمیذاریم چون مشکل ایجاد میکنه
    # warehouse = relationship - اینو هم همینطور


class OrderItem(Base):
    """اقلام سفارش"""
    __tablename__ = 'order_items'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    order_id = Column(Integer, ForeignKey('orders.id'), nullable=False)
    
    product_title = Column(String(500))
    product_code = Column(String(100))
    product_image = Column(Text)
    quantity = Column(Integer, default=1)
    price = Column(Float, default=0)
    
    order = relationship("Order", back_populates="items")


class SMSLog(Base):
    """لاگ ارسال پیامک"""
    __tablename__ = 'sms_logs'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    order_id = Column(Integer, ForeignKey('orders.id'), nullable=False)
    tracking_code = Column(String(50))
    phone_number = Column(String(20))
    message = Column(Text)
    sent_at = Column(DateTime, default=datetime.utcnow)
    is_successful = Column(Boolean, default=True)
    error_message = Column(Text)
    
    order = relationship("Order", back_populates="sms_logs")


class SenderProfile(Base):
    """پروفایل‌های فرستنده"""
    __tablename__ = 'sender_profiles'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    profile_name = Column(String(200), unique=True, nullable=False)
    sender_name = Column(String(200))
    address = Column(Text)
    postal_code = Column(String(20))
    phone = Column(String(20))
    is_default = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)


# ============= بخش انبار =============

class Warehouse(Base):
    """انبارها"""
    __tablename__ = 'warehouses'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(200), nullable=False)
    location = Column(String(500))
    manager_name = Column(String(200))
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # 🔥 حذف products relationship برای جلوگیری از circular import


class Product(Base):
    """محصولات موجود در انبار"""
    __tablename__ = 'products'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    dkp_code = Column(String(100), unique=True, index=True)
    title = Column(String(500))
    category = Column(String(200))
    stock_quantity = Column(Integer, default=0)
    min_stock_alert = Column(Integer, default=5)
    cost_price = Column(Float, default=0)
    sell_price = Column(Float, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)


# ============= بخش حسابداری =============

class Invoice(Base):
    """فاکتورها"""
    __tablename__ = 'invoices'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    invoice_number = Column(String(50), unique=True, nullable=False)
    order_id = Column(Integer, ForeignKey('orders.id'))
    total_amount = Column(Float, default=0)
    paid_amount = Column(Float, default=0)
    payment_status = Column(String(50))
    created_at = Column(DateTime, default=datetime.utcnow)


# ============= Database Setup =============

def init_database(db_path="sales.db"):
    """ایجاد دیتابیس و جداول"""
    engine = create_engine(f'sqlite:///{db_path}', echo=False)
    Base.metadata.create_all(engine)
    return engine


def get_session(engine):
    """ایجاد session برای کار با دیتابیس"""
    Session = sessionmaker(bind=engine)
    return Session()


if __name__ == "__main__":
    engine = init_database("digikala_sales.db")
    session = get_session(engine)
    
    print("✅ دیتابیس با موفقیت ایجاد شد!")
    print("📊 جداول ایجاد شده:")
    for table in Base.metadata.tables.keys():
        print(f"  - {table}")