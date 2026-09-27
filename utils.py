import os
import qrcode
from PIL import Image, ImageDraw, ImageFont
from flask import current_app

def generate_table_qr(table_number, base_url="http://localhost:5000"):
    """
    Generates a stylish QR code for a given table number.
    Points to: {base_url}/menu?table={table_number}
    """
    qr_dir = current_app.config['QR_FOLDER']
    os.makedirs(qr_dir, exist_ok=True)
    
    target_url = f"{base_url}/menu?table={table_number}"
    
    # Create QR Code with high error correction
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_H,
        box_size=10,
        border=2,
    )
    qr.add_data(target_url)
    qr.make(fit=True)
    
    # Theme colors: Dark charcoal (#1a1a2e) on warm cream (#fdfbf7)
    qr_img = qr.make_image(fill_color="#1a1a2e", back_color="#faf7f2").convert('RGBA')
    
    # Create a nice badge canvas
    canvas_w = qr_img.width + 40
    canvas_h = qr_img.height + 90
    canvas = Image.new('RGBA', (canvas_w, canvas_h), '#faf7f2')
    draw = ImageDraw.Draw(canvas)
    
    # Draw border with gold accent
    draw.rectangle([2, 2, canvas_w - 3, canvas_h - 3], outline="#d4a574", width=3)
    
    # Paste QR code
    canvas.paste(qr_img, (20, 20), qr_img)
    
    # Draw header / table text
    header_text = f"TABLE {table_number}"
    sub_text = "SCAN TO ORDER"
    
    # Use default bitmap font or fallback
    try:
        font_large = ImageFont.load_default(size=18)
        font_small = ImageFont.load_default(size=12)
    except TypeError:
        # Older Pillow fallback
        font_large = ImageFont.load_default()
        font_small = ImageFont.load_default()
        
    bbox_large = draw.textbbox((0, 0), header_text, font=font_large)
    w_large = bbox_large[2] - bbox_large[0]
    draw.text(((canvas_w - w_large) / 2, qr_img.height + 28), header_text, fill="#1a1a2e", font=font_large)
    
    bbox_small = draw.textbbox((0, 0), sub_text, font=font_small)
    w_small = bbox_small[2] - bbox_small[0]
    draw.text(((canvas_w - w_small) / 2, qr_img.height + 56), sub_text, fill="#d4a574", font=font_small)
    
    file_name = f"table_{table_number}.png"
    file_path = os.path.join(qr_dir, file_name)
    canvas.save(file_path, "PNG")
    
    # Return web-accessible path
    return f"/static/qrcodes/{file_name}"
