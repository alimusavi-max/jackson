#!/bin/bash

echo "======================================"
echo "🔧 اسکریپت رفع مشکل فونت فارسی"
echo "======================================"

# رنگ‌ها
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# پیدا کردن روت پروژه
PROJECT_ROOT=$(pwd)
echo -e "\n📁 روت پروژه: ${PROJECT_ROOT}"

# بررسی وجود فونت
FONT_PATHS=(
    "${PROJECT_ROOT}/Vazir.ttf"
    "${PROJECT_ROOT}/backend/Vazir.ttf"
    "${PROJECT_ROOT}/backend/utils/Vazir.ttf"
)

FONT_FOUND=false
FONT_LOCATION=""

echo -e "\n🔍 جستجوی فونت..."
for path in "${FONT_PATHS[@]}"; do
    if [ -f "$path" ]; then
        echo -e "${GREEN}✅ پیدا شد: ${path}${NC}"
        FONT_FOUND=true
        FONT_LOCATION="$path"
        break
    else
        echo -e "${RED}❌ یافت نشد: ${path}${NC}"
    fi
done

if [ "$FONT_FOUND" = false ]; then
    echo -e "\n${YELLOW}⚠️  فونت Vazir.ttf پیدا نشد!${NC}"
    echo "آیا می‌خواهید الان دانلود شود؟ (y/n)"
    read -r response
    
    if [[ "$response" =~ ^[Yy]$ ]]; then
        echo -e "\n📥 در حال دانلود فونت..."
        
        cd "$PROJECT_ROOT" || exit
        
        wget -q https://github.com/rastikerdar/vazir-font/releases/download/v30.1.0/Vazir.ttf
        
        if [ -f "Vazir.ttf" ]; then
            echo -e "${GREEN}✅ فونت با موفقیت دانلود شد!${NC}"
            FONT_LOCATION="${PROJECT_ROOT}/Vazir.ttf"
            FONT_FOUND=true
        else
            echo -e "${RED}❌ خطا در دانلود فونت${NC}"
            exit 1
        fi
    else
        echo -e "${RED}❌ لطفاً فونت Vazir.ttf را دستی در روت پروژه قرار دهید${NC}"
        exit 1
    fi
fi

# کپی فونت به مکان‌های مورد نیاز
echo -e "\n📋 کپی فونت به مکان‌های مختلف..."

DEST_PATHS=(
    "${PROJECT_ROOT}/Vazir.ttf"
    "${PROJECT_ROOT}/backend/Vazir.ttf"
    "${PROJECT_ROOT}/backend/utils/Vazir.ttf"
)

for dest in "${DEST_PATHS[@]}"; do
    dest_dir=$(dirname "$dest")
    
    if [ ! -d "$dest_dir" ]; then
        mkdir -p "$dest_dir"
    fi
    
    if [ "$dest" != "$FONT_LOCATION" ]; then
        cp "$FONT_LOCATION" "$dest"
        if [ -f "$dest" ]; then
            echo -e "${GREEN}✅ کپی شد: ${dest}${NC}"