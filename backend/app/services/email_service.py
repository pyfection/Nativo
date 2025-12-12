"""
Email service for sending password reset emails and other notifications.
"""
import logging
from typing import Optional
from fastapi import HTTPException, status

logger = logging.getLogger(__name__)


class EmailService:
    """
    Service for sending emails.
    
    This is a placeholder implementation. In production, integrate with
    a real email service provider (e.g., SendGrid, AWS SES, SMTP).
    """
    
    @staticmethod
    async def send_password_reset_email(
        email: str,
        reset_token: str,
        reset_url: Optional[str] = None
    ) -> bool:
        """
        Send a password reset email to the user.
        
        Args:
            email: Recipient email address
            reset_token: Password reset token
            reset_url: Optional full reset URL (if not provided, token is sent)
            
        Returns:
            True if email was sent successfully, False otherwise
            
        Raises:
            HTTPException: If email sending fails critically
        """
        try:
            # In production, replace this with actual email sending logic
            # Example with SendGrid:
            # from sendgrid import SendGridAPIClient
            # from sendgrid.helpers.mail import Mail
            # 
            # message = Mail(
            #     from_email='noreply@nativo.app',
            #     to_emails=email,
            #     subject='Password Reset Request',
            #     html_content=f'<p>Click <a href="{reset_url}">here</a> to reset your password.</p>'
            # )
            # sg = SendGridAPIClient(settings.SENDGRID_API_KEY)
            # response = sg.send(message)
            
            # For now, log the email that would be sent
            logger.info(
                f"Password reset email would be sent to {email}",
                extra={
                    "email": email,
                    "reset_token": reset_token[:10] + "..." if len(reset_token) > 10 else reset_token,
                    "reset_url": reset_url
                }
            )
            
            # Simulate email sending (in dev, this always succeeds)
            # In production, check the actual email service response
            return True
            
        except Exception as e:
            logger.error(
                f"Failed to send password reset email to {email}",
                extra={"email": email, "error": str(e)},
                exc_info=True
            )
            # Don't raise exception here - we want to return success to prevent email enumeration
            # Log the error for admin review
            return False


# Create a singleton instance
email_service = EmailService()
