"""
📝 Candle Collection Models
캔들 데이터 수집 프로세스 관련 모델들

Created: 2025-09-22
Purpose: CollectionState, ChunkInfo, ProcessingStats 등 수집 과정 추적 모델
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import List, Optional, Dict, Any

# TYPE_CHECKING을 사용하여 순환 import 방지
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from .candle_core_models import OverlapStatus
    from .candle_request_models import OverlapResult


@dataclass
class CollectionState:
    """캔들 수집 상태 관리 - CandleDataProvider v4.0"""
    request_id: str
    symbol: str
    timeframe: str
    total_requested: int
    total_collected: int = 0
    completed_chunks: List['ChunkInfo'] = field(default_factory=list)
    current_chunk: Optional['ChunkInfo'] = None
    last_candle_time: Optional[str] = None  # 마지막 수집된 캔들 시간 (연속성용)
    estimated_total_chunks: int = 0
    estimated_completion_time: Optional[datetime] = None
    start_time: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    is_completed: bool = False
    error_message: Optional[str] = None

    # 남은 시간 추적 필드들
    last_update_time: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    avg_chunk_duration: float = 0.0  # 평균 청크 처리 시간 (초)
    remaining_chunks: int = 0  # 남은 청크 수
    estimated_remaining_seconds: float = 0.0  # 실시간 계산된 남은 시간


@dataclass
class CollectionPlan:
    """수집 계획 (최소 정보만) - CandleDataProvider v4.0"""
    total_count: int
    estimated_chunks: int
    estimated_duration_seconds: float
    first_chunk_params: Dict[str, Any]  # 첫 번째 청크 요청 파라미터

    def __post_init__(self):
        """계획 정보 검증"""
        if self.total_count <= 0:
            raise ValueError(f"총 개수는 1 이상이어야 합니다: {self.total_count}")
        if self.estimated_chunks <= 0:
            raise ValueError(f"예상 청크 수는 1 이상이어야 합니다: {self.estimated_chunks}")
        if self.estimated_duration_seconds < 0:
            raise ValueError(f"예상 소요시간은 0 이상이어야 합니다: {self.estimated_duration_seconds}")


@dataclass(frozen=False)  # 실시간 조정을 위해 mutable
class ChunkInfo:
    """
    CandleDataProvider v6.2 개별 청크 정보 - 전체 처리 단계 추적 지원

    실시간 시간 조정이 가능한 개별 청크 메타정보.
    청크 처리의 전체 단계를 추적하여 디버깅과 확장성을 향상시킴.

    추적 단계:
    1. 요청 단계: 오버랩 분석 결과 기반 API 요청 정보
    2. 응답 단계: 실제 API 응답으로부터 받은 캔들 정보
    3. 최종 단계: 빈 캔들 처리 완료 후 최종 결과 정보

    주요 기능:
    - 단계별 캔들 개수, 시작/종료 시간 추적
    - 전체 처리 과정 요약 정보 제공 (디버깅용)
    - 이전 청크 결과에 따른 동적 시간 범위 조정
    - temp_chunk 생성 제거로 성능 최적화
    """
    # === 청크 식별 정보 ===
    chunk_id: str                         # 청크 고유 식별자
    chunk_index: int                      # 청크 순서 (0부터 시작)
    symbol: str                           # 거래 심볼
    timeframe: str                        # 타임프레임

    # === 청크 파라미터 (실시간 조정 가능) ===
    count: int                            # 이 청크에서 요청할 캔들 개수
    to: Optional[datetime] = None         # 이 청크의 시작 캔들 시간
    end: Optional[datetime] = None        # 이 청크의 종료 시간

    # === 청크 처리 단계별 추적 필드들 ===
    overlap_status: Optional['OverlapStatus'] = None        # 겹침 분석 결과

    # === OverlapResult 통합 필드 (COMPLETE_OVERLAP 지원) ===
    # DB 기존 데이터 정보 (OverlapResult에서 추출)
    db_start: Optional[datetime] = None                     # DB 데이터 시작점
    db_end: Optional[datetime] = None                       # DB 데이터 종료점

    # 요청 단계 (오버랩 분석 결과)
    api_request_count: Optional[int] = None                 # 요청할 API 호출 개수 (부분 겹침 시)
    api_request_start: Optional[datetime] = None            # API 요청 시작점 (부분 겹침 시)
    api_request_end: Optional[datetime] = None              # API 요청 종료점 (부분 겹침 시)

    # 응답 단계 (실제 API 응답)
    api_response_count: Optional[int] = None                # 실제 받은 캔들 개수
    api_response_start: Optional[datetime] = None           # 응답 첫 캔들 시간
    api_response_end: Optional[datetime] = None             # 응답 마지막 캔들 시간

    # 최종 처리 단계 (빈 캔들 처리 후)
    final_candle_count: Optional[int] = None                # 최종 캔들 개수
    final_candle_start: Optional[datetime] = None           # 최종 첫 캔들 시간
    final_candle_end: Optional[datetime] = None             # 최종 마지막 캔들 시간

    # === 처리 상태 정보 ===
    status: str = "pending"               # pending, processing, completed, failed
    created_at: Optional[datetime] = field(default_factory=lambda: datetime.now(timezone.utc))

    # === 연결 정보 ===
    previous_chunk_id: Optional[str] = None   # 이전 청크 ID
    next_chunk_id: Optional[str] = None       # 다음 청크 ID

    def __post_init__(self):
        """청크 정보 검증 및 기본값 설정"""
        # ============================================
        # 🔍 VALIDATION ZONE - 성능 최적화시 제거 가능
        # ============================================
        if not self.chunk_id:
            raise ValueError("청크 ID는 필수입니다")
        if self.chunk_index < 0:
            raise ValueError(f"청크 인덱스는 0 이상이어야 합니다: {self.chunk_index}")
        if self.count < 1 or self.count > 200:
            raise ValueError(f"청크 count는 1~200 범위여야 합니다: {self.count}")
        if self.status not in ["pending", "processing", "completed", "failed"]:
            raise ValueError(f"잘못된 상태값: {self.status}")
        # ============================================
        # 🔍 END VALIDATION ZONE
        # ============================================

    def adjust_times(self, new_to: Optional[datetime] = None, new_end: Optional[datetime] = None) -> None:
        """실시간 시간 조정 (이전 청크 결과 반영)"""
        if new_to is not None:
            self.to = new_to
        if new_end is not None:
            self.end = new_end

    def mark_processing(self) -> None:
        """처리 중 상태로 변경"""
        self.status = "processing"

    def mark_completed(self) -> None:
        """완료 상태로 변경"""
        self.status = "completed"

    def mark_failed(self) -> None:
        """실패 상태로 변경"""
        self.status = "failed"

    def is_pending(self) -> bool:
        """대기 중 상태 확인"""
        return self.status == "pending"

    def is_completed(self) -> bool:
        """완료 상태 확인"""
        return self.status == "completed"

    def get_effective_end_time(self) -> Optional[datetime]:
        """
        청크가 실제로 다룬 데이터의 끝 시간 (우선순위 기반)

        COMPLETE_OVERLAP 상황에서도 db_end로 완전한 정보 제공!

        우선순위:
        1. final_candle_end: 빈 캔들 처리 후 최종 시간
        2. db_end: DB 기존 데이터 끝 (COMPLETE_OVERLAP 해결!)
        3. api_response_end: API 응답 마지막 시간
        4. end: 계획된 청크 끝점

        Returns:
            Optional[datetime]: 유효한 끝 시간, 없으면 None
        """
        # 1순위: 빈 캔들 처리 후 최종 시간
        if self.final_candle_end:
            return self.final_candle_end

        # 2순위: DB 기존 데이터 끝 (COMPLETE_OVERLAP 해결!)
        elif self.db_end:
            return self.db_end

        # 3순위: API 응답 마지막 시간
        elif self.api_response_end:
            return self.api_response_end

        # 4순위: 계획된 청크 끝점
        elif self.end:
            return self.end

        return None

    def get_time_source(self) -> str:
        """시간 정보 출처 반환 (디버깅용)"""
        if self.final_candle_end:
            return "final_processing"
        elif self.db_end:
            return "db_overlap"  # COMPLETE_OVERLAP 식별!
        elif self.api_response_end:
            return "api_response"
        elif self.end:
            return "planned"
        return "none"

    def has_complete_time_info(self) -> bool:
        """완전한 시간 정보 보유 여부"""
        return self.get_effective_end_time() is not None

    # === Overlap 최적화 메서드들 ===

    def set_overlap_info(self, overlap_result: 'OverlapResult', api_count: Optional[int] = None) -> None:
        """
        겹침 분석 결과를 ChunkInfo에 완전 통합

        OverlapResult의 모든 정보를 ChunkInfo로 이전하여
        COMPLETE_OVERLAP에서도 완전한 시간 정보 확보

        Args:
            overlap_result: OverlapAnalyzer 결과
            api_count: API 요청 개수 (선택적, 자동 계산 가능)
        """
        from upbit_auto_trading.infrastructure.logging import create_component_logger
        logger = create_component_logger("ChunkInfo")

        # 겹침 상태 설정
        self.overlap_status = overlap_result.status

        # DB 기존 데이터 정보 추출 (COMPLETE_OVERLAP 해결!)
        self.db_start = getattr(overlap_result, 'db_start', None)
        self.db_end = getattr(overlap_result, 'db_end', None)  # 핵심!

        # API 요청 정보 설정 (기존 필드 사용)
        self.api_request_start = overlap_result.api_start
        self.api_request_end = overlap_result.api_end

        # API 요청 개수 설정 (부분 겹침 시)
        if api_count is not None:
            self.api_request_count = api_count
        elif overlap_result.api_start and overlap_result.api_end:
            # API 요청 개수 자동 계산
            from upbit_auto_trading.infrastructure.market_data.candle.time_utils import TimeUtils
            self.api_request_count = TimeUtils.calculate_expected_count(
                overlap_result.api_start, overlap_result.api_end, self.timeframe
            )

        # 통합 검증 로깅
        logger.debug(f"OverlapResult 통합 완료: {self.chunk_id}")
        logger.debug(f"  overlap_status: {self.overlap_status}")
        logger.debug(f"  db_range: {self.db_start} ~ {self.db_end}")
        logger.debug(f"  api_request_range: {self.api_request_start} ~ {self.api_request_end}")
        logger.debug(f"  effective_end: {self.get_effective_end_time()}")
        logger.debug(f"  time_source: {self.get_time_source()}")

    def has_overlap_info(self) -> bool:
        """겹침 분석 정보 보유 여부 확인"""
        return self.overlap_status is not None

    def needs_api_call(self) -> bool:
        """API 호출 필요 여부 확인"""
        if not self.has_overlap_info():
            return True  # 겹침 분석 없으면 API 호출 필요

        from .candle_core_models import OverlapStatus
        return self.overlap_status != OverlapStatus.COMPLETE_OVERLAP

    def needs_partial_api_call(self) -> bool:
        """부분 API 호출 필요 여부 확인"""
        if not self.has_overlap_info():
            return False

        from .candle_core_models import OverlapStatus
        return self.overlap_status in [OverlapStatus.PARTIAL_START, OverlapStatus.PARTIAL_MIDDLE_CONTINUOUS]

    def get_api_params(self) -> tuple[int, Optional[datetime]]:
        """API 호출 파라미터 반환 (count, to)"""
        if self.needs_partial_api_call() and self.api_request_count and self.api_request_start:
            # 부분 겹침: 요청 단계 정보 사용
            return self.api_request_count, self.api_request_start
        else:
            # 전체 호출: 기본 정보 사용
            return self.count, self.to

    # === 단계별 정보 설정 메서드들 ===

    def set_api_response_info(self, candles: List[Dict[str, Any]]) -> None:
        """
        API 응답 정보 설정

        Args:
            candles: 업비트 API 응답 캔들 리스트 (Dict 형태)
        """
        if not candles:
            self.api_response_count = 0
            self.api_response_start = None
            self.api_response_end = None
            return

        self.api_response_count = len(candles)

        # 업비트 API는 최신순 정렬: 첫 번째가 최신, 마지막이 가장 과거
        first_candle_time = candles[0]['candle_date_time_utc']
        last_candle_time = candles[-1]['candle_date_time_utc']

        # datetime 변환 (ISO 형식 처리)
        try:
            # UTC 시간 문자열을 datetime으로 변환
            self.api_response_start = datetime.fromisoformat(first_candle_time.replace('Z', '+00:00'))
            self.api_response_end = datetime.fromisoformat(last_candle_time.replace('Z', '+00:00'))
        except Exception:
            # 파싱 실패 시에도 개수는 기록
            self.api_response_start = None
            self.api_response_end = None

    def set_final_candle_info(self, candles: List[Dict[str, Any]]) -> None:
        """
        최종 처리 결과 설정 (빈 캔들 처리 후)

        Args:
            candles: 빈 캔들 처리 완료된 최종 캔들 리스트 (Dict 형태)
        """
        if not candles:
            self.final_candle_count = 0
            self.final_candle_start = None
            self.final_candle_end = None
            return

        self.final_candle_count = len(candles)

        # 최종 처리된 캔들들의 첫 번째와 마지막 시간
        first_candle_time = candles[0]['candle_date_time_utc']
        last_candle_time = candles[-1]['candle_date_time_utc']

        # datetime 변환 (timezone-aware로 직접 생성)
        try:
            start_dt = datetime.fromisoformat(first_candle_time.replace('Z', '+00:00'))
            end_dt = datetime.fromisoformat(last_candle_time.replace('Z', '+00:00'))
            self.final_candle_start = start_dt.replace(tzinfo=timezone.utc)
            self.final_candle_end = end_dt.replace(tzinfo=timezone.utc)
        except Exception:
            self.final_candle_start = None
            self.final_candle_end = None

    def get_processing_status(self) -> dict:
        """전체 처리 단계 상태 요약"""
        return {
            'chunk_id': self.chunk_id,
            'status': self.status,
            'has_plan': self.end is not None,
            'has_overlap_info': self.overlap_status is not None,
            'has_api_response': self.api_response_count is not None,
            'has_final_processing': self.final_candle_end is not None,
            'effective_end_time': self.get_effective_end_time(),
            'time_source': self.get_time_source(),
            'overlap_status': self.overlap_status.value if self.overlap_status else None,
            'db_range': {
                'start': self.db_start,
                'end': self.db_end
            } if self.db_start or self.db_end else None
        }

    def _get_available_times(self) -> dict:
        """사용 가능한 모든 시간 정보 반환 (디버깅용)"""
        return {
            'planned_end': self.end,
            'db_end': self.db_end,
            'api_response_end': self.api_response_end,
            'final_candle_end': self.final_candle_end
        }

    def handle_complete_overlap_time_info(self, overlap_result: 'OverlapResult') -> None:
        """
        COMPLETE_OVERLAP 상황에서 완전한 시간 정보 확보

        기존: API 호출도 빈캔들 처리도 없어서 시간 정보 완전 손실
        개선: OverlapResult.db_end 활용으로 완전한 시간 정보 확보
        """
        from upbit_auto_trading.infrastructure.logging import create_component_logger
        logger = create_component_logger("ChunkInfo")

        # OverlapResult 정보 설정
        self.set_overlap_info(overlap_result)

        # COMPLETE_OVERLAP 전용 처리
        if self.overlap_status and self.overlap_status.value == 'complete_overlap':
            if self.db_end:
                logger.debug(f"COMPLETE_OVERLAP 시간 정보 확보: {self.chunk_id}")
                logger.debug(f"  db_end: {self.db_end}")
                logger.debug(f"  effective_end: {self.get_effective_end_time()}")
                logger.debug(f"  time_source: {self.get_time_source()}")
            else:
                logger.warning(f"COMPLETE_OVERLAP이지만 db_end 없음: {self.chunk_id}")

        # 완전성 검증
        if not self.has_complete_time_info():
            logger.warning(f"청크 시간 정보 불완전: {self.chunk_id}")
            logger.warning(f"  overlap_status: {self.overlap_status}")
            logger.warning(f"  available_times: {self._get_available_times()}")

    def get_processing_summary(self) -> str:
        """
        전체 처리 과정 요약 정보 반환 (디버깅용)

        Returns:
            str: 요청 → API 응답 → 최종 결과의 변화 과정 요약
        """
        lines = []
        lines.append(f"🔍 청크 처리 요약: {self.chunk_id}")
        lines.append(f"├─ 상태: {self.status}")

        # 겹침 분석 결과 (개선된 정보)
        if self.overlap_status:
            lines.append(f"├─ 겹침 분석: {self.overlap_status.value}")
            if self.db_start or self.db_end:
                lines.append(f"│  └─ DB 범위: {self.db_start} ~ {self.db_end}")

        # 요청 단계
        lines.append("├─ 📋 요청 단계:")
        lines.append(f"│  ├─ 계획 개수: {self.count}")
        if self.api_request_count is not None:
            lines.append(f"│  ├─ 실제 요청: {self.api_request_count}개")
            if self.api_request_start and self.api_request_end:
                lines.append(f"│  └─ 요청 범위: {self.api_request_start} ~ {self.api_request_end}")
        else:
            lines.append(f"│  └─ 요청 범위: {self.to} ~ {self.end}")

        # API 응답 단계
        lines.append("├─ 📡 API 응답:")
        if self.api_response_count is not None:
            lines.append(f"│  ├─ 응답 개수: {self.api_response_count}개")
            if self.api_response_start and self.api_response_end:
                lines.append(f"│  └─ 응답 범위: {self.api_response_start} ~ {self.api_response_end}")
        else:
            lines.append("│  └─ 미처리")

        # 최종 처리 단계
        lines.append("├─ 🎯 최종 결과:")
        if self.final_candle_count is not None:
            lines.append(f"│  ├─ 최종 개수: {self.final_candle_count}개")
            if self.final_candle_start and self.final_candle_end:
                lines.append(f"│  └─ 최종 범위: {self.final_candle_start} ~ {self.final_candle_end}")
        else:
            lines.append("│  └─ 미처리")

        # 통합된 시간 정보
        lines.append("└─ ⭐ 통합 시간 정보:")
        effective_time = self.get_effective_end_time()
        time_source = self.get_time_source()
        if effective_time:
            lines.append(f"   ├─ 유효 끝시간: {effective_time}")
            lines.append(f"   └─ 정보 출처: {time_source}")
        else:
            lines.append("   └─ 시간 정보 없음")

        # 변화 과정 요약 (개선된 버전)
        if (self.api_request_count is not None
                and self.api_response_count is not None
                and self.final_candle_count is not None):

            changes = []
            if self.api_request_count != self.api_response_count:
                diff = self.api_response_count - self.api_request_count
                changes.append(f"API응답 {diff:+d}")

            if self.api_response_count != self.final_candle_count:
                diff = self.final_candle_count - self.api_response_count
                changes.append(f"빈캔들처리 {diff:+d}")

            if changes:
                lines.append(f"\n💡 변화: 요청{self.api_request_count} → "
                             + f"응답{self.api_response_count} → 최종{self.final_candle_count} "
                             + f"({', '.join(changes)})")

        return '\n'.join(lines)

    @classmethod
    def create_chunk(cls, chunk_index: int, symbol: str, timeframe: str, count: int,
                     to: Optional[datetime] = None, end: Optional[datetime] = None) -> 'ChunkInfo':
        """새 청크 생성 헬퍼"""
        chunk_id = f"{symbol}_{timeframe}_{chunk_index:03d}"
        return cls(
            chunk_id=chunk_id,
            chunk_index=chunk_index,
            symbol=symbol,
            timeframe=timeframe,
            count=count,
            to=to,
            end=end
        )


@dataclass
class ProcessingStats:
    """
    CandleDataProvider v4.0 처리 통계

    전체 처리 과정의 성능 및 상태 정보.
    """
    # === 기본 정보 ===
    total_chunks_planned: int             # 계획된 총 청크 수
    processing_start_time: datetime       # 처리 시작 시간
    chunks_completed: int = 0             # 완료된 청크 수
    chunks_failed: int = 0                # 실패한 청크 수

    # === 시간 정보 ===
    processing_end_time: Optional[datetime] = None  # 처리 완료 시간

    # === API 통계 ===
    total_api_requests: int = 0           # 총 API 요청 수
    api_request_time_ms: float = 0.0      # 총 API 요청 시간

    # === 캐시 통계 ===
    cache_hits: int = 0                   # 캐시 히트 수
    cache_misses: int = 0                 # 캐시 미스 수

    # === 데이터 통계 ===
    total_candles_collected: int = 0      # 수집된 총 캔들 수

    def __post_init__(self):
        """통계 검증"""
        if self.total_chunks_planned <= 0:
            raise ValueError(f"계획된 총 청크 수는 1 이상이어야 합니다: {self.total_chunks_planned}")
        if any(count < 0 for count in [self.chunks_completed, self.chunks_failed,
                                       self.total_api_requests, self.cache_hits,
                                       self.cache_misses, self.total_candles_collected]):
            raise ValueError("모든 통계 값은 0 이상이어야 합니다")

    def get_completion_rate(self) -> float:
        """완료율 계산 (0.0 ~ 1.0)"""
        if self.total_chunks_planned == 0:
            return 0.0
        return self.chunks_completed / self.total_chunks_planned

    def get_cache_hit_rate(self) -> float:
        """캐시 히트율 계산 (0.0 ~ 1.0)"""
        total_cache_requests = self.cache_hits + self.cache_misses
        if total_cache_requests == 0:
            return 0.0
        return self.cache_hits / total_cache_requests

    def get_average_api_time_ms(self) -> float:
        """평균 API 요청 시간 (ms)"""
        if self.total_api_requests == 0:
            return 0.0
        return self.api_request_time_ms / self.total_api_requests

    def get_total_processing_time_ms(self) -> float:
        """총 처리 시간 (ms)"""
        if self.processing_end_time is None:
            end_time = datetime.now()
        else:
            end_time = self.processing_end_time

        delta = end_time - self.processing_start_time
        return delta.total_seconds() * 1000

    def mark_completed(self) -> None:
        """처리 완료 마킹"""
        self.processing_end_time = datetime.now()
