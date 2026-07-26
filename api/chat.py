from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends
from typing import Dict, Set
from bson import ObjectId
from database import get_database
from datetime import datetime, timezone
import json
import logging

logger = logging.getLogger(__name__)
router = APIRouter()

class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, Set[WebSocket]] = {}
    
    async def connect(self, user_id: str, websocket: WebSocket):
        await websocket.accept()
        if user_id not in self.active_connections:
            self.active_connections[user_id] = set()
        self.active_connections[user_id].add(websocket)
        logger.info(f'User {user_id} connected to chat')
    
    def disconnect(self, user_id: str, websocket: WebSocket):
        if user_id in self.active_connections:
            self.active_connections[user_id].discard(websocket)
            if not self.active_connections[user_id]:
                del self.active_connections[user_id]
        logger.info(f'User {user_id} disconnected from chat')
    
    async def send_message(self, user_id: str, message: dict):
        if user_id in self.active_connections:
            for connection in self.active_connections[user_id]:
                try:
                    await connection.send_json(message)
                except Exception as e:
                    logger.error(f'Error sending message to {user_id}: {str(e)}')

manager = ConnectionManager()

@router.websocket('/ws/chat/{user_id}')
async def chat_websocket(websocket: WebSocket, user_id: str, db=Depends(get_database)):
    """WebSocket endpoint for real-time chat"""
    await manager.connect(user_id, websocket)
    
    try:
        while True:
            data = await websocket.receive_text()
            message_data = json.loads(data)
            
            conversation_id = message_data.get('conversation_id')
            receiver_id = message_data.get('receiver_id')
            message_text = message_data.get('message')
            sender_role = message_data.get('sender_role', 'client')
            
            if not all([conversation_id, receiver_id, message_text]):
                continue
            
            chat_message = {
                'conversation_id': conversation_id,
                'sender_id': user_id,
                'sender_role': sender_role,
                'receiver_id': receiver_id,
                'message': message_text,
                'is_read': False,
                'created_at': datetime.now(timezone.utc),
                'updated_at': datetime.now(timezone.utc),
                'deleted_at': None
            }
            
            result = await db.chat_messages.insert_one(chat_message)
            chat_message['id'] = str(result.inserted_id)
            chat_message.pop('_id', None)
            chat_message['created_at'] = chat_message['created_at'].isoformat()
            chat_message['updated_at'] = chat_message['updated_at'].isoformat()
            
            await manager.send_message(user_id, {'type': 'message_sent', 'data': chat_message})
            await manager.send_message(receiver_id, {'type': 'new_message', 'data': chat_message})
    
    except WebSocketDisconnect:
        manager.disconnect(user_id, websocket)
    except Exception as e:
        logger.error(f'WebSocket error: {str(e)}')
        manager.disconnect(user_id, websocket)

@router.get('/api/chat/conversations')
async def get_conversations(user_id: str, db=Depends(get_database)):
    """Get user's conversations"""
    messages = await db.chat_messages.find(
        {'$or': [{'sender_id': user_id}, {'receiver_id': user_id}], 'deleted_at': None},
        {'_id': 0}
    ).sort('created_at', -1).to_list(length=1000)
    
    conversations = {}
    for msg in messages:
        other_id = msg['receiver_id'] if msg['sender_id'] == user_id else msg['sender_id']
        conv_id = msg['conversation_id']
        
        if conv_id not in conversations:
            conversations[conv_id] = {
                'conversation_id': conv_id,
                'other_user_id': other_id,
                'last_message': msg['message'],
                'last_message_time': msg['created_at'],
                'unread_count': 0
            }
        
        if msg['receiver_id'] == user_id and not msg['is_read']:
            conversations[conv_id]['unread_count'] += 1
    
    return list(conversations.values())

@router.get('/api/chat/messages/{conversation_id}')
async def get_messages(conversation_id: str, db=Depends(get_database)):
    """Get messages for a conversation"""
    messages = await db.chat_messages.find(
        {'conversation_id': conversation_id, 'deleted_at': None},
        {'_id': 0}
    ).sort('created_at', 1).to_list(length=1000)
    
    for msg in messages:
        if '_id' in msg:
            msg['id'] = str(msg.pop('_id'))
    
    return messages
