"""
CandleDataProvider v4.0 데이터 모델 통합
업비트 특화 캔들 데이터 구조 및 API 요청/응답 모델
"""

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import List, Optional, Dict, Any, Union
from enum import Enum


class CandleTimeframe(Enum):
    """업비트 지원 캔들 타임프레임 (공식 API 기준)"""
    # 초 캔들 (최대 3개월)
    SEC_1 = "1s"

    # 분 캔들 (Unit 지원: 1, 3, 5, 10, 15, 30, 60, 240)
    MIN_1 = "1m"
    MIN_3 = "3m"
    MIN_5 = "5m"
    MIN_10 = "10m"
    MIN_15 = "15m"
    MIN_30 = "30m"
    MIN_60 = "60m"   # 1시간
    MIN_240 = "240m"  # 4시간

    # 일/주/월/연 캔들
    DAY_1 = "1d"
    WEEK_1 = "1w"
    MONTH_1 = "1M"
    YEAR_1 = "1y"

    @property
    def api_endpoint(self) -> str:
        """업비트 API 엔드포인트 생성"""
        if self == self.SEC_1:
            return "seconds"
        elif self.value.endswith('m'):
            unit = self.value[:-1]
            return f"minutes/{unit}"
        elif self == self.DAY_1:
            return "days"
        elif self == self.WEEK_1:
            return "weeks"
        elif self == self.MONTH_1:
            return "months"
        elif self == self.YEAR_1:
            return "years"
        else:
            raise ValueError(f"지원하지 않는 타임프레임: {self.value}")

    @property
    def has_data_limit(self) -> bool:
        """데이터 조회 제한 여부 (초 캔들은 3개월)"""
        return self == self.SEC_1

    @classmethod
    def from_string(cls, timeframe: str) -> 'CandleTimeframe':
        """문자열에서 타임프레임 변환"""
        # 하위 호환성을 위한 매핑
        mapping = {
            "1h": cls.MIN_60,
            "4h": cls.MIN_240,
            "1y": cls.YEAR_1
        }

        timeframe_normalized = mapping.get(timeframe, timeframe)

        for tf in cls:
            if tf.value == timeframe_normalized:
                return tf

        raise ValueError(f"지원하지 않는 타임프레임: {timeframe}")


@dataclass
class CandleData:
    """
    업비트 캔들 데이터 모델 (공식 API 응답 완전 호환)

    모든 캔들 타입(초/분/일/주/월/연)의 공통 필드와 선택적 필드 지원
    """
    # 공통 필드 (모든 캔들 타입)
    market: str
    candle_date_time_utc: datetime
    candle_date_time_kst: datetime
    opening_price: Decimal
    high_price: Decimal
    low_price: Decimal
    trade_price: Decimal  # 종가
    timestamp: int
    candle_acc_trade_price: Decimal
    candle_acc_trade_volume: Decimal

    # 분 캔들 전용 필드
    unit: Optional[int] = None

    # 일/주/월/연 캔들 전용 필드
    prev_closing_price: Optional[Decimal] = None
    change_price: Optional[Decimal] = None
    change_rate: Optional[Decimal] = None

    # 연 캔들 전용 필드
    first_day_of_period: Optional[str] = None

    # 시스템 필드
    created_at: Optional[datetime] = None

    @classmethod
    def from_upbit_api(cls, api_data: Dict[str, Any], timeframe: Optional[str] = None) -> 'CandleData':
        """
        업비트 API 응답에서 CandleData 객체 생성

        Args:
            api_data: 업비트 API 응답 딕셔너리
            timeframe: 타임프레임 정보 (선택적 필드 처리용)

        Returns:
            CandleData 객체
        """
        # UTC 시간 파싱 (Z 제거)
        utc_time_str = api_data['candle_date_time_utc']
        if utc_time_str.endswith('Z'):
            utc_time_str = utc_time_str[:-1] + '+00:00'

        return cls(
            market=api_data['market'],
            candle_date_time_utc=datetime.fromisoformat(utc_time_str),
            candle_date_time_kst=datetime.fromisoformat(api_data['candle_date_time_kst']),
            opening_price=Decimal(str(api_data['opening_price'])),
            high_price=Decimal(str(api_data['high_price'])),
            low_price=Decimal(str(api_data['low_price'])),
            trade_price=Decimal(str(api_data['trade_price'])),
            timestamp=api_data['timestamp'],
            candle_acc_trade_price=Decimal(str(api_data['candle_acc_trade_price'])),
            candle_acc_trade_volume=Decimal(str(api_data['candle_acc_trade_volume'])),

            # 분 캔들 전용 필드
            unit=api_data.get('unit'),

            # 일/주/월/연 캔들 전용 필드
            prev_closing_price=Decimal(str(api_data['prev_closing_price'])) if 'prev_closing_price' in api_data else None,
            change_price=Decimal(str(api_data['change_price'])) if 'change_price' in api_data else None,
            change_rate=Decimal(str(api_data['change_rate'])) if 'change_rate' in api_data else None,

            # 연 캔들 전용 필드
            first_day_of_period=api_data.get('first_day_of_period')
        )

    def to_dict(self) -> Dict[str, Any]:
        """딕셔너리 형태로 변환 (7규칙 전략 호환)"""
        result = {
            'market': self.market,
            'candle_date_time_utc': self.candle_date_time_utc.isoformat() + 'Z',
            'candle_date_time_kst': self.candle_date_time_kst.isoformat(),
            'opening_price': float(self.opening_price),
            'high_price': float(self.high_price),
            'low_price': float(self.low_price),
            'trade_price': float(self.trade_price),
            'timestamp': self.timestamp,
            'candle_acc_trade_price': float(self.candle_acc_trade_price),
            'candle_acc_trade_volume': float(self.candle_acc_trade_volume)
        }

        # 선택적 필드 추가
        if self.unit is not None:
            result['unit'] = self.unit
        if self.prev_closing_price is not None:
            result['prev_closing_price'] = float(self.prev_closing_price)
        if self.change_price is not None:
            result['change_price'] = float(self.change_price)
        if self.change_rate is not None:
            result['change_rate'] = float(self.change_rate)
        if self.first_day_of_period:
            result['first_day_of_period'] = self.first_day_of_period

        return result

    def to_db_tuple(self) -> tuple:
        """데이터베이스 INSERT를 위한 튜플 변환"""
        return (
            self.market,
            self.candle_date_time_utc,
            self.candle_date_time_kst,
            self.opening_price,
            self.high_price,
            self.low_price,
            self.trade_price,
            self.timestamp,
            self.candle_acc_trade_price,
            self.candle_acc_trade_volume,
            self.unit,
            self.prev_closing_price,
            self.change_price,
            self.change_rate,
            self.first_day_of_period
        )

    @property
    def is_daily_or_longer(self) -> bool:
        """일/주/월/연 캔들 여부 (변화율 정보 포함)"""
        return self.prev_closing_price is not None

    @property
    def is_minute_candle(self) -> bool:
        """분 캔들 여부 (unit 정보 포함)"""
        return self.unit is not None

    @property
    def is_yearly_candle(self) -> bool:
        """연 캔들 여부 (first_day_of_period 포함)"""
        return self.first_day_of_period is not None


@dataclass
class ApiRequest:
    """
    업비트 API 요청 모델 (4단계 최적화용)
    """
    symbol: str
    timeframe: Union[str, CandleTimeframe]
    count: int
    to: Optional[datetime] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None

    def to_upbit_params(self) -> Dict[str, Any]:
        """업비트 API 파라미터로 변환"""
        params = {
            'market': self.symbol,
            'count': min(self.count, 200)  # 업비트 200개 제한
        }

        if self.to:
            params['to'] = self.to.strftime('%Y-%m-%dT%H:%M:%S+09:00')

        return params

    @property
    def api_endpoint(self) -> str:
        """업비트 API 엔드포인트 반환"""
        if isinstance(self.timeframe, CandleTimeframe):
            return self.timeframe.api_endpoint
        # 문자열인 경우 변환 시도
        try:
            return CandleTimeframe(self.timeframe).api_endpoint
        except ValueError:
            # 기본값으로 분봉 사용
            return CandleTimeframe.MIN_1.api_endpoint


@dataclass
class OptimizationResult:
    """
    4단계 최적화 결과 모델
    """
    api_requests: List[ApiRequest]
    optimization_stage: str  # "complete_overlap", "partial_overlap", "fragmented", "no_overlap"
    api_calls_saved: int
    cache_hit_segments: int
    db_segments: int

    @property
    def total_api_requests(self) -> int:
        """총 API 요청 수"""
        return len(self.api_requests)

    @property
    def optimization_rate(self) -> float:
        """최적화율 (0.0 ~ 1.0)"""
        if self.api_calls_saved == 0:
            return 0.0
        total_calls = self.total_api_requests + self.api_calls_saved
        return self.api_calls_saved / total_calls if total_calls > 0 else 0.0


@dataclass
class CacheKey:
    """
    캐시 키 모델 (심볼별 캐시 관리)
    """
    symbol: str
    timeframe: str
    start_time: datetime
    count: int

    def __str__(self) -> str:
        """캐시 키 문자열 생성"""
        return f"{self.symbol}:{self.timeframe}:{self.start_time.isoformat()}:{self.count}"

    @classmethod
    def from_string(cls, key_str: str) -> 'CacheKey':
        """문자열에서 캐시 키 복원"""
        parts = key_str.split(':')
        if len(parts) != 4:
            raise ValueError(f"잘못된 캐시 키 형식: {key_str}")

        return cls(
            symbol=parts[0],
            timeframe=parts[1],
            start_time=datetime.fromisoformat(parts[2]),
            count=int(parts[3])
        )


@dataclass
class TableInfo:
    """
    개별 테이블 정보 모델
    """
    table_name: str
    symbol: str
    timeframe: str
    row_count: int
    size_mb: float
    created_at: datetime
    last_updated: datetime

    @property
    def is_valid(self) -> bool:
        """테이블 유효성 검사"""
        return (
            self.table_name.startswith('candles_')
            and '_' in self.symbol
            and any(self.timeframe == tf.value for tf in CandleTimeframe)
        )


@dataclass
class PerformanceMetrics:
    """
    성능 지표 모델 (모니터링용)
    """
    symbol: str
    timeframe: str
    response_time_ms: float
    cache_hit_rate: float
    api_call_reduction: float
    optimization_stage: str
    table_size_mb: float
    fragmentation_rate: float
    time_consistency_rate: float

    def to_dict(self) -> Dict[str, Any]:
        """딕셔너리로 변환 (로깅용)"""
        return {
            'symbol': self.symbol,
            'timeframe': self.timeframe,
            'response_time_ms': self.response_time_ms,
            'cache_hit_rate': self.cache_hit_rate,
            'api_call_reduction': self.api_call_reduction,
            'optimization_stage': self.optimization_stage,
            'table_size_mb': self.table_size_mb,
            'fragmentation_rate': self.fragmentation_rate,
            'time_consistency_rate': self.time_consistency_rate
        }


@dataclass
class SyncProgress:
    """
    대용량 동기화 진행률 모델
    """
    symbol: str
    timeframe: str
    total_periods: int
    completed_periods: int
    api_calls_made: int
    api_calls_saved: int
    start_time: datetime
    estimated_completion: Optional[datetime] = None

    @property
    def progress_rate(self) -> float:
        """진행률 (0.0 ~ 1.0)"""
        return self.completed_periods / self.total_periods if self.total_periods > 0 else 0.0

    @property
    def api_efficiency(self) -> float:
        """API 효율성 (절약된 호출 비율)"""
        total_calls = self.api_calls_made + self.api_calls_saved
        return self.api_calls_saved / total_calls if total_calls > 0 else 0.0
