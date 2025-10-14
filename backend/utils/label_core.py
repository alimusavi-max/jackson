# utils/label_core.py

import io
import qrcode
import textwrap
from PIL import Image, ImageDraw, ImageFont
from bidi.algorithm import get_display
import arabic_reshaper
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader
import treepoem

def process_persian(text):
    """Reshapes and prepares Persian text for PIL."""
    return get_display(arabic_reshaper.reshape(str(text)))

def generate_label_portrait(order_id, sender_info, receiver_info, include_datamatrix=True):
    """Generates an A5 portrait shipping label with improved product details."""
    label = Image.new('RGB', (600, 400), color='white')
    draw = ImageDraw.Draw(label)
    try:
        font_path = "Vazir.ttf"  # Ensure this font is in the root or utils directory
        font = ImageFont.truetype(font_path, 16)
        small_font = ImageFont.truetype(font_path, 14)
        qty_font = ImageFont.truetype(font_path, 32)
        warning_font = ImageFont.truetype(font_path, 18)
    except IOError:
        font = ImageFont.load_default()
        small_font = ImageFont.load_default()
        qty_font = ImageFont.load_default()
        warning_font = ImageFont.load_default()

    text_color = (0, 0, 0)
    line_height = 20

    # Barcodes section
    qr = qrcode.make(str(order_id)).resize((100, 100))
    label.paste(qr, (20, 20))
    draw.text((70, 122), str(order_id), font=font, fill=text_color, anchor='mt')
    if include_datamatrix:
        datamatrix_string = (
            f"{receiver_info.get('city', '')}\t"
            f"{receiver_info.get('نام مشتری', '')} {order_id}\t\t"
            f"{receiver_info.get('postalCode', '') or receiver_info.get('کد پستی', '')}\t\t"
            f"{receiver_info.get('phoneNumber', '') or receiver_info.get('شماره تلفن', '')}\t"
            f"{receiver_info.get('address', '') or receiver_info.get('آدرس کامل', '')}\t"
            f"{receiver_info.get('city', '')}\t\r"
        )
        try:
            dm_image = treepoem.generate_barcode(barcode_type='datamatrix', data=datamatrix_string)
            dm_image_resized = dm_image.resize((100, 100))
            label.paste(dm_image_resized, (20, 140))
        except Exception as e:
            print(f"Error generating Data Matrix barcode for {order_id}: {e}")
            draw.rectangle([20, 140, 120, 240], fill='lightgray')

    # Sender and Receiver Info
    y_pos = 10
    draw.text((580, y_pos), process_persian("فرستنده:"), font=font, fill=text_color, anchor='ra')
    y_pos += line_height
    draw.text((580, y_pos), process_persian(f"نام: {sender_info.get('name', '')}"), font=font, fill=text_color, anchor='ra')
    y_pos += line_height
    for line in textwrap.wrap(f"آدرس: {sender_info.get('address', '')}", width=45):
        draw.text((580, y_pos), process_persian(line), font=font, fill=text_color, anchor='ra')
        y_pos += line_height
    draw.text((580, y_pos), process_persian(f"کد پستی: {sender_info.get('postal_code', '')}"), font=font, fill=text_color, anchor='ra')
    y_pos += line_height
    draw.text((580, y_pos), process_persian(f"تلفن: {sender_info.get('phone', '')}"), font=font, fill=text_color, anchor='ra')

    y_pos += line_height * 1.5
    draw.text((580, y_pos), process_persian("گیرنده:"), font=font, fill=text_color, anchor='ra')
    y_pos += line_height
    draw.text((580, y_pos), process_persian(f"نام: {receiver_info.get('نام مشتری', 'نامشخص')}"), font=font, fill=text_color, anchor='ra')
    y_pos += line_height
    for line in textwrap.wrap(f"آدرس: {receiver_info.get('address', '') or receiver_info.get('آدرس کامل', 'نامشخص')}", width=45):
        draw.text((580, y_pos), process_persian(line), font=font, fill=text_color, anchor='ra')
        y_pos += line_height
    
    address_parts = [
        f"استان: {receiver_info.get('state', '') or receiver_info.get('استان', '')}",
        f"شهر: {receiver_info.get('city', '') or receiver_info.get('شهر', '')}",
        f"کد پستی: {receiver_info.get('postalCode', '') or receiver_info.get('کد پستی', '')}"
    ]
    draw.text((580, y_pos), process_persian(" - ".join(p for p in address_parts if p.split(': ')[1])), font=font, fill=text_color, anchor='ra')
    y_pos += line_height
    draw.text((580, y_pos), process_persian(f"تلفن: {receiver_info.get('phoneNumber', '') or receiver_info.get('شماره تلفن', 'نامشخص')}"), font=font, fill=text_color, anchor='ra')

    # Improved Product Details Section
    products = receiver_info.get('products', [])
    y_pos = 390  # Start drawing products from the bottom up

    # Draw separator line
    draw.line([(140, y_pos - (len(products) * 65)), (580, y_pos - (len(products) * 65))], fill='black', width=1)

    for item in reversed(products):
        item_name = item.get('name', 'نامشخص')
        item_qty = int(item.get('qty', 1))

        wrapped_lines = textwrap.wrap(item_name, width=35)
        name_height = len(wrapped_lines) * (line_height - 4)
        item_height = max(55, name_height)
        
        y_pos -= item_height
        
        # Quantity circle
        draw.ellipse([(530, y_pos), (580, y_pos + 50)], outline='black', width=2)
        draw.text((555, y_pos + 25), str(item_qty), font=qty_font, fill=text_color, anchor='mm')

        # Product name
        name_y = y_pos + (item_height - name_height) / 2
        for line in wrapped_lines:
            draw.text((510, name_y), process_persian(line), font=small_font, fill=text_color, anchor='ra')
            name_y += (line_height - 4)
        
        y_pos -= 10 # Spacing between items

    # Multi-item warning
    if len(products) > 1:
        draw.rectangle([(250, 5), (450, 35)], fill='#FFD700')
        draw.text((350, 20), process_persian("⚠️ توجه: چندقلمی"), font=warning_font, fill='black', anchor='mm')
        
    return label

def generate_label_landscape(order_id, sender_info, receiver_info):
    # This function is kept simple as per original code but now accepts `receiver_info` correctly.
    # You can apply the same detailed product drawing logic from portrait if needed.
    label = Image.new('RGB', (400, 600), color='white') # Note: Swapped dimensions for landscape
    draw = ImageDraw.Draw(label)
    try:
        font_path = "Vazir.ttf"
        font = ImageFont.truetype(font_path, 16)
        small_font = ImageFont.truetype(font_path, 14)
    except IOError:
        font = ImageFont.load_default()
        small_font = ImageFont.load_default()

    # Drawing logic for landscape can be added here, similar to portrait version.
    # For now, it will just show a basic message.
    draw.text((200, 300), process_persian(f"سفارش: {order_id}"), font=font, fill='black', anchor='mm')
    products = receiver_info.get('products', [])
    y_pos = 320
    for item in products:
        draw.text((200, y_pos), process_persian(f"{item.get('name')} - {item.get('qty')} عدد"), font=small_font, fill='black', anchor='mm')
        y_pos += 20
        
    return label

def create_pdf_two_labels(label_images, output_path, page_size):
    """Creates a PDF with two labels per page."""
    c = canvas.Canvas(output_path, pagesize=page_size)
    page_w, page_h = page_size
    half_h = page_h / 2
    for i in range(0, len(label_images), 2):
        if i < len(label_images):
            c.drawImage(ImageReader(label_images[i]), 0, half_h, width=page_w, height=half_h, preserveAspectRatio=True, anchor='c')
        if i + 1 < len(label_images):
            c.drawImage(ImageReader(label_images[i + 1]), 0, 0, width=page_w, height=half_h, preserveAspectRatio=True, anchor='c')
        c.showPage()
    c.save()