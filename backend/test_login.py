# test_login.py - تست مستقیم API
import requests

url = "http://localhost:8000/api/auth/login"

# داده‌های فرم (form-data)
data = {
    "username": "admin",
    "password": "admin123"
}

try:
    print("🔄 ارسال درخواست به:", url)
    response = requests.post(url, data=data, timeout=10)
    
    print(f"📡 Status Code: {response.status_code}")
    print(f"📄 Response:")
    print(response.json())
    
    if response.status_code == 200:
        print("\n✅ لاگین موفق!")
        token = response.json().get("access_token")
        print(f"🔑 Token: {token[:50]}...")
    else:
        print("\n❌ لاگین ناموفق!")
        
except requests.exceptions.ConnectionError:
    print("❌ خطا: Backend در حال اجرا نیست!")
    print("   لطفاً backend را با 'python main.py' اجرا کنید")
except Exception as e:
    print(f"❌ خطا: {e}")