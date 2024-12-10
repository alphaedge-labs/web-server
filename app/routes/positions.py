from fastapi import APIRouter, Query
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

@router.get("/performance")
async def get_performance_stats(
    user_id: str = Query(..., description="User ID"),
    from_date: datetime = Query(default=None, description="Start date"),
    to_date: datetime = Query(default=None, description="End date")
):
    """
    Get detailed performance statistics for a user within a date range
    """

    if from_date is None:
        from_date = get_current_time().replace(hour=0, minute=0, second=0, microsecond=0)
    if to_date is None:
        to_date = from_date + timedelta(days=1)

    pipeline = [
        {
            "$match": {
                "user_id": user_id,
                "timestamp": {
                    "$gte": from_date,
                    "$lt": to_date
                }
            }
        },
        {
            "$addFields": {
                "trade_result": {
                    "$cond": [
                        {"$gt": ["$unrealized_pnl", 0]},
                        "win",
                        "loss"
                    ]
                }
            }
        },
        {
            "$group": {
                "_id": "$trade_result",
                "count": {"$sum": 1},
                "max_pnl": {"$max": "$unrealized_pnl"},
                "min_pnl": {"$min": "$unrealized_pnl"},
                "total_pnl": {"$sum": "$unrealized_pnl"}
            }
        },
        {
            "$group": {
                "_id": None,
                "winning_trades": {
                    "$sum": {
                        "$cond": [{"$eq": ["$_id", "win"]}, "$count", 0]
                    }
                },
                "losing_trades": {
                    "$sum": {
                        "$cond": [{"$eq": ["$_id", "loss"]}, "$count", 0]
                    }
                },
                "max_win": {
                    "$max": {
                        "$cond": [{"$eq": ["$_id", "win"]}, "$max_pnl", None]
                    }
                },
                "max_loss": {
                    "$min": {
                        "$cond": [{"$eq": ["$_id", "loss"]}, "$min_pnl", None]
                    }
                },
                "total_win": {
                    "$sum": {
                        "$cond": [{"$eq": ["$_id", "win"]}, "$total_pnl", 0]
                    }
                },
                "total_loss": {
                    "$sum": {
                        "$cond": [{"$eq": ["$_id", "loss"]}, "$total_pnl", 0]
                    }
                },
                "total_pnl": {"$sum": "$total_pnl"}
            }
        },
        {
            "$addFields": {
                "avg_winner": {
                    "$cond": [
                        {"$gt": ["$winning_trades", 0]},
                        {"$round": [{"$divide": ["$total_win", "$winning_trades"]}, 2]},
                        0
                    ]
                },
                "avg_loser": {
                    "$cond": [
                        {"$gt": ["$losing_trades", 0]},
                        {"$round": [{"$divide": ["$total_loss", "$losing_trades"]}, 2]},
                        0
                    ]
                },
                "total_win": {"$round": ["$total_win", 2]},
                "total_loss": {"$round": ["$total_loss", 2]},
                "total_pnl": {"$round": ["$total_pnl", 2]},
                "max_win": {"$round": ["$max_win", 2]},
                "max_loss": {"$round": ["$max_loss", 2]}
            }
        },
        {
            "$project": {
                "_id": 0,
                "winning_trades": 1,
                "losing_trades": 1,
                "max_win": 1,
                "max_loss": 1,
                "total_win": 1,
                "total_loss": 1,
                "total_pnl": 1,
                "avg_winner": 1,
                "avg_loser": 1
            }
        }
    ]

    result = await db.closed_positions.aggregate(pipeline).to_list(length=1)

    return result[0] if result else {
        "winning_trades": 0,
        "losing_trades": 0,
        "max_win": 0,
        "max_loss": 0,
        "total_win": 0,
        "total_loss": 0,
        "total_pnl": 0,
        "avg_winner": 0,
        "avg_loser": 0
    }
