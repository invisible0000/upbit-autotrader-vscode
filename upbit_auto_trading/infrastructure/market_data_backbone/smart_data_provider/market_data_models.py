"""
Market Data Models - 통합 모델 시스템

모든 SmartDataProvider V4.0의 데이터 모델을 통합 관리
- DataResponse, Priority (핵심 API 모델)
- CacheModels (캐시 성능 지표)
- CollectionModels (빈 캔들 추적)
- 성능 지표 모델
"""
from dataclasses import dataclass, field
from typing import Dict, Any, Optional, Union, List
from datetime import datetime
from enum import Enum
from decimal import Decimal


# =====================================
# � 데이터 소스 유형 정의
# =====================================

class DataSourceType(Enum):
    """데이터 소스 유형"""
    WEBSOCKET = "websocket"        # 실시간 웹소켓 데이터
    REST_API = "rest_api"          # REST API 호출
    CACHE = "cache"                # 캐시된 데이터
    DATABASE = "database"          # 로컬 DB 데이터
    HYBRID = "hybrid"              # 혼합 (캐시 + API)
    SIMULATION = "simulation"      # 시뮬레이션 데이터
    ERROR = "error"                # 에러 상태


class StreamType(Enum):
    """스트림 유형 (웹소켓 전용)"""
    TICKER = "ticker"              # 현재가 스트림
    ORDERBOOK = "orderbook"        # 호가 스트림
    TRADE = "trade"                # 체결 스트림
    CANDLE_1M = "candle_1m"        # 1분 캔들 스트림
    CANDLE_5M = "candle_5m"        # 5분 캔들 스트림
    CANDLE_15M = "candle_15m"      # 15분 캔들 스트림
    CANDLE_1H = "candle_1h"        # 1시간 캔들 스트림
    CANDLE_4H = "candle_4h"        # 4시간 캔들 스트림
    CANDLE_1D = "candle_1d"        # 일 캔들 스트림
    UNKNOWN = "unknown"            # 알 수 없는 스트림


# =====================================
# �🎯 핵심 API 모델
# =====================================

@dataclass
class DataResponse:
    """
    통합 데이터 응답 모델

    모든 API 메서드의 표준 응답 형식
    - 데이터 소스 유형 명확화
    - 웹소켓/REST API 구분
    - 스트림 정보 포함
    """
    success: bool
    data: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
    cache_hit: bool = False
    response_time_ms: float = 0.0

    # 🌐 데이터 소스 정보 (개선됨)
    data_source: str = "unknown"           # 기존 호환성 유지
    data_source_type: DataSourceType = DataSourceType.REST_API  # 명확한 타입
    stream_type: Optional[StreamType] = None  # 웹소켓 스트림 타입

    # 📊 실시간 데이터 메타데이터
    is_realtime: bool = False              # 실시간 데이터 여부
    data_timestamp: Optional[datetime] = None  # 데이터 생성 시각
    server_timestamp: Optional[datetime] = None  # 서버 응답 시각

    @classmethod
    def create_success(cls, data: Dict[str, Any], **metadata) -> 'DataResponse':
        """성공 응답 생성"""
        # 데이터 소스 타입 자동 판단
        data_source = metadata.get('data_source', 'api')
        data_source_type = cls._determine_source_type(data_source, metadata)
        stream_type = cls._determine_stream_type(metadata)

        # 웹소켓 데이터인 경우 stream_type을 data에도 추가
        if data_source_type == DataSourceType.WEBSOCKET and stream_type:
            if isinstance(data, dict):
                data = data.copy()  # 원본 수정 방지
                data['stream_type'] = stream_type.value

        return cls(
            success=True,
            data=data,
            cache_hit=metadata.get('cache_hit', False),
            response_time_ms=metadata.get('response_time_ms', 0.0),
            data_source=data_source,
            data_source_type=data_source_type,
            stream_type=stream_type,
            is_realtime=data_source_type == DataSourceType.WEBSOCKET,
            data_timestamp=metadata.get('data_timestamp'),
            server_timestamp=metadata.get('server_timestamp', datetime.now())
        )

    @classmethod
    def create_error(cls, error: str, **metadata) -> 'DataResponse':
        """실패 응답 생성"""
        return cls(
            success=False,
            error_message=error,
            cache_hit=metadata.get('cache_hit', False),
            response_time_ms=metadata.get('response_time_ms', 0.0),
            data_source=metadata.get('data_source', 'error'),
            data_source_type=DataSourceType.ERROR,
            server_timestamp=datetime.now()
        )

    @classmethod
    def _determine_source_type(cls, data_source: str, metadata: Dict[str, Any]) -> DataSourceType:
        """데이터 소스 문자열에서 타입 판단"""
        data_source_lower = data_source.lower()

        if any(keyword in data_source_lower for keyword in ['websocket', 'ws', 'stream', 'realtime']):
            return DataSourceType.WEBSOCKET
        elif any(keyword in data_source_lower for keyword in ['cache', 'cached']):
            return DataSourceType.CACHE
        elif any(keyword in data_source_lower for keyword in ['database', 'db', 'local']):
            return DataSourceType.DATABASE
        elif any(keyword in data_source_lower for keyword in ['simulation', 'sim', 'mock']):
            return DataSourceType.SIMULATION
        elif any(keyword in data_source_lower for keyword in ['error', 'fail']):
            return DataSourceType.ERROR
        elif any(keyword in data_source_lower for keyword in ['hybrid', 'mixed']):
            return DataSourceType.HYBRID
        else:
            return DataSourceType.REST_API

    @classmethod
    def _determine_stream_type(cls, metadata: Dict[str, Any]) -> Optional[StreamType]:
        """메타데이터에서 스트림 타입 판단"""
        # 명시적 스트림 타입 지정
        if 'stream_type' in metadata:
            stream_value = metadata['stream_type']
            if isinstance(stream_value, StreamType):
                return stream_value
            elif isinstance(stream_value, str):
                try:
                    return StreamType(stream_value.lower())
                except ValueError:
                    return StreamType.UNKNOWN

        # 데이터 타입에서 추론
        data_type = metadata.get('data_type', '').lower()
        if data_type:
            if data_type == 'ticker':
                return StreamType.TICKER
            elif data_type == 'orderbook':
                return StreamType.ORDERBOOK
            elif data_type == 'trades' or data_type == 'trade':
                return StreamType.TRADE
            elif 'candle' in data_type:
                if '1m' in data_type:
                    return StreamType.CANDLE_1M
                elif '5m' in data_type:
                    return StreamType.CANDLE_5M
                elif '15m' in data_type:
                    return StreamType.CANDLE_15M
                elif '1h' in data_type:
                    return StreamType.CANDLE_1H
                elif '4h' in data_type:
                    return StreamType.CANDLE_4H
                elif '1d' in data_type:
                    return StreamType.CANDLE_1D

        return None

    def get(self, key: Optional[str] = None) -> Any:
        """키별 데이터 반환 또는 전체 Dict 반환"""
        if self.data is None:
            return {} if key else None
        if key:
            return self.data.get(key, {})
        return self.data

    def get_single(self, symbol: str) -> Dict[str, Any]:
        """단일 심볼 데이터 반환"""
        if self.data is None:
            return {}
        return self.data.get(symbol, {})

    def get_all(self) -> Dict[str, Any]:
        """전체 Dict 데이터 반환"""
        return self.data if self.data is not None else {}

    def is_websocket_data(self) -> bool:
        """웹소켓 데이터 여부"""
        return self.data_source_type == DataSourceType.WEBSOCKET

    def is_cached_data(self) -> bool:
        """캐시된 데이터 여부"""
        return self.data_source_type == DataSourceType.CACHE

    def is_api_data(self) -> bool:
        """REST API 데이터 여부"""
        return self.data_source_type == DataSourceType.REST_API

    def get_data_age_seconds(self) -> Optional[float]:
        """데이터 생성 후 경과 시간 (초)"""
        if self.data_timestamp:
            return (datetime.now() - self.data_timestamp).total_seconds()
        return None

    def to_dict(self) -> Dict[str, Any]:
        """딕셔너리 형태로 변환 (직렬화용)"""
        return {
            'success': self.success,
            'data': self.data,
            'error_message': self.error_message,
            'cache_hit': self.cache_hit,
            'response_time_ms': self.response_time_ms,
            'data_source': self.data_source,
            'data_source_type': self.data_source_type.value,
            'stream_type': self.stream_type.value if self.stream_type else None,
            'is_realtime': self.is_realtime,
            'data_timestamp': self.data_timestamp.isoformat() if self.data_timestamp else None,
            'server_timestamp': self.server_timestamp.isoformat() if self.server_timestamp else None
        }


class Priority(Enum):
    """
    통합 우선순위 시스템

    SmartRouter와 완전 호환되는 우선순위 정책
    """
    CRITICAL = 1    # 실거래봇 (< 50ms)
    HIGH = 2        # 실시간 모니터링 (< 100ms)
    NORMAL = 3      # 차트뷰어 (< 500ms)
    LOW = 4         # 백테스터 (백그라운드)

    @property
    def max_response_time_ms(self) -> float:
        """우선순위별 최대 응답 시간 (밀리초)"""
        response_times = {
            Priority.CRITICAL: 50.0,
            Priority.HIGH: 100.0,
            Priority.NORMAL: 500.0,
            Priority.LOW: 5000.0
        }
        return response_times[self]

    @property
    def description(self) -> str:
        """우선순위 설명"""
        descriptions = {
            Priority.CRITICAL: "실거래봇 (최우선)",
            Priority.HIGH: "실시간 모니터링",
            Priority.NORMAL: "차트뷰어",
            Priority.LOW: "백테스터 (백그라운드)"
        }
        return descriptions[self]

    @property
    def smart_router_priority(self) -> str:
        """SmartRouter 호환 우선순위 문자열"""
        mapping = {
            Priority.CRITICAL: "high",
            Priority.HIGH: "high",
            Priority.NORMAL: "normal",
            Priority.LOW: "low"
        }
        return mapping[self]

    def __str__(self) -> str:
        return self.description


# =====================================
# 💾 캐시 성능 모델
# =====================================

@dataclass(frozen=True)
class CacheItem:
    """캐시 아이템"""
    key: str
    data: Any
    cached_at: datetime
    ttl_seconds: float
    source: str  # "fast_cache", "memory_cache", "smart_router"

    @property
    def is_expired(self) -> bool:
        """만료 여부 확인"""
        age_seconds = (datetime.now() - self.cached_at).total_seconds()
        return age_seconds > self.ttl_seconds

    @property
    def age_seconds(self) -> float:
        """캐시 생성 후 경과 시간 (초)"""
        return (datetime.now() - self.cached_at).total_seconds()


@dataclass
class CacheMetrics:
    """캐시 성능 지표"""
    total_requests: int = 0
    cache_hits: int = 0
    cache_misses: int = 0
    fast_cache_hits: int = 0
    memory_cache_hits: int = 0
    smart_router_calls: int = 0

    @property
    def hit_rate(self) -> float:
        """전체 캐시 적중률 (%)"""
        if self.total_requests == 0:
            return 0.0
        return (self.cache_hits / self.total_requests) * 100

    @property
    def fast_cache_rate(self) -> float:
        """FastCache 적중률 (%)"""
        if self.total_requests == 0:
            return 0.0
        return (self.fast_cache_hits / self.total_requests) * 100


# =====================================
# 📊 수집 상태 모델
# =====================================

class CollectionStatus(Enum):
    """캔들 수집 상태"""
    COLLECTED = "COLLECTED"  # 정상 수집 완료
    EMPTY = "EMPTY"          # 거래가 없어서 빈 캔들
    PENDING = "PENDING"      # 아직 수집하지 않음
    FAILED = "FAILED"        # 수집 실패


@dataclass(frozen=True)
class CollectionStatusRecord:
    """수집 상태 레코드"""
    id: Optional[int]
    symbol: str
    timeframe: str
    target_time: datetime
    collection_status: CollectionStatus
    last_attempt_at: Optional[datetime] = None
    attempt_count: int = 0
    api_response_code: Optional[int] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    @classmethod
    def create_pending(cls, symbol: str, timeframe: str, target_time: datetime) -> 'CollectionStatusRecord':
        """새로운 PENDING 상태 레코드 생성"""
        return cls(
            id=None,
            symbol=symbol,
            timeframe=timeframe,
            target_time=target_time,
            collection_status=CollectionStatus.PENDING,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )


@dataclass
class CandleWithStatus:
    """상태가 포함된 캔들 데이터"""
    # 캔들 데이터
    symbol: str
    timeframe: str
    timestamp: datetime
    open_price: Optional[Decimal] = None
    high_price: Optional[Decimal] = None
    low_price: Optional[Decimal] = None
    close_price: Optional[Decimal] = None
    volume: Optional[Decimal] = None

    # 상태 정보
    collection_status: CollectionStatus = CollectionStatus.PENDING
    is_empty: bool = False


# =====================================
# 📈 성능 지표 모델
# =====================================

@dataclass
class PerformanceMetrics:
    """성능 지표"""
    # 요청 통계
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0

    # 응답 시간 통계
    avg_response_time_ms: float = 0.0
    min_response_time_ms: float = 0.0
    max_response_time_ms: float = 0.0

    # 캐시 통계
    cache_metrics: CacheMetrics = field(default_factory=CacheMetrics)

    # 데이터 통계
    symbols_per_second: float = 0.0
    data_volume_mb: float = 0.0

    @property
    def success_rate(self) -> float:
        """성공률 (%)"""
        if self.total_requests == 0:
            return 0.0
        return (self.successful_requests / self.total_requests) * 100


# =====================================
# 🌐 시장 상황 모델
# =====================================

class MarketCondition(Enum):
    """시장 상황"""
    ACTIVE = "ACTIVE"           # 활발한 거래 (높은 변동성)
    NORMAL = "NORMAL"           # 정상 거래
    QUIET = "QUIET"             # 조용한 거래 (낮은 변동성)
    CLOSED = "CLOSED"           # 시장 휴무
    UNKNOWN = "UNKNOWN"         # 상황 불명


class TimeZoneActivity(Enum):
    """시간대별 활동성"""
    ASIA_PRIME = "ASIA_PRIME"       # 아시아 주 거래시간 (09:00-18:00 KST)
    EUROPE_PRIME = "EUROPE_PRIME"   # 유럽 주 거래시간 (15:00-24:00 KST)
    US_PRIME = "US_PRIME"           # 미국 주 거래시간 (22:00-07:00 KST)
    OFF_HOURS = "OFF_HOURS"         # 비활성 시간대


# =====================================
# ⏳ 백그라운드 작업 모델
# =====================================

class TaskStatus(Enum):
    """작업 상태"""
    PENDING = "pending"        # 대기 중
    RUNNING = "running"        # 실행 중
    COMPLETED = "completed"    # 완료
    FAILED = "failed"          # 실패
    CANCELLED = "cancelled"    # 취소


@dataclass
class ProgressStep:
    """진행률 스텝"""
    step_id: str
    description: str
    total_items: int
    completed_items: int = 0
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error: Optional[str] = None

    @property
    def progress_percentage(self) -> float:
        """진행률 (%)"""
        if self.total_items == 0:
            return 100.0
        return min(100.0, (self.completed_items / self.total_items) * 100)

    @property
    def is_completed(self) -> bool:
        """완료 여부"""
        return self.completed_items >= self.total_items
