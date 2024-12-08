import json
import asyncio
from loguru import logger
from app.database.redis import redis_client
from app.services.websocket import manager

class RealtimeService:
    def __init__(self):
        self.pubsub = redis_client.get_pubsub()
        self.channels = ["orders", "positions", "trades", "signals"]
        self.running = False

    def get_position_stats(self):
        positions = redis_client.get_all_hashes("positions")
        print(positions)
        stats = {
            "total_positions": len(positions),
            "total_pnl": sum(round(float(position["unrealized_pnl"]), 2) for position in positions)
        }
        redis_client.set_hash("stats", "web", stats)
        return stats

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

                    # Log the message
                    logger.info(f"Received event from channel '{channel}': {data}")

                    if channel == "positions":
                        stats = self.get_position_stats()
                        broadcast_message = json.dumps({
                            "type": channel,
                            "action": data["action"],
                            "data": stats
                        })
                        await manager.broadcast(broadcast_message)

                    if channel == "signals":
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