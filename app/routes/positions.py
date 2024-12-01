from fastapi import APIRouter
from app.database.redis import redis_client

router = APIRouter()

@router.get("/")
async def get_positions():
    """
    Get all positions from redis
    """
    position_keys = redis_client.get_all_keys("positions")
    positions = []
    for key in position_keys:
        # Extract position ID from the key (alphaedge:positions:ID)
        position_id = key.split(":")[-1]
        position = redis_client.get_hash("positions", position_id)
        if position:
            positions.append({"id": position_id, **position})
    return positions

@router.get("/{position_id}")
async def get_position(position_id: str):
    """
    Get a specific position by ID from redis
    """
    position = redis_client.get_hash("positions", position_id)
    if not position:
        return {"error": "Position not found"}
    return {"id": position_id, **position}

@router.get("/status")
async def positions_status():
    """
    Check positions endpoint health
    """
    return {"status": "healthy"}
