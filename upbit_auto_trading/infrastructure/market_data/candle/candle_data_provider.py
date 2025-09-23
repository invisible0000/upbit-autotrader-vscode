"""
CandleDataProvider v7.0 - ChunkProcessor 완전 통합 버전

Created: 2025-09-23
Updated: ChunkProcessor 통합으로 청크 처리 로직 완전 분리
Purpose: ChunkProcessor를 활용한 깔끔하고 효율적인 캔들 데이터 수집
Features: 4단계 파이프라인, 조기 종료 최적화, 성능 추적, 무한 루프 방지
Architecture: DDD Infrastructure 계층, 의존성 주        - 빈 캔듡 처리 및 정규화 패턴

주요 개선사항:
1. ChunkProcessor 완전 통합: 청크 처리 로직을 ChunkProcessor로 위임
2. 청크 진행 로직 수정: 무한 루프 방지 및 올바른 청크 인덱스 관리
3. 결과 처리 개선: ChunkResult 기반 상태 업데이트
4. 성능 최적화: 4단계 파이프라인으로 효율성 극대화
"""

from datetime import datetime, timezone, timedelta
from typing import Optional, List, Dict, Any
from dataclasses import dataclass

from upbit_auto_trading.infrastructure.logging import create_component_logger
from upbit_auto_trading.infrastructure.market_data.candle.time_utils import TimeUtils
from upbit_auto_trading.infrastructure.market_data.candle.models import (
    ChunkInfo, CandleData, CollectionState, RequestInfo, RequestType
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
from upbit_auto_trading.infrastructure.market_data.candle.empty_candle_detector import (
    EmptyCandleDetector
)

logger = create_component_logger("CandleDataProvider")


@dataclass
class CollectionPlan:
    """수집 계획"""
    total_count: int
    estimated_chunks: int
    estimated_duration_seconds: float
    first_chunk_params: Dict[str, Any]


class CandleDataProvider:
    """
    캔들 데이터 제공자 v7.0 - ChunkProcessor 완전 통합 버전

    주요 개선사항:
    1. ChunkProcessor 완전 통합: 청크 처리를 전문 클래스에 위임
    2. 청크 진행 로직 개선: 무한 루프 방지 및 올바른 상태 관리
    3. 결과 기반 처리: ChunkResult를 통한 명확한 상태 전환
    4. 성능 최적화: 4단계 파이프라인으로 효율성 극대화

    책임:
    - 전체 수집 프로세스 조정 (Orchestrator 역할)
    - Collection 상태 관리
    - 수집 계획 수립
    - 최종 결과 조회
    """

    def __init__(
        self,
        repository: CandleRepositoryInterface,
        upbit_client: UpbitPublicClient,
        overlap_analyzer: OverlapAnalyzer,
        chunk_size: int = 200,
        enable_empty_candle_processing: bool = True
    ):
        """CandleDataProvider v7.0 초기화 (ChunkProcessor 완전 통합)"""
        self.repository = repository
        self.upbit_client = upbit_client
        self.overlap_analyzer = overlap_analyzer
        self.chunk_size = min(chunk_size, 200)  # 업비트 제한 준수
        self.active_collections: Dict[str, CollectionState] = {}
        self.api_rate_limit_rps = 10  # 10 RPS 기준

        # 빈 캔들 처리 설정 (하위 호환성 유지)
        self.enable_empty_candle_processing = enable_empty_candle_processing
        self.empty_candle_detectors: Dict[str, EmptyCandleDetector] = {}

        # 🆕 ChunkProcessor 의존성 주입
        from upbit_auto_trading.infrastructure.market_data.candle.chunk_processor import ChunkProcessor

        self.chunk_processor = ChunkProcessor(
            overlap_analyzer=overlap_analyzer,
            upbit_client=upbit_client,
            repository=repository,
            empty_candle_detector_factory=self._get_empty_candle_detector
        )

        logger.info("CandleDataProvider v7.0 (ChunkProcessor 완전 통합) 초기화")
        logger.info(f"청크 크기: {self.chunk_size}, API Rate Limit: {self.api_rate_limit_rps} RPS")
        logger.info(f"빈 캔들 처리: {'활성화' if enable_empty_candle_processing else '비활성화'}")

    def _get_empty_candle_detector(self, symbol: str, timeframe: str) -> EmptyCandleDetector:
        """(symbol, timeframe) 조합별 EmptyCandleDetector 캐시"""
        cache_key = f"{symbol}_{timeframe}"
        if cache_key not in self.empty_candle_detectors:
            self.empty_candle_detectors[cache_key] = EmptyCandleDetector(symbol, timeframe)
            logger.debug(f"EmptyCandleDetector 생성: {symbol} {timeframe}")
        return self.empty_candle_detectors[cache_key]

    # =========================================================================
    # 핵심 공개 API
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
        완전 자동화된 캔들 수집 - ChunkProcessor 통합 버전

        ChunkProcessor를 활용한 고성능 캔들 데이터 수집
        """
        logger.info(f"캔들 수집 요청: {symbol} {timeframe}")
        if count:
            logger.info(f"개수: {count}개")
        if to:
            logger.info(f"시작: {to}")
        if end:
            logger.info(f"종료: {end}")

        # 🚀 UTC 통일: 진입점에서 한 번만 정규화
        normalized_to = TimeUtils.normalize_datetime_to_utc(to)
        normalized_end = TimeUtils.normalize_datetime_to_utc(end)

        logger.debug(f"UTC 정규화: to={to} → {normalized_to}, end={end} → {normalized_end}")

        # 수집 시작
        request_id = self.start_collection(
            symbol=symbol,
            timeframe=timeframe,
            count=count,
            to=normalized_to,
            end=normalized_end
        )

        try:
            # 청크별 자동 처리 루프 (ChunkProcessor 활용)
            while True:
                chunk_info = self.get_next_chunk(request_id)
                if chunk_info is None:
                    break

                # ChunkProcessor를 통한 청크 완료 처리
                is_collection_complete = await self.mark_chunk_completed(request_id)
                if is_collection_complete:
                    break

            # 수집 상태에서 결과 추출
            collection_state = self.active_collections.get(request_id)
            if collection_state and collection_state.is_completed:
                logger.info(f"캔들 수집 완료: {collection_state.total_collected}개")

                # Repository에서 수집된 데이터 조회
                collected_candles = await self._get_final_result(
                    collection_state, symbol, timeframe, count, to, end
                )
                return collected_candles

            return []

        except Exception as e:
            logger.error(f"캔들 수집 실패: {e}")
            raise
        finally:
            # 수집 상태 정리 (메모리 해제)
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
            estimated_remaining_seconds=plan.estimated_duration_seconds
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
        ✨ ChunkProcessor 통합 청크 완료 처리

        ChunkProcessor의 4단계 파이프라인을 활용하여:
        - 준비 및 겹침 분석
        - 최적화된 API 데이터 수집
        - 빈 캔들 처리 및 정규화
        - Repository를 통한 데이터 저장        Returns:
            bool: 전체 수집 완료 여부
        """
        if request_id not in self.active_collections:
            raise ValueError(f"알 수 없는 요청 ID: {request_id}")

        state = self.active_collections[request_id]
        current_chunk = state.current_chunk

        if current_chunk is None:
            raise ValueError("처리 중인 청크가 없습니다")

        logger.info(f"청크 처리 시작: {current_chunk.chunk_id}")

        try:
            # 🚀 핵심: ChunkProcessor에 위임
            chunk_result = await self.chunk_processor.execute_chunk_pipeline(
                current_chunk, state
            )

            # 결과 처리 및 상태 업데이트
            self._process_chunk_result(state, chunk_result)

            # 🆕 업비트 데이터 끝 도달 확인 (최우선 종료 조건)
            if hasattr(state, 'reached_upbit_data_end') and state.reached_upbit_data_end:
                state.is_completed = True
                state.current_chunk = None
                logger.info(f"🔴 업비트 데이터 끝 도달로 수집 완료: {request_id}")
                return True

            # 수집 완료 확인
            if self._is_collection_complete(state):
                state.is_completed = True
                state.current_chunk = None
                logger.info(f"전체 수집 완료: {request_id}")
                return True

            # 다음 청크 준비
            request_type = state.request_info.get_request_type()
            self._prepare_next_chunk(state, request_type)
            return False

        except Exception as e:
            # 청크 실패 처리
            if state.current_chunk:
                state.current_chunk.status = "failed"
                state.error_message = str(e)
            logger.error(f"청크 처리 실패: {current_chunk.chunk_id}, 오류: {e}")
            raise

    def _process_chunk_result(self, state: CollectionState, chunk_result) -> None:
        """청크 처리 결과를 CollectionState에 반영"""
        from upbit_auto_trading.infrastructure.market_data.candle.models import ChunkResultStatus

        if chunk_result.is_successful():
            # 성공적인 청크 완료 처리
            completed_chunk = state.current_chunk
            completed_chunk.status = "completed"
            state.completed_chunks.append(completed_chunk)

            # 🔄 수정된 카운팅 로직: 실제 저장된 개수 기준
            # 기존: 청크 담당 범위 기준 → 수정: 실제 저장 개수 기준
            state.total_collected += chunk_result.saved_count

            # 업비트 데이터 끝 도달 확인
            if chunk_result.status == ChunkResultStatus.EARLY_EXIT:
                state.reached_upbit_data_end = True
                logger.warning(f"📊 업비트 데이터 끝 도달: {completed_chunk.symbol} {completed_chunk.timeframe}")

            # 진행률 업데이트
            state.last_update_time = datetime.now(timezone.utc)

            logger.info(f"청크 완료: {completed_chunk.chunk_id}, "
                        f"저장: {chunk_result.saved_count}개, "
                        f"누적: {state.total_collected}/{state.total_requested}")

            # 상세한 청크 처리 요약 (디버깅용)
            if logger.level <= 10:  # DEBUG 레벨일 때만
                if hasattr(completed_chunk, 'get_processing_summary'):
                    summary = completed_chunk.get_processing_summary()
                    logger.debug(f"\n{summary}")

        else:
            # 실패 처리
            state.current_chunk.status = "failed"
            state.error_message = str(chunk_result.error)
            raise chunk_result.error

    # =========================================================================
    # 수집 계획 및 청크 관리
    # =========================================================================

    def plan_collection(
        self,
        symbol: str,
        timeframe: str,
        count: Optional[int] = None,
        to: Optional[datetime] = None,
        end: Optional[datetime] = None
    ) -> CollectionPlan:
        """수집 계획 수립"""
        # RequestInfo 생성 (검증 포함)
        request_info = RequestInfo(
            symbol=symbol,
            timeframe=timeframe,
            count=count,
            to=to,
            end=end
        )

        logger.info(f"수집 계획 수립: {request_info.to_internal_log_string()}")

        # 동적 비즈니스 검증 - 요청 시점 기준
        if to is not None and to > request_info.request_at:
            raise ValueError(f"to 시점이 미래입니다: {to}")
        if end is not None and end > request_info.request_at:
            raise ValueError(f"end 시점이 미래입니다: {end}")

        # 총 캔들 개수 계산
        total_count = self._calculate_total_count_by_type(request_info)

        # 예상 청크 수 계산
        estimated_chunks = (total_count + self.chunk_size - 1) // self.chunk_size

        # 예상 완료 시간 계산 (10 RPS 기준)
        estimated_duration_seconds = estimated_chunks / self.api_rate_limit_rps

        # 첫 번째 청크 파라미터 생성
        first_chunk_params = self._create_first_chunk_params_by_type(request_info)

        plan = CollectionPlan(
            total_count=total_count,
            estimated_chunks=estimated_chunks,
            estimated_duration_seconds=estimated_duration_seconds,
            first_chunk_params=first_chunk_params
        )

        logger.info(f"계획 수립 완료: {total_count:,}개 캔들, {estimated_chunks}청크, "
                    f"예상 소요시간: {estimated_duration_seconds:.1f}초")
        return plan

    def _create_next_chunk(
        self,
        collection_state: CollectionState,
        chunk_params: Dict[str, Any],
        chunk_index: int
    ) -> ChunkInfo:
        """다음 청크 정보 생성"""
        chunk_id = f"{collection_state.symbol}_{collection_state.timeframe}_{chunk_index:05d}"

        # 'to' 파라미터 처리
        if "to" in chunk_params and chunk_params["to"]:
            to_param = chunk_params["to"]
            if isinstance(to_param, datetime):
                to_datetime = to_param
            elif isinstance(to_param, str):
                try:
                    to_datetime = datetime.fromisoformat(to_param)
                except (ValueError, TypeError):
                    logger.warning(f"'to' 파라미터 파싱 실패: {to_param}")
                    to_datetime = None
            else:
                logger.warning(f"'to' 파라미터 타입 오류: {type(to_param)}")
                to_datetime = None
        else:
            to_datetime = None  # COUNT_ONLY는 None 유지

        # end 시간 계산 - 실제 데이터 범위 끝
        calculated_end = None
        if to_datetime and chunk_params.get("count"):
            # to와 count가 있으면 실제 데이터 범위 끝 계산
            calculated_end = TimeUtils.get_time_by_ticks(
                to_datetime,
                collection_state.timeframe,
                -(chunk_params["count"] - 1)
            )

        chunk_info = ChunkInfo(
            chunk_id=chunk_id,
            chunk_index=chunk_index,
            symbol=collection_state.symbol,
            timeframe=collection_state.timeframe,
            count=chunk_params["count"],
            to=to_datetime,
            end=calculated_end,
            status="pending"
        )

        return chunk_info

    def _is_collection_complete(self, state: CollectionState) -> bool:
        """수집 완료 여부 확인"""
        # 기본 개수 기준 완료 확인
        count_reached = state.total_collected >= state.total_requested

        # 업비트 데이터 끝 도달 확인
        upbit_data_end = getattr(state, 'reached_upbit_data_end', False)

        # 시간 기준 완료 확인 (TO_END, END_ONLY 타입)
        time_reached = False
        request_type = state.request_info.get_request_type()
        if request_type in [RequestType.TO_END, RequestType.END_ONLY] and state.completed_chunks:
            # 마지막 완료된 청크의 시간 정보 확인
            last_chunk = state.completed_chunks[-1]
            if hasattr(last_chunk, 'get_effective_end_time'):
                last_effective_time = last_chunk.get_effective_end_time()
                target_end = state.request_info.end
                if last_effective_time and target_end:
                    time_reached = last_effective_time <= target_end

        should_complete = count_reached or upbit_data_end or time_reached

        if should_complete:
            completion_reasons = []
            if count_reached:
                completion_reasons.append("개수달성")
            if upbit_data_end:
                completion_reasons.append("업비트데이터끝")
            if time_reached:
                completion_reasons.append("시간도달")

            logger.debug(f"🎯 수집 완료: {', '.join(completion_reasons)}")

        return should_complete

    def _prepare_next_chunk(self, state: CollectionState, request_type: RequestType):
        """다음 청크 준비 - 무한 루프 방지"""
        # 🔄 수정: 청크 인덱스를 completed_chunks 기준으로 정확히 계산
        next_chunk_index = len(state.completed_chunks)
        remaining_count = state.total_requested - state.total_collected

        # 남은 개수가 0 이하면 수집 완료
        if remaining_count <= 0:
            logger.info("남은 수집 개수가 없어 수집 완료")
            state.is_completed = True
            state.current_chunk = None
            return

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

        logger.debug(f"다음 청크 생성: {next_chunk.chunk_id} (인덱스: {next_chunk_index})")

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

        # 🔄 ChunkResult 기반 연속성 (완료된 청크들에서 마지막 시간 정보 추출)
        if state.completed_chunks:
            last_chunk = state.completed_chunks[-1]
            if hasattr(last_chunk, 'get_effective_end_time'):
                last_effective_time = last_chunk.get_effective_end_time()
                if last_effective_time:
                    try:
                        # 다음 청크 시작 = 이전 청크 유효 끝시간 - 1틱 (연속성 보장)
                        next_chunk_start = TimeUtils.get_time_by_ticks(last_effective_time, state.timeframe, -1)
                        params["to"] = next_chunk_start

                        time_source = last_chunk.get_time_source() if hasattr(last_chunk, 'get_time_source') else "unknown"
                        logger.debug(f"ChunkResult 연속성: {last_effective_time} (출처: {time_source}) → {next_chunk_start}")

                    except Exception as e:
                        logger.warning(f"ChunkResult 연속성 계산 실패: {e}")

        return params

    # =========================================================================
    # 파라미터 생성 및 유틸리티
    # =========================================================================

    def _calculate_total_count_by_type(
        self,
        request_info: RequestInfo
    ) -> int:
        """사전 계산된 예상 캔들 개수 반환 (항상 존재 보장)"""
        return request_info.get_expected_count()

    def _create_first_chunk_params_by_type(
        self,
        request_info: RequestInfo
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

    # =========================================================================
    # 최종 결과 조회
    # =========================================================================

    async def _get_final_result(
        self,
        collection_state: CollectionState,
        symbol: str,
        timeframe: str,
        count: Optional[int],
        to: Optional[datetime],
        end: Optional[datetime]
    ) -> List[CandleData]:
        """최종 결과 조회 (CandleData 변환은 여기서만 수행)"""
        try:
            # 업비트 API 특성 고려한 실제 수집 범위 계산
            aligned_to = collection_state.request_info.get_aligned_to_time()
            expected_count = collection_state.request_info.get_expected_count()
            request_type = collection_state.request_info.get_request_type()

            # 실제 수집 범위 계산
            if request_type in [RequestType.COUNT_ONLY, RequestType.END_ONLY]:
                # COUNT_ONLY/END_ONLY: 첫 번째 청크의 실제 API 응답 시작점 사용
                if collection_state.completed_chunks and hasattr(collection_state.completed_chunks[0], 'api_response_start'):
                    actual_start = collection_state.completed_chunks[0].api_response_start
                else:
                    actual_start = TimeUtils.get_time_by_ticks(aligned_to, timeframe, -1)
            else:
                # TO_COUNT/TO_END: aligned_to에서 1틱 과거로 이동
                actual_start = TimeUtils.get_time_by_ticks(aligned_to, timeframe, -1)

            # Count 기반 종료점 재계산
            actual_end = TimeUtils.get_time_by_ticks(actual_start, timeframe, -(expected_count - 1))

            logger.debug(f"🔍 실제 수집 범위: {aligned_to} → {actual_start} ~ {actual_end} ({expected_count}개)")

            return await self.repository.get_candles_by_range(
                symbol, timeframe, actual_start, actual_end
            )

        except Exception as e:
            logger.error(f"최종 결과 조회 실패: {e}")
            return []
