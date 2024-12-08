from fastapi import APIRouter
from app.database.redis import redis_client

router = APIRouter()

@router.get("/{order_id}")
async def get_order(order_id: str):
    """
    Get a specific order by ID from redis
    """
    order = redis_client.get_hash("orders", order_id)
    if not order:
        return {"error": "Order not found"}
    return {"id": order_id, **order}

@router.get("/status")
async def orders_status():
    """
    Check orders endpoint health
    """
    return {"status": "healthy"}
