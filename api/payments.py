from fastapi import APIRouter, Depends, HTTPException, Request
from services.stripe_service import StripeService
from auth.dependencies import get_current_user
from database import get_database
from datetime import datetime, timezone
import stripe
import logging

logger = logging.getLogger(__name__)
router = APIRouter(prefix='/api/payments', tags=['payments'])

@router.post('/checkout')
async def create_checkout(
    order_id: str,
    current_user: dict = Depends(get_current_user),
    db=Depends(get_database),
    request: Request = None
):
    """Create Stripe checkout session"""
    from bson import ObjectId
    
    order = await db.orders.find_one({'_id': ObjectId(order_id), 'deleted_at': None})
    
    if not order:
        raise HTTPException(status_code=404, detail='Order not found')
    
    if str(order['client_id']) != current_user['id']:
        raise HTTPException(status_code=403, detail='Not authorized')
    
    origin_url = str(request.base_url).rstrip('/')
    success_url = f"{origin_url}/payment/success?session_id={{CHECKOUT_SESSION_ID}}"
    cancel_url = f"{origin_url}/payment/cancel"
    
    session = await StripeService.create_checkout_session(
        amount=order['total'],
        currency='usd',
        success_url=success_url,
        cancel_url=cancel_url,
        metadata={'order_id': order_id, 'user_id': current_user['id']}
    )
    
    await db.orders.update_one(
        {'_id': ObjectId(order_id)},
        {'$set': {'payment_session_id': session.id, 'updated_at': datetime.now(timezone.utc)}}
    )
    
    await db.payment_transactions.insert_one({
        'session_id': session.id,
        'order_id': order_id,
        'user_id': current_user['id'],
        'amount': order['total'],
        'currency': 'usd',
        'status': 'initiated',
        'payment_status': 'pending',
        'created_at': datetime.now(timezone.utc),
        'updated_at': datetime.now(timezone.utc)
    })
    
    return {'checkout_url': session.url, 'session_id': session.id}

@router.get('/status/{session_id}')
async def get_payment_status(session_id: str, db=Depends(get_database)):
    """Get payment status"""
    transaction = await db.payment_transactions.find_one({'session_id': session_id}, {'_id': 0})
    
    if not transaction:
        raise HTTPException(status_code=404, detail='Transaction not found')
    
    if transaction.get('payment_status') != 'paid':
        try:
            status = await StripeService.get_session_status(session_id)
            if status['payment_status'] == 'paid' or status['status'] == 'complete':
                await db.payment_transactions.update_one(
                    {'session_id': session_id, 'payment_status': {'$ne': 'paid'}},
                    {'$set': {'status': 'completed', 'payment_status': 'paid', 'updated_at': datetime.now(timezone.utc)}}
                )
                
                await db.orders.update_one(
                    {'payment_session_id': session_id},
                    {'$set': {'payment_status': 'paid', 'status': 'processing', 'updated_at': datetime.now(timezone.utc)}}
                )
                
                transaction = await db.payment_transactions.find_one({'session_id': session_id}, {'_id': 0})
        except Exception as e:
            logger.error(f'Error checking payment status: {str(e)}')
    
    return {
        'session_id': transaction['session_id'],
        'status': transaction['status'],
        'payment_status': transaction['payment_status']
    }

@router.post('/stripe/webhook')
async def stripe_webhook(request: Request, db=Depends(get_database)):
    """Handle Stripe webhooks"""
    from config import settings
    
    payload = await request.body()
    sig = request.headers.get('stripe-signature', '')
    
    try:
        event = stripe.Webhook.construct_event(payload, sig, settings.STRIPE_WEBHOOK_SECRET)
    except Exception as e:
        logger.error(f'Webhook signature verification failed: {str(e)}')
        raise HTTPException(status_code=400, detail='Invalid signature')
    
    obj = event['data']['object']
    event_type = event['type']
    
    if event_type == 'checkout.session.completed':
        await db.payment_transactions.update_one(
            {'session_id': obj['id'], 'payment_status': {'$ne': 'paid'}},
            {'$set': {
                'status': 'completed',
                'payment_status': obj.get('payment_status', 'paid'),
                'updated_at': datetime.now(timezone.utc)
            }}
        )
        
        await db.orders.update_one(
            {'payment_session_id': obj['id']},
            {'$set': {'payment_status': 'paid', 'status': 'processing', 'updated_at': datetime.now(timezone.utc)}}
        )
    
    elif event_type == 'checkout.session.async_payment_succeeded':
        await db.payment_transactions.update_one(
            {'session_id': obj['id']},
            {'$set': {'payment_status': 'paid', 'updated_at': datetime.now(timezone.utc)}}
        )
        
        await db.orders.update_one(
            {'payment_session_id': obj['id']},
            {'$set': {'payment_status': 'paid', 'status': 'processing', 'updated_at': datetime.now(timezone.utc)}}
        )
    
    elif event_type == 'checkout.session.async_payment_failed':
        await db.payment_transactions.update_one(
            {'session_id': obj['id']},
            {'$set': {'status': 'failed', 'payment_status': 'failed', 'updated_at': datetime.now(timezone.utc)}}
        )
        
        await db.orders.update_one(
            {'payment_session_id': obj['id']},
            {'$set': {'payment_status': 'failed', 'updated_at': datetime.now(timezone.utc)}}
        )
    
    return {'status': 'ok'}
