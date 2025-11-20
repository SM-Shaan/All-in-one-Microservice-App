"""
Event Publisher
===============

Simple event publisher for publishing events to Kafka topics.
"""

import json
from typing import Any, Dict, Optional
from aiokafka import AIOKafkaProducer
import asyncio


class EventPublisher:
    """
    Static event publisher for publishing events to Kafka.

    This is a simplified publisher that doesn't maintain a persistent connection.
    Each publish creates a new producer, sends the message, and closes.
    """

    _bootstrap_servers: str = "kafka:29092"
    _producer: Optional[AIOKafkaProducer] = None
    _lock = asyncio.Lock()

    @classmethod
    async def _get_producer(cls) -> AIOKafkaProducer:
        """Get or create a Kafka producer"""
        async with cls._lock:
            if cls._producer is None:
                cls._producer = AIOKafkaProducer(
                    bootstrap_servers=cls._bootstrap_servers,
                    value_serializer=lambda v: json.dumps(v).encode('utf-8'),
                    key_serializer=lambda k: k.encode('utf-8') if k else None,
                    acks='all',
                    enable_idempotence=True,
                    compression_type='gzip'
                )
                await cls._producer.start()
        return cls._producer

    @classmethod
    async def publish(
        cls,
        topic: str,
        event: Dict[str, Any],
        key: Optional[str] = None
    ) -> None:
        """
        Publish an event to a Kafka topic.

        Args:
            topic: Kafka topic name
            event: Event data as dictionary
            key: Optional partition key
        """
        try:
            producer = await cls._get_producer()
            await producer.send(topic, value=event, key=key)
        except Exception as e:
            print(f"❌ Failed to publish event to {topic}: {e}")
            # Don't raise - we don't want event publishing to break the request

    @classmethod
    async def close(cls) -> None:
        """Close the producer connection"""
        async with cls._lock:
            if cls._producer is not None:
                await cls._producer.stop()
                cls._producer = None
