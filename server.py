from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from pathlib import Path
import logging
import os

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

from database import Database
from config import settings
from auth.hash_utils import hash_password, verify_password

from api import auth, products, categories, cart, orders, reviews, favorites, admin, payments, chatbot, chat

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = FastAPI(title='WIBAZA API', version='1.0.0')

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.FRONTEND_URL] if settings.FRONTEND_URL != '*' else ['*'],
    allow_credentials=True,
    allow_methods=['*'],
    allow_headers=['*'],
)

app.include_router(auth.router)
app.include_router(products.router)
app.include_router(categories.router)
app.include_router(cart.router)
app.include_router(orders.router)
app.include_router(reviews.router)
app.include_router(favorites.router)
app.include_router(admin.router)
app.include_router(payments.router)
app.include_router(chatbot.router)
app.include_router(chat.router)

@app.on_event('startup')
async def startup_event():
    """Initialize database and seed admin"""
    await Database.connect_db()
    db = Database.get_db()
    
    await db.users.create_index('email', unique=True)
    await db.categories.create_index('slug', unique=True)
    await db.password_reset_tokens.create_index('expires_at', expireAfterSeconds=0)
    
    admin_email = settings.ADMIN_EMAIL
    admin_password = settings.ADMIN_PASSWORD
    
    existing_admin = await db.users.find_one({'email': admin_email})
    
    if not existing_admin:
        from datetime import datetime, timezone
        admin_user = {
            'email': admin_email,
            'password_hash': hash_password(admin_password),
            'name': 'Administrator',
            'role': 'admin',
            'is_approved': True,
            'is_active': True,
            'created_at': datetime.now(timezone.utc),
            'updated_at': datetime.now(timezone.utc),
            'deleted_at': None
        }
        await db.users.insert_one(admin_user)
        logger.info(f'Admin user created: {admin_email}')
    elif not verify_password(admin_password, existing_admin['password_hash']):
        await db.users.update_one(
            {'email': admin_email},
            {'$set': {'password_hash': hash_password(admin_password)}}
        )
        logger.info('Admin password updated')
 # Usando caminho relativo para a pasta do projeto
    memory_dir = Path('./memory')
    memory_dir.mkdir(parents=True, exist_ok=True)
    
    with open(memory_dir / 'test_credentials.md', 'w') as f:
        f.write(f"""# WIBAZA Test Credentials

        

## Admin Account
- **Email:** {admin_email}
- **Password:** {admin_password}
- **Role:** admin

## Endpoints
- **Auth:** /api/auth/login, /api/auth/register, /api/auth/me, /api/auth/logout
- **Products:** /api/products
- **Categories:** /api/categories
- **Cart:** /api/cart
- **Orders:** /api/orders
- **Payments:** /api/payments
- **Admin:** /api/admin
""")
    
    logger.info('WIBAZA API started successfully')

@app.on_event('shutdown')
async def shutdown_event():
    """Close database connection"""
    await Database.close_db()

@app.get('/api/')
async def root():
    return {
        'message': 'WIBAZA Marketplace API',
        'version': '1.0.0',
        'status': 'online'
    }

@app.get('/api/health')
async def health_check():
    return {'status': 'healthy'}
