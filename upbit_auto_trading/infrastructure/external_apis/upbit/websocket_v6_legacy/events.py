from dataclasses import dataclass, field
from typing import List, Dict, Any

# Base class for all events to include metadata if needed in the future
@dataclass
class WebSocketEvent:
    """Base class for all WebSocket events."""
    event_type: str
    symbol: str
    received_at: float # timestamp

@dataclass
class TickerEvent(WebSocketEvent):
    """Represents a real-time ticker update."""
    trade_price: float
    trade_volume: float
    opening_price: float
    high_price: float
    low_price: float
    prev_closing_price: float
    change: str # RISE, EVEN, FALL
    acc_trade_volume_24h: float
    acc_trade_price_24h: float
    trade_timestamp: int
    v: int = 1 # Schema version

@dataclass
class OrderbookUnit:
    """A single unit in the orderbook."""
    ask_price: float
    bid_price: float
    ask_size: float
    bid_size: float

@dataclass
class OrderbookEvent(WebSocketEvent):
    """Represents a real-time orderbook update."""
    total_ask_size: float
    total_bid_size: float
    orderbook_units: List[OrderbookUnit]
    v: int = 1 # Schema version

@dataclass
class TradeEvent(WebSocketEvent):
    """Represents a real-time trade (execution) update."""
    trade_price: float
    trade_volume: float
    ask_bid: str # ASK or BID
    trade_timestamp: int
    sequential_id: int
    v: int = 1 # Schema version

@dataclass
class CandleEvent(WebSocketEvent):
    """Represents a real-time candle update."""
    interval: str
    opening_price: float
    high_price: float
    low_price: float
    trade_price: float # Closing price of the candle
    candle_acc_trade_volume: float
    candle_acc_trade_price: float
    candle_date_time_kst: str
    v: int = 1 # Schema version

@dataclass
class MyOrderEvent(WebSocketEvent):
    """Represents an update on one of the user's own orders (Private)."""
    uuid: str
    side: str # bid, ask
    ord_type: str # limit, price, market
    price: float
    state: str # wait, watch, done, cancel
    remaining_volume: float
    executed_volume: float
    trades_count: int
    v: int = 1 # Schema version

@dataclass
class MyAssetEvent(WebSocketEvent):
    """Represents an update on the user's own assets (Private)."""
    currency: str
    balance: float
    locked: float
    avg_buy_price: float
    v: int = 1 # Schema version
