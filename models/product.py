from pydantic import BaseModel, Field
from typing import Optional, List, Literal, Dict, Any
from models.base import BaseDocument

class ProductDimensions(BaseModel):
    length: Optional[float] = None
    width: Optional[float] = None
    height: Optional[float] = None
    unit: str = 'cm'

class Product(BaseDocument):
    seller_id: str
    name: str
    description: str
    category_id: str
    subcategory_id: Optional[str] = None
    brand: Optional[str] = None
    sku: Optional[str] = None
    internal_code: Optional[str] = None
    price: float
    promotional_price: Optional[float] = None
    stock: int = 0
    weight: Optional[float] = None
    dimensions: Optional[ProductDimensions] = None
    images: List[str] = Field(default_factory=list)
    videos: List[str] = Field(default_factory=list)
    tags: List[str] = Field(default_factory=list)
    colors: List[str] = Field(default_factory=list)
    sizes: List[str] = Field(default_factory=list)
    variations: List[Dict[str, Any]] = Field(default_factory=list)
    attributes: List[Dict[str, Any]] = Field(default_factory=list)
    product_type: Literal['physical', 'digital'] = 'physical'
    download_url: Optional[str] = None
    approval_status: Literal['pending', 'approved', 'rejected'] = 'pending'
    is_active: bool = True
    average_rating: float = 0.0
    total_reviews: int = 0

class ProductCreate(BaseModel):
    name: str
    description: str
    category_id: str
    subcategory_id: Optional[str] = None
    brand: Optional[str] = None
    sku: Optional[str] = None
    price: float
    promotional_price: Optional[float] = None
    stock: int = 0
    weight: Optional[float] = None
    dimensions: Optional[Dict[str, Any]] = None
    images: List[str] = Field(default_factory=list)
    videos: List[str] = Field(default_factory=list)
    tags: List[str] = Field(default_factory=list)
    colors: List[str] = Field(default_factory=list)
    sizes: List[str] = Field(default_factory=list)
    attributes: List[Dict[str, Any]] = Field(default_factory=list)
    product_type: Literal['physical', 'digital'] = 'physical'

class ProductUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    category_id: Optional[str] = None
    brand: Optional[str] = None
    sku: Optional[str] = None
    price: Optional[float] = None
    promotional_price: Optional[float] = None
    stock: Optional[int] = None
    weight: Optional[float] = None
    dimensions: Optional[Dict[str, Any]] = None
    images: Optional[List[str]] = None
    tags: Optional[List[str]] = None
    colors: Optional[List[str]] = None
    sizes: Optional[List[str]] = None
    attributes: Optional[List[Dict[str, Any]]] = None
    is_active: Optional[bool] = None
