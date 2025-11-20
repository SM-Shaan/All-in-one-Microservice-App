"""
Email Service
=============

Service for sending emails via SMTP or SendGrid.
"""

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional, Dict, Any

from app.core.config import settings


class EmailService:
    """
    Service for sending emails.

    Supports both SMTP and SendGrid.
    """

    def __init__(self):
        """Initialize email service"""
        self.from_email = settings.smtp_from_email
        self.from_name = settings.smtp_from_name

    async def send_email(
        self,
        to_email: str,
        subject: str,
        body: str,
        html_body: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Send an email.

        Args:
            to_email: Recipient email
            subject: Email subject
            body: Plain text body
            html_body: HTML body (optional)
            metadata: Additional metadata

        Returns:
            Result dictionary with status and message_id

        Raises:
            Exception: If sending fails
        """
        if settings.sendgrid_api_key:
            return await self._send_via_sendgrid(
                to_email, subject, body, html_body, metadata
            )
        else:
            return await self._send_via_smtp(
                to_email, subject, body, html_body
            )

    async def _send_via_smtp(
        self,
        to_email: str,
        subject: str,
        body: str,
        html_body: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Send email via SMTP.

        Args:
            to_email: Recipient email
            subject: Email subject
            body: Plain text body
            html_body: HTML body (optional)

        Returns:
            Result dictionary
        """
        try:
            # Create message
            msg = MIMEMultipart('alternative')
            msg['From'] = f"{self.from_name} <{self.from_email}>"
            msg['To'] = to_email
            msg['Subject'] = subject

            # Add plain text part
            text_part = MIMEText(body, 'plain')
            msg.attach(text_part)

            # Add HTML part if provided
            if html_body:
                html_part = MIMEText(html_body, 'html')
                msg.attach(html_part)

            # Send email
            with smtplib.SMTP(settings.smtp_host, settings.smtp_port) as server:
                server.starttls()
                if settings.smtp_username and settings.smtp_password:
                    server.login(settings.smtp_username, settings.smtp_password)
                server.send_message(msg)

            return {
                "success": True,
                "provider": "smtp",
                "message_id": None,  # SMTP doesn't return message ID
                "message": "Email sent successfully via SMTP"
            }

        except Exception as e:
            return {
                "success": False,
                "provider": "smtp",
                "error": str(e),
                "message": f"Failed to send email via SMTP: {str(e)}"
            }

    async def _send_via_sendgrid(
        self,
        to_email: str,
        subject: str,
        body: str,
        html_body: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Send email via SendGrid.

        Args:
            to_email: Recipient email
            subject: Email subject
            body: Plain text body
            html_body: HTML body (optional)
            metadata: Additional metadata

        Returns:
            Result dictionary
        """
        try:
            # Import SendGrid
            from sendgrid import SendGridAPIClient
            from sendgrid.helpers.mail import Mail, Content

            # Create message
            message = Mail(
                from_email=self.from_email,
                to_emails=to_email,
                subject=subject,
                plain_text_content=body,
                html_content=html_body
            )

            # Add custom args (metadata)
            if metadata:
                for key, value in metadata.items():
                    message.custom_arg = {key: str(value)}

            # Send email
            sg = SendGridAPIClient(settings.sendgrid_api_key)
            response = sg.send(message)

            return {
                "success": True,
                "provider": "sendgrid",
                "message_id": response.headers.get('X-Message-Id'),
                "status_code": response.status_code,
                "message": "Email sent successfully via SendGrid"
            }

        except Exception as e:
            return {
                "success": False,
                "provider": "sendgrid",
                "error": str(e),
                "message": f"Failed to send email via SendGrid: {str(e)}"
            }

    async def send_bulk_emails(
        self,
        recipients: list,
        subject: str,
        body: str,
        html_body: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Send bulk emails.

        Args:
            recipients: List of recipient emails
            subject: Email subject
            body: Plain text body
            html_body: HTML body (optional)

        Returns:
            Result dictionary with success/failure counts
        """
        results = {
            "total": len(recipients),
            "succeeded": 0,
            "failed": 0,
            "failures": []
        }

        for recipient in recipients:
            try:
                result = await self.send_email(
                    to_email=recipient,
                    subject=subject,
                    body=body,
                    html_body=html_body
                )

                if result["success"]:
                    results["succeeded"] += 1
                else:
                    results["failed"] += 1
                    results["failures"].append({
                        "recipient": recipient,
                        "error": result.get("error")
                    })

            except Exception as e:
                results["failed"] += 1
                results["failures"].append({
                    "recipient": recipient,
                    "error": str(e)
                })

        return results


# Singleton instance
email_service = EmailService()
