import resend
import asyncio
import logging
from config import settings

logger = logging.getLogger(__name__)

resend.api_key = settings.RESEND_API_KEY

class EmailService:
    @staticmethod
    async def send_email(to: str, subject: str, html_content: str):
        """Send email using Resend (async)"""
        params = {
            'from': settings.SENDER_EMAIL,
            'to': [to],
            'subject': subject,
            'html': html_content
        }
        
        try:
            email = await asyncio.to_thread(resend.Emails.send, params)
            logger.info(f"Email sent to {to}: {email.get('id')}")
            return email
        except Exception as e:
            logger.error(f"Failed to send email to {to}: {str(e)}")
            raise
    
    @staticmethod
    async def send_welcome_email(to: str, name: str):
        subject = 'Bem-vindo ao WIBAZA!'
        html = f"""
        <html>
            <body style="font-family: sans-serif;">
                <h1>Olá {name}!</h1>
                <p>Bem-vindo ao WIBAZA, seu marketplace internacional.</p>
                <p>Estamos felizes em tê-lo conosco!</p>
            </body>
        </html>
        """
        return await EmailService.send_email(to, subject, html)
    
    @staticmethod
    async def send_password_reset_email(to: str, reset_token: str):
        reset_link = f"{settings.FRONTEND_URL}/reset-password?token={reset_token}"
        subject = 'Recuperação de Senha - WIBAZA'
        html = f"""
        <html>
            <body style="font-family: sans-serif;">
                <h1>Recuperação de Senha</h1>
                <p>Clique no link abaixo para redefinir sua senha:</p>
                <a href="{reset_link}">Redefinir Senha</a>
                <p>Este link expira em 1 hora.</p>
            </body>
        </html>
        """
        return await EmailService.send_email(to, subject, html)
    
    @staticmethod
    async def send_order_confirmation_email(to: str, order_number: str, total: float):
        subject = f'Pedido Confirmado #{order_number} - WIBAZA'
        html = f"""
        <html>
            <body style="font-family: sans-serif;">
                <h1>Pedido Confirmado!</h1>
                <p>Seu pedido <strong>#{order_number}</strong> foi confirmado.</p>
                <p>Total: ${total:.2f}</p>
                <p>Obrigado por comprar na WIBAZA!</p>
            </body>
        </html>
        """
        return await EmailService.send_email(to, subject, html)
    
    @staticmethod
    async def send_seller_approval_email(to: str, name: str, approved: bool):
        if approved:
            subject = 'Conta de Vendedor Aprovada - WIBAZA'
            html = f"""
            <html>
                <body style="font-family: sans-serif;">
                    <h1>Parabéns {name}!</h1>
                    <p>Sua conta de vendedor foi aprovada.</p>
                    <p>Você já pode começar a vender no WIBAZA!</p>
                </body>
            </html>
            """
        else:
            subject = 'Conta de Vendedor Recusada - WIBAZA'
            html = f"""
            <html>
                <body style="font-family: sans-serif;">
                    <h1>Olá {name}</h1>
                    <p>Infelizmente sua conta de vendedor foi recusada.</p>
                    <p>Entre em contato conosco para mais informações.</p>
                </body>
            </html>
            """
        return await EmailService.send_email(to, subject, html)
