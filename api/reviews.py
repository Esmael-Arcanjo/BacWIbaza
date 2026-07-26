from fastapi import APIRouter, Depends, HTTPException
from bson import ObjectId
from models.review import ReviewCreate
from auth.dependencies import get_current_user
from database import get_database
from datetime import datetime, timezone

router = APIRouter(prefix='/api/reviews', tags=['reviews'])

@router.post('/')
async def create_review(
    review_data: ReviewCreate,
    current_user: dict = Depends(get_current_user),
    db=Depends(get_database)
):
    """Create product review"""
    if review_data.rating < 1 or review_data.rating > 5:
        raise HTTPException(status_code=400, detail='Rating must be between 1 and 5')
    
    product = await db.products.find_one({'_id': ObjectId(review_data.product_id), 'deleted_at': None})
    
    if not product:
        raise HTTPException(status_code=404, detail='Product not found')
    
    existing = await db.reviews.find_one({
        'product_id': review_data.product_id,
        'user_id': current_user['id'],
        'deleted_at': None
    })
    
    if existing:
        raise HTTPException(status_code=400, detail='You have already reviewed this product')
    
    order = await db.orders.find_one({
        'client_id': current_user['id'],
        'items.product_id': review_data.product_id,
        'payment_status': 'paid',
        'deleted_at': None
    })
    
    is_verified = bool(order)
    
    review = {
        'product_id': review_data.product_id,
        'user_id': current_user['id'],
        'user_name': current_user.get('name', 'Anonymous'),
        'rating': review_data.rating,
        'comment': review_data.comment,
        'is_verified_purchase': is_verified,
        'created_at': datetime.now(timezone.utc),
        'updated_at': datetime.now(timezone.utc),
        'deleted_at': None
    }
    
    result = await db.reviews.insert_one(review)
    
    reviews = await db.reviews.find({'product_id': review_data.product_id, 'deleted_at': None}).to_list(length=1000)
    avg_rating = sum(r['rating'] for r in reviews) / len(reviews) if reviews else 0.0
    
    await db.products.update_one(
        {'_id': ObjectId(review_data.product_id)},
        {'$set': {'average_rating': avg_rating, 'total_reviews': len(reviews)}}
    )
    
    review['id'] = str(result.inserted_id)
    review.pop('_id', None)
    
    return review

@router.get('/product/{product_id}')
async def get_product_reviews(product_id: str, db=Depends(get_database)):
    """Get reviews for a product"""
    reviews = await db.reviews.find(
        {'product_id': product_id, 'deleted_at': None},
        {'_id': 0}
    ).sort('created_at', -1).to_list(length=100)
    
    for review in reviews:
        if '_id' in review:
            review['id'] = str(review.pop('_id'))
    
    return reviews
