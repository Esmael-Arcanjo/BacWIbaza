from pydantic import BaseModel
from typing import List
from models.base import BaseDocument

class CartItem(BaseModel):
    product_id: str
    quantity: int
    selected_variation: dict = {}

class Cart(BaseDocument):
    user_id: str
    items: List[CartItem] = []

class CartAddItem(BaseModel):
    product_id: str
    quantity: int = 1
    selected_variation: dict = {}

class CartUpdateItem(BaseModel):
    product_id: str
    quantity: int
