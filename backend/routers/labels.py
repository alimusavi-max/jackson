# backend/utils/label_core.py
import io
import os
import qrcode
import textwrap
from PIL import Image, ImageDraw, ImageFont
from bidi.algorithm import get_display
import arabic_reshaper
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader
from reportlab.lib.pagesizes import A5
import treepoem

# مسیر فونت را به درستی پیدا کن
def get_font_path():
    """پیدا کردن مسیر فونت Vazir"""
    # جستجو در چند مسیر احتمالی
    possible_paths = [
        "Vazir.ttf",  # روت پروژه
        "../Vazir.ttf",  # یک سطح بالاتر
        "../../Vazir.ttf",  # دو سطح بالاتر
        os.path.join(os.path.dirname(__file__), "..", "..", "Vazir.ttf"),  # مسیر نسبی
    ]
    
    for path in possible_paths:
        abs_path = os.path.abspath(path)
        if os.path.exists(abs_path):
            print(f"✅ فونت پیدا شد: {abs_path}")
            return abs_path
    
    print("⚠️ فونت Vazir.ttf پیدا نشد، از فونت پیش‌فرض استفاده می‌شود")
    return None


def process_persian(text):
    """آماده‌سازی متن فارسی برای نمایش صحیح"""
    if not text:
        return ""
    try:
        reshaped_text = arabic_reshaper.reshape(str(text))
        bidi_text = get_display(reshaped_text)
        return bidi_text
    except Exception as e:
        print(f"خطا در پردازش متن فارسی: {e}")
        return str(text)


def load_fonts():
    """بارگذاری فونت‌ها با اندازه‌های مختلف"""
    font_path = get_font_path()
    
    try:
        if font_path:
            return {
                'regular': ImageFont.truetype(font_path, 16),
                'small': ImageFont.truetype(font_path, 14),
                'large': ImageFont.truetype(font_path, 32),
                'warning': ImageFont.truetype(font_path, 18),
            }
    except Exception as e:
        print(f"خطا در بارگذاری فونت: {e}")
    
    # اگر فونت لود نشد، از فونت پیش‌فرض استفاده کن
    default = ImageFont.load_default()
    return {
        'regular': default,
        'small': default,
        'large': default,
        'warning': default,
    }


def generate_label_portrait(order_id, sender_info, receiver_info, include_datamatrix=True):
    """تولید برچسب پستی عمودی A5 با پشتیبانی کامل فارسی"""
    
    # ایجاد تصویر پایه
    label = Image.new('RGB', (600, 400), color='white')
    draw = ImageDraw.Draw(label)
    
    # بارگذاری فونت‌ها
    fonts = load_fonts()
    
    text_color = (0, 0, 0)
    line_height = 20

    # ========== بخش بارکدها (سمت چپ) ==========
    try:
        # QR Code
        qr = qrcode.QRCode(version=1, box_size=10, border=2)
        qr.add_data(str(order_id))
        qr.make(fit=True)
        qr_img = qr.make_image(fill_color="black", back_color="white")
        qr_img = qr_img.resize((100, 100))
        label.paste(qr_img, (20, 20))
        
        # کد سفارش زیر QR
        draw.text((70, 125), str(order_id), font=fonts['regular'], fill=text_color, anchor='mt')
    except Exception as e:
        print(f"خطا در تولید QR Code: {e}")

    # Data Matrix Barcode
    if include_datamatrix:
        try:
            dm_string = (
                f"{receiver_info.get('city', receiver_info.get('شهر', ''))}\t"
                f"{receiver_info.get('نام مشتری', '')} {order_id}\t\t"
                f"{receiver_info.get('postalCode', receiver_info.get('کد پستی', ''))}\t\t"
                f"{receiver_info.get('phoneNumber', receiver_info.get('شماره تلفن', ''))}\t"
                f"{receiver_info.get('address', receiver_info.get('آدرس کامل', ''))}\t"
                f"{receiver_info.get('city', receiver_info.get('شهر', ''))}\t\r"
            )
            
            dm_image = treepoem.generate_barcode(
                barcode_type='datamatrix',
                data=dm_string
            )
            dm_image_resized = dm_image.convert('RGB').resize((100, 100))
            label.paste(dm_image_resized, (20, 150))
        except Exception as e:
            print(f"خطا در تولید Data Matrix: {e}")
            draw.rectangle([20, 150, 120, 250], fill='lightgray')

    # ========== بخش اطلاعات فرستنده و گیرنده (سمت راست) ==========
    y_pos = 10
    
    # فرستنده
    draw.text((580, y_pos), process_persian("فرستنده:"), 
              font=fonts['regular'], fill=text_color, anchor='ra')
    y_pos += line_height
    
    draw.text((580, y_pos), process_persian(f"نام: {sender_info.get('name', '')}"), 
              font=fonts['regular'], fill=text_color, anchor='ra')
    y_pos += line_height
    
    # آدرس فرستنده (چندخطی)
    sender_address = f"آدرس: {sender_info.get('address', '')}"
    for line in textwrap.wrap(sender_address, width=40):
        draw.text((580, y_pos), process_persian(line), 
                  font=fonts['small'], fill=text_color, anchor='ra')
        y_pos += line_height - 2
    
    draw.text((580, y_pos), process_persian(f"کد پستی: {sender_info.get('postal_code', '')}"), 
              font=fonts['regular'], fill=text_color, anchor='ra')
    y_pos += line_height
    
    draw.text((580, y_pos), process_persian(f"تلفن: {sender_info.get('phone', '')}"), 
              font=fonts['regular'], fill=text_color, anchor='ra')
    y_pos += line_height * 1.5

    # گیرنده
    draw.text((580, y_pos), process_persian("گیرنده:"), 
              font=fonts['regular'], fill=text_color, anchor='ra')
    y_pos += line_height
    
    customer_name = receiver_info.get('نام مشتری', receiver_info.get('customer_name', 'نامشخص'))
    draw.text((580, y_pos), process_persian(f"نام: {customer_name}"), 
              font=fonts['regular'], fill=text_color, anchor='ra')
    y_pos += line_height
    
    # آدرس گیرنده (چندخطی)
    receiver_address = receiver_info.get('address', receiver_info.get('آدرس کامل', 'نامشخص'))
    for line in textwrap.wrap(f"آدرس: {receiver_address}", width=40):
        draw.text((580, y_pos), process_persian(line), 
                  font=fonts['small'], fill=text_color, anchor='ra')
        y_pos += line_height - 2
    
    # شهر و استان
    province = receiver_info.get('state', receiver_info.get('استان', ''))
    city = receiver_info.get('city', receiver_info.get('شهر', ''))
    postal = receiver_info.get('postalCode', receiver_info.get('کد پستی', ''))
    
    location_text = f"استان: {province} - شهر: {city} - کد پستی: {postal}"
    draw.text((580, y_pos), process_persian(location_text), 
              font=fonts['small'], fill=text_color, anchor='ra')
    y_pos += line_height
    
    phone = receiver_info.get('phoneNumber', receiver_info.get('شماره تلفن', 'نامشخص'))
    draw.text((580, y_pos), process_persian(f"تلفن: {phone}"), 
              font=fonts['regular'], fill=text_color, anchor='ra')

    # ========== بخش محصولات (پایین صفحه) ==========
    products = receiver_info.get('products', [])
    
    if products:
        y_pos = 390  # شروع از پایین
        
        # خط جداکننده
        separator_y = y_pos - (len(products) * 60)
        draw.line([(140, separator_y), (580, separator_y)], fill='black', width=2)
        
        # رسم هر محصول از پایین به بالا
        for item in reversed(products):
            item_name = item.get('name', item.get('product_title', 'نامشخص'))
            item_qty = int(item.get('qty', item.get('quantity', 1)))
            
            # محاسبه ارتفاع مورد نیاز
            wrapped_lines = textwrap.wrap(item_name, width=35)
            name_height = len(wrapped_lines) * 18
            item_height = max(55, name_height + 10)
            
            y_pos -= item_height
            
            # دایره تعداد
            circle_x, circle_y = 530, y_pos
            draw.ellipse(
                [(circle_x, circle_y), (circle_x + 50, circle_y + 50)],
                outline='black',
                width=3
            )
            draw.text(
                (circle_x + 25, circle_y + 25),
                str(item_qty),
                font=fonts['large'],
                fill=text_color,
                anchor='mm'
            )
            
            # نام محصول (چندخطی)
            name_y = y_pos + (item_height - name_height) / 2
            for line in wrapped_lines:
                draw.text(
                    (510, name_y),
                    process_persian(line),
                    font=fonts['small'],
                    fill=text_color,
                    anchor='ra'
                )
                name_y += 18
            
            y_pos -= 5  # فاصله بین اقلام

    # ========== هشدار چندقلمی ==========
    if len(products) > 1:
        draw.rectangle([(230, 5), (470, 35)], fill='#FFD700', outline='#FF8C00', width=2)
        draw.text(
            (350, 20),
            process_persian("⚠️ توجه: سفارش چندقلمی"),
            font=fonts['warning'],
            fill='#8B0000',
            anchor='mm'
        )

    return label


def generate_label_landscape(order_id, sender_info, receiver_info):
    """تولید برچسب افقی (ساده‌تر)"""
    label = Image.new('RGB', (400, 600), color='white')
    draw = ImageDraw.Draw(label)
    
    fonts = load_fonts()
    
    # QR Code
    try:
        qr = qrcode.make(str(order_id)).resize((100, 100))
        label.paste(qr, (20, 20))
    except:
        pass
    
    # متن ساده
    y = 140
    draw.text((200, y), process_persian(f"سفارش: {order_id}"), 
              font=fonts['regular'], fill='black', anchor='mm')
    
    y += 30
    customer = receiver_info.get('نام مشتری', 'نامشخص')
    draw.text((200, y), process_persian(f"مشتری: {customer}"), 
              font=fonts['regular'], fill='black', anchor='mm')
    
    # محصولات
    products = receiver_info.get('products', [])
    y += 40
    for item in products:
        name = item.get('name', 'نامشخص')
        qty = item.get('qty', 1)
        draw.text((200, y), process_persian(f"{name} - {qty} عدد"), 
                  font=fonts['small'], fill='black', anchor='mm')
        y += 25

    return label


def create_pdf_two_labels(label_images, output_path, page_size):
    """ایجاد PDF با دو برچسب در هر صفحه"""
    c = canvas.Canvas(output_path, pagesize=page_size)
    page_w, page_h = page_size
    half_h = page_h / 2
    
    for i in range(0, len(label_images), 2):
        # برچسب بالا
        if i < len(label_images):
            label_images[i].seek(0)  # بازگشت به ابتدای BytesIO
            c.drawImage(
                ImageReader(label_images[i]),
                0, half_h,
                width=page_w,
                height=half_h,
                preserveAspectRatio=True,
                anchor='c'
            )
        
        # برچسب پایین
        if i + 1 < len(label_images):
            label_images[i + 1].seek(0)
            c.drawImage(
                ImageReader(label_images[i + 1]),
                0, 0,
                width=page_w,
                height=half_h,
                preserveAspectRatio=True,
                anchor='c'
            )
        
        c.showPage()
    
    c.save()
    print(f"✅ PDF ذخیره شد: {output_path}")