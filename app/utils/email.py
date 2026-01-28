import os
import requests
from typing import Optional
from app.core import config


def send_password_reset_email(email: str, reset_link: str) -> bool:
    """
    Send password reset email using Resend API
    
    Args:
        email: Recipient email address
        reset_link: Password reset link with token
        
    Returns:
        bool: True if email sent successfully, False otherwise
    """
    resend_api_key = config.settings.resend_api_key
    
    if not resend_api_key:
        raise ValueError("RESEND_API_KEY is not configured in environment variables")
    
    try:
        response = requests.post(
            "https://api.resend.com/emails",
            headers={
                "Authorization": f"Bearer {resend_api_key}",
                "Content-Type": "application/json"
            },
            json={
                "from": "Organised Gym <noreply@organisedgym.com>",
                "to": [email],
                "subject": "Reset Your Password - Organised Gym",
                "html": f"""
                <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
                    <h2 style="color: #333;">Password Reset Request</h2>
                    <p>Hello,</p>
                    <p>You have requested to reset your password for your Organised Gym account.</p>
                    <p>Click the link below to reset your password (valid for 15 minutes):</p>
                    <p style="margin: 20px 0;">
                        <a href="{reset_link}" 
                           style="background-color: #007bff; color: white; padding: 12px 24px; 
                                  text-decoration: none; border-radius: 5px; display: inline-block;">
                            Reset Password
                        </a>
                    </p>
                    <p>Or copy and paste this link into your browser:</p>
                    <p style="word-break: break-all; color: #666;">{reset_link}</p>
                    <p style="margin-top: 30px; color: #999; font-size: 12px;">
                        If you did not request this password reset, please ignore this email.
                    </p>
                    <p style="color: #999; font-size: 12px;">
                        This link will expire in 15 minutes.
                    </p>
                </div>
                """
            }
        )
        
        if response.status_code == 200:
            return True
        else:
            print(f"Failed to send email: {response.status_code} - {response.text}")
            return False
            
    except Exception as e:
        print(f"Error sending email: {str(e)}")
        return False
