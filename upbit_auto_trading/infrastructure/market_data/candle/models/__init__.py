"""
📝 Candle Data Models Package
캔들 데이터 관련 모델들의 통합 패키지 - 정리된 버전

Created: 2025-09-25 (Restructured)
Purpose: candle_data_models와 candle_business_models의 명확한 분리

현재 구조:
- candle_data_models: 순수 데이터 모델 (CandleData, CandleDataResponse)
- candle_business_models: 비즈니스 로직 모델 (RequestInfo, ChunkInfo, CollectionResult, Enum 등)
"""

# === 순수 데이터 모델 (candle_data_models.py) ===
from .candle_data_models import (
    # 핵심 데이터 모델
    CandleData,
    CandleDataResponse,
)

# === 비즈니스 로직 모델 (candle_business_models.py) ===
from .candle_business_models import (
    # Enum 타입 (소스의 원천)
    OverlapStatus,
    ChunkStatus,
    RequestType,

    # 핵심 비즈니스 모델
    RequestInfo,
    CollectionPlan,
    CollectionResult,
    ChunkInfo,
    OverlapRequest,
    OverlapResult,

    # 헬퍼 함수들
    should_complete_collection,
    create_collection_plan,
)

# === Legacy 호환을 위한 별칭 정의 ===
# CandleDataProvider에서 사용하는 모델들에 대한 별칭
CollectionState = dict  # Legacy 호환: 딕셔너리로 간주


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
    # 순수 데이터 모델
    'CandleData', 'CandleDataResponse',

    # Enum 타입 (소스의 원천)
    'OverlapStatus', 'ChunkStatus', 'RequestType',

    # 비즈니스 로직 모델
    'RequestInfo', 'CollectionPlan', 'CollectionResult', 'ChunkInfo',
    'OverlapRequest', 'OverlapResult',

    # 헬퍼 함수들
    'should_complete_collection', 'create_collection_plan',

    # Legacy 호환
    'CollectionState',

    # 편의성 함수
    'create_success_response', 'create_error_response',
]

# === 버전 정보 ===
__version__ = "3.1.0"
__author__ = "Upbit AutoTrader"
__description__ = "Restructured candle data models with clear separation of concerns"
