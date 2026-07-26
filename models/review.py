from pydantic import BaseModel
from models.base import BaseDocument

class Review(BaseDocument):
    product_id: str
    user_id: str
    user_name: str
    rating: int
    comment: str
    is_verified_purchase: bool = False

class ReviewCreate(BaseModel):
    product_id: str
    rating: int
    comment: str
