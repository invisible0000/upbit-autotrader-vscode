"""
CandleDataProvider v5.0 - 리팩터링된 깔끔한 버전

Created: 2025-09-17
Purpose: 코드 가독성 향상, 중복 제거, 논리적 메서드 순서 재정렬
Features: RequestType Enum, 사전 계산된 RequestInfo, 타입별 분기 로직, 최적화된 OverlapAnalyzer
Architecture: DDD Infrastructure 계층, 의존성 주입 패턴
"""

from datetime import datetime, timezone, timedelta
from typing import Optional, List, Dict, Any
from enum import Enum
from dataclasses import dataclass, field

from upbit_auto_trading.infrastructure.logging import create_component_logger
from upbit_auto_trading.infrastructure.market_data.candle.time_utils import TimeUtils
from upbit_auto_trading.infrastructure.market_data.candle.candle_models import (
    ChunkInfo, CandleData
)
from upbit_auto_trading.domain.repositories.candle_repository_interface import (
    CandleRepositoryInterface
)
from upbit_auto_trading.infrastructure.external_apis.upbit.upbit_public_client import (
    UpbitPublicClient
)
from upbit_auto_trading.infrastructure.market_data.candle.overlap_analyzer import (
    OverlapAnalyzer
)

logger = create_component_logger("CandleDataProvider")


class RequestType(Enum):
    """요청 타입 분류 - 시간 정렬 및 OverlapAnalyzer 최적화용"""
    COUNT_ONLY = "count_only"      # count만, to=None (첫 청크 OverlapAnalyzer 건너뜀)
    TO_COUNT = "to_count"          # to + count (to만 정렬, OverlapAnalyzer 사용)
    TO_END = "to_end"              # to + end (to만 정렬, OverlapAnalyzer 사용)
    END_ONLY = "end_only"          # end만, COUNT_ONLY처럼 동작 (동적 count 계산)


@dataclass(frozen=True)
class RequestInfo:
    """
    강화된 요청 정보 모델 - 사전 계산된 안전한 시간 정렬 지원

    주요 개선사항:
    - 생성 시점에 aligned_to, aligned_end, expected_count 사전 계산
    - 중복 계산 제거로 성능 향상 및 일관성 보장
    - 타입별 분류 및 OverlapAnalyzer 최적화 지원
    """
    # 필수 파라미터
    symbol: str
    timeframe: str

    # 선택적 파라미터 (원시 입력)
    count: Optional[int] = None
    to: Optional[datetime] = None
    end: Optional[datetime] = None

    # 요청 시점 기록
    request_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    # 사전 계산된 필드들 (성능 + 일관성 보장)
    aligned_to: Optional[datetime] = field(init=False)
    aligned_end: Optional[datetime] = field(init=False)
    expected_count: Optional[int] = field(init=False)

    def __post_init__(self):
        """요청 정보 검증 및 사전 계산"""
        # 기본 파라미터 검증
        if not self.symbol:
            raise ValueError("symbol은 필수입니다")
        if not self.timeframe:
            raise ValueError("timeframe은 필수입니다")

        # count 범위 검증
        if self.count is not None and self.count < 1:
            raise ValueError("count는 1 이상이어야 합니다")

        # 시간 순서 검증 (to > end 이어야 함)
        if self.to is not None and self.end is not None and self.to <= self.end:
            raise ValueError("to 시점은 end 시점보다 미래여야 합니다")

        # count와 end 동시 사용 방지
        if self.count is not None and self.end is not None:
            raise ValueError("count와 end는 동시에 사용할 수 없습니다")

        # 최소 파라미터 조합 확인
        has_count = self.count is not None
        has_to = self.to is not None
        has_end = self.end is not None

        valid_combinations = [
            has_count and not has_end,  # count만 또는 to + count
            has_to and has_end and not has_count,  # to + end
            has_end and not has_count and not has_to  # end만
        ]

        if not any(valid_combinations):
            raise ValueError("유효하지 않은 파라미터 조합입니다")

        # 사전 계산 영역 - 성능 + 일관성 보장
        request_type = self._get_request_type_internal()

        # 1. 시간 정렬 사전 계산
        if request_type in [RequestType.TO_COUNT, RequestType.TO_END] and self.to is not None:
            object.__setattr__(self, 'aligned_to', TimeUtils.align_to_candle_boundary(self.to, self.timeframe))
        else:
            object.__setattr__(self, 'aligned_to', None)

        if self.end is not None:
            object.__setattr__(self, 'aligned_end', TimeUtils.align_to_candle_boundary(self.end, self.timeframe))
        else:
            object.__setattr__(self, 'aligned_end', None)

        # 2. 예상 캔들 개수 사전 계산
        if request_type in [RequestType.COUNT_ONLY, RequestType.TO_COUNT]:
            object.__setattr__(self, 'expected_count', self.count)
        elif request_type in [RequestType.TO_END, RequestType.END_ONLY]:
            if self.aligned_to and self.aligned_end:
                calculated_count = TimeUtils.calculate_expected_count(
                    self.aligned_to, self.aligned_end, self.timeframe
                )
                object.__setattr__(self, 'expected_count', calculated_count)
            else:
                # END_ONLY의 경우 현재 시간 기준으로 계산
                current_time = datetime.now(timezone.utc)
                aligned_current = TimeUtils.align_to_candle_boundary(current_time, self.timeframe)
                calculated_count = TimeUtils.calculate_expected_count(
                    aligned_current, self.aligned_end, self.timeframe
                )
                object.__setattr__(self, 'expected_count', calculated_count)
        else:
            object.__setattr__(self, 'expected_count', None)

    def _get_request_type_internal(self) -> RequestType:
        """내부용 요청 타입 계산 (frozen 필드 설정 전 사용)"""
        has_count = self.count is not None
        has_to = self.to is not None
        has_end = self.end is not None

        if has_count and not has_to and not has_end:
            return RequestType.COUNT_ONLY
        elif has_to and has_count and not has_end:
            return RequestType.TO_COUNT
        elif has_to and has_end and not has_count:
            return RequestType.TO_END
        elif has_end and not has_to and not has_count:
            return RequestType.END_ONLY
        else:
            raise ValueError(f"알 수 없는 요청 타입: count={has_count}, to={has_to}, end={has_end}")

    def get_request_type(self) -> RequestType:
        """요청 타입 자동 분류"""
        return self._get_request_type_internal()

    def should_align_time(self) -> bool:
        """시간 정렬 필요 여부 - TO_COUNT, TO_END만 true"""
        request_type = self.get_request_type()
        return request_type in [RequestType.TO_COUNT, RequestType.TO_END]

    def needs_current_time_fallback(self) -> bool:
        """현재 시간 폴백 필요 여부 - END_ONLY만 true"""
        return self.get_request_type() == RequestType.END_ONLY

    def should_skip_overlap_analysis_for_first_chunk(self) -> bool:
        """첫 청크 OverlapAnalyzer 건너뛸지 - COUNT_ONLY와 END_ONLY만 true"""
        request_type = self.get_request_type()
        return request_type in [RequestType.COUNT_ONLY, RequestType.END_ONLY]

    def get_aligned_to_time(self) -> Optional[datetime]:
        """사전 계산된 정렬 시간 반환"""
        return self.aligned_to

    def get_aligned_end_time(self) -> Optional[datetime]:
        """사전 계산된 정렬 종료 시간 반환"""
        return self.aligned_end

    def get_expected_count(self) -> Optional[int]:
        """사전 계산된 예상 캔들 개수 반환"""
        return self.expected_count

    def to_log_string(self) -> str:
        """로깅용 문자열 (디버깅 편의성)"""
        request_type = self.get_request_type()
        return (f"RequestInfo[{request_type.value}]: {self.symbol} {self.timeframe}, "
                f"count={self.count}, to={self.to}, end={self.end}")


class ChunkStatus(Enum):
    """청크 처리 상태"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class CollectionState:
    """캔들 수집 상태 관리 - RequestInfo 포함"""
    request_id: str
    request_info: RequestInfo
    symbol: str
    timeframe: str
    total_requested: int
    total_collected: int = 0
    completed_chunks: List[ChunkInfo] = field(default_factory=list)
    current_chunk: Optional[ChunkInfo] = None
    last_candle_time: Optional[str] = None
    estimated_total_chunks: int = 0
    estimated_completion_time: Optional[datetime] = None
    start_time: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    is_completed: bool = False
    error_message: Optional[str] = None
    target_end: Optional[datetime] = None

    # 실시간 시간 추적 필드들
    last_update_time: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    avg_chunk_duration: float = 0.0
    remaining_chunks: int = 0
    estimated_remaining_seconds: float = 0.0


@dataclass
class CollectionPlan:
    """수집 계획 (최소 정보만)"""
    total_count: int
    estimated_chunks: int
    estimated_duration_seconds: float
    first_chunk_params: Dict[str, Any]


class CandleDataProvider:
    """
    캔들 데이터 제공자 v5.0 - 리팩터링된 깔끔한 버전

    주요 개선사항:
    1. 중복 메서드 제거 - 래퍼 메서드들 완전 제거
    2. 논리적 흐름에 따른 메서드 재배치
    3. RequestInfo 생성 최적화 - 각 메서드에서 한 번만 생성
    4. 코드 가독성 극대화 - 과도한 로깅과 주석 정리
    5. 핵심 로직과 성능 최적화는 모두 유지

    해결되는 문제:
    - 중복 메서드들로 인한 코드 복잡성
    - RequestInfo 중복 생성 문제
    - 메서드 순서의 논리성 부족
    - 과도한 로깅과 장식으로 인한 가독성 저하
    """

    def __init__(
        self,
        repository: CandleRepositoryInterface,
        upbit_client: UpbitPublicClient,
        overlap_analyzer: OverlapAnalyzer,
        chunk_size: int = 200
    ):
        """CandleDataProvider v5.0 초기화 - DI 패턴 적용"""
        self.repository = repository
        self.upbit_client = upbit_client
        self.overlap_analyzer = overlap_analyzer
        self.chunk_size = min(chunk_size, 200)  # 업비트 제한 준수
        self.active_collections: Dict[str, CollectionState] = {}
        self.api_rate_limit_rps = 10  # 10 RPS 기준

        logger.info("CandleDataProvider v5.0 (리팩터링 완료) 초기화")
        logger.info(f"청크 크기: {self.chunk_size}, API Rate Limit: {self.api_rate_limit_rps} RPS")

    # =========================================================================
    # 핵심 공개 API - 사용자가 주로 호출하는 메서드들
    # =========================================================================

    async def get_candles(
        self,
        symbol: str,
        timeframe: str,
        count: Optional[int] = None,
        to: Optional[datetime] = None,
        end: Optional[datetime] = None
    ) -> List[CandleData]:
        """
        완전 자동화된 캔들 수집 - 간편한 인터페이스

        Args:
            symbol: 거래 심볼 (예: 'KRW-BTC')
            timeframe: 타임프레임 (예: '1m', '5m')
            count: 수집할 캔들 개수
            to: 시작 시간 (사용자 관점에서 최신 캔들 시간)
            end: 종료 시간 (사용자 관점에서 가장 과거 캔들 시간)

        Returns:
            List[CandleData]: 수집된 캔들 데이터 (업비트 내림차순)
        """
        logger.info(f"캔들 수집 요청: {symbol} {timeframe}")
        if count:
            logger.info(f"개수: {count}개")
        if to:
            logger.info(f"시작: {to}")
        if end:
            logger.info(f"종료: {end}")

        # 수집 시작
        request_id = self.start_collection(
            symbol=symbol,
            timeframe=timeframe,
            count=count,
            to=to,
            end=end
        )

        collected_candles = []

        try:
            # 청크별 자동 처리 루프
            while True:
                chunk_info = self.get_next_chunk(request_id)
                if chunk_info is None:
                    break

                # 청크 완료 처리 (내부적으로 수집 및 DB 저장)
                await self.mark_chunk_completed(request_id)

            # 수집 상태에서 결과 추출
            collection_state = self.active_collections.get(request_id)
            if collection_state and collection_state.is_completed:
                logger.info(f"캔들 수집 완료: {collection_state.total_collected}개")

                # Repository에서 수집된 데이터 조회
                if to and count:
                    # aligned_to = TimeUtils.align_to_candle_boundary(to, timeframe)
                    aligned_to = collection_state.completed_chunks[0].to
                    end_time = TimeUtils.get_time_by_ticks(aligned_to, timeframe, -(count - 1))
                    collected_candles = await self.repository.get_candles_by_range(
                        symbol, timeframe, aligned_to, end_time
                    )
                elif count:
                    collected_candles = await self.repository.get_latest_candles(
                        symbol, timeframe, count
                    )

            return collected_candles

        except Exception as e:
            logger.error(f"캔들 수집 실패: {e}")
            raise
        finally:
            # 수집 상태 정리
            if request_id in self.active_collections:
                del self.active_collections[request_id]

    def start_collection(
        self,
        symbol: str,
        timeframe: str,
        count: Optional[int] = None,
        to: Optional[datetime] = None,
        end: Optional[datetime] = None
    ) -> str:
        """캔들 수집 시작"""
        # RequestInfo 생성 (검증 포함)
        request_info = RequestInfo(
            symbol=symbol,
            timeframe=timeframe,
            count=count,
            to=to,
            end=end
        )

        logger.info(f"캔들 수집 시작: {request_info.to_log_string()}")

        # 수집 계획 수립
        plan = self.plan_collection(symbol, timeframe, count, to, end)

        # 요청 ID 생성
        request_id = f"{symbol}_{timeframe}_{int(datetime.now().timestamp())}"

        # 수집 상태 초기화
        estimated_completion = datetime.now(timezone.utc) + timedelta(
            seconds=plan.estimated_duration_seconds
        )

        collection_state = CollectionState(
            request_id=request_id,
            request_info=request_info,
            symbol=symbol,
            timeframe=timeframe,
            total_requested=plan.total_count,
            estimated_total_chunks=plan.estimated_chunks,
            estimated_completion_time=estimated_completion,
            remaining_chunks=plan.estimated_chunks,
            estimated_remaining_seconds=plan.estimated_duration_seconds,
            target_end=end
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

        logger.info(f"수집 시작 완료: 요청 ID {request_id}")
        return request_id

    def get_next_chunk(self, request_id: str) -> Optional[ChunkInfo]:
        """다음 처리할 청크 정보 반환"""
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

    async def mark_chunk_completed(self, request_id: str) -> bool:
        """
        청크 완료 처리 - RequestInfo 기반 최적화 적용

        Returns:
            bool: 전체 수집 완료 여부 (True: 완료, False: 계속)
        """
        if request_id not in self.active_collections:
            raise ValueError(f"알 수 없는 요청 ID: {request_id}")

        state = self.active_collections[request_id]

        if state.current_chunk is None:
            raise ValueError("처리 중인 청크가 없습니다")

        # 요청 타입 기반 최적화
        is_first_chunk = len(state.completed_chunks) == 0
        request_type = state.request_info.get_request_type()

        logger.info(f"청크 처리 시작: {state.current_chunk.chunk_id} [{request_type.value}]")

        try:
            # COUNT_ONLY와 END_ONLY 첫 청크는 OverlapAnalyzer 건너뜀
            if is_first_chunk and request_type in [RequestType.COUNT_ONLY, RequestType.END_ONLY]:
                logger.debug(f"{request_type.value} 첫 청크: OverlapAnalyzer 건너뜀")

                api_response = await self._fetch_chunk_from_api(state.current_chunk)
                candle_data_list = self._convert_upbit_response_to_candles(
                    api_response, state.timeframe
                )

            else:
                # 일반적인 경우: OverlapAnalyzer 사용
                logger.debug(f"OverlapAnalyzer 적용: {request_type.value}")

                chunk_start = state.current_chunk.to
                chunk_end = self._calculate_chunk_end_time(state.current_chunk)

                overlap_result = await self._analyze_chunk_overlap(
                    state.symbol, state.timeframe, chunk_start, chunk_end
                )

                if overlap_result and hasattr(overlap_result, 'status'):
                    candle_data_list, _ = await self._collect_data_by_overlap_strategy(
                        state.current_chunk, overlap_result
                    )
                    logger.info(f"겹침 분석 적용: {overlap_result.status.value}")
                else:
                    # 겹침 분석 실패 시 폴백
                    logger.warning("겹침 분석 실패 → API 호출 폴백")
                    api_response = await self._fetch_chunk_from_api(state.current_chunk)
                    candle_data_list = self._convert_upbit_response_to_candles(
                        api_response, state.timeframe
                    )

            # Repository를 통한 DB 저장
            if candle_data_list:
                saved_count = await self._save_candles_to_repository(
                    state.symbol, state.timeframe, candle_data_list
                )
            else:
                saved_count = 0

            # 현재 청크 완료 처리
            completed_chunk = state.current_chunk
            completed_chunk.status = "completed"
            state.completed_chunks.append(completed_chunk)
            state.total_collected += len(candle_data_list)

            # 마지막 캔들 시간 업데이트 (다음 청크 연속성용)
            if candle_data_list:
                last_candle = candle_data_list[-1]
                if hasattr(last_candle, 'candle_date_time_utc'):
                    state.last_candle_time = last_candle.candle_date_time_utc
                elif isinstance(last_candle, dict) and 'candle_date_time_utc' in last_candle:
                    state.last_candle_time = last_candle['candle_date_time_utc']

            # 남은 시간 정보 업데이트
            self._update_remaining_time_estimates(state)

            logger.info(f"청크 완료: {completed_chunk.chunk_id}, "
                        f"수집: {len(candle_data_list)}개, 저장: {saved_count}개, "
                        f"누적: {state.total_collected}/{state.total_requested}")

            # 수집 완료 확인 (개수 + 시간 조건)
            count_reached = state.total_collected >= state.total_requested

            # end 시점 도달 확인
            end_time_reached = False
            if state.target_end and candle_data_list:
                try:
                    last_candle = candle_data_list[-1]
                    last_candle_time_str = None

                    if hasattr(last_candle, 'candle_date_time_utc'):
                        last_candle_time_str = last_candle.candle_date_time_utc
                    elif isinstance(last_candle, dict) and 'candle_date_time_utc' in last_candle:
                        last_candle_time_str = last_candle['candle_date_time_utc']

                    if last_candle_time_str:
                        if last_candle_time_str.endswith('Z'):
                            last_candle_time_str = last_candle_time_str[:-1] + '+00:00'
                        last_candle_time = datetime.fromisoformat(last_candle_time_str)
                        end_time_reached = last_candle_time <= state.target_end

                except Exception as e:
                    logger.warning(f"시간 파싱 실패: {e}")

            if count_reached or end_time_reached:
                completion_reason = "개수 달성" if count_reached else "end 시점 도달"
                state.is_completed = True
                state.current_chunk = None
                logger.info(f"전체 수집 완료 ({completion_reason}): {request_id}")
                return True

            # 다음 청크 생성
            next_chunk_index = len(state.completed_chunks)
            remaining_count = state.total_requested - state.total_collected
            next_chunk_size = min(remaining_count, self.chunk_size)

            next_chunk_params = self._create_next_chunk_params(
                state, next_chunk_size, request_type
            )

            next_chunk = self._create_next_chunk(
                collection_state=state,
                chunk_params=next_chunk_params,
                chunk_index=next_chunk_index
            )
            state.current_chunk = next_chunk

            logger.debug(f"다음 청크 생성: {next_chunk.chunk_id}")
            return False

        except Exception as e:
            # 청크 실패 처리
            if state.current_chunk:
                state.current_chunk.status = "failed"
                state.error_message = str(e)

            logger.error(f"청크 처리 실패: {state.current_chunk.chunk_id if state.current_chunk else 'Unknown'}, 오류: {e}")
            raise

    def get_collection_status(self, request_id: str) -> Dict[str, Any]:
        """수집 상태 조회 - RequestInfo 정보 포함"""
        if request_id not in self.active_collections:
            raise ValueError(f"알 수 없는 요청 ID: {request_id}")

        state = self.active_collections[request_id]

        progress_percentage = (state.total_collected / state.total_requested) * 100
        elapsed_time = datetime.now(timezone.utc) - state.start_time
        completed_chunks = len(state.completed_chunks)

        return {
            "request_id": request_id,
            "request_info": {
                "type": state.request_info.get_request_type().value,
                "symbol": state.request_info.symbol,
                "timeframe": state.request_info.timeframe,
                "count": state.request_info.count,
                "to": state.request_info.to.isoformat() if state.request_info.to else None,
                "end": state.request_info.end.isoformat() if state.request_info.end else None,
                "request_at": state.request_info.request_at.isoformat(),
                "should_align_time": state.request_info.should_align_time(),
                "skip_first_overlap_analysis": state.request_info.should_skip_overlap_analysis_for_first_chunk(),
                "aligned_to": state.request_info.aligned_to.isoformat() if state.request_info.aligned_to else None,
                "aligned_end": state.request_info.aligned_end.isoformat() if state.request_info.aligned_end else None,
                "expected_count": state.request_info.expected_count
            },
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

    # =========================================================================
    # 계획 수립
    # =========================================================================

    def plan_collection(
        self,
        symbol: str,
        timeframe: str,
        count: Optional[int] = None,
        to: Optional[datetime] = None,
        end: Optional[datetime] = None
    ) -> CollectionPlan:
        """수집 계획 수립 - RequestInfo 기반"""
        # RequestInfo 생성 (검증 포함)
        request_info = RequestInfo(
            symbol=symbol,
            timeframe=timeframe,
            count=count,
            to=to,
            end=end
        )

        logger.info(f"수집 계획 수립: {request_info.to_log_string()}")

        # 동적 비즈니스 검증
        current_time = datetime.now(timezone.utc)
        if to is not None and to > current_time:
            raise ValueError(f"to 시점이 미래입니다: {to}")
        if end is not None and end > current_time:
            raise ValueError(f"end 시점이 미래입니다: {end}")

        # 총 캔들 개수 계산
        total_count = self._calculate_total_count_by_type(request_info, current_time)

        # 예상 청크 수 계산
        estimated_chunks = (total_count + self.chunk_size - 1) // self.chunk_size

        # 예상 완료 시간 계산 (10 RPS 기준)
        estimated_duration_seconds = estimated_chunks / self.api_rate_limit_rps

        # 첫 번째 청크 파라미터 생성
        first_chunk_params = self._create_first_chunk_params_by_type(request_info, current_time)

        plan = CollectionPlan(
            total_count=total_count,
            estimated_chunks=estimated_chunks,
            estimated_duration_seconds=estimated_duration_seconds,
            first_chunk_params=first_chunk_params
        )

        logger.info(f"계획 수립 완료: {total_count:,}개 캔들, {estimated_chunks}청크, "
                    f"예상 소요시간: {estimated_duration_seconds:.1f}초")
        return plan

    # =========================================================================
    # 청크 처리 핵심 로직
    # =========================================================================

    async def _fetch_chunk_from_api(self, chunk_info: ChunkInfo) -> List[Dict[str, Any]]:
        """실제 API 호출을 통한 청크 데이터 수집"""
        logger.debug(f"API 청크 요청: {chunk_info.chunk_id}")

        try:
            # 타임프레임별 API 메서드 선택
            if chunk_info.timeframe == '1s':
                # 초봉 API 지출점 보정 (내부 → API 요청 시간)
                to_param = None
                if chunk_info.to:
                    timeframe_delta = TimeUtils.get_timeframe_delta(chunk_info.timeframe)
                    fetch_time = chunk_info.to + timeframe_delta
                    to_param = fetch_time.strftime("%Y-%m-%dT%H:%M:%S")

                candles = await self.upbit_client.get_candles_seconds(
                    market=chunk_info.symbol,
                    count=chunk_info.count,
                    to=to_param
                )

            elif chunk_info.timeframe.endswith('m'):
                # 분봉
                unit = int(chunk_info.timeframe[:-1])
                if unit not in [1, 3, 5, 10, 15, 30, 60, 240]:
                    raise ValueError(f"지원하지 않는 분봉 단위: {unit}")

                # 분봉 API 지출점 보정 (내부 → API 요청 시간)
                to_param = None
                if chunk_info.to:
                    timeframe_delta = TimeUtils.get_timeframe_delta(chunk_info.timeframe)
                    fetch_time = chunk_info.to + timeframe_delta
                    to_param = fetch_time.strftime("%Y-%m-%dT%H:%M:%S")

                candles = await self.upbit_client.get_candles_minutes(
                    unit=unit,
                    market=chunk_info.symbol,
                    count=chunk_info.count,
                    to=to_param
                )

            elif chunk_info.timeframe == '1d':
                # 일봉 API 지출점 보정
                to_param = None
                if chunk_info.to:
                    fetch_start_time = TimeUtils.get_time_by_ticks(chunk_info.to, chunk_info.timeframe, 1)
                    to_param = fetch_start_time.strftime("%Y-%m-%d")

                candles = await self.upbit_client.get_candles_days(
                    market=chunk_info.symbol,
                    count=chunk_info.count,
                    to=to_param
                )

            elif chunk_info.timeframe == '1w':
                # 주봉 API 지출점 보정
                to_param = None
                if chunk_info.to:
                    fetch_start_time = TimeUtils.get_time_by_ticks(chunk_info.to, chunk_info.timeframe, 1)
                    to_param = fetch_start_time.strftime("%Y-%m-%d")

                candles = await self.upbit_client.get_candles_weeks(
                    market=chunk_info.symbol,
                    count=chunk_info.count,
                    to=to_param
                )

            elif chunk_info.timeframe == '1M':
                # 월봉 API 지출점 보정
                to_param = None
                if chunk_info.to:
                    fetch_start_time = TimeUtils.get_time_by_ticks(chunk_info.to, chunk_info.timeframe, 1)
                    to_param = fetch_start_time.strftime("%Y-%m")

                candles = await self.upbit_client.get_candles_months(
                    market=chunk_info.symbol,
                    count=chunk_info.count,
                    to=to_param
                )

            elif chunk_info.timeframe == '1y':
                # 연봉 API 지출점 보정
                to_param = None
                if chunk_info.to:
                    fetch_start_time = TimeUtils.get_time_by_ticks(chunk_info.to, chunk_info.timeframe, 1)
                    to_param = fetch_start_time.strftime("%Y")

                candles = await self.upbit_client.get_candles_years(
                    market=chunk_info.symbol,
                    count=chunk_info.count,
                    to=to_param
                )

            else:
                raise ValueError(f"지원하지 않는 타임프레임: {chunk_info.timeframe}")

            logger.info(f"API 청크 완료: {chunk_info.chunk_id}, 수집: {len(candles)}개")
            return candles

        except Exception as e:
            logger.error(f"API 청크 실패: {chunk_info.chunk_id}, 오류: {e}")
            raise

    def _convert_upbit_response_to_candles(
        self,
        api_response: List[Dict[str, Any]],
        timeframe: str
    ) -> List[CandleData]:
        """업비트 API 응답을 CandleData 객체로 변환"""
        logger.debug(f"API 응답 변환: {len(api_response)}개 캔들")

        try:
            converted_candles = []
            for candle_dict in api_response:
                candle_data = CandleData.from_upbit_api(candle_dict, timeframe)
                converted_candles.append(candle_data)

            logger.debug(f"API 응답 변환 완료: {len(converted_candles)}개")
            return converted_candles

        except Exception as e:
            logger.error(f"API 응답 변환 실패: {e}")
            raise

    async def _save_candles_to_repository(
        self,
        symbol: str,
        timeframe: str,
        candles: List[CandleData]
    ) -> int:
        """Repository를 통한 캔들 데이터 DB 저장"""
        if not candles:
            logger.warning("저장할 캔들 데이터가 없습니다")
            return 0

        logger.debug(f"DB 저장: {symbol} {timeframe}, {len(candles)}개")

        try:
            saved_count = await self.repository.save_candle_chunk(symbol, timeframe, candles)
            logger.debug(f"DB 저장 완료: {saved_count}/{len(candles)}개")
            return saved_count

        except Exception as e:
            logger.error(f"DB 저장 실패: {e}")
            raise

    async def _analyze_chunk_overlap(
        self,
        symbol: str,
        timeframe: str,
        start_time: datetime,
        end_time: datetime
    ):
        """OverlapAnalyzer를 활용한 청크 겹침 분석"""
        logger.debug(f"겹침 분석: {symbol} {timeframe}")

        try:
            from upbit_auto_trading.infrastructure.market_data.candle.candle_models import OverlapRequest

            # Timezone 안전 처리: 모든 datetime을 UTC로 통일
            safe_start_time = self._ensure_utc_timezone(start_time)
            safe_end_time = self._ensure_utc_timezone(end_time)

            # 예상 캔들 개수 계산
            expected_count = self._calculate_api_count(safe_start_time, safe_end_time, timeframe)

            overlap_request = OverlapRequest(
                symbol=symbol,
                timeframe=timeframe,
                target_start=safe_start_time,
                target_end=safe_end_time,
                target_count=expected_count
            )

            overlap_result = await self.overlap_analyzer.analyze_overlap(overlap_request)
            logger.debug(f"겹침 분석 결과: {overlap_result.status.value}")

            return overlap_result

        except Exception as e:
            logger.warning(f"겹침 분석 실패: {e}")
            return None

    async def _collect_data_by_overlap_strategy(
        self,
        chunk_info: ChunkInfo,
        overlap_result
    ) -> tuple[list, bool]:
        """겹침 분석 결과에 따른 최적화된 데이터 수집"""
        from upbit_auto_trading.infrastructure.market_data.candle.candle_models import OverlapStatus

        status = overlap_result.status

        if status == OverlapStatus.COMPLETE_OVERLAP:
            # 완전 겹침: DB에서만 데이터 가져오기
            logger.debug("완전 겹침 → DB 조회")
            db_candles = await self.repository.get_candles_by_range(
                chunk_info.symbol,
                chunk_info.timeframe,
                overlap_result.db_start,
                overlap_result.db_end
            )
            return db_candles, False  # API 호출 없음

        elif status == OverlapStatus.NO_OVERLAP:
            # 겹침 없음: API에서만 데이터 가져오기
            logger.debug("겹침 없음 → 전체 API 요청")
            api_response = await self._fetch_chunk_from_api(chunk_info)
            candle_data_list = self._convert_upbit_response_to_candles(
                api_response, chunk_info.timeframe
            )
            return candle_data_list, True

        elif status in [OverlapStatus.PARTIAL_START, OverlapStatus.PARTIAL_MIDDLE_CONTINUOUS]:
            # 부분 겹침: DB + API 혼합 처리
            logger.debug(f"부분 겹침 ({status.value}) → DB + API 혼합")

            # DB 데이터 수집
            db_candles = []
            if overlap_result.db_start and overlap_result.db_end:
                db_candles = await self.repository.get_candles_by_range(
                    chunk_info.symbol,
                    chunk_info.timeframe,
                    overlap_result.db_start,
                    overlap_result.db_end
                )

            # API 데이터 수집
            api_candles = []
            if overlap_result.api_start and overlap_result.api_end:
                # API 요청 개수 동적 계산
                api_count = self._calculate_api_count(
                    overlap_result.api_start,
                    overlap_result.api_end,
                    chunk_info.timeframe
                )

                # 부분 API 요청을 위한 임시 청크 정보 생성
                temp_chunk = ChunkInfo(
                    chunk_id=f"{chunk_info.chunk_id}_partial",
                    chunk_index=chunk_info.chunk_index,
                    symbol=chunk_info.symbol,
                    timeframe=chunk_info.timeframe,
                    count=api_count,
                    to=overlap_result.api_start,
                    end=overlap_result.api_end,
                    status="pending"
                )
                api_response = await self._fetch_chunk_from_api(temp_chunk)
                api_candles = self._convert_upbit_response_to_candles(
                    api_response, chunk_info.timeframe
                )

            # 시간순으로 병합 (업비트 내림차순 기준)
            combined_candles = self._merge_candles_by_time(db_candles, api_candles)
            return combined_candles, len(api_candles) > 0

        else:
            # PARTIAL_MIDDLE_FRAGMENT 또는 기타: 안전한 폴백 → 전체 API 요청
            logger.debug("복잡한 겹침 → 전체 API 요청 폴백")
            api_response = await self._fetch_chunk_from_api(chunk_info)
            candle_data_list = self._convert_upbit_response_to_candles(
                api_response, chunk_info.timeframe
            )
            return candle_data_list, True

    # =========================================================================
    # RequestInfo 및 파라미터 생성
    # =========================================================================

    def _calculate_total_count_by_type(
        self,
        request_info: RequestInfo,
        current_time: datetime
    ) -> int:
        """사전 계산된 예상 캔들 개수 반환"""
        expected_count = request_info.get_expected_count()

        if expected_count is None:
            raise ValueError(f"예상 캔들 개수가 계산되지 않았습니다: {request_info.get_request_type()}")

        return expected_count

    def _create_first_chunk_params_by_type(
        self,
        request_info: RequestInfo,
        current_time: datetime
    ) -> Dict[str, Any]:
        """요청 타입별 첫 번째 청크 파라미터 생성"""
        request_type = request_info.get_request_type()
        params = {"market": request_info.symbol}

        if request_type == RequestType.COUNT_ONLY:
            # COUNT_ONLY: to 파라미터 없이 count만 사용
            chunk_size = min(request_info.count, self.chunk_size)
            params["count"] = chunk_size
            logger.debug(f"COUNT_ONLY: count={chunk_size} (서버 최신부터)")

        elif request_type == RequestType.TO_COUNT:
            # to + count: 사전 계산된 정렬 시간 사용
            chunk_size = min(request_info.count, self.chunk_size)
            aligned_to = request_info.get_aligned_to_time()

            # 진입점 보정 (사용자 시간 → 내부 시간 변환)
            first_chunk_start_time = TimeUtils.get_time_by_ticks(aligned_to, request_info.timeframe, -1)

            params["count"] = chunk_size
            params["to"] = first_chunk_start_time
            logger.debug(f"TO_COUNT: 진입점보정 {aligned_to} → {first_chunk_start_time}")

        elif request_type == RequestType.TO_END:
            # to + end: 사전 계산된 정렬 시간 사용
            aligned_to = request_info.get_aligned_to_time()

            # 진입점 보정 (사용자 시간 → 내부 시간 변환)
            first_chunk_start_time = TimeUtils.get_time_by_ticks(aligned_to, request_info.timeframe, -1)

            params["count"] = self.chunk_size
            params["to"] = first_chunk_start_time
            logger.debug(f"TO_END: 진입점보정 {aligned_to} → {first_chunk_start_time}")

        elif request_type == RequestType.END_ONLY:
            # END_ONLY: COUNT_ONLY처럼 to 없이 count만 사용
            params["count"] = self.chunk_size
            logger.debug(f"END_ONLY: count={self.chunk_size} (서버 최신부터)")

        return params

    def _create_next_chunk_params(
        self,
        state: CollectionState,
        chunk_size: int,
        request_type: RequestType
    ) -> Dict[str, Any]:
        """다음 청크 파라미터 생성 - 연속성 보장"""
        params = {
            "market": state.symbol,
            "count": chunk_size
        }

        # 청크 간 연속성 보장 로직
        if state.last_candle_time:
            try:
                # 마지막 캔들 시간을 datetime으로 변환
                last_time = datetime.fromisoformat(state.last_candle_time.replace('Z', '+00:00'))

                if request_type in [RequestType.COUNT_ONLY, RequestType.END_ONLY]:
                    # COUNT_ONLY와 END_ONLY는 두 번째 청크부터 마지막 시간 사용
                    params["to"] = last_time
                    logger.debug(f"{request_type.value} 후속 청크: to={last_time}")
                else:
                    # 청크 간 연속성 보장 (시간 순서 유지)
                    next_internal_time = TimeUtils.get_time_by_ticks(last_time, state.timeframe, -1)
                    params["to"] = next_internal_time
                    logger.debug(f"{request_type.value} 후속 청크: {last_time} → {next_internal_time}")

            except Exception as e:
                logger.warning(f"시간 조정 실패: {e}")
                try:
                    fallback_time = datetime.fromisoformat(state.last_candle_time.replace('Z', '+00:00'))
                    params["to"] = fallback_time
                except Exception:
                    logger.error("마지막 캔들 시간 파싱 실패")

        return params

    def _create_next_chunk(
        self,
        collection_state: CollectionState,
        chunk_params: Dict[str, Any],
        chunk_index: int
    ) -> ChunkInfo:
        """다음 청크 정보 생성"""
        chunk_id = f"{collection_state.symbol}_{collection_state.timeframe}_{chunk_index:05d}"
        current_time = datetime.now(timezone.utc)

        # 'to' 파라미터 처리
        if "to" in chunk_params and chunk_params["to"]:
            to_param = chunk_params["to"]
            if isinstance(to_param, datetime):
                to_datetime = to_param
            elif isinstance(to_param, str):
                try:
                    to_datetime = datetime.fromisoformat(to_param.replace('Z', '+00:00'))
                except (ValueError, TypeError):
                    logger.warning(f"'to' 파라미터 파싱 실패: {to_param}")
                    to_datetime = None
            else:
                logger.warning(f"'to' 파라미터 타입 오류: {type(to_param)}")
                to_datetime = None
        else:
            to_datetime = None  # COUNT_ONLY는 None 유지

        chunk_info = ChunkInfo(
            chunk_id=chunk_id,
            chunk_index=chunk_index,
            symbol=collection_state.symbol,
            timeframe=collection_state.timeframe,
            count=chunk_params["count"],
            to=to_datetime,
            end=current_time,
            status="pending"
        )

        return chunk_info

    # =========================================================================
    # 상태 관리 및 유틸리티
    # =========================================================================

    def resume_collection(self, request_id: str) -> Optional[ChunkInfo]:
        """중단된 수집 재개"""
        if request_id not in self.active_collections:
            raise ValueError(f"알 수 없는 요청 ID: {request_id}")

        state = self.active_collections[request_id]

        if state.is_completed:
            logger.info(f"이미 완료된 수집: {request_id}")
            return None

        if state.current_chunk is not None:
            logger.info(f"수집 재개: {request_id}")
            return state.current_chunk

        # 현재 청크가 없으면 새로 생성
        next_chunk_index = len(state.completed_chunks)
        remaining_count = state.total_requested - state.total_collected

        if remaining_count <= 0:
            state.is_completed = True
            return None

        next_chunk_size = min(remaining_count, self.chunk_size)
        request_type = state.request_info.get_request_type()

        next_chunk_params = self._create_next_chunk_params(
            state, next_chunk_size, request_type
        )

        next_chunk = self._create_next_chunk(
            collection_state=state,
            chunk_params=next_chunk_params,
            chunk_index=next_chunk_index
        )
        state.current_chunk = next_chunk

        logger.info(f"수집 재개: 새 청크 생성 {next_chunk.chunk_id}")
        return next_chunk

    def _update_remaining_time_estimates(self, state: CollectionState):
        """실시간 남은 시간 추정 업데이트"""
        current_time = datetime.now(timezone.utc)
        completed_chunks_count = len(state.completed_chunks)

        if completed_chunks_count == 0:
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

        state.last_update_time = current_time

    def get_realtime_remaining_time(self, request_id: str) -> Dict[str, Any]:
        """실시간 남은 시간 정보 조회"""
        if request_id not in self.active_collections:
            raise ValueError(f"알 수 없는 요청 ID: {request_id}")

        state = self.active_collections[request_id]
        current_time = datetime.now(timezone.utc)

        # 실시간 남은 시간 재계산
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

        if completed_ids:
            logger.info(f"수집 상태 정리 완료: {len(completed_ids)}개")

    # =========================================================================
    # 헬퍼 메서드들
    # =========================================================================

    def _calculate_chunk_end_time(self, chunk_info: ChunkInfo) -> datetime:
        """청크 요청의 예상 종료 시점 계산"""
        end_time = TimeUtils.get_time_by_ticks(chunk_info.to, chunk_info.timeframe, -(chunk_info.count - 1))
        logger.debug(f"청크 종료 시간 계산: {chunk_info.to} → {end_time}")
        return end_time

    def _ensure_utc_timezone(self, dt: datetime) -> datetime:
        """DateTime이 timezone을 가지지 않으면 UTC로 설정"""
        if dt.tzinfo is None:
            return dt.replace(tzinfo=timezone.utc)
        return dt

    def _calculate_api_count(self, start_time: datetime, end_time: datetime, timeframe: str) -> int:
        """API 요청에 필요한 캔들 개수 계산"""
        return TimeUtils.calculate_expected_count(start_time, end_time, timeframe)

    def _merge_candles_by_time(self, db_candles: list, api_candles: list) -> list:
        """시간 기준으로 캔들 데이터 병합 (업비트 내림차순 정렬 유지)"""
        # 모든 캔들을 합치고 중복 제거 후 시간순 정렬
        all_candles = db_candles + api_candles

        # candle_date_time_utc 기준으로 중복 제거
        unique_candles = {}
        for candle in all_candles:
            if hasattr(candle, 'candle_date_time_utc'):
                key = candle.candle_date_time_utc
            elif isinstance(candle, dict) and 'candle_date_time_utc' in candle:
                key = candle['candle_date_time_utc']
            else:
                continue
            unique_candles[key] = candle

        # 업비트 내림차순 정렬 (최신 → 과거)
        sorted_candles = sorted(
            unique_candles.values(),
            key=lambda x: (
                x.candle_date_time_utc if hasattr(x, 'candle_date_time_utc')
                else x.get('candle_date_time_utc', '')
            ),
            reverse=True
        )

        logger.debug(f"캔들 병합 완료: DB {len(db_candles)}개 + API {len(api_candles)}개 → 병합 {len(sorted_candles)}개")
        return sorted_candles

    def _is_collection_on_track(self, state: CollectionState) -> bool:
        """수집이 예정대로 진행되고 있는지 확인"""
        if len(state.completed_chunks) == 0:
            return True

        # 초기 예상 시간과 현재 평균 시간 비교
        initial_expected_duration = state.estimated_total_chunks / self.api_rate_limit_rps
        return state.avg_chunk_duration <= initial_expected_duration * 1.2

    def _get_performance_info(self, state: CollectionState) -> Dict[str, Any]:
        """수집 성능 정보 제공"""
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
