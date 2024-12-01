import json
import asyncio
from loguru import logger
from app.database.redis import redis_client
from app.services.websocket import manager

class RealtimeService:
    def __init__(self):
        self.pubsub = redis_client.get_pubsub()
        self.channels = ["orders", "positions", "trades"]
        self.running = False

    async def start_listening(self):
        """Start listening to Redis channels"""
        self.running = True
        self.pubsub.subscribe(*self.channels)
        
        logger.info(f"Started listening to channels: {self.channels}")
        
        while self.running:
            try:
                message = self.pubsub.get_message()
                if message and message['type'] == 'message':
                    channel = message['channel'].decode('utf-8')
                    data = json.loads(message['data'].decode('utf-8'))
                    
                    # Format the message for broadcasting
                    broadcast_message = json.dumps({
                        "type": channel,
                        "action": data["action"],
                        "category": data["category"],
                        "data": data["data"]
                    })
                    
                    logger.info(f"Broadcasting {data['action']} event for {channel}")
                    await manager.broadcast(broadcast_message)
                    
            except Exception as e:
                logger.error(f"Error processing message: {str(e)}")
                await asyncio.sleep(1)
                continue
                
            await asyncio.sleep(0.1) # Prevent CPU overload

    async def stop_listening(self):
        """Stop listening to Redis channels"""
        self.running = False
        self.pubsub.unsubscribe()
        logger.info("Stopped listening to Redis channels") 