"""
📋 ChunkProcessor v3.0 - candle_business_models.py 기반 단순화 버전
Created: 2025-09-23
Purpose: "소스의 원천" 원칙에 따른 단순화된 청크 처리 엔진
Architecture: RequestInfo + List[ChunkInfo] = 완전한 비즈니스 로직

핵심 설계 변경:
1. 상태 관리 제거: InternalCollectionState, CollectionProgress 등 제거
2. 단일 소스 원칙: candle_business_models.py의 4개 핵심 모델만 사용
3. 순수 청크 처리: ChunkProcessor는 개별 청크 처리만 담당
4. 모니터링 분리: 복잡한 상태 추적을 별도 계층으로 분리

주요 변경사항:
- execute_full_collection() → process_collection() (단순화)
- InternalCollectionState 제거 → List[ChunkInfo] 직접 사용
- 복잡한 완료 판단 → should_complete_collection() 함수 사용
- 상태 동기화 로직 제거 → ChunkInfo에서 직접 상태 관리

기대 효과:
- 코드 복잡도 50% 이상 감소
- 디버깅 용이성 향상 (ChunkInfo JSON 로그)
- 확장성 향상 (모니터링 요구사항 변경 시 핵심 로직 영향 없음)
"""

import time
import json
from datetime import datetime
from typing import Optional, Dict, Any, Callable, List
# Infrastructure 로깅
from upbit_auto_trading.infrastructure.logging import create_component_logger
# 핵심 비즈니스 모델 (candle_business_models.py)
from upbit_auto_trading.infrastructure.market_data.candle.models.candle_business_models import (
    RequestInfo,
    CollectionPlan,
    CollectionResult,
    ChunkInfo,
    OverlapRequest,
    OverlapResult,
    RequestType,
    should_complete_collection,
    create_collection_plan
)
# 의존성 (Infrastructure 계층)
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
from upbit_auto_trading.infrastructure.market_data.candle.time_utils import TimeUtils

# 진행 상황 콜백 타입
ProgressCallback = Callable[[int, int], None]  # (completed_chunks, total_chunks)
logger = create_component_logger("ChunkProcessor")


class ChunkProcessor:
    """
    ChunkProcessor v3.0 - 단순화된 청크 처리 엔진
    핵심 원칙:
    1. 단일 소스: candle_business_models.py의 4개 핵심 모델만 사용
    2. 상태 관리 제거: 복잡한 CollectionState, InternalCollectionState 제거
    3. 순수 처리: RequestInfo + List[ChunkInfo] = 완전한 비즈니스 로직
    4. 모니터링 분리: 진행 상황은 별도 계층에서 ChunkInfo 기반 분석
    주요 인터페이스:
    - process_collection(): RequestInfo → List[ChunkInfo] (메인 API)
    - process_single_chunk(): 개별 청크 처리 (CandleDataProvider 연동용)
    """

    def __init__(
        self,
        repository: CandleRepositoryInterface,
        upbit_client: UpbitPublicClient,
        overlap_analyzer: OverlapAnalyzer,
        empty_candle_detector_factory: Callable[[str, str], EmptyCandleDetector],
        chunk_size: int = 200,
        enable_empty_candle_processing: bool = True,
        dry_run: bool = False
    ):
        """
        ChunkProcessor v3.0 초기화
        Args:
            repository: 캔들 데이터 저장소
            upbit_client: 업비트 API 클라이언트
            overlap_analyzer: 겹침 분석기
            empty_candle_detector_factory: 빈 캔들 감지기 팩토리
            chunk_size: 청크 크기 (기본 200, 업비트 제한)
            enable_empty_candle_processing: 빈 캔들 처리 활성화 여부
            dry_run: 건식 실행 (실제 저장하지 않음)
        """

        # 의존성 주입
        self.repository = repository
        self.upbit_client = upbit_client
        self.overlap_analyzer = overlap_analyzer
        self.empty_candle_detector_factory = empty_candle_detector_factory

        # 설정
        self.chunk_size = min(chunk_size, 200)  # 업비트 제한 준수
        self.enable_empty_candle_processing = enable_empty_candle_processing
        self.dry_run = dry_run

        # Legacy 호환 설정
        self.api_rate_limit_rps = 10  # 10 RPS 기준
        logger.info("ChunkProcessor v3.0 초기화 완료 (단순화 버전)")
        logger.info(f"청크 크기: {self.chunk_size}, "
                    f"빈 캔들 처리: {'활성화' if enable_empty_candle_processing else '비활성화'}, "
                    f"API Rate Limit: {self.api_rate_limit_rps} RPS, "
                    f"DRY-RUN: {'활성화' if dry_run else '비활성화'}")

    def _log_chunk_info_debug(
        self,
        chunk_info: ChunkInfo,
        status: str = "unknown"
    ) -> None:
        """ChunkInfo 상태를 JSON 형식으로 디버그 출력 - 모든 ChunkInfo 속성 포함"""
        if not chunk_info:
            return
        try:
            effective_end = chunk_info.get_effective_end_time()
            debug_data = {
                # === 청크 식별 정보 ===
                "chunk_id": chunk_info.chunk_id,
                "chunk_index": chunk_info.chunk_index,
                "symbol": chunk_info.symbol,
                "timeframe": chunk_info.timeframe,
                "status": status,
                "chunk_status": chunk_info.chunk_status.value,

                # === 청크 파라미터 ===
                "count": chunk_info.count,
                "to": chunk_info.to.isoformat() if chunk_info.to else None,
                "end": chunk_info.end.isoformat() if chunk_info.end else None,

                # === 겹침 분석 정보 ===
                "overlap_status": chunk_info.overlap_status.value if chunk_info.overlap_status else None,

                # === OverlapResult 통합 필드 (DB 기존 데이터) ===
                "db_start": chunk_info.db_start.isoformat() if chunk_info.db_start else None,
                "db_end": chunk_info.db_end.isoformat() if chunk_info.db_end else None,

                # === 요청 단계 (오버랩 분석 결과) ===
                "api_request_count": chunk_info.api_request_count,
                "api_request_start": (
                    chunk_info.api_request_start.isoformat()
                    if chunk_info.api_request_start else None
                ),
                "api_request_end": (
                    chunk_info.api_request_end.isoformat()
                    if chunk_info.api_request_end else None
                ),

                # === API 호출 캐시 파라미터 ===
                "api_fetch_count": chunk_info.api_fetch_count,
                "api_fetch_to": (
                    chunk_info.api_fetch_to.isoformat()
                    if chunk_info.api_fetch_to else None
                ),

                # === 응답 단계 (실제 API 응답) ===
                "api_response_count": chunk_info.api_response_count,
                "api_response_start": (
                    chunk_info.api_response_start.isoformat()
                    if chunk_info.api_response_start else None
                ),
                "api_response_end": (
                    chunk_info.api_response_end.isoformat()
                    if chunk_info.api_response_end else None
                ),

                # === 최종 처리 단계 (빈 캔들 처리 후) ===
                "final_candle_count": chunk_info.final_candle_count,
                "final_candle_start": (
                    chunk_info.final_candle_start.isoformat()
                    if chunk_info.final_candle_start else None
                ),
                "final_candle_end": (
                    chunk_info.final_candle_end.isoformat()
                    if chunk_info.final_candle_end else None
                ),

                # === 계산된 캔들 수 캐시 ===
                "effective_candle_count": chunk_info.effective_candle_count,
                "cumulative_candle_count": chunk_info.cumulative_candle_count,

                # === 처리 상태 정보 ===
                "created_at": (
                    chunk_info.created_at.isoformat()
                    if chunk_info.created_at else None
                ),
                "processing_started_at": (
                    chunk_info.processing_started_at.isoformat()
                    if chunk_info.processing_started_at else None
                ),
                "completed_at": (
                    chunk_info.completed_at.isoformat()
                    if chunk_info.completed_at else None
                ),
                "processing_duration_seconds": chunk_info.get_processing_duration(),

                # === 계산된/파생 정보 (편의 필드) ===
                "effective_end_time": (
                    effective_end.isoformat() if effective_end else None
                ),
                "time_source": chunk_info.get_time_source(),
                "processing_time_ms": (
                    chunk_info.get_processing_duration() * 1000
                    if chunk_info.get_processing_duration() else None
                ),
                "has_overlap_info": chunk_info.has_overlap_info(),
                "needs_api_call": chunk_info.needs_api_call(),
                "needs_partial_api_call": chunk_info.needs_partial_api_call(),
                "has_complete_time_info": chunk_info.has_complete_time_info(),
                "calculated_effective_candle_count": (
                    chunk_info.calculate_effective_candle_count()
                ),

                # === API 파라미터 (현재 계산값) ===
                "current_api_params": {
                    "count": chunk_info.get_api_params()[0],
                    "to": (
                        chunk_info.get_api_params()[1].isoformat()
                        if chunk_info.get_api_params()[1] else None
                    )
                }
            }
            logger.debug(
                f"🔍 ChunkInfo Complete Dump: "
                f"{json.dumps(debug_data, ensure_ascii=False, indent=2)}"
            )
        except Exception as e:
            logger.warning(f"ChunkInfo 디버그 로그 생성 실패: {e}")

    def _log_request_info_debug(
        self,
        request_info: RequestInfo,
        status: str = "created"
    ) -> None:
        """RequestInfo 상태를 JSON 형식으로 디버그 출력 - 모든 RequestInfo 속성 포함"""
        if not request_info:
            return
        try:
            debug_data = {
                # === 기본 파라미터 (사용자 입력) ===
                "symbol": request_info.symbol,
                "timeframe": request_info.timeframe,
                "count": request_info.count,
                "to": request_info.to.isoformat() if request_info.to else None,
                "end": request_info.end.isoformat() if request_info.end else None,
                "request_at": (
                    request_info.request_at.isoformat()
                    if request_info.request_at else None
                ),

                # === 사전 계산된 필드들 (정규화/최적화됨) ===
                "aligned_to": (
                    request_info.aligned_to.isoformat()
                    if request_info.aligned_to else None
                ),
                "aligned_end": (
                    request_info.aligned_end.isoformat()
                    if request_info.aligned_end else None
                ),
                "expected_count": request_info.expected_count,

                # === 계산된/파생 정보 (분석용) ===
                "request_type": request_info.get_request_type().value,
                "should_align_time": request_info.should_align_time(),
                "needs_current_time_fallback": request_info.needs_current_time_fallback(),
                "should_skip_overlap_analysis_for_first_chunk": (
                    request_info.should_skip_overlap_analysis_for_first_chunk()
                ),

                # === 편의 접근자 결과 ===
                "aligned_to_time": (
                    request_info.get_aligned_to_time().isoformat()
                    if request_info.get_aligned_to_time() else None
                ),
                "aligned_end_time": (
                    request_info.get_aligned_end_time().isoformat()
                    if request_info.get_aligned_end_time() else None
                ),
                "expected_count_accessor": request_info.get_expected_count(),

                # === 로깅 문자열 ===
                "log_string": request_info.to_log_string(),
                "internal_log_string": request_info.to_internal_log_string(),

                # === 디버그 상태 ===
                "status": status
            }
            logger.debug(
                f"🔍 RequestInfo Complete Dump: "
                f"{json.dumps(debug_data, ensure_ascii=False, indent=2)}"
            )
        except Exception as e:
            logger.warning(f"RequestInfo 디버그 로그 생성 실패: {e}")

    # 🚀 메인 API - 단순화된 청크 처리
    async def process_collection(
        self,
        symbol: str,
        timeframe: str,
        count: Optional[int] = None,
        to: Optional[datetime] = None,
        end: Optional[datetime] = None,
        progress_callback: Optional[ProgressCallback] = None
    ) -> CollectionResult:
        """
        🚀 단순화된 캔들 수집 - candle_business_models.py 기반
        복잡한 상태 관리 클래스 제거하고 RequestInfo + List[ChunkInfo]만으로 동작.
        청크 처리의 자연스러운 흐름을 구현한 메인 API.
        Args:
            symbol: 거래 심볼 (예: 'KRW-BTC')
            timeframe: 타임프레임 (예: '1m', '5m', '1d')
            count: 수집할 캔들 개수
            to: 시작 시점 (최신 캔들 기준)
            end: 종료 시점 (과거 캔들 기준)
            progress_callback: 진행 상황 콜백 함수 (completed_chunks, total_chunks)
        Returns:
            CollectionResult: 수집 결과 요약 정보
        Raises:
            ValueError: 잘못된 파라미터
            Exception: 수집 과정 오류
        """
        start_time = time.time()

        logger.info(f"단순화된 캔들 수집 시작: {symbol} {timeframe}")
        if count:
            logger.info(f"개수: {count:,}개")
        if to:
            logger.info(f"시작: {to}")
        if end:
            logger.info(f"종료: {end}")
        if self.dry_run:
            logger.info("🔄 DRY-RUN 모드: 실제 저장하지 않음")
        try:
            # 1. RequestInfo 생성 (단일 소스)
            request_info = RequestInfo(
                symbol=symbol,
                timeframe=timeframe,
                count=count,
                to=TimeUtils.normalize_datetime_to_utc(to) if to else None,
                end=TimeUtils.normalize_datetime_to_utc(end) if end else None
            )

            # RequestInfo 디버그 출력 (한 번만)
            self._log_request_info_debug(request_info, "initialized")

            # 2. 수집 계획 수립 (단순화)
            plan = create_collection_plan(request_info, self.chunk_size, self.api_rate_limit_rps)
            logger.info(f"계획 수립 완료: {plan.total_count:,}개 캔들, {plan.estimated_chunks}청크, "
                        f"예상 소요시간: {plan.estimated_duration_seconds:.1f}초")

            # 3. 청크별 순차 처리 (단순한 리스트 관리)
            chunks: List[ChunkInfo] = []
            for chunk_index in range(plan.estimated_chunks):

                # 청크 생성 (이전 청크 결과 기반 연속성)
                chunk = self._create_chunk(chunk_index, request_info, plan, chunks)

                # 개별 청크 처리
                await self._process_single_chunk(chunk)

                previous_total = 0
                if chunks:
                    # 지금까지 처리된 청크들 중에서, 누적 캔들 수가 확정된 가장 최근 청크를 찾아서 그 누적 count를 사용
                    last_completed = next((c for c in reversed(chunks) if c.cumulative_candle_count is not None), None)
                    if last_completed:
                        previous_total = last_completed.cumulative_candle_count
                    else:
                        # 모두 없으면, 모든 완료된 청크들의 유효 캔들 수 합산
                        previous_total = sum(
                            c.calculate_effective_candle_count()
                            for c in chunks
                            if c.is_completed()
                        )

                chunk.update_cumulative_candle_count(previous_total)
                chunks.append(chunk)

                # 진행률 보고
                if progress_callback:
                    progress_callback(len(chunks), plan.estimated_chunks)

                # 완료 판단 (단순화)
                if should_complete_collection(request_info, chunks):
                    logger.info(f"수집 완료 조건 달성: {len(chunks)}개 청크 처리")
                    break

            # 4. 최종 결과 생성
            processing_time = time.time() - start_time
            logger.info(f"수집 완료: {len(chunks)}개 청크, 처리 시간 {processing_time:.2f}s")
            return self._create_success_result(chunks, request_info)

        except Exception as e:
            logger.error(f"단순화된 캔들 수집 실패: {e}")
            return self._create_error_result(e)

    # 🔗 CandleDataProvider 연동용 API (하위 호환성)
    async def process_single_chunk(self, chunk: ChunkInfo) -> ChunkInfo:
        """
        ### 단일 청크 처리 - CandleDataProvider 연동용
        - 기존 execute_single_chunk() 인터페이스 대체.
        - ChunkInfo를 받아서 처리하고 동일한 ChunkInfo를 반환 (상태 업데이트됨).
        Args:
            chunk: 처리할 청크 정보
        Returns:
            ChunkInfo: 처리 완료된 동일한 청크 (상태 업데이트됨)
        """
        logger.debug(f"단일 청크 처리: {chunk.chunk_id}")
        try:
            await self._process_single_chunk(chunk)
            return chunk

        except Exception as e:
            logger.error(f"단일 청크 처리 실패: {chunk.chunk_id}, 오류: {e}")
            chunk.mark_failed()
            raise

    # 🏗️ 핵심 처리 로직 - Legacy 로직 보존하되 단순화
    async def _process_single_chunk(self, chunk: ChunkInfo) -> None:
        """
        ### 개별 청크 처리 핵심 로직
        - 기존 _process_current_chunk() 로직을 단순화하여 이식.
        - 상태 관리는 ChunkInfo에서 직접 처리하고, 복잡한 중간 상태 제거.
        """
        logger.info(f"청크 처리 시작: {chunk.chunk_id}")
        chunk.mark_processing()
        try:
            # 1. 겹침 분석 (첫 청크는 조건부 건너뛰기)
            request_type = self._get_request_type_from_chunk(chunk)
            is_first_chunk = chunk.chunk_index == 0
            if not self._should_skip_overlap_analysis(is_first_chunk, request_type):
                overlap_result = await self._analyze_chunk_overlap(chunk)
                if overlap_result:
                    chunk.set_overlap_info(overlap_result)
                    self._log_chunk_info_debug(chunk, status="overlap_analyzed")

            # 2. 데이터 수집 및 처리
            if chunk.needs_api_call():
                # API 데이터 수집
                api_response = await self._fetch_api_data(chunk)
                chunk.set_api_response_info(api_response)
                # 빈 캔들 처리
                final_candles = await self._process_empty_candles(api_response, chunk, is_first_chunk)
                chunk.set_final_candle_info(final_candles)
                # 저장
                if not self.dry_run:
                    await self.repository.save_raw_api_data(
                        chunk.symbol, chunk.timeframe, final_candles
                    )
                else:
                    logger.info(f"🔄 DRY-RUN: 저장 시뮬레이션 {len(final_candles)}개")
            else:
                # COMPLETE_OVERLAP: API 호출 없이 완료
                logger.debug("완전 겹침 → API 호출 없이 완료")
                chunk.set_api_response_info([])
                chunk.set_final_candle_info([])
            # 3. 청크 완료 처리
            chunk.mark_completed()
            self._log_chunk_info_debug(chunk, status="completed")
            logger.info(f"청크 처리 완료: {chunk.chunk_id}")
        except Exception as e:
            chunk.mark_failed()
            logger.error(f"청크 처리 실패: {chunk.chunk_id}, 오류: {e}")
            raise

    def _create_chunk(
        self,
        chunk_index: int,
        request_info: RequestInfo,
        plan: CollectionPlan,
        completed_chunks: List[ChunkInfo]
    ) -> ChunkInfo:
        """
        ### 청크 생성 (이전 청크 기반 연속성)
        - 기존 _create_next_chunk() 로직을 단순화하여 이식.
        - InternalCollectionState 없이 List[ChunkInfo]만으로 연속성 관리.
        """
        # 청크 크기 계산 (남은 개수 고려)
        collected_count = 0
        if completed_chunks:
            last_completed = next((c for c in reversed(completed_chunks) if c.is_completed()), None)

            if last_completed:
                if last_completed.cumulative_candle_count is not None:
                    collected_count = last_completed.cumulative_candle_count

                else:
                    collected_count = sum(
                        c.calculate_effective_candle_count()
                        for c in completed_chunks
                        if c.is_completed()
                    )

        remaining_count = request_info.expected_count - collected_count
        chunk_count = min(remaining_count, self.chunk_size)

        if chunk_index == 0:
            # 첫 번째 청크: plan의 first_chunk_params 사용
            params = plan.first_chunk_params.copy()
            chunk_count = params.get("count", chunk_count)
            to_time = params.get("to", None)

            if isinstance(to_time, str):
                # 문자열이면 datetime으로 변환
                to_time = datetime.fromisoformat(to_time)

            # end 시간 계산
            end_time = None
            if to_time and chunk_count:
                end_time = TimeUtils.get_time_by_ticks(to_time, request_info.timeframe, -(chunk_count - 1))
        else:
            # 후속 청크: 이전 청크의 유효 끝 시간 기반 연속성
            last_chunk = completed_chunks[-1]
            last_effective_time = last_chunk.get_effective_end_time()

            if not last_effective_time:
                raise ValueError(f"이전 청크({last_chunk.chunk_id})에서 유효한 끝 시간을 가져올 수 없습니다")

            # 다음 청크 시작 = 이전 청크 끝 - 1틱 (연속성)
            to_time = TimeUtils.get_time_by_ticks(last_effective_time, request_info.timeframe, -1)
            end_time = TimeUtils.get_time_by_ticks(to_time, request_info.timeframe, -(chunk_count - 1))

        # ChunkInfo 생성
        chunk = ChunkInfo(
            chunk_id=f"{request_info.symbol}_{request_info.timeframe}_{chunk_index:05d}",
            chunk_index=chunk_index,
            symbol=request_info.symbol,
            timeframe=request_info.timeframe,
            count=chunk_count,
            to=to_time,
            end=end_time
        )

        self._log_chunk_info_debug(chunk, status="created")
        return chunk

    def _get_request_type_from_chunk(self, chunk: ChunkInfo) -> RequestType:
        """청크로부터 요청 타입 추정 (Legacy 호환)"""
        if chunk.chunk_index == 0:
            # 첫 청크: to 여부로 판단
            if chunk.to is None:
                return RequestType.COUNT_ONLY
            else:
                return RequestType.TO_COUNT  # 단순화 (TO_END는 별도 처리 필요)
        else:
            # 후속 청크: 항상 TO_COUNT 패턴
            return RequestType.TO_COUNT

    def _should_skip_overlap_analysis(self, is_first_chunk: bool, request_type: RequestType) -> bool:
        """겹침 분석 건너뛰기 여부 판단"""
        return is_first_chunk and request_type in [RequestType.COUNT_ONLY, RequestType.END_ONLY]

    async def _analyze_chunk_overlap(self, chunk: ChunkInfo) -> Optional[OverlapResult]:
        """
        청크 겹침 분석
        기존 _analyze_overlap() 로직 단순화.
        ChunkInfo에서 직접 정보 추출하여 OverlapAnalyzer 호출.
        """
        if not chunk.to or not chunk.end:
            logger.debug(f"겹침 분석 건너뜀: {chunk.chunk_id} (시간 정보 없음)")
            return None
        logger.debug(f"겹침 분석: {chunk.symbol} {chunk.timeframe}")
        try:
            # 예상 캔들 개수 계산
            expected_count = TimeUtils.calculate_expected_count(chunk.to, chunk.end, chunk.timeframe)
            overlap_request = OverlapRequest(
                symbol=chunk.symbol,
                timeframe=chunk.timeframe,
                target_start=chunk.to,
                target_end=chunk.end,
                target_count=expected_count
            )

            overlap_result = await self.overlap_analyzer.analyze_overlap(overlap_request)
            logger.debug(f"겹침 분석 결과: {overlap_result.status.value}")
            return overlap_result

        except Exception as e:
            logger.warning(f"겹침 분석 실패: {chunk.chunk_id}, 오류: {e}")
            return None

    async def _fetch_api_data(self, chunk: ChunkInfo) -> List[Dict[str, Any]]:
        """
        API 데이터 수집
        기존 _fetch_from_api() 로직을 ChunkInfo 기반으로 단순화.
        타임프레임별 API 분기는 그대로 유지하되 상태 관리 제거.
        """
        logger.debug(f"API 데이터 수집: {chunk.chunk_id}")
        api_count, api_to = chunk.get_api_params()

        if api_count <= 0:
            logger.debug(f"API 호출 건수 0으로 skip: {chunk.chunk_id}")
            return []

        if api_to is None:
            to_param = None
            logger.debug(f"청크 {chunk.chunk_id}는 COUNT_ONLY 또는 END_ONLY → to 파라미터 없음")
        else:
            try:
                # Upbit to exclusive 이므로 미래로 한 틱 보정
                fetch_time = TimeUtils.get_time_by_ticks(api_to, chunk.timeframe, 1)
                logger.debug(f"진출점 보정 {api_to} → {fetch_time}")
                to_param = fetch_time.strftime("%Y-%m-%dT%H:%M:%S")

            except Exception as exc:
                logger.error(f"to 파라미터 계산 실패: {chunk.chunk_id}, 오류: {exc}")
                raise
        try:
            if chunk.timeframe == '1s':
                candles = await self.upbit_client.get_candles_seconds(
                    market=chunk.symbol, count=api_count, to=to_param
                )

            elif chunk.timeframe.endswith('m'):

                unit = int(chunk.timeframe[:-1])

                if unit not in [1, 3, 5, 10, 15, 30, 60, 240]:
                    raise ValueError(f"지원하지 않는 분봉 단위: {unit}")

                candles = await self.upbit_client.get_candles_minutes(
                    unit=unit, market=chunk.symbol, count=api_count, to=to_param
                )

            elif chunk.timeframe == '1d':
                candles = await self.upbit_client.get_candles_days(
                    market=chunk.symbol, count=api_count, to=to_param
                )

            elif chunk.timeframe == '1w':
                candles = await self.upbit_client.get_candles_weeks(
                    market=chunk.symbol, count=api_count, to=to_param
                )

            elif chunk.timeframe == '1M':
                candles = await self.upbit_client.get_candles_months(
                    market=chunk.symbol, count=api_count, to=to_param
                )

            elif chunk.timeframe == '1y':
                candles = await self.upbit_client.get_candles_years(
                    market=chunk.symbol, count=api_count, to=to_param
                )

            else:
                raise ValueError(f"지원하지 않는 타임프레임: {chunk.timeframe}")

            overlap_info = f" (overlap: {chunk.overlap_status.value})" if chunk.overlap_status else ""
            logger.info(f"API 수집 완료: {chunk.chunk_id}, {len(candles)}개{overlap_info}, to={to_param}")
            return candles

        except Exception as e:
            logger.error(f"API 데이터 수집 실패: {chunk.chunk_id}, 오류: {e}")
            raise

    async def _process_empty_candles(
        self,
        api_candles: List[Dict[str, Any]],
        chunk: ChunkInfo,
        is_first_chunk: bool
    ) -> List[Dict[str, Any]]:
        """
        빈 캔들 처리
        기존 _process_empty_candles() 로직을 ChunkInfo 기반으로 단순화.
        복잡한 안전 범위 계산은 EmptyCandleDetector에 위임.
        """
        if not self.enable_empty_candle_processing:
            return api_candles
        logger.debug(f"빈 캔들 처리: {chunk.chunk_id}")
        try:
            # EmptyCandleDetector 생성
            detector = self.empty_candle_detector_factory(chunk.symbol, chunk.timeframe)

            # TEST01: 앞이 열린 빈 캔들 처리 강제 테스트
            # handle_front_open_empty_candle = chunk.to is not None  # to가 있으면 처리 허용
            handle_front_open_empty_candle = False  # 기본적으로 앞이 열린 빈 캔들 처리 안 함

            # 빈 캔들 감지 및 채우기
            processed_candles = detector.detect_and_fill_gaps(
                api_candles,
                api_start=chunk.api_request_start or chunk.to,
                api_end=chunk.api_request_end or chunk.end,
                handle_front_open_empty_candle=handle_front_open_empty_candle,  # TEST01: 앞이 열린 빈 캔들 처리 허용
                is_first_chunk=is_first_chunk
            )

            # 결과 로깅
            if len(processed_candles) != len(api_candles):
                empty_count = len(processed_candles) - len(api_candles)
                logger.info(f"빈 캔들 채움: {len(api_candles)}개 + {empty_count}개 = {len(processed_candles)}개")
            return processed_candles

        except Exception as e:
            logger.warning(f"빈 캔들 처리 실패: {chunk.chunk_id}, 오류: {e}")
            # 폴백: 원본 반환
            return api_candles

    def _create_success_result(
        self,
        chunks: List[ChunkInfo],
        request_info: RequestInfo
    ) -> CollectionResult:
        """성공 결과 생성"""
        request_start, request_end = self._calculate_request_bounds(request_info, chunks)

        return CollectionResult(
            success=True,
            request_start_time=request_start,
            request_end_time=request_end
        )

    def _create_error_result(
        self,
        error: Exception
    ) -> CollectionResult:
        """오류 결과 생성"""
        return CollectionResult(
            success=False,
            request_start_time=None,
            request_end_time=None,
            error=error
        )

    def _calculate_request_bounds(
        self,
        request_info: RequestInfo,
        chunks: List[ChunkInfo]
    ) -> tuple[Optional[datetime], Optional[datetime]]:
        """요청 타입에 따른 실제 수집 범위 계산"""
        if not chunks:
            return None, None

        request_type = request_info.get_request_type()
        timeframe = request_info.timeframe

        if request_type in (RequestType.COUNT_ONLY, RequestType.END_ONLY):
            first_chunk = chunks[0]
            start_time = first_chunk.api_response_start
            if start_time is None:
                aligned_to = request_info.get_aligned_to_time()
                if aligned_to:
                    start_time = TimeUtils.get_time_by_ticks(aligned_to, timeframe, -1)
            if start_time is None:
                return None, None

            expected = request_info.get_expected_count()

            if expected <= 1:
                end_time = start_time
            else:
                end_time = TimeUtils.get_time_by_ticks(start_time, timeframe, -(expected - 1))
            return start_time, end_time

        aligned_to = request_info.get_aligned_to_time()
        start_time = TimeUtils.get_time_by_ticks(aligned_to, timeframe, -1) if aligned_to else None
        end_time = request_info.get_aligned_end_time()

        return start_time, end_time
