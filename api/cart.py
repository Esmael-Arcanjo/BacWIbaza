from fastapi import APIRouter, Depends, HTTPException
from bson import ObjectId
from models.cart import CartAddItem, CartUpdateItem
from auth.dependencies import get_current_user
from database import get_database
from datetime import datetime, timezone

router = APIRouter(prefix='/api/cart', tags=['cart'])

@router.get('')
async def get_cart(current_user: dict = Depends(get_current_user), db=Depends(get_database)):
    """Get current user's cart"""
    cart = await db.carts.find_one({'user_id': current_user['id'], 'deleted_at': None}, {'_id': 0})
    
    if not cart:
        cart = {
            'user_id': current_user['id'],
            'items': [],
            'created_at': datetime.now(timezone.utc),
            'updated_at': datetime.now(timezone.utc)
        }
        await db.carts.insert_one(cart)
        cart.pop('_id', None)
    
    enriched_items = []
    for item in cart.get('items', []):
        product = await db.products.find_one(
            {'_id': ObjectId(item['product_id']), 'deleted_at': None},
            {'_id': 0, 'name': 1, 'price': 1, 'promotional_price': 1, 'images': 1, 'stock': 1}
        )
        if product:
            enriched_items.append({
                **item,
                'product': product
            })
    
    cart['items'] = enriched_items
    return cart

@router.post('/items')
async def add_to_cart(
    item: CartAddItem,
    current_user: dict = Depends(get_current_user),
    db=Depends(get_database)
):
    """Add item to cart"""
    product = await db.products.find_one({'_id': ObjectId(item.product_id), 'deleted_at': None})
    
    if not product:
        raise HTTPException(status_code=404, detail='Product not found')
    
    if product.get('stock', 0) < item.quantity:
        raise HTTPException(status_code=400, detail='Insufficient stock')
    
    cart = await db.carts.find_one({'user_id': current_user['id'], 'deleted_at': None})
    
    if not cart:
        cart = {
            'user_id': current_user['id'],
            'items': [],
            'created_at': datetime.now(timezone.utc),
            'updated_at': datetime.now(timezone.utc),
            'deleted_at': None
        }
        await db.carts.insert_one(cart)
    
    items = cart.get('items', [])
    existing_item = next((i for i in items if i['product_id'] == item.product_id), None)
    
    if existing_item:
        existing_item['quantity'] += item.quantity
    else:
        items.append(item.model_dump())
    
    await db.carts.update_one(
        {'user_id': current_user['id']},
        {'$set': {'items': items, 'updated_at': datetime.now(timezone.utc)}}
    )
    
    return {'message': 'Item added to cart'}

@router.put('/items')
async def update_cart_item(
    item: CartUpdateItem,
    current_user: dict = Depends(get_current_user),
    db=Depends(get_database)
):
    """Update cart item quantity"""
    cart = await db.carts.find_one({'user_id': current_user['id'], 'deleted_at': None})
    
    if not cart:
        raise HTTPException(status_code=404, detail='Cart not found')
    
    items = cart.get('items', [])
    cart_item = next((i for i in items if i['product_id'] == item.product_id), None)
    
    if not cart_item:
        raise HTTPException(status_code=404, detail='Item not in cart')
    
    if item.quantity <= 0:
        items = [i for i in items if i['product_id'] != item.product_id]
    else:
        cart_item['quantity'] = item.quantity
    
    await db.carts.update_one(
        {'user_id': current_user['id']},
        {'$set': {'items': items, 'updated_at': datetime.now(timezone.utc)}}
    )
    
    return {'message': 'Cart updated'}

@router.delete('/items/{product_id}')
async def remove_from_cart(
    product_id: str,
    current_user: dict = Depends(get_current_user),
    db=Depends(get_database)
):
    """Remove item from cart"""
    cart = await db.carts.find_one({'user_id': current_user['id'], 'deleted_at': None})
    
    if not cart:
        raise HTTPException(status_code=404, detail='Cart not found')
    
    items = [i for i in cart.get('items', []) if i['product_id'] != product_id]
    
    await db.carts.update_one(
        {'user_id': current_user['id']},
        {'$set': {'items': items, 'updated_at': datetime.now(timezone.utc)}}
    )
    
    return {'message': 'Item removed from cart'}

@router.delete('/')
async def clear_cart(current_user: dict = Depends(get_current_user), db=Depends(get_database)):
    """Clear cart"""
    await db.carts.update_one(
        {'user_id': current_user['id']},
        {'$set': {'items': [], 'updated_at': datetime.now(timezone.utc)}}
    )
    
    return {'message': 'Cart cleared'}
