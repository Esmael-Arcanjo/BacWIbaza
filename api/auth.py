from fastapi import APIRouter, Depends, HTTPException, Response, Request
from bson import ObjectId
from models.user import UserCreate, LoginRequest, PasswordResetRequest, PasswordResetConfirm
from services.user_service import UserService
from services.email_service import EmailService
from auth.jwt_utils import create_access_token, create_refresh_token, decode_token
from auth.dependencies import get_current_user
from database import get_database
import logging

logger = logging.getLogger(__name__)
router = APIRouter(prefix='/api/auth', tags=['auth'])

@router.post('/register')
async def register(user_data: UserCreate, response: Response, db=Depends(get_database)):
    """Register new user"""
    try:
        user_service = UserService(db)
        user = await user_service.create_user(user_data)
        
        access_token = create_access_token(user['id'], user['email'], user['role'])
        refresh_token = create_refresh_token(user['id'])
        
        response.set_cookie(
            key='access_token',
            value=access_token,
            httponly=True,
            secure=False,
            samesite='lax',
            max_age=900,
            path='/'
        )
        response.set_cookie(
            key='refresh_token',
            value=refresh_token,
            httponly=True,
            secure=False,
            samesite='lax',
            max_age=604800,
            path='/'
        )
        
        try:
            await EmailService.send_welcome_email(user['email'], user['name'])
        except Exception as e:
            logger.error(f'Failed to send welcome email: {str(e)}')
        
        return user
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f'Registration error: {str(e)}')
        raise HTTPException(status_code=500, detail='Registration failed')

@router.post('/login')
async def login(login_data: LoginRequest, response: Response, db=Depends(get_database)):
    """Login user"""
    user_service = UserService(db)
    user = await user_service.authenticate_user(login_data.email, login_data.password)
    
    if not user:
        raise HTTPException(status_code=401, detail='Invalid credentials')
    
    if not user.get('is_active'):
        raise HTTPException(status_code=403, detail='Account is inactive')
    
    if user.get('role') == 'seller' and not user.get('is_approved'):
        raise HTTPException(status_code=403, detail='Seller account pending approval')
    
    access_token = create_access_token(user['id'], user['email'], user['role'])
    refresh_token = create_refresh_token(user['id'])
    
    response.set_cookie(
        key='access_token',
        value=access_token,
        httponly=True,
        secure=False,
        samesite='lax',
        max_age=900,
        path='/'
    )
    response.set_cookie(
        key='refresh_token',
        value=refresh_token,
        httponly=True,
        secure=False,
        samesite='lax',
        max_age=604800,
        path='/'
    )
    
    return user

@router.post('/logout')
async def logout(response: Response, current_user: dict = Depends(get_current_user)):
    """Logout user"""
    response.delete_cookie(key='access_token', path='/')
    response.delete_cookie(key='refresh_token', path='/')
    return {'message': 'Logged out successfully'}

@router.get('/me')
async def get_current_user_info(current_user: dict = Depends(get_current_user)):
    """Get current user info"""
    return current_user

@router.post('/refresh')
async def refresh_token(request: Request, response: Response, db=Depends(get_database)):
    """Refresh access token"""
    refresh = request.cookies.get('refresh_token')
    
    if not refresh:
        raise HTTPException(status_code=401, detail='No refresh token')
    
    try:
        payload = decode_token(refresh)
        
        if payload.get('type') != 'refresh':
            raise HTTPException(status_code=401, detail='Invalid token type')
        
        user = await db.users.find_one({'_id': ObjectId(payload['sub']), 'deleted_at': None})
        
        if not user:
            raise HTTPException(status_code=401, detail='User not found')
        
        access_token = create_access_token(str(user['_id']), user['email'], user['role'])
        
        response.set_cookie(
            key='access_token',
            value=access_token,
            httponly=True,
            secure=False,
            samesite='lax',
            max_age=900,
            path='/'
        )
        
        return {'message': 'Token refreshed'}
    
    except Exception as e:
        raise HTTPException(status_code=401, detail='Invalid refresh token')

@router.post('/forgot-password')
async def forgot_password(request: PasswordResetRequest, db=Depends(get_database)):
    """Request password reset"""
    user_service = UserService(db)
    token = await user_service.create_password_reset_token(request.email)
    
    if token:
        try:
            await EmailService.send_password_reset_email(request.email, token)
        except Exception as e:
            logger.error(f'Failed to send reset email: {str(e)}')
    
    return {'message': 'If the email exists, a reset link has been sent'}

@router.post('/reset-password')
async def reset_password(request: PasswordResetConfirm, db=Depends(get_database)):
    """Reset password with token"""
    user_service = UserService(db)
    success = await user_service.reset_password(request.token, request.new_password)
    
    if not success:
        raise HTTPException(status_code=400, detail='Invalid or expired token')
    
    return {'message': 'Password reset successfully'}
