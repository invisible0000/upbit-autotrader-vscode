"""
📋 CandleDataProvider v4.0 - TASK_02 구현 완료
요청 정규화 및 청크 생성 로직 구현 + 하이브리드 순차 처리

Created: 2025-09-11 (Updated: 2025-09-12)
Purpose: normalize_request와 create_chunks 메서드 구현 + 순차 청크 관리
Features: 4가지 파라미터 조합 지원, 설정 가능한 청크 분할, 실시간 상태 관리
Architecture: 기존 TASK_02 요구사항 + New04 하이브리드 방식 결합
"""

from datetime import datetime, timezone, timedelta
from typing import Optional, List, Dict, Any
from enum import Enum
from dataclasses import dataclass, field

from upbit_auto_trading.infrastructure.logging import create_component_logger
from upbit_auto_trading.infrastructure.market_data.candle.time_utils import TimeUtils
from upbit_auto_trading.infrastructure.market_data.candle.candle_models import (
    ChunkInfo
)

logger = create_component_logger("CandleDataProvider")


class ChunkStatus(Enum):
    """청크 처리 상태"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class CollectionState:
    """캔들 수집 상태 관리"""
    request_id: str
    symbol: str
    timeframe: str
    total_requested: int
    total_collected: int = 0
    completed_chunks: List[ChunkInfo] = field(default_factory=list)
    current_chunk: Optional[ChunkInfo] = None
    last_candle_time: Optional[str] = None  # 마지막 수집된 캔들 시간 (연속성용)
    estimated_total_chunks: int = 0
    estimated_completion_time: Optional[datetime] = None
    start_time: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    is_completed: bool = False
    error_message: Optional[str] = None
    target_end: Optional[datetime] = None  # end 파라미터 목표 시점 (Phase 1 추가)

    # 남은 시간 추적 필드들
    last_update_time: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    avg_chunk_duration: float = 0.0  # 평균 청크 처리 시간 (초)
    remaining_chunks: int = 0  # 남은 청크 수
    estimated_remaining_seconds: float = 0.0  # 실시간 계산된 남은 시간


@dataclass
class CollectionPlan:
    """수집 계획 (최소 정보만)"""
    total_count: int
    estimated_chunks: int
    estimated_duration_seconds: float
    first_chunk_params: Dict[str, Any]  # 첫 번째 청크 요청 파라미터


class CandleDataProvider:
    """
    캔들 데이터 제공자 v4.0 - TASK_02 구현 완료

    핵심 원리:
    1. 최소한의 사전 계획 (청크 수와 예상 시간만)
    2. 실시간 순차 청크 생성 (이전 응답 기반)
    3. 상태 추적으로 중단/재시작 지원
    4. 10 RPS 기반 예상 완료 시간 제공

    장점:
    - new01의 안정성: 상태 관리, 검증, 중단/재시작
    - new02의 효율성: 순차 처리, 응답 기반 연속성
    - 최소 오버헤드: 사전 계획 최소화
    - 실시간 확장: 필요할 때만 청크 생성
    """

    def __init__(self, chunk_size: int = 200):
        """CandleDataProviderNew04 초기화"""
        self.chunk_size = min(chunk_size, 200)  # 업비트 제한 준수
        self.active_collections: Dict[str, CollectionState] = {}
        self.api_rate_limit_rps = 10  # 10 RPS 기준

        logger.info("CandleDataProvider v4.0 (TASK_02 + 하이브리드 순차 처리) 초기화 완료")
        logger.info(f"청크 크기: {self.chunk_size}, API Rate Limit: {self.api_rate_limit_rps} RPS")

    def plan_collection(
        self,
        symbol: str,
        timeframe: str,
        count: Optional[int] = None,
        to: Optional[datetime] = None,
        end: Optional[datetime] = None
    ) -> CollectionPlan:
        """
        수집 계획 수립 (최소한의 정보만)

        Args:
            symbol: 심볼 (예: 'KRW-BTC')
            timeframe: 타임프레임 (예: '1m', '5m', '1h', '1d')
            count: 조회할 캔들 개수
            to: 시작점 (첫 번째 청크용)
            end: 종료점

        Returns:
            CollectionPlan: 최소 계획 정보
        """
        logger.info(f"수집 계획 수립: {symbol} {timeframe}, count={count}, to={to}, end={end}")

        # 동적 비즈니스 검증
        current_time = datetime.now(timezone.utc)
        if to is not None and to > current_time:
            raise ValueError(f"to 시점이 미래입니다: {to}")
        if end is not None and end > current_time:
            raise ValueError(f"end 시점이 미래입니다: {end}")

        # 총 캔들 개수 계산 (최소한의 정규화)
        total_count = self._calculate_total_count(
            count=count,
            to=to,
            end=end,
            timeframe=timeframe,
            current_time=current_time
        )

        # 예상 청크 수 계산
        estimated_chunks = (total_count + self.chunk_size - 1) // self.chunk_size

        # 예상 완료 시간 계산 (10 RPS 기준)
        estimated_duration_seconds = estimated_chunks / self.api_rate_limit_rps

        # 첫 번째 청크 파라미터 생성
        first_chunk_params = self._create_first_chunk_params(
            symbol=symbol,
            count=count,
            to=to,
            end=end,
            current_time=current_time
        )

        plan = CollectionPlan(
            total_count=total_count,
            estimated_chunks=estimated_chunks,
            estimated_duration_seconds=estimated_duration_seconds,
            first_chunk_params=first_chunk_params
        )

        logger.info(f"✅ 계획 수립 완료: {total_count:,}개 캔들, {estimated_chunks}청크, "
                    f"예상 소요시간: {estimated_duration_seconds:.1f}초")
        return plan

    def start_collection(
        self,
        symbol: str,
        timeframe: str,
        count: Optional[int] = None,
        to: Optional[datetime] = None,
        end: Optional[datetime] = None
    ) -> str:
        """
        캔들 수집 시작 (상태 추적 시작)

        Args:
            symbol: 심볼
            timeframe: 타임프레임
            count: 조회할 캔들 개수
            to: 시작점
            end: 종료점

        Returns:
            str: 수집 요청 ID (상태 추적용)
        """
        logger.info(f"캔들 수집 시작: {symbol} {timeframe}")

        # 계획 수립
        plan = self.plan_collection(symbol, timeframe, count, to, end)

        # 요청 ID 생성 (타임스탬프 기반)
        request_id = f"{symbol}_{timeframe}_{int(datetime.now().timestamp())}"

        # 수집 상태 초기화
        estimated_completion = datetime.now(timezone.utc) + timedelta(
            seconds=plan.estimated_duration_seconds
        )

        collection_state = CollectionState(
            request_id=request_id,
            symbol=symbol,
            timeframe=timeframe,
            total_requested=plan.total_count,
            estimated_total_chunks=plan.estimated_chunks,
            estimated_completion_time=estimated_completion,
            remaining_chunks=plan.estimated_chunks,
            estimated_remaining_seconds=plan.estimated_duration_seconds,
            target_end=end  # Phase 1: end 파라미터 보관
        )

        # 첫 번째 청크 생성
        first_chunk = self._create_next_chunk(
            collection_state=collection_state,
            chunk_params=plan.first_chunk_params,
            chunk_index=0
        )
        collection_state.current_chunk = first_chunk

        # 상태 등록
        self.active_collections[request_id] = collection_state

        logger.info(f"✅ 수집 시작: 요청 ID {request_id}, 예상 완료: {estimated_completion}")
        return request_id

    def get_next_chunk(self, request_id: str) -> Optional[ChunkInfo]:
        """
        다음 처리할 청크 정보 반환

        Args:
            request_id: 수집 요청 ID

        Returns:
            ChunkInfo: 다음 청크 정보 (완료된 경우 None)
        """
        if request_id not in self.active_collections:
            raise ValueError(f"알 수 없는 요청 ID: {request_id}")

        state = self.active_collections[request_id]

        if state.is_completed:
            logger.info(f"수집 완료됨: {request_id}")
            return None

        if state.current_chunk is None:
            logger.warning(f"처리할 청크가 없습니다: {request_id}")
            return None

        logger.debug(f"다음 청크 반환: {state.current_chunk.chunk_id}")
        return state.current_chunk

    def mark_chunk_completed(
        self,
        request_id: str,
        candles: List[Dict[str, Any]]
    ) -> bool:
        """
        청크 완료 처리 및 다음 청크 생성

        Args:
            request_id: 수집 요청 ID
            candles: 수집된 캔들 데이터

        Returns:
            bool: 전체 수집 완료 여부
        """
        if request_id not in self.active_collections:
            raise ValueError(f"알 수 없는 요청 ID: {request_id}")

        state = self.active_collections[request_id]

        if state.current_chunk is None:
            raise ValueError("처리 중인 청크가 없습니다")

        # 현재 청크 완료 처리
        completed_chunk = state.current_chunk
        completed_chunk.status = "completed"  # ChunkStatus.COMPLETED.value 대신 문자열 사용
        state.completed_chunks.append(completed_chunk)
        state.total_collected += len(candles)

        # 마지막 캔들 시간 업데이트 (다음 청크 연속성용)
        if candles:
            state.last_candle_time = candles[-1]["candle_date_time_utc"]

        # 남은 시간 정보 업데이트
        self._update_remaining_time_estimates(state)

        logger.debug(f"청크 완료: {completed_chunk.chunk_id}, "
                     f"수집: {len(candles)}개, 누적: {state.total_collected}/{state.total_requested}, "
                     f"남은시간: {state.estimated_remaining_seconds:.1f}초")

        # 수집 완료 확인 (Phase 1: 개수 + 시간 조건)
        count_reached = state.total_collected >= state.total_requested

        # end 시점 도달 확인
        end_time_reached = False
        if state.target_end and candles:
            try:
                # 마지막 수집 캔들의 시간을 datetime으로 변환
                last_candle_time_str = candles[-1]["candle_date_time_utc"]
                # ISO format 처리 (Z suffix 제거)
                if last_candle_time_str.endswith('Z'):
                    last_candle_time_str = last_candle_time_str[:-1] + '+00:00'
                last_candle_time = datetime.fromisoformat(last_candle_time_str)

                # 마지막 캔들 시간이 target_end보다 과거면 정지
                end_time_reached = last_candle_time <= state.target_end

                logger.debug(
                    f"시간 조건 확인: 마지막캔들={last_candle_time}, "
                    f"목표종료={state.target_end}, 도달={end_time_reached}"
                )
            except Exception as e:
                logger.warning(f"시간 파싱 실패: {e}")

        if count_reached or end_time_reached:
            completion_reason = "개수 달성" if count_reached else "end 시점 도달"
            state.is_completed = True
            state.current_chunk = None
            logger.info(f"✅ 전체 수집 완료 ({completion_reason}): {request_id}, {state.total_collected}개")
            return True

        # 다음 청크 생성
        next_chunk_index = len(state.completed_chunks)
        remaining_count = state.total_requested - state.total_collected
        next_chunk_size = min(remaining_count, self.chunk_size)

        # 다음 청크 파라미터 (이전 응답 기반)
        next_chunk_params = {
            "market": state.symbol,
            "count": next_chunk_size,
            "to": state.last_candle_time  # 연속성 보장
        }

        # 다음 청크 생성
        next_chunk = self._create_next_chunk(
            collection_state=state,
            chunk_params=next_chunk_params,
            chunk_index=next_chunk_index
        )
        state.current_chunk = next_chunk

        logger.debug(f"다음 청크 생성: {next_chunk.chunk_id}, 잔여: {remaining_count}개")
        return False

    def get_collection_status(self, request_id: str) -> Dict[str, Any]:
        """
        수집 상태 조회

        Args:
            request_id: 수집 요청 ID

        Returns:
            Dict: 상세 상태 정보
        """
        if request_id not in self.active_collections:
            raise ValueError(f"알 수 없는 요청 ID: {request_id}")

        state = self.active_collections[request_id]

        progress_percentage = (state.total_collected / state.total_requested) * 100
        elapsed_time = datetime.now(timezone.utc) - state.start_time
        completed_chunks = len(state.completed_chunks)

        return {
            "request_id": request_id,
            "symbol": state.symbol,
            "timeframe": state.timeframe,
            "progress": {
                "collected": state.total_collected,
                "requested": state.total_requested,
                "percentage": round(progress_percentage, 1)
            },
            "chunks": {
                "completed": completed_chunks,
                "estimated_total": state.estimated_total_chunks,
                "current": state.current_chunk.chunk_id if state.current_chunk else None
            },
            "timing": {
                "elapsed_seconds": elapsed_time.total_seconds(),
                "estimated_total_seconds": (
                    state.estimated_completion_time - state.start_time
                    if state.estimated_completion_time else None
                ),
                "estimated_remaining_seconds": state.estimated_remaining_seconds,
                "avg_chunk_duration": state.avg_chunk_duration,
                "remaining_chunks": state.remaining_chunks
            },
            "is_completed": state.is_completed,
            "error": state.error_message
        }

    def resume_collection(self, request_id: str) -> Optional[ChunkInfo]:
        """
        중단된 수집 재개

        Args:
            request_id: 수집 요청 ID

        Returns:
            ChunkInfo: 재개할 청크 정보
        """
        if request_id not in self.active_collections:
            raise ValueError(f"알 수 없는 요청 ID: {request_id}")

        state = self.active_collections[request_id]

        if state.is_completed:
            logger.info(f"이미 완료된 수집: {request_id}")
            return None

        if state.current_chunk is not None:
            logger.info(f"수집 재개: {request_id}, 현재 청크: {state.current_chunk.chunk_id}")
            return state.current_chunk

        # 현재 청크가 없으면 새로 생성 (마지막 상태 기준)
        next_chunk_index = len(state.completed_chunks)
        remaining_count = state.total_requested - state.total_collected

        if remaining_count <= 0:
            state.is_completed = True
            return None

        next_chunk_size = min(remaining_count, self.chunk_size)
        next_chunk_params = {
            "market": state.symbol,
            "count": next_chunk_size,
            "to": state.last_candle_time
        }

        next_chunk = self._create_next_chunk(
            collection_state=state,
            chunk_params=next_chunk_params,
            chunk_index=next_chunk_index
        )
        state.current_chunk = next_chunk

        logger.info(f"수집 재개: 새 청크 생성 {next_chunk.chunk_id}")
        return next_chunk

    def _calculate_total_count(
        self,
        count: Optional[int],
        to: Optional[datetime],
        end: Optional[datetime],
        timeframe: str,
        current_time: datetime
    ) -> int:
        """총 캔들 개수 계산 (최소 정규화)"""

        # count가 직접 제공된 경우
        if count is not None:
            return count

        # end가 제공된 경우: 기간 계산
        if end is not None:
            start_time = to if to is not None else current_time
            normalized_start = TimeUtils.align_to_candle_boundary(start_time, timeframe)
            normalized_end = TimeUtils.align_to_candle_boundary(end, timeframe)

            if normalized_start <= normalized_end:
                raise ValueError("시작 시점이 종료 시점보다 이전입니다")

            return TimeUtils.calculate_expected_count(
                start_time=normalized_start,
                end_time=normalized_end,
                timeframe=timeframe
            )

        raise ValueError("count 또는 end 중 하나는 반드시 제공되어야 합니다")

    def _create_first_chunk_params(
        self,
        symbol: str,
        count: Optional[int],
        to: Optional[datetime],
        end: Optional[datetime],
        current_time: datetime
    ) -> Dict[str, Any]:
        """첫 번째 청크 파라미터 생성"""

        params = {"market": symbol}

        # count 기반 요청 (가장 단순)
        if count is not None:
            chunk_size = min(count, self.chunk_size)
            params["count"] = chunk_size

            # to가 있으면 시작점 지정
            if to is not None:
                params["to"] = to.strftime("%Y-%m-%dT%H:%M:%S")
            # to가 없으면 현재 시간 기준 (count only)

        # end 기반 요청
        elif end is not None:
            params["count"] = self.chunk_size

            # to가 있으면 시작점 지정
            if to is not None:
                params["to"] = to.strftime("%Y-%m-%dT%H:%M:%S")
            # to가 없으면 현재 시간 기준 (end only)

        return params

    def _create_next_chunk(
        self,
        collection_state: CollectionState,
        chunk_params: Dict[str, Any],
        chunk_index: int
    ) -> ChunkInfo:
        """다음 청크 정보 생성"""

        chunk_id = f"{collection_state.symbol}_{collection_state.timeframe}_{chunk_index:05d}"

        # 시간 정보는 실제 API 호출 시에만 정확히 알 수 있으므로
        # 여기서는 기본값으로 설정
        current_time = datetime.now(timezone.utc)

        chunk_info = ChunkInfo(
            chunk_id=chunk_id,
            chunk_index=chunk_index,
            symbol=collection_state.symbol,
            timeframe=collection_state.timeframe,
            count=chunk_params["count"],
            to=current_time,  # 실제로는 API 응답 후 업데이트
            end=current_time,  # 실제로는 API 응답 후 업데이트
            status="pending"  # ChunkStatus.PENDING.value 대신 문자열 직접 사용
        )

        return chunk_info

    def _update_remaining_time_estimates(self, state: CollectionState):
        """
        실시간 남은 시간 추정 업데이트

        Args:
            state: 수집 상태 객체
        """
        current_time = datetime.now(timezone.utc)

        # 완료된 청크 수
        completed_chunks_count = len(state.completed_chunks)

        if completed_chunks_count == 0:
            # 아직 완료된 청크가 없으면 초기 추정값 사용
            return

        # 평균 청크 처리 시간 계산
        total_elapsed = (current_time - state.start_time).total_seconds()
        state.avg_chunk_duration = total_elapsed / completed_chunks_count

        # 남은 청크 수 계산
        state.remaining_chunks = state.estimated_total_chunks - completed_chunks_count

        # 실시간 남은 시간 추정
        if state.remaining_chunks > 0:
            state.estimated_remaining_seconds = state.remaining_chunks * state.avg_chunk_duration
        else:
            state.estimated_remaining_seconds = 0.0

        # 예상 완료 시간 업데이트
        if state.estimated_remaining_seconds > 0:
            state.estimated_completion_time = current_time + timedelta(
                seconds=state.estimated_remaining_seconds
            )

        # 업데이트 시간 기록
        state.last_update_time = current_time

        logger.debug(f"남은 시간 업데이트: 평균 청크 시간 {state.avg_chunk_duration:.2f}초, "
                     f"남은 청크 {state.remaining_chunks}개, 예상 남은 시간 {state.estimated_remaining_seconds:.1f}초")

    def get_realtime_remaining_time(self, request_id: str) -> Dict[str, Any]:
        """
        실시간 남은 시간 정보 조회

        Args:
            request_id: 수집 요청 ID

        Returns:
            Dict: 실시간 남은 시간 정보
        """
        if request_id not in self.active_collections:
            raise ValueError(f"알 수 없는 요청 ID: {request_id}")

        state = self.active_collections[request_id]
        current_time = datetime.now(timezone.utc)

        # 실시간 남은 시간 재계산 (최신 정보 반영)
        if len(state.completed_chunks) > 0:
            self._update_remaining_time_estimates(state)

        return {
            "request_id": request_id,
            "current_time": current_time.isoformat(),
            "avg_chunk_duration": state.avg_chunk_duration,
            "remaining_chunks": state.remaining_chunks,
            "estimated_remaining_seconds": state.estimated_remaining_seconds,
            "estimated_completion_time": (
                state.estimated_completion_time.isoformat()
                if state.estimated_completion_time else None
            ),
            "progress_percentage": round(
                (state.total_collected / state.total_requested) * 100, 1
            ),
            "is_on_track": self._is_collection_on_track(state),
            "performance_info": self._get_performance_info(state)
        }

    def _is_collection_on_track(self, state: CollectionState) -> bool:
        """
        수집이 예정대로 진행되고 있는지 확인

        Args:
            state: 수집 상태 객체

        Returns:
            bool: 예정대로 진행 중이면 True
        """
        if len(state.completed_chunks) == 0:
            return True  # 아직 시작 단계

        # 초기 예상 시간과 현재 평균 시간 비교
        initial_expected_duration = state.estimated_total_chunks / self.api_rate_limit_rps

        # 현재 평균이 초기 예상의 120% 이내면 정상
        return state.avg_chunk_duration <= initial_expected_duration * 1.2

    def _get_performance_info(self, state: CollectionState) -> Dict[str, Any]:
        """
        수집 성능 정보 제공

        Args:
            state: 수집 상태 객체

        Returns:
            Dict: 성능 정보
        """
        if len(state.completed_chunks) == 0:
            return {"status": "초기 단계"}

        initial_expected_rps = self.api_rate_limit_rps
        current_rps = 1.0 / state.avg_chunk_duration if state.avg_chunk_duration > 0 else 0

        return {
            "expected_rps": initial_expected_rps,
            "current_rps": round(current_rps, 2),
            "efficiency_percentage": round((current_rps / initial_expected_rps) * 100, 1),
            "avg_chunk_duration": state.avg_chunk_duration,
            "total_chunks_completed": len(state.completed_chunks)
        }

    def cleanup_completed_collections(self, max_age_hours: int = 24):
        """완료된 수집 상태 정리"""

        current_time = datetime.now(timezone.utc)
        cutoff_time = current_time - timedelta(hours=max_age_hours)

        completed_ids = []
        for request_id, state in self.active_collections.items():
            if state.is_completed and state.start_time < cutoff_time:
                completed_ids.append(request_id)

        for request_id in completed_ids:
            del self.active_collections[request_id]
            logger.debug(f"완료된 수집 상태 정리: {request_id}")

        if completed_ids:
            logger.info(f"수집 상태 정리 완료: {len(completed_ids)}개")
