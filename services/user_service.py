import secrets
from datetime import datetime, timezone, timedelta
from bson import ObjectId
from typing import Optional
from models.user import User, UserCreate
from auth.hash_utils import hash_password, verify_password

class UserService:
    def __init__(self, db):
        self.db = db
    
    async def create_user(self, user_data: UserCreate) -> dict:
        """Create new user"""
        existing = await self.db.users.find_one({'email': user_data.email.lower()})
        if existing:
            raise ValueError('Email already registered')
        
        user = User(
            email=user_data.email.lower(),
            password_hash=hash_password(user_data.password),
            name=user_data.name,
            role=user_data.role,
            phone=user_data.phone,
            country=user_data.country,
            is_approved=True if user_data.role == 'client' else False
        )
        
        result = await self.db.users.insert_one(user.model_dump())
        created_user = await self.db.users.find_one({'_id': result.inserted_id}, {'_id': 0, 'password_hash': 0})
        created_user['id'] = str(result.inserted_id)
        return created_user
    
    async def authenticate_user(self, email: str, password: str) -> Optional[dict]:
        """Authenticate user by email and password"""
        user = await self.db.users.find_one({'email': email.lower(), 'deleted_at': None})
        
        if not user:
            return None
        
        if not verify_password(password, user['password_hash']):
            return None
        
        user['id'] = str(user['_id'])
        user.pop('_id', None)
        user.pop('password_hash', None)
        return user
    
    async def get_user_by_id(self, user_id: str) -> Optional[dict]:
        """Get user by ID"""
        user = await self.db.users.find_one({'_id': ObjectId(user_id), 'deleted_at': None}, {'_id': 0, 'password_hash': 0})
        if user:
            user['id'] = user_id
        return user
    
    async def update_user(self, user_id: str, update_data: dict) -> Optional[dict]:
        """Update user"""
        update_data['updated_at'] = datetime.now(timezone.utc)
        await self.db.users.update_one({'_id': ObjectId(user_id)}, {'$set': update_data})
        return await self.get_user_by_id(user_id)
    
    async def create_password_reset_token(self, email: str) -> Optional[str]:
        """Create password reset token"""
        user = await self.db.users.find_one({'email': email.lower(), 'deleted_at': None})
        if not user:
            return None
        
        token = secrets.token_urlsafe(32)
        expires_at = datetime.now(timezone.utc) + timedelta(hours=1)
        
        await self.db.password_reset_tokens.insert_one({
            'token': token,
            'user_id': str(user['_id']),
            'email': email.lower(),
            'expires_at': expires_at,
            'used': False,
            'created_at': datetime.now(timezone.utc)
        })
        
        return token
    
    async def reset_password(self, token: str, new_password: str) -> bool:
        """Reset user password with token"""
        reset_token = await self.db.password_reset_tokens.find_one({
            'token': token,
            'used': False,
            'expires_at': {'$gt': datetime.now(timezone.utc)}
        })
        
        if not reset_token:
            return False
        
        await self.db.users.update_one(
            {'_id': ObjectId(reset_token['user_id'])},
            {'$set': {'password_hash': hash_password(new_password), 'updated_at': datetime.now(timezone.utc)}}
        )
        
        await self.db.password_reset_tokens.update_one(
            {'_id': reset_token['_id']},
            {'$set': {'used': True}}
        )
        
        return True
