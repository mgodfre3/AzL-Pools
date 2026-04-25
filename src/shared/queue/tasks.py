"""Shared ARQ task queue definitions."""

import os
from arq import create_pool
from arq.connections import RedisSettings


REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")

QUEUE_POOL_DETECTION = "pool-detection-queue"
QUEUE_POOL_DESIGN = "pool-design-queue"
QUEUE_CONTACT_ENRICHMENT = "contact-enrichment-queue"


def get_redis_settings() -> RedisSettings:
    """Parse REDIS_URL into ARQ RedisSettings."""
    url = REDIS_URL.replace("redis://", "")
    host, port = url.split(":")
    return RedisSettings(host=host, port=int(port))


async def enqueue_detection(property_id: int):
    redis = await create_pool(get_redis_settings())
    await redis.lpush(QUEUE_POOL_DETECTION, str(property_id))


async def enqueue_design(property_id: int):
    redis = await create_pool(get_redis_settings())
    await redis.lpush(QUEUE_POOL_DESIGN, str(property_id))


async def enqueue_enrichment(property_id: int):
    redis = await create_pool(get_redis_settings())
    await redis.lpush(QUEUE_CONTACT_ENRICHMENT, str(property_id))
