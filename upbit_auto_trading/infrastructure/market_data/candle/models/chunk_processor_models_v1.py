"""
ChunkProcessor 전용 데이터 모델

Created: 2025-09-23
Purpose: ChunkProcessor의 4단계 파이프라인에서 사용할 결과 객체들 정의
Features: 각 Phase별 처리 결과를 구조화하여 타입 안전성과 디버깅 용이성 확보
Architecture: DDD Infrastructure 계층, Immutable 데이터 구조
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, Any, List, Optional, Tuple
from enum import Enum


@dataclass
class ExecutionPlan:
    """청크 실행 계획

    Phase 1에서 생성되어 전체 파이프라인의 실행 전략을 결정합니다.
    겹침 분석 결과를 바탕으로 API 호출 최적화와 조기 종료 판단을 수행합니다.
    """
    strategy: str  # 'skip_complete_overlap', 'partial_fetch', 'full_fetch'
    should_skip_api_call: bool
    optimized_api_params: Dict[str, Any]
    expected_data_range: Tuple[datetime, datetime]
    overlap_optimization: bool = True

    def get_optimized_api_params(self) -> Dict[str, Any]:
        """겹침 분석 기반 최적화된 API 파라미터 반환"""
        return self.optimized_api_params.copy()


@dataclass
class OverlapAnalysis:
    """겹침 분석 결과

    OverlapAnalyzer의 결과를 구조화하여 ExecutionPlan 수립에 활용합니다.
    """
    overlap_result: Any  # OverlapResult 객체 (순환 import 방지를 위해 Any 사용)
    analysis_time: datetime
    optimization_applied: bool
    recommendations: List[str] = field(default_factory=list)


@dataclass
class ValidationResult:
    """데이터 검증 결과"""
    is_valid: bool
    has_critical_errors: bool
    validation_messages: List[str] = field(default_factory=list)
    validation_time: datetime = field(default_factory=lambda: datetime.now())


@dataclass
class ApiResponse:
    """API 응답 래퍼

    Phase 2에서 생성되어 API 호출 결과와 검증 정보를 포함합니다.
    업비트 데이터 끝 도달 감지와 조기 종료 판단을 위한 정보를 제공합니다.
    """
    raw_data: List[Dict[str, Any]]
    validation_result: ValidationResult
    has_upbit_data_end: bool
    requires_early_exit: bool
    response_metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ProcessedData:
    """처리된 캔들 데이터

    Phase 3에서 생성되어 빈 캔들 처리와 데이터 정규화 결과를 포함합니다.
    """
    candles: List[Dict[str, Any]]
    gap_filled_count: int
    processing_metadata: Dict[str, Any]
    validation_passed: bool


@dataclass
class StorageResult:
    """데이터 저장 결과

    Phase 4에서 생성되어 Repository를 통한 데이터 저장 결과를 포함합니다.
    """
    saved_count: int
    expected_count: int
    storage_time: datetime
    validation_passed: bool
    metadata: Dict[str, Any]


class ChunkResultStatus(Enum):
    """청크 처리 결과 상태"""
    SUCCESS = "success"
    SKIPPED = "skipped"
    EARLY_EXIT = "early_exit"
    ERROR = "error"


@dataclass
class ChunkResult:
    """청크 처리 최종 결과

    전체 파이프라인 실행 결과를 포함하는 최상위 결과 객체입니다.
    성공/실패 여부, 처리 성능, 메타데이터를 포함합니다.
    """
    success: bool
    status: ChunkResultStatus
    chunk_id: str
    saved_count: int
    processing_time_ms: float
    phases_completed: List[str]
    metadata: Dict[str, Any] = field(default_factory=dict)
    error: Optional[Exception] = None

    def is_successful(self) -> bool:
        """성공 여부 확인"""
        return self.success and self.error is None and self.status == ChunkResultStatus.SUCCESS

    def get_performance_summary(self) -> Dict[str, Any]:
        """성능 요약 정보 반환"""
        return {
            "processing_time_ms": self.processing_time_ms,
            "phases_completed": len(self.phases_completed),
            "saved_count": self.saved_count,
            "status": self.status.value
        }


# 팩토리 함수들

def create_skip_result(execution_plan: ExecutionPlan, chunk_id: str) -> ChunkResult:
    """완전 겹침으로 인한 스킵 결과 생성"""
    return ChunkResult(
        success=True,
        status=ChunkResultStatus.SKIPPED,
        chunk_id=chunk_id,
        saved_count=0,
        processing_time_ms=0.0,
        phases_completed=["preparation"],
        metadata={
            "skip_reason": "complete_overlap",
            "strategy": execution_plan.strategy
        }
    )


def create_early_exit_result(api_response: ApiResponse, chunk_id: str,
                             processing_time_ms: float) -> ChunkResult:
    """업비트 데이터 끝 도달로 인한 조기 종료 결과 생성"""
    return ChunkResult(
        success=True,
        status=ChunkResultStatus.EARLY_EXIT,
        chunk_id=chunk_id,
        saved_count=len(api_response.raw_data),
        processing_time_ms=processing_time_ms,
        phases_completed=["preparation", "api_fetch"],
        metadata={
            "early_exit_reason": "upbit_data_end",
            "response_count": len(api_response.raw_data)
        }
    )


def create_success_result(storage_result: StorageResult, chunk_id: str,
                          processing_time_ms: float) -> ChunkResult:
    """정상 처리 완료 결과 생성"""
    return ChunkResult(
        success=True,
        status=ChunkResultStatus.SUCCESS,
        chunk_id=chunk_id,
        saved_count=storage_result.saved_count,
        processing_time_ms=processing_time_ms,
        phases_completed=["preparation", "api_fetch", "data_processing", "data_storage"],
        metadata={
            "storage_validation": storage_result.validation_passed,
            "storage_metadata": storage_result.metadata
        }
    )


def create_error_result(error: Exception, chunk_id: str,
                        processing_time_ms: float = 0.0,
                        phases_completed: List[str] = None) -> ChunkResult:
    """오류 발생 결과 생성"""
    return ChunkResult(
        success=False,
        status=ChunkResultStatus.ERROR,
        chunk_id=chunk_id,
        saved_count=0,
        processing_time_ms=processing_time_ms,
        phases_completed=phases_completed or [],
        error=error,
        metadata={
            "error_message": str(error),
            "error_type": type(error).__name__
        }
    )
