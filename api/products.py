from fastapi import APIRouter, Depends, HTTPException, Query
from bson import ObjectId
from typing import List, Optional
from models.product import ProductCreate, ProductUpdate
from auth.dependencies import get_current_user, require_role
from database import get_database
from datetime import datetime, timezone
import logging

logger = logging.getLogger(__name__)
router = APIRouter(prefix='/api/products', tags=['products'])

@router.post('')
async def create_product(
    product_data: ProductCreate,
    current_user: dict = Depends(get_current_user),
    db=Depends(get_database)
):
    """Create product (Seller or Admin)"""
    if current_user['role'] not in ['seller', 'admin']:
        raise HTTPException(status_code=403, detail='Only sellers and admins can create products')
    
    product = product_data.model_dump()
    product['seller_id'] = current_user['id']
    product['approval_status'] = 'approved' if current_user['role'] == 'admin' else 'pending'
    product['is_active'] = True
    product['videos'] = product.get('videos', [])
    product['variations'] = product.get('variations', [])
    product['average_rating'] = 0.0
    product['total_reviews'] = 0
    product['created_at'] = datetime.now(timezone.utc)
    product['updated_at'] = datetime.now(timezone.utc)
    product['deleted_at'] = None
    
    result = await db.products.insert_one(product)
    product['id'] = str(result.inserted_id)
    product.pop('_id', None)
    
    return product

@router.get('')
async def get_products(
    category_id: Optional[str] = None,
    seller_id: Optional[str] = None,
    search: Optional[str] = None,
    min_price: Optional[float] = None,
    max_price: Optional[float] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db=Depends(get_database)
):
    """Get products with filters"""
    query = {'deleted_at': None, 'is_active': True, 'approval_status': 'approved'}
    
    if category_id:
        query['category_id'] = category_id
    
    if seller_id:
        query['seller_id'] = seller_id
    
    if search:
        query['$or'] = [
            {'name': {'$regex': search, '$options': 'i'}},
            {'description': {'$regex': search, '$options': 'i'}},
            {'tags': {'$in': [search]}}
        ]
    
    if min_price is not None or max_price is not None:
        price_query = {}
        if min_price is not None:
            price_query['$gte'] = min_price
        if max_price is not None:
            price_query['$lte'] = max_price
        query['price'] = price_query
    
    total = await db.products.count_documents(query)
    products = await db.products.find(query).skip(skip).limit(limit).to_list(length=limit)
    
    for product in products:
        if '_id' in product:
            product['id'] = str(product.pop('_id'))
    
    return {'products': products, 'total': total, 'skip': skip, 'limit': limit}

@router.get('/{product_id}')
async def get_product(product_id: str, db=Depends(get_database)):
    """Get single product"""
    product = await db.products.find_one({'_id': ObjectId(product_id), 'deleted_at': None}, {'_id': 0})
    
    if not product:
        raise HTTPException(status_code=404, detail='Product not found')
    
    product['id'] = product_id
    return product

@router.put('/{product_id}')
async def update_product(
    product_id: str,
    product_data: ProductUpdate,
    current_user: dict = Depends(get_current_user),
    db=Depends(get_database)
):
    """Update product (Owner or Admin)"""
    product = await db.products.find_one({'_id': ObjectId(product_id), 'deleted_at': None})
    
    if not product:
        raise HTTPException(status_code=404, detail='Product not found')
    
    if current_user['role'] != 'admin' and str(product['seller_id']) != current_user['id']:
        raise HTTPException(status_code=403, detail='Not authorized to update this product')
    
    update_data = {k: v for k, v in product_data.model_dump().items() if v is not None}
    update_data['updated_at'] = datetime.now(timezone.utc)
    
    await db.products.update_one({'_id': ObjectId(product_id)}, {'$set': update_data})
    
    updated_product = await db.products.find_one({'_id': ObjectId(product_id)}, {'_id': 0})
    updated_product['id'] = product_id
    
    return updated_product

@router.delete('/{product_id}')
async def delete_product(
    product_id: str,
    current_user: dict = Depends(get_current_user),
    db=Depends(get_database)
):
    """Soft delete product (Owner or Admin)"""
    product = await db.products.find_one({'_id': ObjectId(product_id), 'deleted_at': None})
    
    if not product:
        raise HTTPException(status_code=404, detail='Product not found')
    
    if current_user['role'] != 'admin' and str(product['seller_id']) != current_user['id']:
        raise HTTPException(status_code=403, detail='Not authorized to delete this product')
    
    await db.products.update_one(
        {'_id': ObjectId(product_id)},
        {'$set': {'deleted_at': datetime.now(timezone.utc)}}
    )
    
    return {'message': 'Product deleted successfully'}

@router.post('/{product_id}/approve')
async def approve_product(
    product_id: str,
    approved: bool,
    current_user: dict = Depends(require_role('admin')),
    db=Depends(get_database)
):
    """Approve or reject product (Admin only)"""
    product = await db.products.find_one({'_id': ObjectId(product_id), 'deleted_at': None})
    
    if not product:
        raise HTTPException(status_code=404, detail='Product not found')
    
    status = 'approved' if approved else 'rejected'
    
    await db.products.update_one(
        {'_id': ObjectId(product_id)},
        {'$set': {'approval_status': status, 'updated_at': datetime.now(timezone.utc)}}
    )
    
    return {'message': f'Product {status}'}
