import redis
from time import sleep
from loguru import logger
import logging
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

    def _publish_event(self, category, action, data):
        """Helper method to publish events"""
        event = {
            "category": category,
            "action": action,
            "data": data
        }
        self.publish(category, json.dumps(event))

    def _generate_key(self, category, *args):
        return f"{self.prefix}:{category}:{':'.join(map(str, args))}"

    # Set or update a hash
    def set_hash(self, category, identifier, data):
        key = self._generate_key(category, identifier)
        self.client.hset(key, mapping=data)
        logger.info(f"Set hash for key: {key}")
        # Publish event
        self._publish_event(category, "create", {
            "identifier": identifier,
            **data
        })

    # Get a hash
    def get_hash(self, category, identifier):
        key = self._generate_key(category, identifier)
        data = self.client.hgetall(key)
        logger.info(f"Retrieved hash for key: {key}")
        return {k.decode('utf-8'): v.decode('utf-8') for k, v in data.items()}

    # Update specific fields in a hash
    def update_hash(self, category, identifier, updates):
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

    # Get all keys in a category
    def get_all_keys(self, category):
        pattern = self._generate_key(category, "*")
        keys = self.client.keys(pattern)
        logger.info(f"Retrieved keys for pattern: {pattern}")
        return [key.decode('utf-8') for key in keys]

    # Increment a field in a hash (e.g., quantity)
    def increment_hash_field(self, category, identifier, field, amount=1):
        key = self._generate_key(category, identifier)
        new_value = self.client.hincrbyfloat(key, field, amount)
        logger.info(f"Incremented {field} by {amount} for key: {key}")
        # Publish event
        self._publish_event(category, "update", {
            "identifier": identifier,
            field: new_value
        })

    def publish(self, channel: str, message: str):
        """Publish a message to a channel"""
        self.client.publish(channel, message)
        logger.info(f"Published message to channel: {channel}")

    def get_pubsub(self):
        """Get a pubsub instance"""
        return self.client.pubsub()

redis_client = RedisClient(
    prefix='alphaedge',
    redis_host=REDIS_HOST,
    redis_port=REDIS_PORT,
    redis_password=REDIS_PASSWORD
)