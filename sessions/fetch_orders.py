import requests

# کوکی‌ها رو از فایل بخون
with open('digikala_cookies.json', 'r') as file:
    cookie_str = file.read().strip()

url = 'https://api.example.com/orders'

headers = {
    'Content-Type': 'application/json'
}

# ارسال کوکی برای احراز هویت
response = requests.get(url, headers=headers, cookies={c.split('=')[0]: c.split('=')[1] for c in cookie_str.split('; ')})

if response.status_code == 200:
    orders = response.json()
    print('لیست سفارش‌ها:')
    for order in orders:
        print(order)
else:
    print('خطا در دریافت سفارش‌ها:', response.status_code, response.text)
