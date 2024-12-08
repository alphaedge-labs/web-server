from fastapi import APIRouter
from datetime import datetime
from app.database.mongodb import db
from typing import List
from pydantic import BaseModel
from datetime import timedelta
from app.utils.datetime import get_current_time
from app.database.redis import redis_client
router = APIRouter()

class PositionResponse(BaseModel):
    date: str
    symbol: str
    tradeId: str
    quantity: int
    price: str
    executionDateTime: datetime
    totalCost: float
    pl: str

@router.get("/latest", response_model=List[dict])
async def get_latest_positions():
    """
    Get latest positions sorted by date, grouped by exit day
    """
    one_week_ago = (get_current_time() - timedelta(days=7)).replace(tzinfo=None)
    # Fetch from MongoDB with date filter
    positions = list(db.closed_positions.find({
        "exit_time": {"$gt": one_week_ago}
    }).sort("exit_time", -1))

    grouped_positions = {}

    for position in positions:
        # Calculate total cost
        total_cost = float(position["quantity"]) * float(position["entry_price"])
        realized_pnl = round(float(position["realized_pnl"]), 2)
        
        # Format the position data
        formatted_position = {
            "symbol": position["symbol"],
            "tradeId": position["position_id"],
            "quantity": int(position["quantity"]),
            "price": f"{float(position['entry_price']):.2f}",
            "executionDateTime": position["exit_time"],
            "totalCost": round(total_cost, 2),
            "pl": realized_pnl
        }

        # Group by date
        date_key = datetime.fromisoformat(str(position["exit_time"])).strftime("%B %d, %Y")
        if date_key not in grouped_positions:
            grouped_positions[date_key] = {
                "date": date_key,
                "trades": [],
                "pnl": 0.0
            }
        
        grouped_positions[date_key]["trades"].append(formatted_position)
        grouped_positions[date_key]["pnl"] += realized_pnl

    # Convert grouped data to a list
    response = list(grouped_positions.values())
    return response

@router.get("/stats")
async def get_positions_stats():
    """
    Get positions stats
    """
    stats = redis_client.get_hash("stats", "web")
    if not stats:
        stats = {
            "total_positions": 0,
            "total_pnl": 0.0
        }
    return stats