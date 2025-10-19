# backend/routers/auth.py
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr
from typing import Optional, List
from datetime import datetime, timedelta
from jose import JWTError, jwt
from passlib.context import CryptContext

from database.models import get_session, init_database
from database.auth_models import User, Role, Permission, AuditLog
import os

router = APIRouter(prefix="/auth", tags=["Authentication"])

# تنظیمات امنیتی
SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-change-this-in-production-123456")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24  # 24 ساعت

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")

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
class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    username: Optional[str] = None


class UserCreate(BaseModel):
    username: str
    email: EmailStr
    full_name: str
    password: str
    phone: Optional[str] = None


class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    full_name: Optional[str] = None
    phone: Optional[str] = None
    is_active: Optional[bool] = None


class UserResponse(BaseModel):
    id: int
    username: str
    email: str
    full_name: str
    phone: Optional[str]
    is_active: bool
    is_superuser: bool
    created_at: datetime
    last_login: Optional[datetime]
    roles: List[str]
    permissions: List[str]
    
    class Config:
        from_attributes = True


class AssignRolesRequest(BaseModel):
    user_id: int
    role_names: List[str]


# ========== توابع کمکی ==========
def verify_password(plain_password: str, hashed_password: str) -> bool:
    """چک کردن رمز عبور"""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """هش کردن رمز عبور"""
    return pwd_context.hash(password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """ایجاد JWT token"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def authenticate_user(db: Session, username: str, password: str):
    """احراز هویت کاربر"""
    user = db.query(User).filter(User.username == username).first()
    if not user:
        return False
    if not verify_password(password, user.password_hash):
        return False
    return user


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
) -> User:
    """دریافت کاربر فعلی از token"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="اعتبار سنجی نشد",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        token_data = TokenData(username=username)
    except JWTError:
        raise credentials_exception
    
    user = db.query(User).filter(User.username == token_data.username).first()
    if user is None:
        raise credentials_exception
    
    if not user.is_active:
        raise HTTPException(status_code=400, detail="کاربر غیرفعال است")
    
    return user


async def get_current_active_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """دریافت کاربر فعال"""
    if not current_user.is_active:
        raise HTTPException(status_code=400, detail="کاربر غیرفعال")
    return current_user


def check_permission(permission: str):
    """دکوراتور چک کردن مجوز"""
    async def permission_checker(
        current_user: User = Depends(get_current_user)
    ):
        if not current_user.has_permission(permission):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"شما دسترسی '{permission}' ندارید"
            )
        return current_user
    return permission_checker


def log_audit(
    db: Session,
    user_id: int,
    action: str,
    entity_type: str = None,
    entity_id: str = None,
    details: str = None,
    ip_address: str = None
):
    """ثبت لاگ فعالیت"""
    log = AuditLog(
        user_id=user_id,
        action=action,
        entity_type=entity_type,
        entity_id=entity_id,
        details=details,
        ip_address=ip_address
    )
    db.add(log)
    db.commit()


# ========== Endpoints ==========

@router.post("/login", response_model=Token)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    """ورود کاربر"""
    user = authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="نام کاربری یا رمز عبور اشتباه است",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # به‌روزرسانی زمان آخرین ورود
    user.last_login = datetime.utcnow()
    db.commit()
    
    # ثبت لاگ
    log_audit(db, user.id, "login", details="ورود موفق")
    
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}


@router.get("/me", response_model=UserResponse)
async def read_users_me(
    current_user: User = Depends(get_current_active_user)
):
    """دریافت اطلاعات کاربر فعلی"""
    return UserResponse(
        id=current_user.id,
        username=current_user.username,
        email=current_user.email,
        full_name=current_user.full_name,
        phone=current_user.phone,
        is_active=current_user.is_active,
        is_superuser=current_user.is_superuser,
        created_at=current_user.created_at,
        last_login=current_user.last_login,
        roles=[role.name for role in current_user.roles],
        permissions=list(set([
            perm.name 
            for role in current_user.roles 
            for perm in role.permissions
        ]))
    )


@router.post("/register", response_model=UserResponse)
async def register_user(
    user_data: UserCreate,
    current_user: User = Depends(check_permission("users_create")),
    db: Session = Depends(get_db)
):
    """ثبت‌نام کاربر جدید (فقط توسط ادمین)"""
    
    # چک کردن تکراری نبودن
    if db.query(User).filter(User.username == user_data.username).first():
        raise HTTPException(status_code=400, detail="نام کاربری تکراری است")
    
    if db.query(User).filter(User.email == user_data.email).first():
        raise HTTPException(status_code=400, detail="ایمیل تکراری است")
    
    # ایجاد کاربر
    new_user = User(
        username=user_data.username,
        email=user_data.email,
        full_name=user_data.full_name,
        password_hash=get_password_hash(user_data.password),
        phone=user_data.phone,
        is_active=True,
        is_superuser=False
    )
    
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    # ثبت لاگ
    log_audit(
        db, 
        current_user.id, 
        "create_user", 
        "user", 
        str(new_user.id),
        f"ایجاد کاربر {new_user.username}"
    )
    
    return UserResponse(
        id=new_user.id,
        username=new_user.username,
        email=new_user.email,
        full_name=new_user.full_name,
        phone=new_user.phone,
        is_active=new_user.is_active,
        is_superuser=new_user.is_superuser,
        created_at=new_user.created_at,
        last_login=new_user.last_login,
        roles=[],
        permissions=[]
    )


@router.get("/users", response_model=List[UserResponse])
async def get_all_users(
    current_user: User = Depends(check_permission("users_view")),
    db: Session = Depends(get_db)
):
    """دریافت لیست تمام کاربران"""
    users = db.query(User).all()
    
    return [
        UserResponse(
            id=user.id,
            username=user.username,
            email=user.email,
            full_name=user.full_name,
            phone=user.phone,
            is_active=user.is_active,
            is_superuser=user.is_superuser,
            created_at=user.created_at,
            last_login=user.last_login,
            roles=[role.name for role in user.roles],
            permissions=list(set([
                perm.name 
                for role in user.roles 
                for perm in role.permissions
            ]))
        )
        for user in users
    ]


@router.post("/users/{user_id}/assign-roles")
async def assign_roles_to_user(
    user_id: int,
    request: AssignRolesRequest,
    current_user: User = Depends(check_permission("users_assign_roles")),
    db: Session = Depends(get_db)
):
    """تخصیص نقش به کاربر"""
    user = db.query(User).get(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="کاربر یافت نشد")
    
    # حذف نقش‌های قبلی
    user.roles.clear()
    
    # اضافه کردن نقش‌های جدید
    for role_name in request.role_names:
        role = db.query(Role).filter(Role.name == role_name).first()
        if role:
            user.roles.append(role)
    
    db.commit()
    
    # ثبت لاگ
    log_audit(
        db,
        current_user.id,
        "assign_roles",
        "user",
        str(user_id),
        f"تخصیص نقش‌های {', '.join(request.role_names)}"
    )
    
    return {"message": "نقش‌ها با موفقیت تخصیص داده شدند"}


@router.get("/roles")
async def get_all_roles(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """دریافت لیست تمام نقش‌ها"""
    roles = db.query(Role).all()
    
    return [
        {
            "id": role.id,
            "name": role.name,
            "display_name": role.display_name,
            "description": role.description,
            "is_system": role.is_system,
            "permissions": [
                {
                    "name": perm.name,
                    "display_name": perm.display_name,
                    "category": perm.category
                }
                for perm in role.permissions
            ]
        }
        for role in roles
    ]


@router.get("/permissions")
async def get_all_permissions(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """دریافت لیست تمام مجوزها"""
    permissions = db.query(Permission).all()
    
    # گروه‌بندی بر اساس category
    grouped = {}
    for perm in permissions:
        if perm.category not in grouped:
            grouped[perm.category] = []
        grouped[perm.category].append({
            "name": perm.name,
            "display_name": perm.display_name,
            "description": perm.description
        })
    
    return grouped


@router.put("/users/{user_id}")
async def update_user(
    user_id: int,
    user_data: UserUpdate,
    current_user: User = Depends(check_permission("users_edit")),
    db: Session = Depends(get_db)
):
    """به‌روزرسانی کاربر"""
    user = db.query(User).get(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="کاربر یافت نشد")
    
    # به‌روزرسانی فیلدها
    if user_data.email:
        # چک تکراری
        existing = db.query(User).filter(
            User.email == user_data.email,
            User.id != user_id
        ).first()
        if existing:
            raise HTTPException(status_code=400, detail="ایمیل تکراری است")
        user.email = user_data.email
    
    if user_data.full_name:
        user.full_name = user_data.full_name
    
    if user_data.phone:
        user.phone = user_data.phone
    
    if user_data.is_active is not None:
        user.is_active = user_data.is_active
    
    user.updated_at = datetime.utcnow()
    db.commit()
    
    # ثبت لاگ
    log_audit(
        db,
        current_user.id,
        "update_user",
        "user",
        str(user_id),
        f"به‌روزرسانی کاربر {user.username}"
    )
    
    return {"message": "کاربر با موفقیت به‌روزرسانی شد"}


@router.delete("/users/{user_id}")
async def delete_user(
    user_id: int,
    current_user: User = Depends(check_permission("users_delete")),
    db: Session = Depends(get_db)
):
    """حذف کاربر"""
    if user_id == current_user.id:
        raise HTTPException(status_code=400, detail="نمی‌توانید خودتان را حذف کنید")
    
    user = db.query(User).get(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="کاربر یافت نشد")
    
    if user.is_superuser:
        raise HTTPException(status_code=400, detail="نمی‌توان ادمین کل را حذف کرد")
    
    username = user.username
    db.delete(user)
    db.commit()
    
    # ثبت لاگ
    log_audit(
        db,
        current_user.id,
        "delete_user",
        "user",
        str(user_id),
        f"حذف کاربر {username}"
    )
    
    return {"message": "کاربر با موفقیت حذف شد"}