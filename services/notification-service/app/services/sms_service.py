"""
SMS Service
===========

Service for sending SMS via Twilio.
"""

from typing import Optional, Dict, Any

from app.core.config import settings


class SMSService:
    """
    Service for sending SMS messages.

    Uses Twilio for SMS delivery.
    """

    def __init__(self):
        """Initialize SMS service"""
        self.from_phone = settings.twilio_phone_number

    async def send_sms(
        self,
        to_phone: str,
        body: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Send an SMS message.

        Args:
            to_phone: Recipient phone number
            body: SMS body
            metadata: Additional metadata

        Returns:
            Result dictionary with status and message_sid

        Raises:
            Exception: If sending fails
        """
        try:
            # Import Twilio
            from twilio.rest import Client

            # Create Twilio client
            client = Client(
                settings.twilio_account_sid,
                settings.twilio_auth_token
            )

            # Send SMS
            message = client.messages.create(
                body=body,
                from_=self.from_phone,
                to=to_phone
            )

            return {
                "success": True,
                "provider": "twilio",
                "message_sid": message.sid,
                "status": message.status,
                "message": "SMS sent successfully"
            }

        except Exception as e:
            return {
                "success": False,
                "provider": "twilio",
                "error": str(e),
                "message": f"Failed to send SMS: {str(e)}"
            }

    async def send_bulk_sms(
        self,
        recipients: list,
        body: str
    ) -> Dict[str, Any]:
        """
        Send bulk SMS messages.

        Args:
            recipients: List of phone numbers
            body: SMS body

        Returns:
            Result dictionary with success/failure counts
        """
        results = {
            "total": len(recipients),
            "succeeded": 0,
            "failed": 0,
            "failures": []
        }

        for phone in recipients:
            try:
                result = await self.send_sms(
                    to_phone=phone,
                    body=body
                )

                if result["success"]:
                    results["succeeded"] += 1
                else:
                    results["failed"] += 1
                    results["failures"].append({
                        "phone": phone,
                        "error": result.get("error")
                    })

            except Exception as e:
                results["failed"] += 1
                results["failures"].append({
                    "phone": phone,
                    "error": str(e)
                })

        return results

    async def check_message_status(self, message_sid: str) -> Dict[str, Any]:
        """
        Check SMS message status.

        Args:
            message_sid: Twilio message SID

        Returns:
            Message status information
        """
        try:
            from twilio.rest import Client

            client = Client(
                settings.twilio_account_sid,
                settings.twilio_auth_token
            )

            message = client.messages(message_sid).fetch()

            return {
                "success": True,
                "message_sid": message.sid,
                "status": message.status,
                "to": message.to,
                "from": message.from_,
                "date_sent": message.date_sent.isoformat() if message.date_sent else None,
                "error_code": message.error_code,
                "error_message": message.error_message
            }

        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": f"Failed to check message status: {str(e)}"
            }


# Singleton instance
sms_service = SMSService()
