from models.base import BaseDocument

class Favorite(BaseDocument):
    user_id: str
    product_id: str
