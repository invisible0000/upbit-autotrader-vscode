"""
📝 Candle Data Models Package
캔들 데이터 관련 모델들의 통합 패키지

Created: 2025-09-22
Purpose: 모든 데이터 구조와 DTO 클래스들을 효율적으로 import할 수 있는 중앙화된 접점

구조:
- candle_core_models: 핵심 도메인 모델 (CandleData, Enum 등)
- candle_request_models: 요청/응답 관련 모델
- candle_cache_models: 캐시 시스템 모델
- candle_collection_models: 수집 프로세스 관리 모델
"""

# === 핵심 모델 (가장 자주 사용) ===
from .candle_core_models import (
    # Enum 타입
    OverlapStatus,
    ChunkStatus,

    # 핵심 데이터 모델
    CandleData,
    CandleDataResponse,
)

# === 요청/응답 모델 ===
from .candle_request_models import (
    CandleChunk,
    OverlapRequest,
    OverlapResult,
    TimeChunk,
    CollectionResult,
    RequestInfo,
)

# === 수집 프로세스 모델 ===
from .candle_collection_models import (
    CollectionState,
    CollectionPlan,
    ChunkInfo,
    ProcessingStats,
)

# === 캐시 모델 (선택적 import) ===
# 캐시 기능을 사용할 때만 명시적으로 import
# from .candle_cache_models import CacheKey, CacheEntry, CacheStats

# === 편의성 함수들 ===
def create_success_response(candles, data_source: str, response_time_ms: float) -> CandleDataResponse:
    """성공 응답 생성 헬퍼"""
    return CandleDataResponse(
        success=True,
        candles=candles,
        total_count=len(candles),
        data_source=data_source,
        response_time_ms=response_time_ms
    )

def create_error_response(error_message: str, response_time_ms: float) -> CandleDataResponse:
    """에러 응답 생성 헬퍼"""
    return CandleDataResponse(
        success=False,
        candles=[],
        total_count=0,
        data_source="error",
        response_time_ms=response_time_ms,
        error_message=error_message
    )

# === 공개 API 정의 ===
__all__ = [
    # 핵심 모델
    'OverlapStatus', 'ChunkStatus', 'CandleData', 'CandleDataResponse',

    # 요청/응답 모델
    'CandleChunk', 'OverlapRequest', 'OverlapResult', 'TimeChunk',
    'CollectionResult', 'RequestInfo',

    # 수집 프로세스 모델
    'CollectionState', 'CollectionPlan', 'ChunkInfo', 'ProcessingStats',

    # 편의성 함수
    'create_success_response', 'create_error_response',
]

# === 버전 정보 ===
__version__ = "2.0.0"
__author__ = "Upbit AutoTrader"
__description__ = "Candle data models with improved structure and separation of concerns"
