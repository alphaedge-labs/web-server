from fastapi import APIRouter
from datetime import datetime
from app.database.redis import redis_client
from app.database.mongodb import db
from typing import List
from pydantic import BaseModel
from datetime import timedelta
from app.utils.datetime import get_current_time

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

class PositionResponse(BaseModel):
    date: str
    symbol: str
    tradeId: str
    quantity: int
    price: str
    executionDateTime: datetime
    totalCost: float
    pl: str

@router.get("/latest", response_model=List[PositionResponse])
async def get_latest_positions():
    """
    Get latest positions sorted by date
    """
    one_week_ago = get_current_time() - timedelta(days=7)
    
    # Fetch from MongoDB with date filter
    positions = list(db.closed_positions.find({
        "exit_time": {"$gte": one_week_ago}
    }).sort("exit_time", -1))

    formatted_positions = []
    for position in positions:
        # Calculate total cost
        total_cost = float(position["quantity"]) * float(position["entry_price"])
        
        # Format the position data
        formatted_position = {
            "date": datetime.fromisoformat(str(position["exit_time"])).strftime("%B %d, %Y"),
            "symbol": position["symbol"],
            "tradeId": position["position_id"],
            "quantity": int(position["quantity"]),
            "price": f"{float(position['entry_price']):.2f}",
            "executionDateTime": position["exit_time"],
            "totalCost": total_cost,
            "pl": f"{position['realized_pnl']:.2f}"
        }
        formatted_positions.append(formatted_position)
    
    return formatted_positions