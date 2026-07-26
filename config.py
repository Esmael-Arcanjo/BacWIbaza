import os
from dotenv import load_dotenv
from pathlib import Path

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

class Settings:
    # MongoDB
    MONGO_URL: str = os.environ.get('MONGO_URL', 'mongodb://localhost:27017')
    DB_NAME: str = os.environ.get('DB_NAME', 'wibaza_marketplace')
    
    # JWT
    JWT_SECRET: str = os.environ.get('JWT_SECRET', '')
    JWT_ALGORITHM: str = 'HS256'
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    
    # Admin
    ADMIN_EMAIL: str = os.environ.get('ADMIN_EMAIL', 'admin@wibaza.com')
    ADMIN_PASSWORD: str = os.environ.get('ADMIN_PASSWORD', 'admin123')
    
    # CORS
    CORS_ORIGINS: list = os.environ.get('CORS_ORIGINS', '*').split(',')
    FRONTEND_URL: str = os.environ.get('FRONTEND_URL', 'http://localhost:3000')
    
    # Stripe
    STRIPE_SECRET_KEY: str = os.environ.get('STRIPE_SECRET_KEY', 'sk_test_emergent')
    STRIPE_PUBLISHABLE_KEY: str = os.environ.get('STRIPE_PUBLISHABLE_KEY', '')
    STRIPE_WEBHOOK_SECRET: str = os.environ.get('STRIPE_WEBHOOK_SECRET', '')
    STRIPE_MODE: str = os.environ.get('STRIPE_MODE', 'test')
    
    # Resend
    RESEND_API_KEY: str = os.environ.get('RESEND_API_KEY', '')
    SENDER_EMAIL: str = os.environ.get('SENDER_EMAIL', 'noreply@wibaza.com')
    
    # OpenAI
    OPENAI_API_KEY: str = os.environ.get('OPENAI_API_KEY', '')
    
    # Integration Proxy
    INTEGRATION_PROXY_URL: str = os.environ.get('INTEGRATION_PROXY_URL', '')

settings = Settings()
