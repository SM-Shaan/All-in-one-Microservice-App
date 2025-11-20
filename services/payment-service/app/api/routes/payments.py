"""
Payment Routes
==============

API endpoints for payment management.
"""

from datetime import datetime
from fastapi import APIRouter, HTTPException, Depends, status
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.models.schemas.payment_schemas import (
    CreatePaymentRequest,
    ProcessPaymentRequest,
    RefundPaymentRequest,
    CancelPaymentRequest,
    PaymentResponse,
    PaymentListResponse,
    RefundResponse,
    PaymentStatusResponse,
    PaymentMethodResponse,
    PaymentEvent
)
from app.models.domain.payment import Payment, PaymentMethod
from app.repositories.payment_repository import PaymentRepository
from app.core.stripe_service import stripe_service
from app.core.database import get_database
from shared.events import EventPublisher

router = APIRouter(prefix="/api/v1/payments", tags=["payments"])


# ============================================================================
# Dependencies
# ============================================================================

async def get_payment_repo(db: AsyncIOMotorDatabase = Depends(get_database)) -> PaymentRepository:
    """Get payment repository"""
    return PaymentRepository(db)


# ============================================================================
# Payment Endpoints
# ============================================================================

@router.post("", response_model=PaymentResponse, status_code=status.HTTP_201_CREATED)
async def create_payment(
    request: CreatePaymentRequest,
    repo: PaymentRepository = Depends(get_payment_repo)
):
    """
    Create a new payment.

    This creates a payment record and Stripe payment intent, but does not
    charge the card yet. Use the process_payment endpoint to complete the payment.
    """
    try:
        # Check if payment already exists for this order
        existing_payment = await repo.get_by_order_id(request.order_id)
        if existing_payment:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Payment already exists for order {request.order_id}"
            )

        # Create payment method with Stripe (tokenize card)
        stripe_payment_method = None
        if request.payment_method.stripe_token:
            # Use existing token
            payment_method_id = request.payment_method.stripe_token
        elif request.payment_method.card_number:
            # Create new payment method (tokenize card)
            stripe_payment_method = await stripe_service.create_payment_method(
                card_number=request.payment_method.card_number,
                exp_month=request.payment_method.exp_month,
                exp_year=request.payment_method.exp_year,
                cvv=request.payment_method.cvv
            )
            payment_method_id = stripe_payment_method["id"]
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Either stripe_token or card details must be provided"
            )

        # Create Stripe payment intent
        payment_intent = await stripe_service.create_payment_intent(
            amount=request.amount,
            currency=request.currency,
            payment_method_id=payment_method_id,
            description=request.description,
            metadata={
                "order_id": request.order_id,
                **(request.metadata or {})
            }
        )

        # Extract payment method details
        if stripe_payment_method:
            card_info = stripe_payment_method["card"]
        else:
            # Will be filled when payment is processed
            card_info = {"brand": None, "last4": None, "exp_month": None, "exp_year": None}

        # Create payment record
        payment = Payment(
            order_id=request.order_id,
            user_id="TODO",  # Get from JWT token
            amount=request.amount,
            currency=request.currency,
            status="pending",
            payment_method=PaymentMethod(
                type=request.payment_method.type,
                brand=card_info.get("brand"),
                last4=card_info.get("last4"),
                exp_month=card_info.get("exp_month"),
                exp_year=card_info.get("exp_year")
            ),
            stripe_payment_intent_id=payment_intent["id"],
            description=request.description,
            metadata=request.metadata
        )

        # Save to database
        payment = await repo.create(payment)

        # Publish event
        event = PaymentEvent(
            event_type="payment_created",
            payment_id=payment.id,
            order_id=payment.order_id,
            user_id=payment.user_id,
            amount=payment.amount,
            currency=payment.currency,
            status=payment.status
        )
        await EventPublisher.publish("payment-events", event.model_dump())

        # Return response
        return PaymentResponse(
            id=payment.id,
            order_id=payment.order_id,
            user_id=payment.user_id,
            amount=payment.amount,
            currency=payment.currency,
            status=payment.status,
            payment_method=PaymentMethodResponse(
                type=payment.payment_method.type,
                brand=payment.payment_method.brand,
                last4=payment.payment_method.last4,
                exp_month=payment.payment_method.exp_month,
                exp_year=payment.payment_method.exp_year
            ),
            description=payment.description,
            created_at=payment.created_at,
            updated_at=payment.updated_at,
            processed_at=payment.processed_at,
            failed_at=payment.failed_at,
            failure_message=payment.failure_message
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create payment: {str(e)}"
        )


@router.post("/{payment_id}/process", response_model=PaymentStatusResponse)
async def process_payment(
    payment_id: str,
    repo: PaymentRepository = Depends(get_payment_repo)
):
    """
    Process a payment (charge the card).

    This confirms the Stripe payment intent and charges the card.
    """
    try:
        # Get payment
        payment = await repo.get_by_id(payment_id)
        if not payment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Payment {payment_id} not found"
            )

        # Check status
        if payment.status != "pending":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Payment cannot be processed. Current status: {payment.status}"
            )

        # Confirm payment intent with Stripe
        result = await stripe_service.confirm_payment_intent(
            payment.stripe_payment_intent_id
        )

        # Update payment status based on Stripe response
        if result["status"] == "succeeded":
            await repo.update_status(payment_id, "succeeded")

            # Update charge ID
            if result["charges"]:
                charge_id = result["charges"][0]["id"]
                await repo.update_stripe_ids(payment_id, charge_id=charge_id)

            # Publish event
            event = PaymentEvent(
                event_type="payment_succeeded",
                payment_id=payment_id,
                order_id=payment.order_id,
                user_id=payment.user_id,
                amount=payment.amount,
                currency=payment.currency,
                status="succeeded"
            )
            await EventPublisher.publish("payment-events", event.model_dump())

            return PaymentStatusResponse(
                payment_id=payment_id,
                status="succeeded",
                message="Payment processed successfully"
            )

        elif result["status"] == "requires_action":
            # 3D Secure or other verification needed
            await repo.update_status(payment_id, "requires_action")
            return PaymentStatusResponse(
                payment_id=payment_id,
                status="requires_action",
                message="Additional verification required"
            )

        else:
            # Payment failed
            await repo.update_status(
                payment_id,
                "failed",
                {"message": "Payment failed"}
            )

            # Publish event
            event = PaymentEvent(
                event_type="payment_failed",
                payment_id=payment_id,
                order_id=payment.order_id,
                user_id=payment.user_id,
                amount=payment.amount,
                currency=payment.currency,
                status="failed"
            )
            await EventPublisher.publish("payment-events", event.model_dump())

            return PaymentStatusResponse(
                payment_id=payment_id,
                status="failed",
                message="Payment failed"
            )

    except HTTPException:
        raise
    except Exception as e:
        # Update status to failed
        await repo.update_status(
            payment_id,
            "failed",
            {"message": str(e)}
        )

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process payment: {str(e)}"
        )


@router.post("/{payment_id}/refund", response_model=RefundResponse)
async def refund_payment(
    payment_id: str,
    request: RefundPaymentRequest,
    repo: PaymentRepository = Depends(get_payment_repo)
):
    """
    Refund a payment (full or partial).
    """
    try:
        # Get payment
        payment = await repo.get_by_id(payment_id)
        if not payment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Payment {payment_id} not found"
            )

        # Check status
        if payment.status != "succeeded":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Only succeeded payments can be refunded. Current status: {payment.status}"
            )

        # Refund with Stripe
        refund_result = await stripe_service.refund_payment(
            charge_id=payment.stripe_charge_id,
            amount=request.amount,
            reason=request.reason
        )

        # Update payment status
        await repo.update_status(
            payment_id,
            "refunded",
            {
                "amount": refund_result["amount"],
                "reason": request.reason
            }
        )

        # Publish event
        event = PaymentEvent(
            event_type="payment_refunded",
            payment_id=payment_id,
            order_id=payment.order_id,
            user_id=payment.user_id,
            amount=refund_result["amount"],
            currency=payment.currency,
            status="refunded",
            metadata={"reason": request.reason}
        )
        await EventPublisher.publish("payment-events", event.model_dump())

        return RefundResponse(
            payment_id=payment_id,
            refund_amount=refund_result["amount"],
            refunded_at=datetime.utcnow(),
            reason=request.reason,
            status="refunded"
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to refund payment: {str(e)}"
        )


@router.post("/{payment_id}/cancel", response_model=PaymentStatusResponse)
async def cancel_payment(
    payment_id: str,
    request: CancelPaymentRequest,
    repo: PaymentRepository = Depends(get_payment_repo)
):
    """
    Cancel a payment (before processing).
    """
    try:
        # Get payment
        payment = await repo.get_by_id(payment_id)
        if not payment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Payment {payment_id} not found"
            )

        # Check status
        if payment.status not in ["pending", "requires_action"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Payment cannot be cancelled. Current status: {payment.status}"
            )

        # Cancel with Stripe
        await stripe_service.cancel_payment_intent(
            payment.stripe_payment_intent_id
        )

        # Update status
        await repo.update_status(payment_id, "cancelled")

        # Publish event
        event = PaymentEvent(
            event_type="payment_cancelled",
            payment_id=payment_id,
            order_id=payment.order_id,
            user_id=payment.user_id,
            amount=payment.amount,
            currency=payment.currency,
            status="cancelled",
            metadata={"reason": request.reason}
        )
        await EventPublisher.publish("payment-events", event.model_dump())

        return PaymentStatusResponse(
            payment_id=payment_id,
            status="cancelled",
            message="Payment cancelled successfully"
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to cancel payment: {str(e)}"
        )


@router.get("/{payment_id}", response_model=PaymentResponse)
async def get_payment(
    payment_id: str,
    repo: PaymentRepository = Depends(get_payment_repo)
):
    """Get payment by ID"""
    payment = await repo.get_by_id(payment_id)
    if not payment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Payment {payment_id} not found"
        )

    return PaymentResponse(
        id=payment.id,
        order_id=payment.order_id,
        user_id=payment.user_id,
        amount=payment.amount,
        currency=payment.currency,
        status=payment.status,
        payment_method=PaymentMethodResponse(
            type=payment.payment_method.type,
            brand=payment.payment_method.brand,
            last4=payment.payment_method.last4,
            exp_month=payment.payment_method.exp_month,
            exp_year=payment.payment_method.exp_year
        ),
        description=payment.description,
        created_at=payment.created_at,
        updated_at=payment.updated_at,
        processed_at=payment.processed_at,
        failed_at=payment.failed_at,
        failure_message=payment.failure_message
    )


@router.get("/order/{order_id}", response_model=PaymentResponse)
async def get_payment_by_order(
    order_id: str,
    repo: PaymentRepository = Depends(get_payment_repo)
):
    """Get payment by order ID"""
    payment = await repo.get_by_order_id(order_id)
    if not payment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Payment for order {order_id} not found"
        )

    return PaymentResponse(
        id=payment.id,
        order_id=payment.order_id,
        user_id=payment.user_id,
        amount=payment.amount,
        currency=payment.currency,
        status=payment.status,
        payment_method=PaymentMethodResponse(
            type=payment.payment_method.type,
            brand=payment.payment_method.brand,
            last4=payment.payment_method.last4,
            exp_month=payment.payment_method.exp_month,
            exp_year=payment.payment_method.exp_year
        ),
        description=payment.description,
        created_at=payment.created_at,
        updated_at=payment.updated_at,
        processed_at=payment.processed_at,
        failed_at=payment.failed_at,
        failure_message=payment.failure_message
    )


@router.get("/user/{user_id}", response_model=PaymentListResponse)
async def get_user_payments(
    user_id: str,
    page: int = 1,
    page_size: int = 10,
    repo: PaymentRepository = Depends(get_payment_repo)
):
    """Get all payments for a user"""
    skip = (page - 1) * page_size
    payments = await repo.get_by_user_id(user_id, skip=skip, limit=page_size)
    total = await repo.count_by_user_id(user_id)

    payment_responses = [
        PaymentResponse(
            id=p.id,
            order_id=p.order_id,
            user_id=p.user_id,
            amount=p.amount,
            currency=p.currency,
            status=p.status,
            payment_method=PaymentMethodResponse(
                type=p.payment_method.type,
                brand=p.payment_method.brand,
                last4=p.payment_method.last4,
                exp_month=p.payment_method.exp_month,
                exp_year=p.payment_method.exp_year
            ),
            description=p.description,
            created_at=p.created_at,
            updated_at=p.updated_at,
            processed_at=p.processed_at,
            failed_at=p.failed_at,
            failure_message=p.failure_message
        )
        for p in payments
    ]

    return PaymentListResponse(
        payments=payment_responses,
        total=total,
        page=page,
        page_size=page_size
    )
