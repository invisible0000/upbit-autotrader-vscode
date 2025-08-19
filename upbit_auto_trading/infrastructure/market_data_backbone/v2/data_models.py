"""
MarketDataBackbone V2 - 데이터 모델 및 구조체

데이터 통합에 사용되는 모든 데이터 클래스와 열거형을 정의합니다.
"""

from typing import Tuple
from decimal import Decimal
from datetime import datetime
from dataclasses import dataclass
from enum import Enum

from .market_data_backbone import TickerData


class DataSource(Enum):
    """데이터 소스 열거형"""
    REST = "rest"
    WEBSOCKET = "websocket"
    WEBSOCKET_SIMPLE = "websocket_simple"
    CACHED = "cached"


class DataQuality(Enum):
    """데이터 품질 등급"""
    HIGH = "high"           # 완전한 데이터, 모든 필드 검증 통과
    MEDIUM = "medium"       # 일부 필드 누락 또는 추정값 포함
    LOW = "low"             # 필수 필드만 존재, 검증 실패 또는 오류 보정
    INVALID = "invalid"     # 사용 불가능한 데이터


@dataclass(frozen=True)
class NormalizedTickerData:
    """정규화된 티커 데이터 모델 (Phase 1.3)"""
    # 기본 TickerData 확장
    ticker_data: TickerData

    # 추가 메타데이터
    data_quality: DataQuality
    confidence_score: Decimal  # 0.0 ~ 1.0
    normalization_timestamp: datetime
    data_checksum: str

    # 검증 결과
    validation_errors: Tuple[str, ...]
    corrected_fields: Tuple[str, ...]

    # 성능 메트릭
    processing_time_ms: Decimal
    data_source_priority: int  # 1(최고) ~ 10(최저)


@dataclass
class CacheEntry:
    """캐시 엔트리 구조"""
    data: NormalizedTickerData
    created_at: datetime
    access_count: int
    last_access: datetime
    ttl_seconds: int


@dataclass
class ProcessingStats:
    """데이터 처리 통계"""
    total_processed: int
    cache_hits: int
    cache_misses: int
    normalization_errors: int
    validation_failures: int
    average_processing_time_ms: Decimal
    data_quality_distribution: dict  # DataQuality -> count
