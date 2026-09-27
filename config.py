import os

BASE_DIR = os.path.abspath(os.path.dirname(__file__))

class Config:
    BASE_DIR = BASE_DIR
    SECRET_KEY = os.environ.get('SECRET_KEY', 'coffee-and-love-secret-key-2026')
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL', f'sqlite:///{os.path.join(BASE_DIR, "coffee_and_love.db")}')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Upload & asset paths
    UPLOAD_FOLDER = os.path.join(BASE_DIR, 'static', 'images', 'menu')
    QR_FOLDER = os.path.join(BASE_DIR, 'static', 'qrcodes')
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16 MB max upload
    
    # Business settings
    TAX_RATE = 0.05  # 5% GST
    CAFE_NAME = "COFFEE & LOVE"
    CAFE_TAGLINE = "Brewed with Passion, Served with Warmth"
    CURRENCY_SYMBOL = "₹"
