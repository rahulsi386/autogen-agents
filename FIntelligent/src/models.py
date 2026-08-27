from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime

class Investor(BaseModel):
    name: str
    age: int
    risk: str
    sectors: str
    budget: float
    description: str = None

class Stock(BaseModel):
    company_Name: str
    ticker: str
    sector: str
    price: float
    beta: float
    exchange_code:str
    country: str
    isactively_trading: bool

class Portfolio(BaseModel):
    investor_name: str
    stocks: List[Stock]
    total_investment: float
    current_value: float
    risk_level: str

class StockOrder(BaseModel):
    order_id: str  # Unique identifier for the order
    symbol: str  # Stock symbol (e.g., "F")
    side: str  # Order side (e.g., "buy" or "sell")
    qty: int  # Quantity of stocks ordered
    order_type: str  # Type of order (e.g., "market", "limit")
    status: str  # Current status of the order (e.g., "accepted", "filled")
    submitted_at: datetime  # Timestamp when the order was submitted
    expires_at: Optional[datetime]  # Expiration time of the order, if applicable
    filled_qty: int  # Quantity of stocks filled
    filled_avg_price: Optional[float]  # Average price at which the order was filled
    