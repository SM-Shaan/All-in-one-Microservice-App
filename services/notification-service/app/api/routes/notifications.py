"""
Notification Routes
===================

API endpoints for notification management.
"""

from datetime import datetime
from fastapi import APIRouter, HTTPException, Depends, status
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.models.schemas.notification_schemas import (
    SendEmailRequest,
    SendSMSRequest,
    SendNotificationRequest,
    NotificationResponse,
    NotificationListResponse,
    NotificationStatusResponse,
    RecipientResponse
)
from app.models.domain.notification import Notification, NotificationRecipient
from app.repositories.notification_repository import NotificationRepository
from app.services.email_service import email_service
from app.services.sms_service import sms_service
from app.core.database import get_database
from shared.events import EventPublisher

router = APIRouter(prefix="/api/v1/notifications", tags=["notifications"])


async def get_notification_repo(db: AsyncIOMotorDatabase = Depends(get_database)) -> NotificationRepository:
    """Get notification repository"""
    return NotificationRepository(db)


@router.post("/email", response_model=NotificationResponse, status_code=status.HTTP_201_CREATED)
async def send_email(
    request: SendEmailRequest,
    repo: NotificationRepository = Depends(get_notification_repo)
):
    """Send an email notification"""
    try:
        # Create notification record
        notification = Notification(
            type="email",
            channel="smtp",
            recipient=NotificationRecipient(**request.recipient.model_dump()),
            subject=request.subject,
            body=request.body,
            html_body=request.html_body,
            status="pending",
            metadata=request.metadata
        )

        notification = await repo.create(notification)

        # Send email
        result = await email_service.send_email(
            to_email=request.recipient.email,
            subject=request.subject,
            body=request.body,
            html_body=request.html_body,
            metadata=request.metadata
        )

        # Update status
        if result["success"]:
            await repo.update_status(
                notification.id,
                "sent",
                provider_id=result.get("message_id"),
                provider_response=result
            )
            status_value = "sent"
        else:
            await repo.update_status(
                notification.id,
                "failed",
                error_message=result.get("error"),
                provider_response=result
            )
            status_value = "failed"

        # Publish event
        from app.models.schemas.notification_schemas import NotificationEvent
        event = NotificationEvent(
            event_type=f"notification_{status_value}",
            notification_id=notification.id,
            type="email",
            recipient=RecipientResponse(**request.recipient.model_dump()),
            status=status_value
        )
        await EventPublisher.publish("notification-events", event.model_dump())

        # Return response
        updated_notification = await repo.get_by_id(notification.id)
        return NotificationResponse(
            id=updated_notification.id,
            type=updated_notification.type,
            channel=updated_notification.channel,
            recipient=RecipientResponse(**updated_notification.recipient.model_dump()),
            subject=updated_notification.subject,
            status=updated_notification.status,
            created_at=updated_notification.created_at,
            sent_at=updated_notification.sent_at,
            failed_at=updated_notification.failed_at,
            error_message=updated_notification.error_message,
            retry_count=updated_notification.retry_count
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to send email: {str(e)}"
        )


@router.post("/sms", response_model=NotificationResponse, status_code=status.HTTP_201_CREATED)
async def send_sms(
    request: SendSMSRequest,
    repo: NotificationRepository = Depends(get_notification_repo)
):
    """Send an SMS notification"""
    try:
        # Create notification record
        notification = Notification(
            type="sms",
            channel="twilio",
            recipient=NotificationRecipient(**request.recipient.model_dump()),
            body=request.body,
            status="pending",
            metadata=request.metadata
        )

        notification = await repo.create(notification)

        # Send SMS
        result = await sms_service.send_sms(
            to_phone=request.recipient.phone,
            body=request.body,
            metadata=request.metadata
        )

        # Update status
        if result["success"]:
            await repo.update_status(
                notification.id,
                "sent",
                provider_id=result.get("message_sid"),
                provider_response=result
            )
            status_value = "sent"
        else:
            await repo.update_status(
                notification.id,
                "failed",
                error_message=result.get("error"),
                provider_response=result
            )
            status_value = "failed"

        # Return response
        updated_notification = await repo.get_by_id(notification.id)
        return NotificationResponse(
            id=updated_notification.id,
            type=updated_notification.type,
            channel=updated_notification.channel,
            recipient=RecipientResponse(**updated_notification.recipient.model_dump()),
            subject=updated_notification.subject,
            status=updated_notification.status,
            created_at=updated_notification.created_at,
            sent_at=updated_notification.sent_at,
            failed_at=updated_notification.failed_at,
            error_message=updated_notification.error_message,
            retry_count=updated_notification.retry_count
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to send SMS: {str(e)}"
        )


@router.get("/{notification_id}", response_model=NotificationResponse)
async def get_notification(
    notification_id: str,
    repo: NotificationRepository = Depends(get_notification_repo)
):
    """Get notification by ID"""
    notification = await repo.get_by_id(notification_id)
    if not notification:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Notification {notification_id} not found"
        )

    return NotificationResponse(
        id=notification.id,
        type=notification.type,
        channel=notification.channel,
        recipient=RecipientResponse(**notification.recipient.model_dump()),
        subject=notification.subject,
        status=notification.status,
        created_at=notification.created_at,
        sent_at=notification.sent_at,
        failed_at=notification.failed_at,
        error_message=notification.error_message,
        retry_count=notification.retry_count
    )


@router.get("/user/{user_id}", response_model=NotificationListResponse)
async def get_user_notifications(
    user_id: str,
    page: int = 1,
    page_size: int = 10,
    repo: NotificationRepository = Depends(get_notification_repo)
):
    """Get all notifications for a user"""
    skip = (page - 1) * page_size
    notifications = await repo.get_by_user_id(user_id, skip=skip, limit=page_size)
    total = await repo.count_by_user_id(user_id)

    notification_responses = [
        NotificationResponse(
            id=n.id,
            type=n.type,
            channel=n.channel,
            recipient=RecipientResponse(**n.recipient.model_dump()),
            subject=n.subject,
            status=n.status,
            created_at=n.created_at,
            sent_at=n.sent_at,
            failed_at=n.failed_at,
            error_message=n.error_message,
            retry_count=n.retry_count
        )
        for n in notifications
    ]

    return NotificationListResponse(
        notifications=notification_responses,
        total=total,
        page=page,
        page_size=page_size
    )
