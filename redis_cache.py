import json
import redis
import os
import hashlib
from datetime import datetime, timedelta
from typing import Any, Optional, List, Dict
import logging

logger = logging.getLogger(__name__)

class RedisCacheManager:
    def __init__(self):
        self.host = os.getenv('REDIS_HOST', 'localhost')
        self.port = int(os.getenv('REDIS_PORT', 6379))
        self.db = int(os.getenv('REDIS_DB', 0))
        self.password = os.getenv('REDIS_PASSWORD')
        self.socket_timeout = 5
        self.socket_connect_timeout = 5
        self.retry_on_timeout = True
        self.health_check_interval = 30

        self._connection_pool = None
        self._redis_client = None
        self._initialize_connection()

    def _initialize_connection(self):
        """Initialize Redis connection with connection pooling and health checks"""
        try:
            self._connection_pool = redis.ConnectionPool(
                host=self.host,
                port=self.port,
                db=self.db,
                password=self.password,
                socket_timeout=self.socket_timeout,
                socket_connect_timeout=self.socket_connect_timeout,
                retry_on_timeout=self.retry_on_timeout,
                health_check_interval=self.health_check_interval,
                max_connections=20
            )

            self._redis_client = redis.Redis(
                connection_pool=self._connection_pool,
                decode_responses=True
            )

            # Test connection
            self._redis_client.ping()
            logger.info("Redis connection established successfully")

        except redis.ConnectionError as e:
            logger.error(f"Failed to connect to Redis: {e}")
            self._redis_client = None
        except Exception as e:
            logger.error(f"Unexpected error connecting to Redis: {e}")
            self._redis_client = None

    def is_connected(self) -> bool:
        """Check if Redis connection is active"""
        if not self._redis_client:
            return False
        try:
            self._redis_client.ping()
            return True
        except:
            return False

    def get_deserialized(self, key: str) -> Optional[Any]:
        """Get and deserialize JSON data from cache"""
        if not self.is_connected():
            return None
        try:
            data = self._redis_client.get(key)
            if data:
                return json.loads(data)
            return None
        except Exception as e:
            logger.error(f"Error getting data from Redis for key {key}: {e}")
            return None

    def set_serialized(self, key: str, data: Any, ttl: int = 300) -> bool:
        """Serialize and set data in cache with TTL"""
        if not self.is_connected():
            return False
        try:
            serialized_data = json.dumps(data, default=str)
            return self._redis_client.setex(key, ttl, serialized_data)
        except Exception as e:
            logger.error(f"Error setting data in Redis for key {key}: {e}")
            return False

    def delete(self, key: str) -> bool:
        """Delete data from cache"""
        if not self.is_connected():
            return False
        try:
            return bool(self._redis_client.delete(key))
        except Exception as e:
            logger.error(f"Error deleting key {key} from Redis: {e}")
            return False

    def get_ttl(self, key: str) -> int:
        """Get remaining TTL for key"""
        if not self.is_connected():
            return -2
        try:
            return self._redis_client.ttl(key)
        except Exception as e:
            logger.error(f"Error getting TTL for key {key}: {e}")
            return -2

    def get_cache_hit_rate(self) -> float:
        """Get Redis cache hit rate statistics"""
        if not self.is_connected():
            return 0.0
        try:
            info = self._redis_client.info()
            keyspace_hits = info.get('keyspace_hits', 0)
            keyspace_misses = info.get('keyspace_misses', 0)
            total_requests = keyspace_hits + keyspace_misses

            if total_requests == 0:
                return 0.0
            return (keyspace_hits / total_requests) * 100
        except Exception as e:
            logger.error(f"Error getting cache hit rate: {e}")
            return 0.0

    def generate_cache_key(self, prefix: str, params: Dict[str, Any] = None) -> str:
        """Generate a consistent cache key with optional parameters"""
        if params:
            # Sort parameters for consistent key generation
            param_string = json.dumps(params, sort_keys=True)
            param_hash = hashlib.md5(param_string.encode()).hexdigest()[:8]
            return f"{prefix}:{param_hash}"
        return prefix

    def warm_cache(self, cache_warmer_func):
        """Cache warming strategy for frequently accessed data"""
        try:
            logger.info("Starting cache warming...")
            cache_warmer_func()
            logger.info("Cache warming completed successfully")
        except Exception as e:
            logger.error(f"Error during cache warming: {e}")

# Cache key patterns
CACHE_KEY_PATTERNS = {
    'recent_tickets': 'zendesk:tickets:recent:{count}',
    'ticket_comments': 'zendesk:tickets:{ticket_id}:comments',
    'user_data': 'zendesk:users:batch:{user_hash}',
    'dashboard_stats': 'zendesk:dashboard:stats:{date_range}',
    'webhook_rate_limit': 'zendesk:webhook:rate:{identifier}',
    'api_rate_limit': 'zendesk:api:rate:{endpoint}'
}

# TTL configurations (in seconds)
CACHE_TTL = {
    'recent_tickets': 300,      # 5 minutes
    'ticket_comments': 1800,    # 30 minutes
    'user_data': 86400,         # 24 hours
    'dashboard_stats': 600,     # 10 minutes
    'webhook_rate_limit': 60,   # 1 minute
    'api_rate_limit': 3600      # 1 hour
}