"""
Payment Repository
==================

Repository for payment data access.
"""

from datetime import datetime
from typing import Optional, List
from motor.motor_asyncio import AsyncIOMotorDatabase
from bson import ObjectId

from app.models.domain.payment import Payment, PaymentHistory


class PaymentRepository:
    """
    Repository for payment operations.

    Handles all database interactions for payments.
    """

    def __init__(self, db: AsyncIOMotorDatabase):
        """
        Initialize repository.

        Args:
            db: MongoDB database instance
        """
        self.db = db
        self.collection = db.payments
        self.history_collection = db.payment_history

    async def create(self, payment: Payment) -> Payment:
        """
        Create a new payment.

        Args:
            payment: Payment to create

        Returns:
            Created payment with ID
        """
        payment_dict = payment.model_dump(by_alias=True, exclude={"id"})
        result = await self.collection.insert_one(payment_dict)
        payment.id = str(result.inserted_id)

        # Add to history
        await self._add_history(
            payment_id=payment.id,
            status=payment.status,
            details={"action": "created"}
        )

        return payment

    async def get_by_id(self, payment_id: str) -> Optional[Payment]:
        """
        Get payment by ID.

        Args:
            payment_id: Payment ID

        Returns:
            Payment or None
        """
        try:
            doc = await self.collection.find_one({"_id": ObjectId(payment_id)})
            if doc:
                doc["_id"] = str(doc["_id"])
                return Payment(**doc)
            return None
        except Exception:
            return None

    async def get_by_order_id(self, order_id: str) -> Optional[Payment]:
        """
        Get payment by order ID.

        Args:
            order_id: Order ID

        Returns:
            Payment or None
        """
        doc = await self.collection.find_one({"order_id": order_id})
        if doc:
            doc["_id"] = str(doc["_id"])
            return Payment(**doc)
        return None

    async def get_by_user_id(
        self,
        user_id: str,
        skip: int = 0,
        limit: int = 10
    ) -> List[Payment]:
        """
        Get payments by user ID.

        Args:
            user_id: User ID
            skip: Number to skip
            limit: Max results

        Returns:
            List of payments
        """
        cursor = self.collection.find({"user_id": user_id}).skip(skip).limit(limit).sort("created_at", -1)
        payments = []
        async for doc in cursor:
            doc["_id"] = str(doc["_id"])
            payments.append(Payment(**doc))
        return payments

    async def get_by_stripe_payment_intent_id(
        self,
        payment_intent_id: str
    ) -> Optional[Payment]:
        """
        Get payment by Stripe payment intent ID.

        Args:
            payment_intent_id: Stripe payment intent ID

        Returns:
            Payment or None
        """
        doc = await self.collection.find_one({"stripe_payment_intent_id": payment_intent_id})
        if doc:
            doc["_id"] = str(doc["_id"])
            return Payment(**doc)
        return None

    async def update_status(
        self,
        payment_id: str,
        status: str,
        details: Optional[dict] = None
    ) -> bool:
        """
        Update payment status.

        Args:
            payment_id: Payment ID
            status: New status
            details: Additional details

        Returns:
            True if updated
        """
        update_data = {
            "status": status,
            "updated_at": datetime.utcnow()
        }

        # Add status-specific fields
        if status == "succeeded":
            update_data["processed_at"] = datetime.utcnow()
        elif status == "failed":
            update_data["failed_at"] = datetime.utcnow()
            if details and "message" in details:
                update_data["failure_message"] = details["message"]
        elif status == "refunded":
            update_data["refunded_at"] = datetime.utcnow()
            if details:
                if "amount" in details:
                    update_data["refund_amount"] = details["amount"]
                if "reason" in details:
                    update_data["refund_reason"] = details["reason"]

        result = await self.collection.update_one(
            {"_id": ObjectId(payment_id)},
            {"$set": update_data}
        )

        if result.modified_count > 0:
            # Add to history
            await self._add_history(
                payment_id=payment_id,
                status=status,
                details=details
            )

        return result.modified_count > 0

    async def update_stripe_ids(
        self,
        payment_id: str,
        payment_intent_id: Optional[str] = None,
        charge_id: Optional[str] = None
    ) -> bool:
        """
        Update Stripe IDs.

        Args:
            payment_id: Payment ID
            payment_intent_id: Stripe payment intent ID
            charge_id: Stripe charge ID

        Returns:
            True if updated
        """
        update_data = {"updated_at": datetime.utcnow()}

        if payment_intent_id:
            update_data["stripe_payment_intent_id"] = payment_intent_id
        if charge_id:
            update_data["stripe_charge_id"] = charge_id

        result = await self.collection.update_one(
            {"_id": ObjectId(payment_id)},
            {"$set": update_data}
        )

        return result.modified_count > 0

    async def count_by_user_id(self, user_id: str) -> int:
        """
        Count payments by user ID.

        Args:
            user_id: User ID

        Returns:
            Count of payments
        """
        return await self.collection.count_documents({"user_id": user_id})

    async def get_history(self, payment_id: str) -> List[PaymentHistory]:
        """
        Get payment history.

        Args:
            payment_id: Payment ID

        Returns:
            List of history entries
        """
        cursor = self.history_collection.find({"payment_id": payment_id}).sort("timestamp", 1)
        history = []
        async for doc in cursor:
            history.append(PaymentHistory(**doc))
        return history

    async def _add_history(
        self,
        payment_id: str,
        status: str,
        details: Optional[dict] = None
    ):
        """
        Add entry to payment history.

        Args:
            payment_id: Payment ID
            status: Payment status
            details: Additional details
        """
        history_entry = PaymentHistory(
            payment_id=payment_id,
            status=status,
            details=details
        )
        await self.history_collection.insert_one(
            history_entry.model_dump(by_alias=True)
        )
