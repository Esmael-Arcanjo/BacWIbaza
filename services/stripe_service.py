import stripe
import urllib.request
import json
import os
import logging
from config import settings
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

stripe.api_key = settings.STRIPE_SECRET_KEY

class StripeService:
    sandbox_data = None
    
    @classmethod
    async def provision_sandbox(cls):
        """Provision Stripe sandbox (Flow A)"""
        base = os.environ.get('INTEGRATION_PROXY_URL', '')
        if not base:
            logger.warning('INTEGRATION_PROXY_URL not set, skipping sandbox provisioning')
            return None
        
        job_id = os.environ.get('JOB_ID', '')
        key = os.environ.get('INTEGRATION_KEY', '')
        
        try:
            req = urllib.request.Request(
                base + '/stripe/sandboxes',
                data=json.dumps({'job_id': job_id}).encode(),
                headers={'Authorization': f'Bearer {key}', 'Content-Type': 'application/json'},
                method='POST',
            )
            with urllib.request.urlopen(req) as r:
                cls.sandbox_data = json.load(r)
                stripe.api_key = cls.sandbox_data['sandbox_secret_key']
                logger.info('Stripe sandbox provisioned successfully')
                return cls.sandbox_data
        except Exception as e:
            logger.error(f'Failed to provision Stripe sandbox: {str(e)}')
            return None
    
    @staticmethod
    async def create_checkout_session(amount: float, currency: str, success_url: str, cancel_url: str, metadata: dict):
        """Create Stripe checkout session"""
        try:
            session = stripe.checkout.Session.create(
                line_items=[{
                    'price_data': {
                        'currency': currency,
                        'unit_amount': int(amount * 100),
                        'product_data': {'name': 'Order Payment'}
                    },
                    'quantity': 1
                }],
                mode='payment',
                success_url=success_url,
                cancel_url=cancel_url,
                metadata=metadata
            )
            return session
        except Exception as e:
            logger.error(f'Stripe checkout error: {str(e)}')
            raise
    
    @staticmethod
    async def get_session_status(session_id: str):
        """Get Stripe session status"""
        try:
            session = stripe.checkout.Session.retrieve(session_id)
            return {
                'session_id': session.id,
                'status': session.status,
                'payment_status': session.payment_status
            }
        except Exception as e:
            logger.error(f'Stripe session retrieval error: {str(e)}')
            raise
