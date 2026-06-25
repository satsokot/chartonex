import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key-change-me')
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL', 'sqlite:///tether_bot.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    TELEGRAM_API_ID = int(os.getenv('TELEGRAM_API_ID', 0))
    TELEGRAM_API_HASH = os.getenv('TELEGRAM_API_HASH', '')
    TELEGRAM_PHONE = os.getenv('TELEGRAM_PHONE', '')
    BOT_TOKEN = os.getenv('BOT_TOKEN', '')

    ADMIN_USERNAME = os.getenv('ADMIN_USERNAME', 'admin')
    ADMIN_PASSWORD = os.getenv('ADMIN_PASSWORD', 'admin123')
