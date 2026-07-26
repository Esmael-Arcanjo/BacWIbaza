from fastapi import APIRouter, Depends, HTTPException
from bson import ObjectId
from auth.dependencies import require_role
from database import get_database
from services.email_service import EmailService
from datetime import datetime, timezone
import logging

logger = logging.getLogger(__name__)
router = APIRouter(prefix='/api/admin', tags=['admin'])

@router.get('/users')
async def get_users(
    current_user: dict = Depends(require_role('admin')),
    db=Depends(get_database)
):
    """Get all users (Admin only)"""
    users = await db.users.find({'deleted_at': None}, {'password_hash': 0}).to_list(length=1000)
    
    for user in users:
        if '_id' in user:
            user['id'] = str(user.pop('_id'))
    
    return users

@router.post('/sellers/{user_id}/approve')
async def approve_seller(
    user_id: str,
    approved: bool,
    current_user: dict = Depends(require_role('admin')),
    db=Depends(get_database)
):
    """Approve or reject seller (Admin only)"""
    user = await db.users.find_one({'_id': ObjectId(user_id), 'role': 'seller', 'deleted_at': None})
    
    if not user:
        raise HTTPException(status_code=404, detail='Seller not found')
    
    await db.users.update_one(
        {'_id': ObjectId(user_id)},
        {'$set': {'is_approved': approved, 'updated_at': datetime.now(timezone.utc)}}
    )
    
    try:
        await EmailService.send_seller_approval_email(user['email'], user['name'], approved)
    except Exception as e:
        logger.error(f'Failed to send approval email: {str(e)}')
    
    return {'message': f'Seller {"approved" if approved else "rejected"}'}

@router.get('/products/pending')
async def get_pending_products(
    current_user: dict = Depends(require_role('admin')),
    db=Depends(get_database)
):
    """Get products pending approval (Admin only)"""
    products = await db.products.find(
        {'approval_status': 'pending', 'deleted_at': None}
    ).to_list(length=1000)
    
    for product in products:
        if '_id' in product:
            product['id'] = str(product.pop('_id'))
    
    return products

@router.get('/stats')
async def get_stats(
    current_user: dict = Depends(require_role('admin')),
    db=Depends(get_database)
):
    """Get dashboard statistics (Admin only)"""
    total_users = await db.users.count_documents({'deleted_at': None})
    total_sellers = await db.users.count_documents({'role': 'seller', 'deleted_at': None})
    total_products = await db.products.count_documents({'deleted_at': None})
    total_orders = await db.orders.count_documents({'deleted_at': None})
    pending_products = await db.products.count_documents({'approval_status': 'pending', 'deleted_at': None})
    pending_sellers = await db.users.count_documents({'role': 'seller', 'is_approved': False, 'deleted_at': None})
    
    orders = await db.orders.find({'payment_status': 'paid', 'deleted_at': None}).to_list(length=10000)
    total_revenue = sum(order.get('total', 0) for order in orders)
    
    return {
        'total_users': total_users,
        'total_sellers': total_sellers,
        'total_products': total_products,
        'total_orders': total_orders,
        'pending_products': pending_products,
        'pending_sellers': pending_sellers,
        'total_revenue': total_revenue
    }
