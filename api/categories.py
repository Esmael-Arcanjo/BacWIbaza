from fastapi import APIRouter, Depends, HTTPException
from bson import ObjectId
from typing import List
from models.category import CategoryCreate
from auth.dependencies import require_role
from database import get_database
from datetime import datetime, timezone
import re

router = APIRouter(prefix='/api/categories', tags=['categories'])

def slugify(text: str) -> str:
    """Convert text to URL-friendly slug"""
    text = text.lower()
    text = re.sub(r'[^a-z0-9\s-]', '', text)
    text = re.sub(r'[\s-]+', '-', text)
    return text.strip('-')

@router.post('/')
async def create_category(
    category_data: CategoryCreate,
    current_user: dict = Depends(require_role('admin')),
    db=Depends(get_database)
):
    """Create category (Admin only)"""
    slug = slugify(category_data.name)
    
    existing = await db.categories.find_one({'slug': slug, 'deleted_at': None})
    if existing:
        raise HTTPException(status_code=400, detail='Category with this name already exists')
    
    category = category_data.model_dump()
    category['slug'] = slug
    category['order'] = 0
    category['is_active'] = True
    category['created_at'] = datetime.now(timezone.utc)
    category['updated_at'] = datetime.now(timezone.utc)
    category['deleted_at'] = None
    
    result = await db.categories.insert_one(category)
    category['id'] = str(result.inserted_id)
    category.pop('_id', None)
    
    return category

@router.get('')
async def get_categories(db=Depends(get_database)):
    """Get all active categories"""
    categories = await db.categories.find(
        {'deleted_at': None, 'is_active': True}
    ).sort('order', 1).to_list(length=100)
    
    for cat in categories:
        if '_id' in cat:
            cat['id'] = str(cat.pop('_id'))
    
    return categories

@router.get('/{category_id}')
async def get_category(category_id: str, db=Depends(get_database)):
    """Get single category"""
    category = await db.categories.find_one(
        {'_id': ObjectId(category_id), 'deleted_at': None},
        {'_id': 0}
    )
    
    if not category:
        raise HTTPException(status_code=404, detail='Category not found')
    
    category['id'] = category_id
    return category

@router.delete('/{category_id}')
async def delete_category(
    category_id: str,
    current_user: dict = Depends(require_role('admin')),
    db=Depends(get_database)
):
    """Soft delete category (Admin only)"""
    category = await db.categories.find_one({'_id': ObjectId(category_id), 'deleted_at': None})
    
    if not category:
        raise HTTPException(status_code=404, detail='Category not found')
    
    await db.categories.update_one(
        {'_id': ObjectId(category_id)},
        {'$set': {'deleted_at': datetime.now(timezone.utc)}}
    )
    
    return {'message': 'Category deleted successfully'}
