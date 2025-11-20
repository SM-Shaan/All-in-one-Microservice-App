"""
Kafka Event Consumer
====================

Consumes events from Kafka topics.

This is an EXAMPLE of how other services would listen to events.

In a real system:
- Notification Service would have its own consumer
- Analytics Service would have its own consumer
- Each service runs independently

Usage:
    python -m app.events.kafka_consumer
"""

from aiokafka import AIOKafkaConsumer
from aiokafka.errors import KafkaError
import json
import asyncio

from app.core.config import settings
from shared.events.schemas.user_events import UserCreatedEvent, UserEventTopics


class KafkaEventConsumer:
    """
    Async Kafka consumer for receiving events.

    Configuration:
    - group_id: Consumer group (multiple consumers can share work)
    - auto_offset_reset='earliest': Start from beginning if no offset
    - enable_auto_commit=False: Manual commit for reliability
    """

    def __init__(self, group_id: str = "user-service-consumer"):
        """
        Initialize consumer.

        Args:
            group_id: Consumer group ID
        """
        self.group_id = group_id
        self.bootstrap_servers = settings.kafka_bootstrap_servers
        self.consumer = None

    async def start(self, topics: list[str]):
        """
        Start consumer and subscribe to topics.

        Args:
            topics: List of Kafka topics to subscribe to
        """
        print(f"🔄 Starting Kafka consumer (group: {self.group_id})...")
        print(f"📡 Subscribing to topics: {topics}")

        self.consumer = AIOKafkaConsumer(
            *topics,  # Subscribe to multiple topics
            bootstrap_servers=self.bootstrap_servers,
            group_id=self.group_id,
            # Deserialize JSON
            value_deserializer=lambda m: json.loads(m.decode('utf-8')),
            # Start from beginning if no previous offset
            auto_offset_reset='earliest',
            # Manual commit for reliability
            enable_auto_commit=False,
        )

        try:
            await self.consumer.start()
            print("✅ Kafka consumer started successfully")
        except KafkaError as e:
            print(f"❌ Failed to start Kafka consumer: {e}")
            raise

    async def stop(self):
        """Stop consumer"""
        if self.consumer:
            await self.consumer.stop()
            print("✅ Kafka consumer stopped")

    async def consume(self, handler):
        """
        Consume messages and process with handler.

        Args:
            handler: Async function to process messages

        Example:
            async def process_event(event_data):
                print(f"Received: {event_data}")

            consumer = KafkaEventConsumer()
            await consumer.start(["users.user.created"])
            await consumer.consume(process_event)
        """
        if not self.consumer:
            raise RuntimeError("Consumer not started. Call start() first.")

        print("\n" + "=" * 60)
        print("👂 Listening for events... (Press Ctrl+C to stop)")
        print("=" * 60 + "\n")

        try:
            async for message in self.consumer:
                try:
                    # Extract message info
                    topic = message.topic
                    partition = message.partition
                    offset = message.offset
                    value = message.value

                    print(f"\n{'='*60}")
                    print(f"📨 EVENT RECEIVED!")
                    print(f"{'='*60}")
                    print(f"Topic: {topic}")
                    print(f"Partition: {partition}")
                    print(f"Offset: {offset}")
                    print(f"Event Type: {value.get('metadata', {}).get('event_type', 'unknown')}")
                    print(f"Event ID: {value.get('metadata', {}).get('event_id', 'unknown')}")
                    print(f"\nPayload:")
                    print(json.dumps(value.get('payload', {}), indent=2))
                    print(f"{'='*60}\n")

                    # Process the event
                    await handler(value)

                    # Commit offset (mark as processed)
                    await self.consumer.commit()

                    print("✅ Event processed and committed")

                except Exception as e:
                    print(f"❌ Error processing message: {e}")
                    # In production: send to dead letter queue

        except KeyboardInterrupt:
            print("\n\n👋 Shutting down consumer...")


# ============================================================================
# Example Handlers
# ============================================================================

async def handle_user_created(event_data: dict):
    """
    Example handler for user.created events.

    In a real system, this might:
    - Send welcome email
    - Create user profile in another service
    - Update analytics
    """
    payload = event_data.get('payload', {})

    print(f"\n🎉 New user registered!")
    print(f"   Email: {payload.get('email')}")
    print(f"   Name: {payload.get('full_name')}")

    # Simulate sending welcome email
    print(f"📧 Sending welcome email to {payload.get('email')}...")
    await asyncio.sleep(0.5)  # Simulate email sending
    print(f"✅ Welcome email sent!")


async def handle_user_updated(event_data: dict):
    """Example handler for user.updated events"""
    payload = event_data.get('payload', {})
    print(f"\n✏️ User updated: {payload.get('email')}")


async def handle_user_deleted(event_data: dict):
    """Example handler for user.deleted events"""
    payload = event_data.get('payload', {})
    print(f"\n🗑️ User deleted: {payload.get('email')}")


# ============================================================================
# Main (for testing)
# ============================================================================

async def main():
    """
    Run consumer to listen to user events.

    This is an EXAMPLE of how a service would consume events.

    To run:
        python -m app.events.kafka_consumer
    """
    consumer = KafkaEventConsumer(group_id="example-consumer")

    try:
        # Subscribe to user events
        await consumer.start([
            UserEventTopics.USER_CREATED,
            # UserEventTopics.USER_UPDATED,
            # UserEventTopics.USER_DELETED,
        ])

        # Start consuming
        await consumer.consume(handle_user_created)

    except KeyboardInterrupt:
        print("\n👋 Goodbye!")
    finally:
        await consumer.stop()


if __name__ == "__main__":
    asyncio.run(main())
