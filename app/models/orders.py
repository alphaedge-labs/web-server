from datetime import datetime
from pydantic import BaseModel, Field

class Order(BaseModel):
    id: str = Field(alias="_id")
    user_id: str
    broker: str
    symbol: str
    strike_price: str
    expiry_date: str
    right: str
    quantity: int
    entry_price: float
    stop_loss: float
    target: float
    order_type: str
    transaction_type: str
    product: str
    position_type: str
    timestamp: datetime
    order_id: str
    status: str
    average_price: float
    exchange_order_id: str
    order_timestamp: datetime
    variety: str
    validity: str
    exchange: str
    position_id: str
    created_at: datetime

    class Config:
        populate_by_name = True
