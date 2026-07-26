from pydantic import BaseModel, Field
from typing import List, Literal, Optional
from models.base import BaseDocument

class OrderItem(BaseModel):
    product_id: str
    product_name: str
    seller_id: str
    quantity: int
    unit_price: float
    total_price: float

class Order(BaseDocument):
    order_number: str
    client_id: str
    items: List[OrderItem]
    subtotal: float
    tax: float = 0.0
    shipping: float = 0.0
    total: float
    status: Literal['pending', 'processing', 'shipped', 'delivered', 'cancelled'] = 'pending'
    payment_status: Literal['pending', 'paid', 'failed', 'refunded'] = 'pending'
    payment_session_id: Optional[str] = None
    shipping_address: dict
    billing_address: dict

class OrderCreate(BaseModel):
    items: List[OrderItem]
    shipping_address: dict
    billing_address: dict
