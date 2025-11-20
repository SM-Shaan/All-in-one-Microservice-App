"""
Stripe Service
==============

Service for interacting with Stripe API.
"""

import stripe
from typing import Optional, Dict, Any
from .config import settings
import uuid
import time
import random
from datetime import datetime


class StripeService:
    """
    Service for processing payments with Stripe.

    This service handles:
    - Payment intent creation
    - Payment confirmation
    - Refunds
    - Webhooks
    """

    def __init__(self):
        """Initialize Stripe service"""
        if not settings.stripe_mock_mode:
            stripe.api_key = settings.stripe_api_key
        self.currency = settings.stripe_currency
        self.mock_mode = settings.stripe_mock_mode
        self.payment_success_rate = 1.0  # 100% success rate for testing

    async def create_payment_intent(
        self,
        amount: float,
        currency: str,
        payment_method_id: Optional[str] = None,
        description: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Create a Stripe payment intent.

        Args:
            amount: Payment amount in dollars
            currency: Currency code (e.g., 'usd')
            payment_method_id: Stripe payment method ID
            description: Payment description
            metadata: Additional metadata

        Returns:
            Payment intent data from Stripe

        Raises:
            stripe.error.StripeError: If Stripe API fails
        """
        # Mock mode - simulate payment processing
        if self.mock_mode:
            return await self._create_mock_payment_intent(
                amount, currency, payment_method_id, description, metadata
            )

        try:
            # Convert amount to cents (Stripe uses smallest currency unit)
            amount_cents = int(amount * 100)

            # Create payment intent
            payment_intent = stripe.PaymentIntent.create(
                amount=amount_cents,
                currency=currency,
                payment_method=payment_method_id,
                description=description,
                metadata=metadata or {},
                # Automatic payment confirmation if payment method provided
                confirm=payment_method_id is not None,
                # Return URL for 3D Secure (if needed)
                return_url="https://example.com/payment/return"
            )

            return {
                "id": payment_intent.id,
                "status": payment_intent.status,
                "amount": amount,
                "currency": currency,
                "client_secret": payment_intent.client_secret,
                "charges": payment_intent.charges.data if payment_intent.charges else []
            }

        except stripe.error.CardError as e:
            # Card declined
            raise Exception(f"Card declined: {e.user_message}")
        except stripe.error.StripeError as e:
            # Stripe error
            raise Exception(f"Stripe error: {str(e)}")

    async def confirm_payment_intent(
        self,
        payment_intent_id: str
    ) -> Dict[str, Any]:
        """
        Confirm a payment intent.

        Args:
            payment_intent_id: Stripe payment intent ID

        Returns:
            Updated payment intent data
        """
        # Mock mode - simulate successful confirmation
        if self.mock_mode:
            # Simulate processing delay
            time.sleep(random.uniform(0.2, 0.5))

            charge_id = f"ch_mock_{uuid.uuid4().hex[:24]}"
            return {
                "id": payment_intent_id,
                "status": "succeeded",
                "amount": 0,  # Will be updated from database
                "currency": "usd",
                "charges": [{
                    "id": charge_id,
                    "status": "succeeded",
                    "created": int(datetime.utcnow().timestamp())
                }]
            }

        try:
            payment_intent = stripe.PaymentIntent.confirm(payment_intent_id)

            return {
                "id": payment_intent.id,
                "status": payment_intent.status,
                "amount": payment_intent.amount / 100,
                "currency": payment_intent.currency,
                "charges": payment_intent.charges.data if payment_intent.charges else []
            }

        except stripe.error.StripeError as e:
            raise Exception(f"Failed to confirm payment: {str(e)}")

    async def create_payment_method(
        self,
        card_number: str,
        exp_month: int,
        exp_year: int,
        cvv: str
    ) -> Dict[str, Any]:
        """
        Create a payment method (tokenize card).

        NOTE: In production, card tokenization should happen on the client side
        for PCI compliance. This is for development/testing only.

        Args:
            card_number: Card number
            exp_month: Expiration month
            exp_year: Expiration year
            cvv: CVV code

        Returns:
            Payment method data
        """
        # Mock mode - return mock payment method
        if self.mock_mode:
            return {
                "id": f"pm_mock_{uuid.uuid4().hex[:24]}",
                "type": "card",
                "card": {
                    "brand": "visa",
                    "last4": card_number[-4:] if len(card_number) >= 4 else "4242",
                    "exp_month": exp_month,
                    "exp_year": exp_year
                }
            }

        try:
            payment_method = stripe.PaymentMethod.create(
                type="card",
                card={
                    "number": card_number,
                    "exp_month": exp_month,
                    "exp_year": exp_year,
                    "cvc": cvv
                }
            )

            return {
                "id": payment_method.id,
                "type": payment_method.type,
                "card": {
                    "brand": payment_method.card.brand,
                    "last4": payment_method.card.last4,
                    "exp_month": payment_method.card.exp_month,
                    "exp_year": payment_method.card.exp_year
                }
            }

        except stripe.error.StripeError as e:
            raise Exception(f"Failed to create payment method: {str(e)}")

    async def refund_payment(
        self,
        charge_id: str,
        amount: Optional[float] = None,
        reason: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Refund a payment.

        Args:
            charge_id: Stripe charge ID
            amount: Refund amount (None for full refund)
            reason: Refund reason

        Returns:
            Refund data
        """
        # Mock mode - simulate successful refund
        if self.mock_mode:
            time.sleep(random.uniform(0.1, 0.3))

            refund_id = f"re_mock_{uuid.uuid4().hex[:24]}"
            return {
                "id": refund_id,
                "amount": amount if amount else 0,
                "currency": "usd",
                "status": "succeeded",
                "reason": reason
            }

        try:
            refund_params = {
                "charge": charge_id
            }

            if amount is not None:
                refund_params["amount"] = int(amount * 100)

            if reason:
                refund_params["reason"] = reason

            refund = stripe.Refund.create(**refund_params)

            return {
                "id": refund.id,
                "amount": refund.amount / 100,
                "currency": refund.currency,
                "status": refund.status,
                "reason": refund.reason
            }

        except stripe.error.StripeError as e:
            raise Exception(f"Failed to refund payment: {str(e)}")

    async def cancel_payment_intent(
        self,
        payment_intent_id: str
    ) -> Dict[str, Any]:
        """
        Cancel a payment intent.

        Args:
            payment_intent_id: Stripe payment intent ID

        Returns:
            Cancelled payment intent data
        """
        try:
            payment_intent = stripe.PaymentIntent.cancel(payment_intent_id)

            return {
                "id": payment_intent.id,
                "status": payment_intent.status,
                "cancellation_reason": payment_intent.cancellation_reason
            }

        except stripe.error.StripeError as e:
            raise Exception(f"Failed to cancel payment: {str(e)}")

    async def retrieve_payment_intent(
        self,
        payment_intent_id: str
    ) -> Dict[str, Any]:
        """
        Retrieve payment intent details.

        Args:
            payment_intent_id: Stripe payment intent ID

        Returns:
            Payment intent data
        """
        try:
            payment_intent = stripe.PaymentIntent.retrieve(payment_intent_id)

            return {
                "id": payment_intent.id,
                "status": payment_intent.status,
                "amount": payment_intent.amount / 100,
                "currency": payment_intent.currency,
                "charges": payment_intent.charges.data if payment_intent.charges else []
            }

        except stripe.error.StripeError as e:
            raise Exception(f"Failed to retrieve payment: {str(e)}")

    def construct_webhook_event(
        self,
        payload: bytes,
        sig_header: str
    ) -> stripe.Event:
        """
        Construct and verify a webhook event from Stripe.

        Args:
            payload: Request payload
            sig_header: Stripe signature header

        Returns:
            Verified Stripe event

        Raises:
            ValueError: If signature verification fails
        """
        try:
            event = stripe.Webhook.construct_event(
                payload,
                sig_header,
                settings.stripe_webhook_secret
            )
            return event

        except ValueError as e:
            raise ValueError(f"Invalid webhook signature: {str(e)}")

    # ========================================================================
    # Mock Payment Methods (for testing without Stripe)
    # ========================================================================

    async def _create_mock_payment_intent(
        self,
        amount: float,
        currency: str,
        payment_method_id: Optional[str] = None,
        description: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Create a mock payment intent for testing.
        Simulates payment processing with configurable success rate.
        """
        # Simulate processing delay (200-800ms)
        delay = random.uniform(0.2, 0.8)
        time.sleep(delay)

        # Validate amount
        if amount <= 0:
            raise Exception("Invalid payment amount")

        # Generate mock IDs
        intent_id = f"pi_mock_{uuid.uuid4().hex[:24]}"
        client_secret = f"{intent_id}_secret_{uuid.uuid4().hex[:16]}"

        # Simulate payment success/failure based on success rate
        is_success = random.random() <= self.payment_success_rate

        if is_success:
            status = "succeeded"
            charge_id = f"ch_mock_{uuid.uuid4().hex[:24]}"
            charges = [{
                "id": charge_id,
                "amount": int(amount * 100),
                "currency": currency,
                "status": "succeeded",
                "created": int(datetime.utcnow().timestamp())
            }]
        else:
            status = "requires_payment_method"
            charges = []

        return {
            "id": intent_id,
            "status": status,
            "amount": amount,
            "currency": currency,
            "client_secret": client_secret,
            "charges": charges
        }


# Singleton instance
stripe_service = StripeService()
