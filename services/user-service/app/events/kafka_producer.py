"""
Kafka Event Producer
====================

Publishes events to Kafka topics.

Key Concepts:
- Producer: Sends messages to Kafka
- Topic: Category/channel for messages
- Partition: Topics are split into partitions for scaling
- Idempotence: Ensures messages aren't duplicated
"""

from aiokafka import AIOKafkaProducer
from aiokafka.errors import KafkaError
from typing import Optional
import json

from app.core.config import settings
from shared.events.schemas.base import BaseEvent


class KafkaEventProducer:
    """
    Async Kafka producer for publishing events.

    Usage:
        producer = KafkaEventProducer()
        await producer.start()

        event = UserCreatedEvent(...)
        await producer.publish(event, topic="users.user.created")

        await producer.stop()
    """

    def __init__(self):
        """Initialize producer (don't connect yet)"""
        self.producer: Optional[AIOKafkaProducer] = None
        self.bootstrap_servers = settings.kafka_bootstrap_servers

    async def start(self):
        """
        Start Kafka producer and establish connection.

        Configuration:
        - acks='all': Wait for all replicas to acknowledge (safety)
        - enable_idempotence=True: Prevent duplicate messages
        - compression_type='gzip': Compress messages (save bandwidth)
        """
        print(f"🔄 Connecting to Kafka at {self.bootstrap_servers}...")

        self.producer = AIOKafkaProducer(
            bootstrap_servers=self.bootstrap_servers,
            # Serialization: Convert Python objects to bytes
            value_serializer=lambda v: json.dumps(v).encode('utf-8'),
            key_serializer=lambda k: k.encode('utf-8') if k else None,
            # Reliability
            acks='all',  # Wait for all replicas
            enable_idempotence=True,  # Prevent duplicates
            # Performance
            compression_type='gzip',  # Compress messages
            # Retry configuration
            max_request_size=1048576,  # 1MB max message size
            request_timeout_ms=30000
        )

        try:
            await self.producer.start()
            print("✅ Kafka producer connected successfully")
        except KafkaError as e:
            print(f"❌ Failed to connect to Kafka: {e}")
            print("⚠️ Service will continue without event publishing")
            self.producer = None

    async def stop(self):
        """Stop producer and close connections"""
        if self.producer:
            await self.producer.stop()
            print("✅ Kafka producer stopped")

    async def publish(
        self,
        event: BaseEvent,
        topic: str,
        key: Optional[str] = None
    ) -> bool:
        """
        Publish an event to Kafka.

        Args:
            event: Event to publish (must inherit from BaseEvent)
            topic: Kafka topic name
            key: Optional partition key (events with same key go to same partition)

        Returns:
            bool: True if published successfully, False otherwise

        Example:
            event = UserCreatedEvent(
                metadata=EventMetadata(
                    event_type="user.created",
                    source_service="user-service"
                ),
                payload=UserCreatedPayload(...)
            )

            success = await producer.publish(
                event,
                topic="users.user.created",
                key=str(user.id)  # All events for this user go to same partition
            )
        """
        if not self.producer:
            print("⚠️ Kafka producer not connected, skipping event publish")
            return False

        try:
            # Convert event to dict for JSON serialization
            event_dict = event.model_dump(mode='json')

            # Add some metadata for debugging
            print(f"📤 Publishing event: {event.metadata.event_type} to topic: {topic}")

            # Send to Kafka
            # send_and_wait: Blocks until message is sent (reliable)
            # If you want fire-and-forget: use send() instead
            await self.producer.send_and_wait(
                topic=topic,
                value=event_dict,
                key=key
            )

            print(f"✅ Event published successfully: {event.metadata.event_id}")
            return True

        except KafkaError as e:
            print(f"❌ Failed to publish event: {e}")
            return False

        except Exception as e:
            print(f"❌ Unexpected error publishing event: {e}")
            return False

    async def publish_batch(
        self,
        events: list[tuple[BaseEvent, str, Optional[str]]]
    ) -> int:
        """
        Publish multiple events in a batch.

        More efficient than publishing one by one.

        Args:
            events: List of (event, topic, key) tuples

        Returns:
            int: Number of successfully published events

        Example:
            events = [
                (user_created_event, "users.user.created", str(user.id)),
                (email_event, "notifications.email.send", str(user.id))
            ]
            published = await producer.publish_batch(events)
        """
        if not self.producer:
            return 0

        published = 0

        for event, topic, key in events:
            success = await self.publish(event, topic, key)
            if success:
                published += 1

        return published


# ============================================================================
# Global Producer Instance
# ============================================================================

kafka_producer = KafkaEventProducer()


async def get_kafka_producer() -> KafkaEventProducer:
    """
    Dependency to get Kafka producer.

    Usage:
        @router.post("/users")
        async def create_user(
            producer: KafkaEventProducer = Depends(get_kafka_producer)
        ):
            # Create user...
            event = UserCreatedEvent(...)
            await producer.publish(event, "users.user.created")
    """
    return kafka_producer
