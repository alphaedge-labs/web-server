import redis
from time import sleep
from loguru import logger
from app.config import (
    REDIS_HOST,
    REDIS_PORT,
    REDIS_PASSWORD
)
import json

redis_logger = logger.bind(name="Redis")

redis_host = REDIS_HOST
redis_port = int(REDIS_PORT) or 6379
redis_password = REDIS_PASSWORD

class RedisClient:
    def __init__(self, prefix, redis_host, redis_port, redis_password, max_retries=20):
        self.prefix = prefix
        self.max_retries = max_retries
        self.client = redis.Redis(
            host=redis_host,
            port=redis_port,
            password=redis_password
        )
        self._connect()
        self.pubsub = self.client.pubsub()

    def _connect(self):
        retries = 0
        while retries < self.max_retries:
            try:
                self.client.ping()
                redis_logger.info("Connected to Redis!!!")
                return
            except redis.ConnectionError:
                retries += 1
                redis_logger.info(f"Attempt {retries} to reconnect...")
                sleep(retries * 0.5)
        raise Exception("Too many retries.")

    def publish(self, channel: str, message: str):
        """Publish a message to a channel"""
        self.client.publish(channel, message)
        logger.info(f"Published message to channel: {channel}")

    def _publish_event(self, category, action, data):
        """Helper method to publish events"""
        event = {
            "category": category,
            "action": action,
            "data": data
        }
        self.publish(category, json.dumps(event))

    def _generate_key(self, category, *args):
        """Generate a key for a category and identifier"""
        return category if not args else f"{category}:{':'.join(map(str, args))}"

    # Set or update a hash
    def set_hash(self, category, key, data):
        """Set or update a hash"""
        if not key:
            key = self._generate_key(category, key)
        self.client.hset(category, key, json.dumps(data))

    # Get a hash
    def get_hash(self, category, key):
        """Get a hash"""
        if not key:
            key = self._generate_key(category, key)
        data = self.client.hget(category, key)
        return json.loads(data) if data else None

    # Update specific fields in a hash
    def update_hash(self, category, identifier, updates):
        """Update specific fields in a hash"""
        key = self._generate_key(category, identifier)
        self.client.hset(key, mapping=updates)
        logger.info(f"Updated hash for key: {key}")
        # Publish event
        self._publish_event(category, "update", {
            "identifier": identifier,
            **updates
        })

    # Delete a hash
    def delete_hash(self, category, identifier):
        """Delete a hash"""
        key = self._generate_key(category, identifier)
        # Get the data before deleting
        data = self.get_hash(category, identifier)
        self.client.delete(key)
        logger.info(f"Deleted hash for key: {key}")
        # Publish event
        self._publish_event(category, "delete", {
            "identifier": identifier,
            **data
        })

    def get_all_hashes(self, category):
        """Get all hashes in a category"""
        data = self.client.hgetall(category)
        return [json.loads(value) for value in data.values()]

    # Increment a field in a hash (e.g., quantity)
    def increment_hash_field(self, category, identifier, field, amount=1):
        """Increment a field in a hash"""
        key = self._generate_key(category, identifier)
        new_value = self.client.hincrbyfloat(key, field, amount)
        logger.info(f"Incremented {field} by {amount} for key: {key}")
        # Publish event
        self._publish_event(category, "update", {
            "identifier": identifier,
            field: new_value
        })

    def get_pubsub(self):
        """Get a pubsub instance"""
        return self.client.pubsub()

redis_client = RedisClient(
    prefix='alphaedge',
    redis_host=REDIS_HOST,
    redis_port=REDIS_PORT,
    redis_password=REDIS_PASSWORD
)