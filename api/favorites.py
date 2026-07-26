from fastapi import APIRouter, Depends, HTTPException
from bson import ObjectId
from auth.dependencies import get_current_user
from database import get_database
from datetime import datetime, timezone

router = APIRouter(prefix='/api/favorites', tags=['favorites'])

@router.get('')
async def get_favorites(current_user: dict = Depends(get_current_user), db=Depends(get_database)):
    """Get user's favorite products"""
    favorites = await db.favorites.find(
        {'user_id': current_user['id'], 'deleted_at': None},
        {'_id': 0}
    ).to_list(length=1000)
    
    product_ids = [ObjectId(fav['product_id']) for fav in favorites]
    products = await db.products.find(
        {'_id': {'$in': product_ids}, 'deleted_at': None},
        {'_id': 0}
    ).to_list(length=1000)
    
    for product in products:
        if '_id' in product:
            product['id'] = str(product.pop('_id'))
    
    return products

@router.post('/{product_id}')
async def add_favorite(
    product_id: str,
    current_user: dict = Depends(get_current_user),
    db=Depends(get_database)
):
    """Add product to favorites"""
    product = await db.products.find_one({'_id': ObjectId(product_id), 'deleted_at': None})
    
    if not product:
        raise HTTPException(status_code=404, detail='Product not found')
    
    existing = await db.favorites.find_one({
        'user_id': current_user['id'],
        'product_id': product_id,
        'deleted_at': None
    })
    
    if existing:
        return {'message': 'Already in favorites'}
    
    favorite = {
        'user_id': current_user['id'],
        'product_id': product_id,
        'created_at': datetime.now(timezone.utc),
        'updated_at': datetime.now(timezone.utc),
        'deleted_at': None
    }
    
    await db.favorites.insert_one(favorite)
    return {'message': 'Added to favorites'}

@router.delete('/{product_id}')
async def remove_favorite(
    product_id: str,
    current_user: dict = Depends(get_current_user),
    db=Depends(get_database)
):
    """Remove product from favorites"""
    await db.favorites.update_one(
        {'user_id': current_user['id'], 'product_id': product_id},
        {'$set': {'deleted_at': datetime.now(timezone.utc)}}
    )
    
    return {'message': 'Removed from favorites'}
