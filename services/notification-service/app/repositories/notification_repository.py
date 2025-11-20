"""
Notification Repository
=======================

Repository for notification data access.
"""

from datetime import datetime
from typing import Optional, List
from motor.motor_asyncio import AsyncIOMotorDatabase
from bson import ObjectId

from app.models.domain.notification import Notification, NotificationTemplate


class NotificationRepository:
    """Repository for notification operations"""

    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db
        self.collection = db.notifications
        self.template_collection = db.notification_templates

    async def create(self, notification: Notification) -> Notification:
        """Create a new notification"""
        notification_dict = notification.model_dump(by_alias=True, exclude={"id"})
        result = await self.collection.insert_one(notification_dict)
        notification.id = str(result.inserted_id)
        return notification

    async def get_by_id(self, notification_id: str) -> Optional[Notification]:
        """Get notification by ID"""
        try:
            doc = await self.collection.find_one({"_id": ObjectId(notification_id)})
            if doc:
                doc["_id"] = str(doc["_id"])
                return Notification(**doc)
            return None
        except Exception:
            return None

    async def get_by_user_id(
        self,
        user_id: str,
        skip: int = 0,
        limit: int = 10
    ) -> List[Notification]:
        """Get notifications by user ID"""
        cursor = self.collection.find(
            {"recipient.user_id": user_id}
        ).skip(skip).limit(limit).sort("created_at", -1)

        notifications = []
        async for doc in cursor:
            doc["_id"] = str(doc["_id"])
            notifications.append(Notification(**doc))
        return notifications

    async def update_status(
        self,
        notification_id: str,
        status: str,
        error_message: Optional[str] = None,
        provider_id: Optional[str] = None,
        provider_response: Optional[dict] = None
    ) -> bool:
        """Update notification status"""
        update_data = {
            "status": status,
            "updated_at": datetime.utcnow()
        }

        if status == "sent":
            update_data["sent_at"] = datetime.utcnow()
        elif status == "failed":
            update_data["failed_at"] = datetime.utcnow()
            if error_message:
                update_data["error_message"] = error_message

        if provider_id:
            update_data["provider_id"] = provider_id
        if provider_response:
            update_data["provider_response"] = provider_response

        result = await self.collection.update_one(
            {"_id": ObjectId(notification_id)},
            {"$set": update_data}
        )

        return result.modified_count > 0

    async def increment_retry_count(self, notification_id: str) -> bool:
        """Increment retry count"""
        result = await self.collection.update_one(
            {"_id": ObjectId(notification_id)},
            {"$inc": {"retry_count": 1}}
        )
        return result.modified_count > 0

    async def count_by_user_id(self, user_id: str) -> int:
        """Count notifications by user ID"""
        return await self.collection.count_documents({"recipient.user_id": user_id})

    # Template methods
    async def create_template(self, template: NotificationTemplate) -> NotificationTemplate:
        """Create a notification template"""
        template_dict = template.model_dump(by_alias=True, exclude={"id"})
        result = await self.template_collection.insert_one(template_dict)
        template.id = str(result.inserted_id)
        return template

    async def get_template_by_name(self, name: str) -> Optional[NotificationTemplate]:
        """Get template by name"""
        doc = await self.template_collection.find_one({"name": name})
        if doc:
            doc["_id"] = str(doc["_id"])
            return NotificationTemplate(**doc)
        return None

    async def list_templates(self, type: Optional[str] = None) -> List[NotificationTemplate]:
        """List all templates"""
        query = {"type": type} if type else {}
        cursor = self.template_collection.find(query).sort("name", 1)

        templates = []
        async for doc in cursor:
            doc["_id"] = str(doc["_id"])
            templates.append(NotificationTemplate(**doc))
        return templates
