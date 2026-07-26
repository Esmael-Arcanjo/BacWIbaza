from pydantic import BaseModel
from typing import Literal
from models.base import BaseDocument

class ChatMessage(BaseDocument):
    conversation_id: str
    sender_id: str
    sender_role: Literal['client', 'seller', 'admin']
    receiver_id: str
    message: str
    is_read: bool = False

class ChatMessageCreate(BaseModel):
    receiver_id: str
    message: str
