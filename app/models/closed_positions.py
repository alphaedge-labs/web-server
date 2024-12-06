from datetime import datetime
from pydantic import BaseModel, Field

class OrderResult(BaseModel):
    order_id: str
    status: str
    broker: str
    average_price: float
    quantity: str
    transaction_type: str
    exchange_order_id: str
    order_timestamp: datetime
    variety: str
    validity: str
    product: str
    exchange: str
    symbol: str

class ClosedPosition(BaseModel):
    id: str = Field(alias="_id")
    position_id: str
    user_id: str
    symbol: str
    strike_price: str
    expiry_date: str
    identifier: str
    broker: str
    position_type: str
    quantity: str
    entry_price: str
    current_price: float
    unrealized_pnl: float
    realized_pnl: float
    stop_loss: str
    take_profit: str
    timestamp: datetime
    status: str
    should_exit: bool
    last_updated: str
    exit_price: float
    exit_time: datetime
    order_result: OrderResult

    class Config:
        populate_by_name = True
