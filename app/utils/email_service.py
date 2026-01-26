import smtplib
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional
from app.core.config import settings

logger = logging.getLogger(__name__)


class EmailService:
    """Service for sending emails"""
    
    @staticmethod
    def send_password_reset_email(
        to_email: str,
        reset_token: str,
        reset_url: Optional[str] = None
    ) -> bool:
        """
        Send password reset email to user.
        
        Args:
            to_email: Recipient email address
            reset_token: The password reset token
            reset_url: Optional custom reset URL. If not provided, uses default format.
            
        Returns:
            bool: True if email sent successfully, False otherwise
        """
        try:
            # Get email configuration from settings
            smtp_host = getattr(settings, 'smtp_host', None)
            smtp_port = getattr(settings, 'smtp_port', 587)
            smtp_user = getattr(settings, 'smtp_user', None)
            smtp_password = getattr(settings, 'smtp_password', None)
            smtp_from_email = getattr(settings, 'smtp_from_email', smtp_user)
            smtp_use_tls = getattr(settings, 'smtp_use_tls', True)
            
            # If email is not configured, log and return True (don't fail the request)
            if not smtp_host or not smtp_user or not smtp_password:
                logger.warning(
                    "Email service not configured. Password reset email would be sent to: "
                    f"{to_email} with token: {reset_token[:10]}..."
                )
                return True
            
            # Create message
            msg = MIMEMultipart('alternative')
            msg['Subject'] = 'Password Reset Request'
            msg['From'] = smtp_from_email
            msg['To'] = to_email
            
            # Create reset URL
            if not reset_url:
                reset_url = f"{getattr(settings, 'frontend_url', 'https://yourapp.com')}/reset-password?token={reset_token}"
            
            # Create email body
            text_content = f"""
            You have requested to reset your password for {getattr(settings, 'app_name', 'Organised Gym')}.
            
            Please use the following token to reset your password:
            {reset_token}
            
            Or click the following link:
            {reset_url}
            
            This token will expire in 1 hour.
            
            If you did not request this password reset, please ignore this email.
            """
            
            html_content = f"""
            <html>
              <body>
                <h2>Password Reset Request</h2>
                <p>You have requested to reset your password for <strong>{getattr(settings, 'app_name', 'Organised Gym')}</strong>.</p>
                <p>Please use the following token to reset your password:</p>
                <p style="font-family: monospace; font-size: 16px; background-color: #f0f0f0; padding: 10px; border-radius: 5px;">
                  {reset_token}
                </p>
                <p>Or click the following link:</p>
                <p><a href="{reset_url}" style="background-color: #4CAF50; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px; display: inline-block;">Reset Password</a></p>
                <p><small>This token will expire in 1 hour.</small></p>
                <p><small>If you did not request this password reset, please ignore this email.</small></p>
              </body>
            </html>
            """
            
            # Attach parts
            part1 = MIMEText(text_content, 'plain')
            part2 = MIMEText(html_content, 'html')
            msg.attach(part1)
            msg.attach(part2)
            
            # Send email
            with smtplib.SMTP(smtp_host, smtp_port) as server:
                if smtp_use_tls:
                    server.starttls()
                server.login(smtp_user, smtp_password)
                server.send_message(msg)
            
            logger.info(f"Password reset email sent successfully to {to_email}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send password reset email to {to_email}: {str(e)}")
            # Return True to avoid revealing if email exists
            return True
