@echo off
echo ========================================
echo    Setup Digikala Management v2.0
echo ========================================
echo.

cd /d C:\Users\Ali\Desktop\orderV5

echo [1/8] Creating folder structure...
mkdir backend\database 2>nul
mkdir backend\routers 2>nul
mkdir backend\utils 2>nul
mkdir frontend\app 2>nul
mkdir frontend\components 2>nul
mkdir frontend\lib 2>nul
mkdir data 2>nul
mkdir sessions 2>nul
mkdir logs 2>nul
mkdir scripts 2>nul
echo Done!

echo.
echo [2/8] Copying existing files...
if exist utils\ (
    xcopy utils backend\utils /E /I /Y >nul
    echo Utils copied!
) else (
    echo WARNING: utils folder not found!
)

if exist orders_database_complete.csv (
    copy orders_database_complete.csv data\ >nul
    echo Database CSV copied!
)

if exist sender_profiles.json (
    copy sender_profiles.json data\ >nul
    echo Sender profiles copied!
)

echo.
echo [3/8] Creating requirements.txt...
cd backend
(
echo fastapi==0.109.0
echo uvicorn[standard]==0.27.0
echo sqlalchemy==2.0.25
echo pydantic==2.5.3
echo pandas==2.2.0
echo python-multipart==0.0.6
echo openpyxl==3.1.2
echo pdfplumber==0.10.3
echo requests==2.31.0
echo python-dotenv==1.0.0
echo selenium==4.16.0
echo beautifulsoup4==4.12.3
echo jdatetime==5.0.0
echo arabic-reshaper==3.0.0
echo python-bidi==0.4.2
echo qrcode==7.4.2
echo pillow==10.2.0
echo reportlab==4.0.9
echo treepoem==3.23.0
) > requirements.txt
cd ..
echo Done!

echo.
echo [4/8] Creating .env file...
(
echo GMAIL_USERNAME=your_email@gmail.com
echo GMAIL_PASSWORD=your_app_password
echo DEVICE_ID=your_device_id
echo DK_KEEP_BROWSER_ON_ERROR=0
echo DATABASE_URL=sqlite:///data/digikala_sales.db
echo COMPANY_NAME=تجارت دریای آرام
) > .env
echo Done!

echo.
echo [5/8] Installing Python packages...
cd backend
pip install -r requirements.txt
cd ..
echo Done!

echo.
echo ========================================
echo    Setup Complete!
echo ========================================
echo.
echo Next Steps:
echo 1. Create Python files manually (see instructions)
echo 2. Edit .env file with your credentials
echo 3. Run: python scripts\migrate_csv_to_sqlite.py
echo 4. Run: cd backend ^&^& uvicorn main:app --reload
echo.
pause