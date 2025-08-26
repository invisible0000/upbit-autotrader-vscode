"""
스마트 라우팅 시스템 V2.0 모델 정의

데이터 요청, 채널 결정, 분석 결과 등을 위한 타입 정의
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Literal
from datetime import datetime
from enum import Enum


class ChannelType(Enum):
    """통신 채널 타입"""
    WEBSOCKET = "websocket"
    REST_API = "rest_api"


class DataType(Enum):
    """데이터 타입"""
    TICKER = "ticker"
    ORDERBOOK = "orderbook"
    TRADES = "trades"
    CANDLES = "candles"
    CANDLES_1S = "candles_1s"
    ACCOUNTS = "accounts"
    ORDERS = "orders"
    DEPOSITS = "deposits"
    WITHDRAWS = "withdraws"


class RealtimePriority(Enum):
    """실시간성 우선순위"""
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class FrequencyCategory(Enum):
    """요청 빈도 카테고리"""
    HIGH_FREQUENCY = "high_frequency"  # < 2초 간격
    MEDIUM_FREQUENCY = "medium_frequency"  # 2-10초 간격
    LOW_FREQUENCY = "low_frequency"  # > 10초 간격
    UNKNOWN = "unknown"


@dataclass
class DataRequest:
    """데이터 요청 정보"""
    symbols: List[str]
    data_type: DataType
    realtime_priority: RealtimePriority = RealtimePriority.MEDIUM
    count: Optional[int] = None
    interval: Optional[str] = None  # 캔들 간격 (예: "1m", "5m", "1h", "1d")
    to: Optional[str] = None  # 조회 기간 종료 시각 (ISO 8601 형식)
    request_id: Optional[str] = None
    requested_at: datetime = field(default_factory=datetime.now)

    # 내부 분석용
    frequency: float = 0.0  # 요청/초
    data_size_estimate: int = 0  # 예상 데이터 크기


@dataclass
class ChannelDecision:
    """채널 선택 결정"""
    channel: ChannelType
    reason: str
    confidence: float
    scores: Optional[Dict[str, float]] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    decided_at: datetime = field(default_factory=datetime.now)


@dataclass
class FrequencyAnalysis:
    """요청 빈도 분석 결과"""
    category: FrequencyCategory
    avg_interval: float
    trend: Literal["accelerating", "decelerating", "stable"]
    confidence: float = 0.0
    sample_size: int = 0


@dataclass
class RoutingMetrics:
    """라우팅 성능 메트릭 - 캐시 메트릭 제거"""
    total_requests: int = 0
    websocket_requests: int = 0
    rest_requests: int = 0
    avg_response_time_ms: float = 0.0
    accuracy_rate: float = 0.0
    # 🚀 cache_hit_ratio 제거: SmartDataProvider에서 관리
    websocket_uptime: float = 0.0

    # 시간별 통계
    last_updated: datetime = field(default_factory=datetime.now)
    hourly_stats: Dict[str, Any] = field(default_factory=dict)


@dataclass
class EndpointConfig:
    """엔드포인트별 설정"""
    data_type: DataType
    supported_channels: List[ChannelType]
    preferred_channel: Optional[ChannelType] = None
    fixed_channel: Optional[ChannelType] = None
    description: str = ""


# 고정 채널 규칙 정의 (진정한 API 제약 사항만)
REST_ONLY_ENDPOINTS = {
    DataType.ACCOUNTS: EndpointConfig(
        data_type=DataType.ACCOUNTS,
        supported_channels=[ChannelType.REST_API],
        fixed_channel=ChannelType.REST_API,
        description="계정 정보는 REST만 지원"
    ),
    DataType.ORDERS: EndpointConfig(
        data_type=DataType.ORDERS,
        supported_channels=[ChannelType.REST_API],
        fixed_channel=ChannelType.REST_API,
        description="주문 관리는 REST만 지원"
    ),
    DataType.DEPOSITS: EndpointConfig(
        data_type=DataType.DEPOSITS,
        supported_channels=[ChannelType.REST_API],
        fixed_channel=ChannelType.REST_API,
        description="입출금 내역은 REST만 지원"
    ),
    DataType.WITHDRAWS: EndpointConfig(
        data_type=DataType.WITHDRAWS,
        supported_channels=[ChannelType.REST_API],
        fixed_channel=ChannelType.REST_API,
        description="출금 내역은 REST만 지원"
    )
}

WEBSOCKET_ONLY_ENDPOINTS = {
    # 현재는 없음 - 모든 시세 데이터는 양쪽 지원
}

FLEXIBLE_ENDPOINTS = {
    DataType.TICKER: EndpointConfig(
        data_type=DataType.TICKER,
        supported_channels=[ChannelType.WEBSOCKET, ChannelType.REST_API],
        preferred_channel=ChannelType.WEBSOCKET,
        description="실시간성 vs 안정성"
    ),
    DataType.ORDERBOOK: EndpointConfig(
        data_type=DataType.ORDERBOOK,
        supported_channels=[ChannelType.WEBSOCKET, ChannelType.REST_API],
        preferred_channel=ChannelType.WEBSOCKET,
        description="실시간성 vs 안정성"
    ),
    DataType.TRADES: EndpointConfig(
        data_type=DataType.TRADES,
        supported_channels=[ChannelType.WEBSOCKET, ChannelType.REST_API],
        preferred_channel=ChannelType.WEBSOCKET,
        description="실시간성 vs 과거 데이터"
    ),
    DataType.CANDLES: EndpointConfig(
        data_type=DataType.CANDLES,
        supported_channels=[ChannelType.WEBSOCKET, ChannelType.REST_API],
        preferred_channel=ChannelType.WEBSOCKET,  # 다중 타임프레임 실시간 전략 효율성 우선
        description="실시간 다중 타임프레임 vs 과거 데이터 조회"
    ),
    DataType.CANDLES_1S: EndpointConfig(
        data_type=DataType.CANDLES_1S,
        supported_channels=[ChannelType.WEBSOCKET, ChannelType.REST_API],
        preferred_channel=ChannelType.WEBSOCKET,
        description="초단위 실시간 캔들"
    )
}

# 모든 엔드포인트 설정 통합
ALL_ENDPOINT_CONFIGS = {
    **REST_ONLY_ENDPOINTS,
    **WEBSOCKET_ONLY_ENDPOINTS,
    **FLEXIBLE_ENDPOINTS
}
