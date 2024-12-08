from datetime import datetime
from typing import List
from pydantic import BaseModel, Field

class StreamerConfig(BaseModel):
    STREAMER_BROKER: str
    STREAMER_APP_KEY: str
    STREAMER_SECRET_KEY: str
    STREAMER_SESSION_TOKEN: str

class TradingConfig(BaseModel):
    TRADING_BROKER: str
    TRADING_APP_KEY: str
    TRADING_SECRET_KEY: str
    TRADING_FIN_KEY: str
    TRADING_CLIENT_ID: str
    TRADING_PASSWORD: str

class RiskManagement(BaseModel):
    ideal_risk_reward_ratio: float
    max_drawdown_percentage: float
    stop_loss_buffer: float
    position_sizing_method: str
    max_open_positions: int

class Capital(BaseModel):
    total_deployed: float
    available_balance: float

class TradingHours(BaseModel):
    start: str
    end: str

class Settings(BaseModel):
    preferred_trading_hours: TradingHours
    trade_frequency: str
    preferred_instruments: List[str]

class ActivityLog(BaseModel):
    timestamp: datetime
    activity: str

class NotificationPreferences(BaseModel):
    email: bool
    sms: bool
    push: bool

class Preferences(BaseModel):
    notifications: NotificationPreferences
    language: str

class User(BaseModel):
    id: str = Field(alias="_id")
    is_admin: bool
    is_active: bool
    is_paper_trading: bool
    streamer: StreamerConfig
    trading: List[TradingConfig]
    active_brokers: List[str]
    mobile: str
    email: str
    name: str
    last_login: datetime
    risk_management: RiskManagement
    capital: Capital
    settings: Settings
    activity_logs: List[ActivityLog]
    preferences: Preferences

    class Config:
        populate_by_name = True
