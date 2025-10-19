# backend/database/auth_models.py
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Table, Enum as SQLEnum
from sqlalchemy.orm import relationship
from datetime import datetime
from database.models import Base
import enum

# جدول رابطه چند به چند بین کاربر و نقش
user_roles = Table(
    'user_roles',
    Base.metadata,
    Column('user_id', Integer, ForeignKey('users.id')),
    Column('role_id', Integer, ForeignKey('roles.id'))
)

# جدول رابطه چند به چند بین نقش و مجوز
role_permissions = Table(
    'role_permissions',
    Base.metadata,
    Column('role_id', Integer, ForeignKey('roles.id')),
    Column('permission_id', Integer, ForeignKey('permissions.id'))
)

class PermissionType(str, enum.Enum):
    """انواع مجوزها"""
    # فروش
    SALES_VIEW = "sales_view"
    SALES_CREATE = "sales_create"
    SALES_EDIT = "sales_edit"
    SALES_DELETE = "sales_delete"
    SALES_SYNC = "sales_sync"
    SALES_CONFIRM = "sales_confirm"
    
    # برچسب پستی
    LABELS_VIEW = "labels_view"
    LABELS_GENERATE = "labels_generate"
    
    # کد رهگیری
    TRACKING_VIEW = "tracking_view"
    TRACKING_UPDATE = "tracking_update"
    
    # پیامک
    SMS_VIEW = "sms_view"
    SMS_SEND = "sms_send"
    
    # گزارشات فروش
    REPORTS_VIEW = "reports_view"
    REPORTS_EXPORT = "reports_export"
    
    # انبارداری
    WAREHOUSE_VIEW = "warehouse_view"
    WAREHOUSE_CREATE = "warehouse_create"
    WAREHOUSE_EDIT = "warehouse_edit"
    WAREHOUSE_DELETE = "warehouse_delete"
    WAREHOUSE_INVENTORY = "warehouse_inventory"
    WAREHOUSE_RECEIVE = "warehouse_receive"
    WAREHOUSE_DISPATCH = "warehouse_dispatch"
    
    # مدیریت کاربران
    USERS_VIEW = "users_view"
    USERS_CREATE = "users_create"
    USERS_EDIT = "users_edit"
    USERS_DELETE = "users_delete"
    USERS_ASSIGN_ROLES = "users_assign_roles"
    
    # تنظیمات
    SETTINGS_VIEW = "settings_view"
    SETTINGS_EDIT = "settings_edit"


class User(Base):
    """مدل کاربر"""
    __tablename__ = 'users'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(50), unique=True, nullable=False, index=True)
    email = Column(String(100), unique=True, nullable=False, index=True)
    full_name = Column(String(200), nullable=False)
    password_hash = Column(String(255), nullable=False)
    
    is_active = Column(Boolean, default=True)
    is_superuser = Column(Boolean, default=False)  # ادمین کل
    
    phone = Column(String(20))
    avatar = Column(String(500))
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_login = Column(DateTime)
    
    # Relations
    roles = relationship("Role", secondary=user_roles, back_populates="users")
    created_orders = relationship("Order", foreign_keys="[Order.created_by]", back_populates="creator", lazy="dynamic")
    
    def has_permission(self, permission: str) -> bool:
        """چک کردن اینکه آیا کاربر مجوز خاصی دارد"""
        if self.is_superuser:
            return True
        
        for role in self.roles:
            if role.has_permission(permission):
                return True
        return False
    
    def has_any_permission(self, permissions: list) -> bool:
        """چک کردن اینکه آیا کاربر حداقل یکی از مجوزها را دارد"""
        return any(self.has_permission(p) for p in permissions)
    
    def has_all_permissions(self, permissions: list) -> bool:
        """چک کردن اینکه آیا کاربر همه مجوزها را دارد"""
        return all(self.has_permission(p) for p in permissions)


class Role(Base):
    """نقش کاربری"""
    __tablename__ = 'roles'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(50), unique=True, nullable=False)  # مثلا: admin, sales_manager, warehouse_staff
    display_name = Column(String(100), nullable=False)  # نام فارسی
    description = Column(String(500))
    
    is_system = Column(Boolean, default=False)  # نقش‌های سیستمی قابل حذف نیستند
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relations
    users = relationship("User", secondary=user_roles, back_populates="roles")
    permissions = relationship("Permission", secondary=role_permissions, back_populates="roles")
    
    def has_permission(self, permission: str) -> bool:
        """چک کردن اینکه آیا این نقش مجوز خاصی دارد"""
        return any(p.name == permission for p in self.permissions)


class Permission(Base):
    """مجوز دسترسی"""
    __tablename__ = 'permissions'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), unique=True, nullable=False)  # sales_view, warehouse_edit, etc
    display_name = Column(String(100), nullable=False)  # نام فارسی
    category = Column(String(50))  # sales, warehouse, admin, etc
    description = Column(String(500))
    
    # Relations
    roles = relationship("Role", secondary=role_permissions, back_populates="permissions")


class AuditLog(Base):
    """لاگ فعالیت‌های کاربران (برای امنیت و پیگیری)"""
    __tablename__ = 'audit_logs'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    action = Column(String(100))  # login, create_order, delete_product, etc
    entity_type = Column(String(50))  # order, product, user, etc
    entity_id = Column(String(100))
    details = Column(String(1000))  # JSON string
    ip_address = Column(String(50))
    user_agent = Column(String(500))
    created_at = Column(DateTime, default=datetime.utcnow)
    
    user = relationship("User")


# ==================== توابع کمکی ====================

def create_default_permissions(session):
    """ایجاد مجوزهای پیش‌فرض"""
    permissions_data = [
        # فروش
        ("sales_view", "مشاهده سفارشات", "sales", "مشاهده لیست و جزئیات سفارشات"),
        ("sales_create", "ایجاد سفارش", "sales", "ثبت سفارش جدید"),
        ("sales_edit", "ویرایش سفارش", "sales", "ویرایش اطلاعات سفارش"),
        ("sales_delete", "حذف سفارش", "sales", "حذف سفارشات"),
        ("sales_sync", "همگام‌سازی", "sales", "همگام‌سازی سفارشات با API"),
        ("sales_confirm", "تایید سفارش", "sales", "تایید سفارشات جدید"),
        
        # برچسب
        ("labels_view", "مشاهده برچسب", "labels", "مشاهده صفحه برچسب"),
        ("labels_generate", "تولید برچسب", "labels", "تولید و دانلود برچسب پستی"),
        
        # رهگیری
        ("tracking_view", "مشاهده رهگیری", "tracking", "مشاهده صفحه رهگیری"),
        ("tracking_update", "ثبت کد رهگیری", "tracking", "ثبت و به‌روزرسانی کد رهگیری"),
        
        # پیامک
        ("sms_view", "مشاهده پیامک", "sms", "مشاهده صفحه پیامک"),
        ("sms_send", "ارسال پیامک", "sms", "ارسال پیامک به مشتریان"),
        
        # گزارشات
        ("reports_view", "مشاهده گزارشات", "reports", "مشاهده گزارشات فروش"),
        ("reports_export", "خروجی گزارشات", "reports", "دانلود و خروجی گزارشات"),
        
        # انبارداری
        ("warehouse_view", "مشاهده انبار", "warehouse", "مشاهده موجودی و محصولات"),
        ("warehouse_create", "ایجاد محصول", "warehouse", "افزودن محصول جدید"),
        ("warehouse_edit", "ویرایش محصول", "warehouse", "ویرایش اطلاعات محصول"),
        ("warehouse_delete", "حذف محصول", "warehouse", "حذف محصولات"),
        ("warehouse_inventory", "موجودی‌گیری", "warehouse", "انجام موجودی‌گیری انبار"),
        ("warehouse_receive", "ورود کالا", "warehouse", "ثبت ورود کالا به انبار"),
        ("warehouse_dispatch", "خروج کالا", "warehouse", "ثبت خروج کالا از انبار"),
        
        # کاربران
        ("users_view", "مشاهده کاربران", "users", "مشاهده لیست کاربران"),
        ("users_create", "ایجاد کاربر", "users", "افزودن کاربر جدید"),
        ("users_edit", "ویرایش کاربر", "users", "ویرایش اطلاعات کاربر"),
        ("users_delete", "حذف کاربر", "users", "حذف کاربران"),
        ("users_assign_roles", "تخصیص نقش", "users", "تخصیص نقش به کاربران"),
        
        # تنظیمات
        ("settings_view", "مشاهده تنظیمات", "settings", "مشاهده تنظیمات سیستم"),
        ("settings_edit", "ویرایش تنظیمات", "settings", "ویرایش تنظیمات سیستم"),
    ]
    
    for name, display_name, category, description in permissions_data:
        perm = session.query(Permission).filter_by(name=name).first()
        if not perm:
            perm = Permission(
                name=name,
                display_name=display_name,
                category=category,
                description=description
            )
            session.add(perm)
    
    session.commit()
    print("✅ مجوزها ایجاد شدند")


def create_default_roles(session):
    """ایجاد نقش‌های پیش‌فرض"""
    # نقش ادمین کل
    admin_role = session.query(Role).filter_by(name="admin").first()
    if not admin_role:
        admin_role = Role(
            name="admin",
            display_name="مدیر کل",
            description="دسترسی کامل به تمام بخش‌ها",
            is_system=True
        )
        # اضافه کردن همه مجوزها
        all_permissions = session.query(Permission).all()
        admin_role.permissions = all_permissions
        session.add(admin_role)
    
    # نقش مدیر فروش
    sales_manager = session.query(Role).filter_by(name="sales_manager").first()
    if not sales_manager:
        sales_manager = Role(
            name="sales_manager",
            display_name="مدیر فروش",
            description="دسترسی کامل به بخش فروش",
            is_system=True
        )
        sales_perms = session.query(Permission).filter(
            Permission.category.in_(["sales", "labels", "tracking", "sms", "reports"])
        ).all()
        sales_manager.permissions = sales_perms
        session.add(sales_manager)
    
    # نقش کارمند فروش
    sales_staff = session.query(Role).filter_by(name="sales_staff").first()
    if not sales_staff:
        sales_staff = Role(
            name="sales_staff",
            display_name="کارمند فروش",
            description="دسترسی محدود به بخش فروش",
            is_system=True
        )
        staff_perms = session.query(Permission).filter(
            Permission.name.in_([
                "sales_view", "sales_edit",
                "labels_view", "labels_generate",
                "tracking_view", "tracking_update",
                "reports_view"
            ])
        ).all()
        sales_staff.permissions = staff_perms
        session.add(sales_staff)
    
    # نقش مدیر انبار
    warehouse_manager = session.query(Role).filter_by(name="warehouse_manager").first()
    if not warehouse_manager:
        warehouse_manager = Role(
            name="warehouse_manager",
            display_name="مدیر انبار",
            description="دسترسی کامل به بخش انبار",
            is_system=True
        )
        warehouse_perms = session.query(Permission).filter(
            Permission.category == "warehouse"
        ).all()
        warehouse_manager.permissions = warehouse_perms
        session.add(warehouse_manager)
    
    # نقش انبار دار
    warehouse_staff = session.query(Role).filter_by(name="warehouse_staff").first()
    if not warehouse_staff:
        warehouse_staff = Role(
            name="warehouse_staff",
            display_name="انبار دار",
            description="دسترسی محدود به بخش انبار",
            is_system=True
        )
        wh_staff_perms = session.query(Permission).filter(
            Permission.name.in_([
                "warehouse_view", "warehouse_edit",
                "warehouse_receive", "warehouse_dispatch"
            ])
        ).all()
        warehouse_staff.permissions = wh_staff_perms
        session.add(warehouse_staff)
    
    session.commit()
    print("✅ نقش‌ها ایجاد شدند")


def create_superuser(session, username: str, email: str, password: str, full_name: str):
    """ایجاد کاربر ادمین اولیه"""
    from passlib.context import CryptContext
    
    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
    
    user = session.query(User).filter_by(username=username).first()
    if not user:
        user = User(
            username=username,
            email=email,
            full_name=full_name,
            password_hash=pwd_context.hash(password),
            is_active=True,
            is_superuser=True
        )
        
        # اضافه کردن نقش admin
        admin_role = session.query(Role).filter_by(name="admin").first()
        if admin_role:
            user.roles.append(admin_role)
        
        session.add(user)
        session.commit()
        print(f"✅ کاربر ادمین '{username}' ایجاد شد")
    else:
        print(f"⚠️ کاربر '{username}' قبلاً وجود دارد")


# ==================== اسکریپت اولیه ====================
if __name__ == "__main__":
    from database.models import init_database, get_session
    
    engine = init_database("../data/digikala_sales.db")
    session = get_session(engine)
    
    print("🔧 در حال ایجاد جداول احراز هویت...")
    Base.metadata.create_all(engine)
    
    print("\n📋 ایجاد مجوزها...")
    create_default_permissions(session)
    
    print("\n👥 ایجاد نقش‌ها...")
    create_default_roles(session)
    
    print("\n👤 ایجاد کاربر ادمین...")
    create_superuser(
        session,
        username="admin",
        email="admin@company.com",
        password="admin123",  # ⚠️ حتماً تغییر بدید!
        full_name="مدیر سیستم"
    )
    
    print("\n✅ راه‌اندازی اولیه کامل شد!")
    session.close()