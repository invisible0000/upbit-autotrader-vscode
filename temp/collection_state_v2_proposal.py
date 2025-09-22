"""
CollectionState v2.0 개선안 - 순수 상태와 계산 로직 분리

개선 목표:
1. 단일 책임 원칙 준수: 순수 상태만 저장
2. 중복 제거: 계산 가능한 값들은 메서드로 제공
3. 불변성 향상: 핵심 정보는 변경 불가
4. 사용성 개선: 직관적인 접근 방법 제공
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import List, Optional

from upbit_auto_trading.infrastructure.market_data.candle.candle_models import ChunkInfo


@dataclass
class CollectionStateV2:
    """
    캔들 수집 상태 v2.0 - 순수 상태 중심 설계

    원칙:
    - 순수 상태만 저장 (계산된 값 제외)
    - 불변성 최대화 (핵심 정보는 변경 불가)
    - 계산 로직은 메서드로 분리
    - 단일 책임: 상태 보관만
    """

    # === 🔒 불변 정보 (한번 설정 후 변경 안됨) ===
    request_id: str
    symbol: str
    timeframe: str
    total_requested: int
    start_time: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    # === 📊 변경 가능한 상태 ===
    total_collected: int = 0
    completed_chunks: List[ChunkInfo] = field(default_factory=list)
    current_chunk: Optional[ChunkInfo] = None
    is_completed: bool = False
    error_message: Optional[str] = None

    # === 🔗 연속성 정보 (다음 청크를 위한) ===
    last_candle_time: Optional[str] = None  # UTC 시간 문자열

    # === ⏱️ 단순 시간 추적 ===
    last_update_time: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    # === 📈 계산된 값들 (Property로 제공) ===

    @property
    def progress_percentage(self) -> float:
        """진행률 (0.0 ~ 100.0)"""
        if self.total_requested <= 0:
            return 0.0
        return (self.total_collected / self.total_requested) * 100.0

    @property
    def completed_chunk_count(self) -> int:
        """완료된 청크 수"""
        return len(self.completed_chunks)

    @property
    def elapsed_seconds(self) -> float:
        """시작 후 경과 시간 (초)"""
        return (datetime.now(timezone.utc) - self.start_time).total_seconds()

    @property
    def avg_chunk_duration(self) -> float:
        """평균 청크 처리 시간 (초)"""
        if not self.completed_chunks:
            return 0.0
        return self.elapsed_seconds / len(self.completed_chunks)

    @property
    def estimated_total_chunks(self) -> int:
        """예상 총 청크 수 (동적 계산)"""
        if self.total_requested <= 0:
            return 0
        chunk_size = 200  # 기본값, 실제로는 설정에서 가져와야 함
        return (self.total_requested + chunk_size - 1) // chunk_size

    @property
    def remaining_chunks(self) -> int:
        """남은 청크 수"""
        return max(0, self.estimated_total_chunks - self.completed_chunk_count)

    @property
    def estimated_remaining_seconds(self) -> float:
        """예상 남은 시간 (초)"""
        if self.remaining_chunks <= 0 or self.avg_chunk_duration <= 0:
            return 0.0
        return self.remaining_chunks * self.avg_chunk_duration

    @property
    def estimated_completion_time(self) -> Optional[datetime]:
        """예상 완료 시간"""
        if self.estimated_remaining_seconds <= 0:
            return None
        return datetime.now(timezone.utc) + timedelta(seconds=self.estimated_remaining_seconds)

    # === 🔧 상태 업데이트 메서드들 ===

    def update_progress(self, collected_count: int) -> None:
        """진행 상황 업데이트"""
        self.total_collected = collected_count
        self.last_update_time = datetime.now(timezone.utc)

    def add_completed_chunk(self, chunk: ChunkInfo) -> None:
        """완료된 청크 추가"""
        if chunk not in self.completed_chunks:
            self.completed_chunks.append(chunk)
        self.last_update_time = datetime.now(timezone.utc)

    def set_current_chunk(self, chunk: Optional[ChunkInfo]) -> None:
        """현재 처리 중인 청크 설정"""
        self.current_chunk = chunk
        self.last_update_time = datetime.now(timezone.utc)

    def mark_completed(self, final_count: Optional[int] = None) -> None:
        """수집 완료 마킹"""
        self.is_completed = True
        if final_count is not None:
            self.total_collected = final_count
        self.current_chunk = None
        self.last_update_time = datetime.now(timezone.utc)

    def set_error(self, error_message: str) -> None:
        """에러 상태 설정"""
        self.error_message = error_message
        self.last_update_time = datetime.now(timezone.utc)

    def clear_error(self) -> None:
        """에러 상태 해제"""
        self.error_message = None
        self.last_update_time = datetime.now(timezone.utc)

    # === 📋 상태 조회 메서드들 ===

    def has_error(self) -> bool:
        """에러 상태 여부"""
        return self.error_message is not None

    def is_in_progress(self) -> bool:
        """진행 중 여부"""
        return not self.is_completed and not self.has_error()

    def get_phase(self) -> str:
        """현재 단계 반환"""
        if self.has_error():
            return "error"
        elif self.is_completed:
            return "completed"
        elif self.current_chunk:
            return "processing"
        elif self.completed_chunks:
            return "collecting"
        else:
            return "initializing"

    def get_completion_info(self) -> dict:
        """완료 조건 정보"""
        # 이 로직은 CandleDataProvider에서 이전해야 함
        # CollectionState는 순수 상태만 관리
        return {
            'progress_pct': self.progress_percentage,
            'is_completed': self.is_completed,
            'has_error': self.has_error(),
            'phase': self.get_phase()
        }

    def to_summary_dict(self) -> dict:
        """요약 정보 딕셔너리"""
        return {
            'request_id': self.request_id,
            'symbol': self.symbol,
            'timeframe': self.timeframe,
            'progress': {
                'collected': self.total_collected,
                'requested': self.total_requested,
                'percentage': round(self.progress_percentage, 1)
            },
            'chunks': {
                'completed': self.completed_chunk_count,
                'estimated_total': self.estimated_total_chunks,
                'remaining': self.remaining_chunks,
                'current': self.current_chunk.chunk_id if self.current_chunk else None
            },
            'timing': {
                'elapsed_seconds': round(self.elapsed_seconds, 1),
                'avg_chunk_duration': round(self.avg_chunk_duration, 2),
                'estimated_remaining': round(self.estimated_remaining_seconds, 1)
            },
            'status': {
                'is_completed': self.is_completed,
                'has_error': self.has_error(),
                'phase': self.get_phase(),
                'error_message': self.error_message
            }
        }


# === 🔄 마이그레이션 헬퍼 ===

def migrate_collection_state(old_state: 'CollectionState') -> CollectionStateV2:
    """기존 CollectionState를 v2.0으로 마이그레이션"""
    return CollectionStateV2(
        request_id=old_state.request_id,
        symbol=old_state.symbol,
        timeframe=old_state.timeframe,
        total_requested=old_state.total_requested,
        start_time=old_state.start_time,
        total_collected=old_state.total_collected,
        completed_chunks=old_state.completed_chunks.copy(),
        current_chunk=old_state.current_chunk,
        is_completed=old_state.is_completed,
        error_message=old_state.error_message,
        last_candle_time=old_state.last_candle_time,
        last_update_time=old_state.last_update_time
    )


# === 📊 사용 예시 ===

if __name__ == "__main__":
    # 생성
    state = CollectionStateV2(
        request_id="test_001",
        symbol="KRW-BTC",
        timeframe="1m",
        total_requested=1000
    )

    # 진행 업데이트
    state.update_progress(250)

    # 계산된 값들 조회
    print(f"진행률: {state.progress_percentage:.1f}%")
    print(f"예상 남은 시간: {state.estimated_remaining_seconds:.1f}초")
    print(f"현재 단계: {state.get_phase()}")

    # 요약 정보
    summary = state.to_summary_dict()
    print(f"요약: {summary}")
