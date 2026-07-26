from openai import AsyncOpenAI
import logging
from config import settings

logger = logging.getLogger(__name__)

client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY) if settings.OPENAI_API_KEY else None

class ChatbotService:
    @staticmethod
    async def get_response(message: str, conversation_history: list = None):
        """Get chatbot response using OpenAI"""
        if conversation_history is None:
            conversation_history = []
        
        if not client:
            return 'Assistente virtual não configurado. Entre em contato com o suporte.'
        
        try:
            messages = [
                {'role': 'system', 'content': 'Você é um assistente virtual da WIBAZA, um marketplace internacional. Ajude os usuários com suas dúvidas sobre produtos, pedidos e navegação no site. Seja educado e prestativo.'}
            ]
            
            for msg in conversation_history:
                if msg.get('role') in ['user', 'assistant']:
                    messages.append({'role': msg['role'], 'content': msg.get('content', '')})
            
            messages.append({'role': 'user', 'content': message})
            
            response = await client.chat.completions.create(
                model='gpt-4o-mini',
                messages=messages,
                max_tokens=500,
                temperature=0.7
            )
            
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f'OpenAI API error: {str(e)}')
            return 'Desculpe, o assistente virtual está temporariamente indisponível. Por favor, tente novamente mais tarde.'
