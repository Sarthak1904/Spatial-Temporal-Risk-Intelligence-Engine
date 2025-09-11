"""Redis cache client factory."""

import redis

from backend.app.core.config import get_settings

settings = get_settings()

redis_client = redis.Redis.from_url(settings.redis_url, decode_responses=False)
