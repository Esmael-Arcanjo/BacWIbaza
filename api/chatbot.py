from fastapi import APIRouter, Depends
from pydantic import BaseModel
from services.chatbot_service import ChatbotService
from database import get_database
import logging

logger = logging.getLogger(__name__)
router = APIRouter(prefix='/api/chatbot', tags=['chatbot'])

class ChatbotRequest(BaseModel):
    message: str
    conversation_history: list = []

@router.post('/message')
async def chatbot_message(request: ChatbotRequest, db=Depends(get_database)):
    """Get chatbot response"""
    try:
        response = await ChatbotService.get_response(
            message=request.message,
            conversation_history=request.conversation_history
        )
        return {'response': response}
    except Exception as e:
        logger.error(f'Chatbot error: {str(e)}')
        return {'response': 'Desculpe, ocorreu um erro. Por favor, tente novamente.'}
