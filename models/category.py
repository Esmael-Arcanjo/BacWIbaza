from pydantic import BaseModel
from typing import Optional, List
from models.base import BaseDocument

class Category(BaseDocument):
    name: str
    slug: str
    description: Optional[str] = None
    image_url: Optional[str] = None
    parent_id: Optional[str] = None
    order: int = 0
    is_active: bool = True

class CategoryCreate(BaseModel):
    name: str
    description: Optional[str] = None
    image_url: Optional[str] = None
    parent_id: Optional[str] = None

class CategoryResponse(BaseModel):
    id: str
    name: str
    slug: str
    description: Optional[str] = None
    image_url: Optional[str] = None
    parent_id: Optional[str] = None
    order: int
    is_active: bool
