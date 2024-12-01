from fastapi import APIRouter
from app.database.redis import redis_client

router = APIRouter()

@router.get("/")
async def get_orders():
    """
    Get all orders from redis
    """
    order_keys = redis_client.get_all_keys("orders")
    orders = []
    for key in order_keys:
        # Extract order ID from the key (alphaedge:orders:ID)
        order_id = key.split(":")[-1]
        order = redis_client.get_hash("orders", order_id)
        if order:
            orders.append({"id": order_id, **order})
    return orders

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
