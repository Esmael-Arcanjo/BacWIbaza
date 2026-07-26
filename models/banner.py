from pydantic import BaseModel
from models.base import BaseDocument

class Banner(BaseDocument):
    title: str
    subtitle: str = ''
    image_url: str
    link_url: str = ''
    order: int = 0
    is_active: bool = True

class BannerCreate(BaseModel):
    title: str
    subtitle: str = ''
    image_url: str
    link_url: str = ''
