from fastapi import Request, HTTPException, Depends
from bson import ObjectId
import jwt
from auth.jwt_utils import decode_token
from database import get_database

async def get_current_user(request: Request, db=Depends(get_database)) -> dict:
    """Extract and validate user from JWT token (cookie or header)"""
    token = request.cookies.get('access_token')
    
    if not token:
        auth_header = request.headers.get('Authorization', '')
        if auth_header.startswith('Bearer '):
            token = auth_header[7:]
    
    if not token:
        raise HTTPException(status_code=401, detail='Not authenticated')
    
    try:
        payload = decode_token(token)
        
        if payload.get('type') != 'access':
            raise HTTPException(status_code=401, detail='Invalid token type')
        
        user = await db.users.find_one({'_id': ObjectId(payload['sub'])})
        
        if not user:
            raise HTTPException(status_code=401, detail='User not found')
        
        if user.get('deleted_at'):
            raise HTTPException(status_code=401, detail='User account is deleted')
        
        user['id'] = str(user['_id'])
        user.pop('_id', None)
        user.pop('password_hash', None)
        
        return user
    
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail='Token expired')
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail='Invalid token')

def require_role(*allowed_roles: str):
    """Dependency to check if user has required role"""
    async def role_checker(current_user: dict = Depends(get_current_user)):
        if current_user.get('role') not in allowed_roles:
            raise HTTPException(status_code=403, detail='Insufficient permissions')
        return current_user
    return role_checker
