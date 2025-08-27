"""
업비트 WebSocket v5.0 - Pydantic 기반 데이터 모델

🎯 특징:
- 강력한 타입 검증
- 자동 데이터 변환
- 명시적인 필드 정의
- API 응답 검증
"""

from datetime import datetime
from typing import Optional, Dict, Any, List
from enum import Enum
from pydantic import BaseModel, Field, field_validator


class StreamType(str, Enum):
    """WebSocket 스트림 타입"""
    SNAPSHOT = "SNAPSHOT"
    REALTIME = "REALTIME"


class DataType(str, Enum):
    """WebSocket 데이터 타입"""
    TICKER = "ticker"
    TRADE = "trade"
    ORDERBOOK = "orderbook"
    CANDLE_1M = "candle.1m"
    CANDLE_3M = "candle.3m"
    CANDLE_5M = "candle.5m"
    CANDLE_15M = "candle.15m"
    CANDLE_30M = "candle.30m"
    CANDLE_1H = "candle.60m"
    CANDLE_4H = "candle.240m"


class WebSocketMessage(BaseModel):
    """WebSocket 메시지 기본 모델"""
    type: DataType
    market: str = Field(..., description="마켓 코드 (예: KRW-BTC)")
    timestamp: datetime = Field(default_factory=datetime.now)
    stream_type: Optional[StreamType] = None
    raw_data: Dict[str, Any] = Field(..., description="원본 데이터")

    @field_validator('market')
    @classmethod
    def validate_market(cls, v):
        """마켓 코드 유효성 검증"""
        if not v or len(v) < 5:
            raise ValueError("유효하지 않은 마켓 코드")
        return v.upper()

    def is_snapshot(self) -> bool:
        """스냅샷 메시지 여부"""
        return self.stream_type == StreamType.SNAPSHOT

    def is_realtime(self) -> bool:
        """실시간 메시지 여부"""
        return self.stream_type == StreamType.REALTIME


class TickerData(BaseModel):
    """현재가 데이터 모델 (업비트 공식 API 필드명 기준)"""
    code: str = Field(..., description="마켓 코드 (업비트 API 필드명)")
    trade_price: float = Field(..., description="현재가")
    trade_volume: float = Field(..., description="거래량")
    change_rate: float = Field(..., description="변화율")
    change_price: float = Field(..., description="변화금액")
    high_price: float = Field(..., description="고가")
    low_price: float = Field(..., description="저가")
    opening_price: float = Field(..., description="시가")
    prev_closing_price: float = Field(..., description="전일 종가")
    acc_trade_volume_24h: float = Field(..., description="24시간 누적 거래량")
    acc_trade_price_24h: float = Field(..., description="24시간 누적 거래대금")

    @field_validator('trade_price', 'high_price', 'low_price', 'opening_price')
    @classmethod
    def validate_positive_prices(cls, v):
        """가격 필드는 양수여야 함"""
        if v <= 0:
            raise ValueError("가격은 0보다 커야 합니다")
        return v


class TradeData(BaseModel):
    """체결 데이터 모델 (업비트 공식 API 필드명 기준)"""
    code: str = Field(..., description="마켓 코드 (업비트 API 필드명)")
    trade_price: float = Field(..., description="체결가")
    trade_volume: float = Field(..., description="체결량")
    ask_bid: str = Field(..., description="매수/매도 구분")
    sequential_id: int = Field(..., description="체결 번호")
    trade_timestamp: datetime = Field(..., description="체결 시각")

    @field_validator('ask_bid')
    @classmethod
    def validate_ask_bid(cls, v):
        """매수/매도 구분 검증"""
        if v not in ['ASK', 'BID']:
            raise ValueError("ask_bid는 ASK 또는 BID여야 합니다")
        return v


class OrderbookUnit(BaseModel):
    """호가 단위 모델"""
    ask_price: float = Field(..., description="매도호가")
    bid_price: float = Field(..., description="매수호가")
    ask_size: float = Field(..., description="매도잔량")
    bid_size: float = Field(..., description="매수잔량")


class OrderbookData(BaseModel):
    """호가 데이터 모델"""
    market: str = Field(..., description="마켓 코드")
    orderbook_units: List[OrderbookUnit] = Field(..., description="호가 정보")
    total_ask_size: float = Field(..., description="총 매도 잔량")
    total_bid_size: float = Field(..., description="총 매수 잔량")
    timestamp: datetime = Field(..., description="호가 시각")


class CandleData(BaseModel):
    """캔들 데이터 모델"""
    market: str = Field(..., description="마켓 코드")
    candle_date_time_utc: datetime = Field(..., description="캔들 기준 시각(UTC)")
    candle_date_time_kst: datetime = Field(..., description="캔들 기준 시각(KST)")
    opening_price: float = Field(..., description="시가")
    high_price: float = Field(..., description="고가")
    low_price: float = Field(..., description="저가")
    trade_price: float = Field(..., description="종가")
    candle_acc_trade_volume: float = Field(..., description="누적거래량")
    candle_acc_trade_price: float = Field(..., description="누적거래대금")
    unit: str = Field(..., description="분 단위")

    @field_validator('opening_price', 'high_price', 'low_price', 'trade_price')
    @classmethod
    def validate_ohlc_prices(cls, v):
        """OHLC 가격 검증"""
        if v <= 0:
            raise ValueError("OHLC 가격은 0보다 커야 합니다")
        return v


class MarketData(BaseModel):
    """통합 마켓 데이터 모델"""
    message: WebSocketMessage
    ticker: Optional[TickerData] = None
    trade: Optional[TradeData] = None
    orderbook: Optional[OrderbookData] = None
    candle: Optional[CandleData] = None

    # TODO: Pydantic V2에서 model_validator로 다시 구현 필요
    # @field_validator('ticker', 'trade', 'orderbook', 'candle')
    # @classmethod
    # def validate_data_consistency(cls, v, values):
    #     """데이터 타입과 실제 데이터 일치성 검증"""
    #     if 'message' in values:
    #         message_type = values['message'].type
    #         if message_type == DataType.TICKER and v is None and cls.__name__ == 'ticker':
    #             raise ValueError("ticker 메시지인데 ticker 데이터가 없습니다")
    #     return v

    def get_market(self) -> str:
        """마켓 코드 반환"""
        return self.message.market

    def get_timestamp(self) -> datetime:
        """타임스탬프 반환"""
        return self.message.timestamp

    def is_realtime(self) -> bool:
        """실시간 데이터 여부"""
        return self.message.is_realtime()


class SubscriptionRequest(BaseModel):
    """구독 요청 모델"""
    data_type: DataType = Field(..., description="구독할 데이터 타입")
    symbols: List[str] = Field(..., description="구독할 심볼 목록")

    @field_validator('symbols')
    @classmethod
    def validate_symbols(cls, v):
        """심볼 목록 검증"""
        if not v or len(v) == 0:
            raise ValueError("최소 1개 이상의 심볼이 필요합니다")
        validated_symbols = []
        for symbol in v:
            if not symbol or len(symbol) < 5:
                raise ValueError(f"유효하지 않은 심볼: {symbol}")
            validated_symbols.append(symbol.upper())
        return validated_symbols

    options: Dict[str, Any] = Field(default_factory=dict, description="추가 옵션")


class SubscriptionStatus(BaseModel):
    """구독 상태 모델"""
    ticket_id: str = Field(..., description="티켓 ID")
    data_type: DataType = Field(..., description="데이터 타입")
    symbols: List[str] = Field(..., description="구독 중인 심볼 목록")
    created_at: datetime = Field(default_factory=datetime.now, description="구독 생성 시각")
    is_active: bool = Field(True, description="활성 상태")
    message_count: int = Field(0, description="수신된 메시지 수")
    last_message_at: Optional[datetime] = Field(None, description="마지막 메시지 수신 시각")

    def update_message_received(self):
        """메시지 수신 시 상태 업데이트"""
        self.message_count += 1
        self.last_message_at = datetime.now()


class MessageType(str, Enum):
    """WebSocket 메시지 타입"""
    TICKER = "ticker"
    TRADE = "trade"
    ORDERBOOK = "orderbook"
    CANDLE = "candle"
    MY_ORDER = "myOrder"
    MY_ASSET = "myAsset"


class ConnectionStatus(BaseModel):
    """WebSocket 연결 상태"""
    state: str = Field(..., description="현재 상태")
    connection_id: str = Field(..., description="연결 ID")
    connected_at: datetime = Field(..., description="연결 시각")
    uptime_seconds: float = Field(..., description="연결 지속 시간 (초)")
    message_count: int = Field(0, description="수신 메시지 수")
    error_count: int = Field(0, description="오류 수")
    active_subscriptions: int = Field(0, description="활성 구독 수")
    last_message_at: datetime = Field(..., description="마지막 메시지 수신 시각")
