"""Email service for password reset and other notifications."""

import logging
import os
from typing import Protocol

logger = logging.getLogger(__name__)


class EmailServiceProtocol(Protocol):
    """Protocol for email service implementations."""

    async def send_password_reset_email(
        self, to_email: str, reset_token: str, user_name: str | None
    ) -> bool:
        """Send password reset email to user."""
        ...


class SendGridEmailService:
    """SendGrid email service implementation."""

    def __init__(self, api_key: str, from_email: str = "noreply@mindflow.ai"):
        """
        Initialize SendGrid email service.

        Args:
            api_key: SendGrid API key
            from_email: Sender email address
        """
        self.api_key = api_key
        self.from_email = from_email
        self._sg_client = None

        # Import SendGrid if available
        try:
            from sendgrid import SendGridAPIClient
            from sendgrid.helpers.mail import Mail

            self._sg_client = SendGridAPIClient(api_key)
            self._Mail = Mail
        except ImportError:
            logger.warning("SendGrid not installed. Email sending will be mocked.")

    async def send_password_reset_email(
        self, to_email: str, reset_token: str, user_name: str | None
    ) -> bool:
        """
        Send password reset email via SendGrid.

        Args:
            to_email: Recipient email address
            reset_token: Password reset token
            user_name: User's name (optional)

        Returns:
            True if email sent successfully, False otherwise
        """
        if not self._sg_client:
            # SendGrid not available - log instead
            logger.info(
                f"[MOCK EMAIL] Password reset for {to_email}\n"
                f"Reset token: {reset_token}\n"
                f"Reset link: https://mindflow.ai/reset-password?token={reset_token}"
            )
            return True

        try:
            reset_link = f"https://mindflow.ai/reset-password?token={reset_token}"
            html_content = self._render_reset_email_html(reset_link, user_name)

            message = self._Mail(
                from_email=self.from_email,
                to_emails=to_email,
                subject="Reset Your MindFlow Password",
                html_content=html_content,
            )

            response = self._sg_client.send(message)
            return response.status_code in (200, 201, 202)
        except Exception as e:
            logger.error(f"Failed to send password reset email: {e}")
            return False

    def _render_reset_email_html(self, reset_link: str, user_name: str | None) -> str:
        """
        Render HTML email template for password reset.

        Args:
            reset_link: Password reset URL
            user_name: User's name (optional)

        Returns:
            HTML email content
        """
        greeting = f"Hi {user_name}," if user_name else "Hello,"

        return f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Reset Your Password</title>
</head>
<body style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Helvetica, Arial, sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: 0 auto; padding: 20px;">
    <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 30px; text-align: center; border-radius: 10px 10px 0 0;">
        <h1 style="color: white; margin: 0; font-size: 28px;">MindFlow</h1>
    </div>

    <div style="background: #ffffff; padding: 40px; border: 1px solid #e1e4e8; border-top: none; border-radius: 0 0 10px 10px;">
        <p style="font-size: 16px; margin-bottom: 20px;">{greeting}</p>

        <p style="font-size: 16px; margin-bottom: 20px;">
            We received a request to reset your password. Click the button below to create a new password:
        </p>

        <div style="text-align: center; margin: 30px 0;">
            <a href="{reset_link}"
               style="display: inline-block; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                      color: white; padding: 14px 28px; text-decoration: none; border-radius: 6px;
                      font-weight: 600; font-size: 16px;">
                Reset Password
            </a>
        </div>

        <p style="font-size: 14px; color: #586069; margin-top: 30px;">
            This link will expire in 1 hour. If you didn't request a password reset, you can safely ignore this email.
        </p>

        <p style="font-size: 14px; color: #586069; margin-top: 20px;">
            If the button doesn't work, copy and paste this link into your browser:<br>
            <a href="{reset_link}" style="color: #667eea; word-break: break-all;">{reset_link}</a>
        </p>

        <hr style="border: none; border-top: 1px solid #e1e4e8; margin: 30px 0;">

        <p style="font-size: 12px; color: #6a737d; text-align: center;">
            MindFlow - Intelligent Task Management<br>
            This is an automated message, please do not reply.
        </p>
    </div>
</body>
</html>
"""


class MockEmailService:
    """Mock email service for development and testing."""

    def __init__(self):
        """Initialize mock email service."""
        self.sent_emails: list[dict] = []

    async def send_password_reset_email(
        self, to_email: str, reset_token: str, user_name: str | None
    ) -> bool:
        """
        Mock sending password reset email (logs instead).

        Args:
            to_email: Recipient email address
            reset_token: Password reset token
            user_name: User's name (optional)

        Returns:
            Always returns True
        """
        reset_link = f"https://mindflow.ai/reset-password?token={reset_token}"

        email_data = {
            "to": to_email,
            "subject": "Reset Your MindFlow Password",
            "token": reset_token,
            "link": reset_link,
            "user_name": user_name,
        }

        self.sent_emails.append(email_data)

        logger.info(
            f"[MOCK EMAIL] Password reset email sent\n"
            f"To: {to_email}\n"
            f"User: {user_name or 'Unknown'}\n"
            f"Reset link: {reset_link}"
        )

        return True


def get_email_service() -> EmailServiceProtocol:
    """
    Get email service instance based on configuration.

    Returns:
        EmailServiceProtocol: Email service instance (SendGrid or Mock)
    """
    sendgrid_api_key = os.getenv("SENDGRID_API_KEY")

    if sendgrid_api_key:
        logger.info("Using SendGrid email service")
        return SendGridEmailService(api_key=sendgrid_api_key)
    else:
        logger.info("Using mock email service (SENDGRID_API_KEY not set)")
        return MockEmailService()
