# backend/routers/sender_profiles.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

from database.models import SenderProfile, init_database, get_session
import os

router = APIRouter(prefix="/sender-profiles", tags=["Sender Profiles"])

# ========== Pydantic Models ==========
class SenderProfileCreate(BaseModel):
    profile_name: str
    sender_name: str
    address: str
    postal_code: str
    phone: str

class SenderProfileUpdate(BaseModel):
    profile_name: Optional[str] = None
    sender_name: Optional[str] = None
    address: Optional[str] = None
    postal_code: Optional[str] = None
    phone: Optional[str] = None

class SenderProfileResponse(BaseModel):
    id: int
    profile_name: str
    sender_name: str
    address: str
    postal_code: str
    phone: str
    is_default: bool
    created_at: datetime

    class Config:
        from_attributes = True

# ========== Database Dependency ==========
def get_db():
    """دریافت session دیتابیس"""
    db_path = os.path.join(os.path.dirname(__file__), '..', '..', 'data', 'digikala_sales.db')
    engine = init_database(db_path)
    db = get_session(engine)
    try:
        yield db
    finally:
        db.close()

# ========== Endpoints ==========

@router.get("/", response_model=List[SenderProfileResponse])
async def get_all_profiles(db: Session = Depends(get_db)):
    """
    دریافت تمام پروفایل‌های فرستنده
    
    Returns:
        لیست تمام پروفایل‌ها، پیش‌فرض در ابتدا
    """
    try:
        profiles = db.query(SenderProfile).order_by(
            SenderProfile.is_default.desc(),
            SenderProfile.created_at.desc()
        ).all()
        
        print(f"✅ {len(profiles)} پروفایل فرستنده دریافت شد")
        return profiles
    except Exception as e:
        print(f"❌ خطا در دریافت پروفایل‌ها: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{profile_id}", response_model=SenderProfileResponse)
async def get_profile(profile_id: int, db: Session = Depends(get_db)):
    """دریافت یک پروفایل خاص"""
    profile = db.query(SenderProfile).filter(SenderProfile.id == profile_id).first()
    
    if not profile:
        raise HTTPException(status_code=404, detail="پروفایل یافت نشد")
    
    return profile


@router.get("/default/get", response_model=SenderProfileResponse)
async def get_default_profile(db: Session = Depends(get_db)):
    """دریافت پروفایل پیش‌فرض"""
    profile = db.query(SenderProfile).filter(SenderProfile.is_default == True).first()
    
    if not profile:
        raise HTTPException(status_code=404, detail="پروفایل پیش‌فرض یافت نشد")
    
    return profile


@router.post("/", response_model=SenderProfileResponse)
async def create_profile(profile: SenderProfileCreate, db: Session = Depends(get_db)):
    """
    ایجاد پروفایل جدید فرستنده
    
    Args:
        profile: اطلاعات پروفایل جدید
    
    Returns:
        پروفایل ایجاد شده
    """
    try:
        # بررسی تکراری نبودن نام
        existing = db.query(SenderProfile).filter(
            SenderProfile.profile_name == profile.profile_name
        ).first()
        
        if existing:
            raise HTTPException(
                status_code=400, 
                detail=f"پروفایل با نام '{profile.profile_name}' قبلاً وجود دارد"
            )
        
        # اگر اولین پروفایل است، آن را پیش‌فرض کن
        is_first = db.query(SenderProfile).count() == 0
        
        new_profile = SenderProfile(
            profile_name=profile.profile_name,
            sender_name=profile.sender_name,
            address=profile.address,
            postal_code=profile.postal_code,
            phone=profile.phone,
            is_default=is_first
        )
        
        db.add(new_profile)
        db.commit()
        db.refresh(new_profile)
        
        print(f"✅ پروفایل '{profile.profile_name}' ایجاد شد (ID: {new_profile.id})")
        
        return new_profile
    
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        print(f"❌ خطا در ایجاد پروفایل: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/{profile_id}", response_model=SenderProfileResponse)
async def update_profile(
    profile_id: int,
    profile: SenderProfileUpdate,
    db: Session = Depends(get_db)
):
    """
    به‌روزرسانی پروفایل موجود
    
    Args:
        profile_id: شناسه پروفایل
        profile: اطلاعات جدید
    
    Returns:
        پروفایل به‌روزرسانی شده
    """
    try:
        db_profile = db.query(SenderProfile).filter(
            SenderProfile.id == profile_id
        ).first()
        
        if not db_profile:
            raise HTTPException(status_code=404, detail="پروفایل یافت نشد")
        
        # به‌روزرسانی فقط فیلدهایی که ارسال شده‌اند
        update_data = profile.dict(exclude_unset=True)
        
        # بررسی تکراری نبودن نام (اگر تغییر کرده)
        if 'profile_name' in update_data:
            existing = db.query(SenderProfile).filter(
                SenderProfile.profile_name == update_data['profile_name'],
                SenderProfile.id != profile_id
            ).first()
            
            if existing:
                raise HTTPException(
                    status_code=400,
                    detail=f"پروفایل با نام '{update_data['profile_name']}' قبلاً وجود دارد"
                )
        
        for key, value in update_data.items():
            setattr(db_profile, key, value)
        
        db.commit()
        db.refresh(db_profile)
        
        print(f"✅ پروفایل {profile_id} به‌روزرسانی شد")
        
        return db_profile
    
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        print(f"❌ خطا در به‌روزرسانی پروفایل: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{profile_id}")
async def delete_profile(profile_id: int, db: Session = Depends(get_db)):
    """
    حذف پروفایل
    
    Args:
        profile_id: شناسه پروفایل
    
    Returns:
        پیام موفقیت
    """
    try:
        db_profile = db.query(SenderProfile).filter(
            SenderProfile.id == profile_id
        ).first()
        
        if not db_profile:
            raise HTTPException(status_code=404, detail="پروفایل یافت نشد")
        
        # جلوگیری از حذف پروفایل پیش‌فرض
        if db_profile.is_default:
            # بررسی اینکه آیا پروفایل دیگری وجود دارد
            other_profiles = db.query(SenderProfile).filter(
                SenderProfile.id != profile_id
            ).count()
            
            if other_profiles > 0:
                raise HTTPException(
                    status_code=400,
                    detail="ابتدا پروفایل دیگری را به عنوان پیش‌فرض انتخاب کنید"
                )
        
        profile_name = db_profile.profile_name
        
        db.delete(db_profile)
        db.commit()
        
        print(f"✅ پروفایل '{profile_name}' حذف شد")
        
        return {
            "success": True,
            "message": f"پروفایل '{profile_name}' با موفقیت حذف شد"
        }
    
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        print(f"❌ خطا در حذف پروفایل: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{profile_id}/set-default")
async def set_default_profile(profile_id: int, db: Session = Depends(get_db)):
    """
    تنظیم پروفایل به عنوان پیش‌فرض
    
    Args:
        profile_id: شناسه پروفایل
    
    Returns:
        پیام موفقیت
    """
    try:
        db_profile = db.query(SenderProfile).filter(
            SenderProfile.id == profile_id
        ).first()
        
        if not db_profile:
            raise HTTPException(status_code=404, detail="پروفایل یافت نشد")
        
        # حذف پیش‌فرض قبلی
        db.query(SenderProfile).update({"is_default": False})
        
        # تنظیم پیش‌فرض جدید
        db_profile.is_default = True
        db.commit()
        
        print(f"✅ پروفایل '{db_profile.profile_name}' به عنوان پیش‌فرض تنظیم شد")
        
        return {
            "success": True,
            "message": f"پروفایل '{db_profile.profile_name}' به عنوان پیش‌فرض تنظیم شد",
            "profile": {
                "id": db_profile.id,
                "profile_name": db_profile.profile_name
            }
        }
    
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        print(f"❌ خطا در تنظیم پیش‌فرض: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/test/connection")
async def test_connection(db: Session = Depends(get_db)):
    """تست اتصال به دیتابیس پروفایل‌ها"""
    try:
        count = db.query(SenderProfile).count()
        return {
            "status": "ok",
            "message": "اتصال به دیتابیس موفق",
            "profiles_count": count
        }
    except Exception as e:
        return {
            "status": "error",
            "message": str(e)
        }