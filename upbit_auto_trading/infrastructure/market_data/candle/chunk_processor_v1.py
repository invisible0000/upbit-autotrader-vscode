"""
ChunkProcessor v1.1 - 캔들 청크 처리 전문 클래스 (Legacy 로직 통합)

Created: 2025-09-23
Updated: 첫 청크 구분, 안전한 범위 계산, 빈 캔들 처리, 업비트 데이터 끝 감지 추가
Purpose: CandleDataProvider에서 청크 처리 로직을 분리하여 단일 책임 원칙 준수
Features: 4단계 파이프라인 처리, 조기 종료 최적화, 성능 추적, Legacy 호환성
Architecture: DDD Infrastructure 계층, 의존성 주입 패턴

책임:
- 개별 청크의 4단계 파이프라인 처리
- API 호출 최적화 및 겹침 분석
- 빈 캔들 처리 및 데이터 정규화 (첫 청크 처리 포함)
- 성능 모니터링 및 에러 처리
- 업비트 데이터 끝 감지 및 CollectionState 업데이트
"""

import time
from datetime import datetime, timezone
from typing import Optional, Dict, Any, Callable, List
from contextlib import contextmanager

from upbit_auto_trading.infrastructure.logging import create_component_logger
from upbit_auto_trading.infrastructure.market_data.candle.time_utils import TimeUtils
from upbit_auto_trading.infrastructure.market_data.candle.overlap_analyzer import OverlapAnalyzer
from upbit_auto_trading.infrastructure.external_apis.upbit.upbit_public_client import UpbitPublicClient
from upbit_auto_trading.domain.repositories.candle_repository_interface import CandleRepositoryInterface
from upbit_auto_trading.infrastructure.market_data.candle.models import (
    ChunkInfo,
    CollectionState,
    ExecutionPlan,
    OverlapAnalysis,
    ValidationResult,
    ApiResponse,
    ProcessedData,
    StorageResult,
    ChunkResult,

    create_skip_result,
    create_early_exit_result,
    create_success_result,
    create_error_result,
)


class PerformanceTracker:
    """청크 처리 성능 추적 클래스"""

    def __init__(self):
        self.metrics = {}
        self.logger = create_component_logger("PerformanceTracker")

    @contextmanager
    def measure_chunk_execution(self, chunk_id: str):
        """전체 청크 실행 시간 측정"""
        start_time = time.time()
        try:
            yield
        finally:
            execution_time = time.time() - start_time
            self.metrics[f"{chunk_id}_total"] = execution_time
            self.logger.info(f"⏱️ 청크 실행 시간: {chunk_id} = {execution_time:.3f}초")

    @contextmanager
    def measure_phase(self, phase_name: str):
        """개별 Phase 시간 측정"""
        start_time = time.time()
        try:
            yield
        finally:
            phase_time = time.time() - start_time
            self.metrics[f"phase_{phase_name}"] = phase_time
            self.logger.debug(f"📊 Phase 시간: {phase_name} = {phase_time:.3f}초")

    def get_performance_report(self) -> Dict[str, float]:
        """성능 리포트 생성"""
        try:
            import numpy as np
            np_mean = np.mean
        except ImportError:
            # numpy가 없으면 내장 함수 사용
            def np_mean(arr):
                return sum(arr) / len(arr) if arr else 0.0

        return {
            'avg_total_time': np_mean([v for k, v in self.metrics.items() if '_total' in k]) if self.metrics else 0.0,
            'avg_preparation_time': np_mean([
                v for k, v in self.metrics.items() if 'phase_preparation' in k
            ]) if self.metrics else 0.0,
            'avg_api_fetch_time': np_mean([
                v for k, v in self.metrics.items() if 'phase_api_fetch' in k
            ]) if self.metrics else 0.0,
            'avg_processing_time': np_mean([
                v for k, v in self.metrics.items() if 'phase_data_processing' in k
            ]) if self.metrics else 0.0,
            'avg_storage_time': np_mean([
                v for k, v in self.metrics.items() if 'phase_data_storage' in k
            ]) if self.metrics else 0.0,
        }


class ChunkProcessor:
    """
    캔들 청크 처리 전문 클래스

    책임:
    - 개별 청크의 4단계 파이프라인 처리
    - API 호출 최적화 및 겹침 분석
    - 빈 캔들 처리 및 데이터 정규화 (첫 청크 처리 포함)
    - 성능 모니터링 및 에러 처리
    - 업비트 데이터 끝 감지 및 상태 업데이트

    4단계 파이프라인:
    1. Phase 1: 준비 및 분석 단계 (겹침 분석, 실행 계획 수립)
    2. Phase 2: 데이터 수집 단계 (API 호출 최적화)
    3. Phase 3: 데이터 처리 단계 (빈 캔들 처리, 정규화)
    4. Phase 4: 데이터 저장 단계 (Repository를 통한 영구 저장)
    """

    def __init__(self,
                 overlap_analyzer: OverlapAnalyzer,
                 upbit_client: UpbitPublicClient,
                 repository: CandleRepositoryInterface,
                 empty_candle_detector_factory: Callable[[str, str], Any],
                 enable_empty_candle_processing: bool = True,
                 performance_tracker: Optional[PerformanceTracker] = None):
        """ChunkProcessor 초기화

        Args:
            overlap_analyzer: 데이터 겹침 분석을 위한 분석기
            upbit_client: 업비트 API 클라이언트
            repository: 캔들 데이터 저장소 인터페이스
            empty_candle_detector_factory: 빈 캔들 감지기 팩토리 함수
            enable_empty_candle_processing: 빈 캔들 처리 활성화 여부
            performance_tracker: 성능 추적기 (선택적)
        """
        # 외부 의존성 주입 (테스트 용이성)
        self.overlap_analyzer = overlap_analyzer
        self.upbit_client = upbit_client
        self.repository = repository
        self.empty_candle_detector_factory = empty_candle_detector_factory
        self.enable_empty_candle_processing = enable_empty_candle_processing

        # 성능 추적 (선택적)
        self.performance_tracker = performance_tracker or PerformanceTracker()

        # 로깅
        self.logger = create_component_logger("ChunkProcessor")

        # 내부 상태
        self._cache = {}  # 계산 결과 캐싱용

        empty_status = '활성화' if enable_empty_candle_processing else '비활성화'
        self.logger.info(f"ChunkProcessor v1.1 초기화 완료 (Legacy 로직 통합, 빈 캔들 처리: {empty_status})")

    async def execute_chunk_pipeline(self,
                                     chunk_info: ChunkInfo,
                                     collection_state: CollectionState) -> ChunkResult:
        """
        🚀 청크 처리 메인 파이프라인 - 전체 흐름이 한눈에 보임

        Args:
            chunk_info: 처리할 청크 정보
            collection_state: 전체 수집 상태

        Returns:
            ChunkResult: 처리 결과 (성공/실패, 저장 개수, 메타데이터)
        """
        chunk_id = chunk_info.chunk_id
        self.logger.info(f"🚀 청크 파이프라인 시작: {chunk_id}")

        # 🆕 첫 청크 판단 로직 추가
        is_first_chunk = len(collection_state.completed_chunks) == 0

        # 🆕 안전한 참조 범위 계산 (첫 청크 ~ 현재 청크)
        safe_range_start = None
        safe_range_end = None
        if collection_state.completed_chunks and chunk_info.end:
            # 첫 번째 완료된 청크의 시작점
            safe_range_start = collection_state.completed_chunks[0].to
            # 현재 청크의 끝점
            safe_range_end = chunk_info.end
            self.logger.debug(f"🔒 안전 범위 계산: [{safe_range_start}, {safe_range_end}]")

        # 처리 시간 측정을 위한 시작 시간 기록
        start_time = time.time()

        with self.performance_tracker.measure_chunk_execution(chunk_id):
            try:
                # Phase 1: 📋 준비 및 분석 단계
                execution_plan = await self._phase1_prepare_execution(chunk_info)

                # 조기 종료: 완전 겹침인 경우 API 호출 생략
                if execution_plan.should_skip_api_call:
                    return create_skip_result(execution_plan, chunk_info)

                # Phase 2: 🌐 데이터 수집 단계
                api_response = await self._phase2_fetch_data(chunk_info, execution_plan)

                # 🆕 업비트 데이터 끝 도달 확인 (CollectionState 업데이트)
                if api_response.has_upbit_data_end:
                    collection_state.reached_upbit_data_end = True
                    self.logger.warning(f"📊 업비트 데이터 끝 도달: {chunk_info.symbol} {chunk_info.timeframe}")

                # 조기 종료: 빈 응답 또는 업비트 데이터 끝
                if api_response.requires_early_exit:
                    return create_early_exit_result(api_response, chunk_info)

                # Phase 3: ⚙️ 데이터 처리 단계
                processed_data = await self._phase3_process_data(
                    api_response, chunk_info, is_first_chunk, safe_range_start, safe_range_end
                )

                # Phase 4: 💾 데이터 저장 단계
                storage_result = await self._phase4_persist_data(processed_data, chunk_info)

                # ✅ 성공 결과 생성 (처리 시간 계산 포함)
                processing_time_ms = (time.time() - start_time) * 1000
                return create_success_result(storage_result, chunk_info.chunk_id, processing_time_ms)

            except Exception as e:
                self.logger.error(f"❌ 청크 파이프라인 실패: {chunk_id}, 오류: {e}")
                return create_error_result(e, chunk_info)

    # =========================================================================
    # Phase 1: 준비 및 분석 단계
    # =========================================================================

    async def _phase1_prepare_execution(self, chunk_info: ChunkInfo) -> ExecutionPlan:
        """
        📋 청크 실행 준비 및 겹침 분석

        책임:
        - 겹침 상태 분석
        - API 호출 전략 결정
        - 실행 계획 수립
        """
        with self.performance_tracker.measure_phase('preparation'):
            self.logger.debug(f"📋 실행 준비: {chunk_info.chunk_id}")

            # 겹침 분석 수행
            overlap_analysis = await self._analyze_data_overlap(chunk_info)

            # 실행 계획 수립
            execution_plan = self._build_execution_plan(chunk_info, overlap_analysis)

            # ChunkInfo 메타데이터 업데이트
            if overlap_analysis and overlap_analysis.overlap_result:
                chunk_info.set_overlap_info(overlap_analysis.overlap_result)

            self.logger.debug(f"📋 실행 준비 완료: {execution_plan.strategy}")
            return execution_plan

    async def _analyze_data_overlap(self, chunk_info: ChunkInfo) -> Optional[OverlapAnalysis]:
        """
        🔍 데이터 겹침 상태 정밀 분석

        현재 _analyze_chunk_overlap() 메서드를 개선:
        - 더 명확한 메서드명
        - 분석 결과를 구조화된 객체로 반환
        """
        if not chunk_info.to or not chunk_info.end:
            self.logger.debug("겹침 분석 건너뛰기: to 또는 end 정보 없음")
            return None

        try:
            from upbit_auto_trading.infrastructure.market_data.candle.models import OverlapRequest

            # 청크 시간 범위 계산
            chunk_start = chunk_info.to
            chunk_end = self._calculate_chunk_end_time(chunk_info)

            self.logger.debug(f"🔍 겹침 분석 범위: {chunk_start} ~ {chunk_end}")

            # 예상 캔들 개수 계산
            expected_count = self._calculate_api_count(chunk_start, chunk_end, chunk_info.timeframe)

            # OverlapAnalyzer를 통한 겹침 분석
            overlap_request = OverlapRequest(
                symbol=chunk_info.symbol,
                timeframe=chunk_info.timeframe,
                target_start=chunk_start,
                target_end=chunk_end,
                target_count=expected_count
            )

            overlap_result = await self.overlap_analyzer.analyze_overlap(overlap_request)

            return OverlapAnalysis(
                overlap_result=overlap_result,
                analysis_time=datetime.now(timezone.utc),
                optimization_applied=True,
                recommendations=[f"분석 전략: {overlap_result.status.value}"]
            )

        except Exception as e:
            self.logger.warning(f"겹침 분석 실패: {e}")
            return None

    def _build_execution_plan(self, chunk_info: ChunkInfo,
                              overlap_analysis: Optional[OverlapAnalysis]) -> ExecutionPlan:
        """겹침 분석 결과를 바탕으로 실행 계획 수립"""

        # 기본 API 파라미터
        base_params = {
            'count': chunk_info.count,
            'to': chunk_info.to
        }

        # 겹침 분석이 없거나 실패한 경우 - 전체 가져오기
        if not overlap_analysis or not overlap_analysis.overlap_result:
            return ExecutionPlan(
                strategy='full_fetch',
                should_skip_api_call=False,
                optimized_api_params=base_params,
                expected_data_range=(chunk_info.to, chunk_info.end) if chunk_info.end else (chunk_info.to, chunk_info.to)
            )

        # 겹침 분석 결과에 따른 전략 결정
        from upbit_auto_trading.infrastructure.market_data.candle.models import OverlapStatus

        overlap_result = overlap_analysis.overlap_result
        status = overlap_result.status

        if status == OverlapStatus.COMPLETE_OVERLAP:
            # 완전 겹침: API 호출 생략
            return ExecutionPlan(
                strategy='skip_complete_overlap',
                should_skip_api_call=True,
                optimized_api_params={},
                expected_data_range=(chunk_info.to, chunk_info.end) if chunk_info.end else (chunk_info.to, chunk_info.to)
            )

        elif status in [OverlapStatus.PARTIAL_START, OverlapStatus.PARTIAL_MIDDLE_CONTINUOUS]:
            # 부분 겹침: 최적화된 API 호출
            if hasattr(overlap_result, 'api_start') and hasattr(overlap_result, 'api_end'):
                api_count = self._calculate_api_count(
                    overlap_result.api_start, overlap_result.api_end, chunk_info.timeframe
                )
                optimized_params = {
                    'count': api_count,
                    'to': overlap_result.api_start
                }
                return ExecutionPlan(
                    strategy='partial_fetch',
                    should_skip_api_call=False,
                    optimized_api_params=optimized_params,
                    expected_data_range=(overlap_result.api_start, overlap_result.api_end)
                )

        # 겹침 없음 또는 기타 경우: 전체 가져오기
        return ExecutionPlan(
            strategy='full_fetch',
            should_skip_api_call=False,
            optimized_api_params=base_params,
            expected_data_range=(chunk_info.to, chunk_info.end) if chunk_info.end else (chunk_info.to, chunk_info.to)
        )

    # =========================================================================
    # Phase 2: 데이터 수집 단계
    # =========================================================================

    async def _phase2_fetch_data(self,
                                 chunk_info: ChunkInfo,
                                 execution_plan: ExecutionPlan) -> ApiResponse:
        """
        🌐 최적화된 API 데이터 수집

        개선사항:
        - 겹침 분석 결과 기반 최적화된 API 호출
        - 응답 데이터 즉시 검증
        - 업비트 데이터 끝 감지
        """
        with self.performance_tracker.measure_phase('api_fetch'):
            self.logger.debug(f"🌐 API 데이터 수집: {chunk_info.chunk_id}")

            # 최적화된 API 파라미터 사용
            api_params = execution_plan.get_optimized_api_params()

            # API 호출 (기존 _fetch_chunk_from_api 로직 활용)
            raw_data = await self._call_upbit_api(chunk_info, api_params)

            # 응답 즉시 검증
            validation_result = self._validate_api_response(raw_data, chunk_info)

            # ChunkInfo에 API 응답 정보 저장
            chunk_info.set_api_response_info(raw_data)

            # 업비트 데이터 끝 감지 (요청한 개수보다 적게 받은 경우)
            expected_count = api_params.get('count', chunk_info.count)
            has_upbit_data_end = len(raw_data) < expected_count

            # 🆕 업비트 데이터 끝 도달 로깅
            if has_upbit_data_end:
                self.logger.warning(f"📊 업비트 데이터 끝 도달: {chunk_info.symbol} {chunk_info.timeframe} - "
                                    f"요청={expected_count}개, 응답={len(raw_data)}개")

            # 구조화된 응답 객체 생성
            return ApiResponse(
                raw_data=raw_data,
                validation_result=validation_result,
                has_upbit_data_end=has_upbit_data_end,
                requires_early_exit=validation_result.has_critical_errors or has_upbit_data_end,
                response_metadata={
                    'expected_count': expected_count,
                    'actual_count': len(raw_data),
                    'api_params': api_params
                }
            )

    async def _call_upbit_api(self, chunk_info: ChunkInfo, api_params: Dict[str, Any]) -> List[Dict]:
        """
        📡 업비트 API 호출 (기존 로직 유지)

        현재 _fetch_chunk_from_api() 메서드를 분리:
        - 더 명확한 메서드명
        - API 호출 로직만 집중
        """
        self.logger.debug(f"API 청크 요청: {chunk_info.chunk_id}")

        # API 파라미터 추출
        api_count = api_params.get('count', chunk_info.count)
        api_to = api_params.get('to', chunk_info.to)

        if chunk_info.has_overlap_info() and chunk_info.needs_partial_api_call():
            self.logger.debug(f"부분 API 호출: count={api_count}, to={api_to} (overlap 최적화)")
        else:
            self.logger.debug(f"전체 API 호출: count={api_count}, to={api_to}")

        try:
            # 기존 _fetch_chunk_from_api의 타임프레임별 분기 로직 그대로 사용
            if chunk_info.timeframe == '1s':
                # 초봉 API 지출점 보정
                to_param = None
                if api_to:
                    timeframe_delta = TimeUtils.get_timeframe_delta(chunk_info.timeframe)
                    fetch_time = api_to + timeframe_delta
                    to_param = fetch_time.strftime("%Y-%m-%dT%H:%M:%S")

                candles = await self.upbit_client.get_candles_seconds(
                    market=chunk_info.symbol,
                    count=api_count,
                    to=to_param
                )

            elif chunk_info.timeframe.endswith('m'):
                # 분봉
                unit = int(chunk_info.timeframe[:-1])
                if unit not in [1, 3, 5, 10, 15, 30, 60, 240]:
                    raise ValueError(f"지원하지 않는 분봉 단위: {unit}")

                # 분봉 API 지출점 보정
                to_param = None
                if api_to:
                    timeframe_delta = TimeUtils.get_timeframe_delta(chunk_info.timeframe)
                    fetch_time = api_to + timeframe_delta
                    to_param = fetch_time.strftime("%Y-%m-%dT%H:%M:%S")

                candles = await self.upbit_client.get_candles_minutes(
                    unit=unit,
                    market=chunk_info.symbol,
                    count=api_count,
                    to=to_param
                )

            elif chunk_info.timeframe == '1d':
                # 일봉 API 지출점 보정
                to_param = None
                if api_to:
                    fetch_start_time = TimeUtils.get_time_by_ticks(api_to, chunk_info.timeframe, 1)
                    to_param = fetch_start_time.strftime("%Y-%m-%d")

                candles = await self.upbit_client.get_candles_days(
                    market=chunk_info.symbol,
                    count=api_count,
                    to=to_param
                )

            elif chunk_info.timeframe == '1w':
                # 주봉 API 지출점 보정
                to_param = None
                if api_to:
                    fetch_start_time = TimeUtils.get_time_by_ticks(api_to, chunk_info.timeframe, 1)
                    to_param = fetch_start_time.strftime("%Y-%m-%d")

                candles = await self.upbit_client.get_candles_weeks(
                    market=chunk_info.symbol,
                    count=api_count,
                    to=to_param
                )

            elif chunk_info.timeframe == '1M':
                # 월봉 API 지출점 보정
                to_param = None
                if api_to:
                    fetch_start_time = TimeUtils.get_time_by_ticks(api_to, chunk_info.timeframe, 1)
                    to_param = fetch_start_time.strftime("%Y-%m")

                candles = await self.upbit_client.get_candles_months(
                    market=chunk_info.symbol,
                    count=api_count,
                    to=to_param
                )

            elif chunk_info.timeframe == '1y':
                # 연봉 API 지출점 보정
                to_param = None
                if api_to:
                    fetch_start_time = TimeUtils.get_time_by_ticks(api_to, chunk_info.timeframe, 1)
                    to_param = fetch_start_time.strftime("%Y")

                candles = await self.upbit_client.get_candles_years(
                    market=chunk_info.symbol,
                    count=api_count,
                    to=to_param
                )

            else:
                raise ValueError(f"지원하지 않는 타임프레임: {chunk_info.timeframe}")

            # 개선: 최적화된 로깅 (overlap 정보 표시)
            overlap_info = f" (overlap: {chunk_info.overlap_status.value})" if chunk_info.has_overlap_info() else ""
            self.logger.info(f"API 청크 완료: {chunk_info.chunk_id}, 수집: {len(candles)}개{overlap_info}")

            return candles

        except Exception as e:
            self.logger.error(f"API 청크 실패: {chunk_info.chunk_id}, 오류: {e}")
            raise

    def _validate_api_response(self, raw_data: List[Dict], chunk_info: ChunkInfo) -> ValidationResult:
        """API 응답 데이터 즉시 검증"""
        validation_messages = []
        has_critical_errors = False

        try:
            # 기본 검증
            if not isinstance(raw_data, list):
                validation_messages.append("API 응답이 리스트가 아님")
                has_critical_errors = True

            # 빈 응답 체크 (경고 수준)
            if len(raw_data) == 0:
                validation_messages.append("빈 API 응답")

            # 캔들 데이터 구조 검증
            for i, candle in enumerate(raw_data[:5]):  # 처음 5개만 검증
                if not isinstance(candle, dict):
                    validation_messages.append(f"캔들 {i}가 딕셔너리가 아님")
                    has_critical_errors = True
                    break

                required_fields = ['candle_date_time_utc', 'opening_price', 'high_price', 'low_price', 'trade_price']
                for field in required_fields:
                    if field not in candle:
                        validation_messages.append(f"캔들 {i}에 필수 필드 {field} 누락")
                        has_critical_errors = True
                        break

        except Exception as e:
            validation_messages.append(f"검증 중 오류 발생: {e}")
            has_critical_errors = True

        return ValidationResult(
            is_valid=not has_critical_errors,
            has_critical_errors=has_critical_errors,
            validation_messages=validation_messages,
            validation_time=datetime.now(timezone.utc)
        )

    # =========================================================================
    # Phase 3: 데이터 처리 단계
    # =========================================================================

    async def _phase3_process_data(self,
                                   api_response: ApiResponse,
                                   chunk_info: ChunkInfo,
                                   is_first_chunk: bool,
                                   safe_range_start: Optional[datetime],
                                   safe_range_end: Optional[datetime]) -> ProcessedData:
        """
        ⚙️ 캔들 데이터 처리 및 정규화

        책임:
        - 빈 캔들 감지 및 채우기
        - 데이터 정규화 및 검증
        - 처리 메타데이터 생성
        """
        with self.performance_tracker.measure_phase('data_processing'):
            self.logger.debug(f"⚙️ 데이터 처리: {chunk_info.chunk_id}")

            # 🆕 첫 청크 정보와 안전 범위 사용
            self.logger.debug(f"첫 청크: {is_first_chunk}, 안전 범위: [{safe_range_start}, {safe_range_end}]")

            # 빈 캔들 처리 (첫 청크 정보 포함)
            filled_data = await self._detect_and_fill_gaps(
                api_response.raw_data, chunk_info, is_first_chunk=is_first_chunk,
                safe_range_start=safe_range_start, safe_range_end=safe_range_end
            )

            # 데이터 정규화
            normalized_data = self._normalize_candle_data(filled_data)

            # 최종 검증
            validation_result = self._validate_processed_data(normalized_data, chunk_info)

            # ChunkInfo에 최종 캔들 정보 저장
            chunk_info.set_final_candle_info(normalized_data)

            return ProcessedData(
                candles=normalized_data,
                gap_filled_count=len(filled_data) - len(api_response.raw_data),
                processing_metadata=self._create_processing_metadata(chunk_info),
                validation_passed=validation_result.is_valid
            )

    # =========================================================================
    # Phase 4: 데이터 저장 단계
    # =========================================================================

    async def _phase4_persist_data(self,
                                   processed_data: ProcessedData,
                                   chunk_info: ChunkInfo) -> StorageResult:
        """
        💾 처리된 데이터 영구 저장

        책임:
        - Repository를 통한 데이터 저장
        - 저장 결과 검증
        - 저장 메타데이터 생성
        """
        with self.performance_tracker.measure_phase('data_storage'):
            self.logger.debug(f"💾 데이터 저장: {chunk_info.chunk_id}")

            # 저장 실행 (기존 로직 이주)
            saved_count = await self.repository.save_raw_api_data(
                chunk_info.symbol,
                chunk_info.timeframe,
                processed_data.candles
            )

            # 저장 결과 검증
            storage_validation = self._validate_storage_result(saved_count, processed_data)

            self.logger.info(f"💾 저장 완료: {saved_count}개 저장")

            return StorageResult(
                saved_count=saved_count,
                expected_count=len(processed_data.candles),
                storage_time=datetime.now(timezone.utc),
                validation_passed=storage_validation.is_valid,
                metadata=self._create_storage_metadata(chunk_info, saved_count)
            )

    # =========================================================================
    # 헬퍼 메서드들
    # =========================================================================

    async def _detect_and_fill_gaps(self,
                                    raw_candles: List[Dict],
                                    chunk_info: ChunkInfo,
                                    is_first_chunk: bool = False,
                                    safe_range_start: Optional[datetime] = None,
                                    safe_range_end: Optional[datetime] = None) -> List[Dict]:
        """
        🔍 빈 캔들 감지 및 채우기 (legacy 로직 완전 이주)

        Args:
            raw_candles: API 원시 응답 데이터
            chunk_info: 청크 정보
            is_first_chunk: 첫 번째 청크 여부 (api_start +1틱 추가 제어)
            safe_range_start: 안전한 참조 범위 시작
            safe_range_end: 안전한 참조 범위 끝

        Returns:
            처리된 캔들 데이터
        """
        # 빈 캔들 처리가 비활성화된 경우
        if not self.enable_empty_candle_processing:
            self.logger.debug("빈 캔들 처리 비활성화됨 → 원본 데이터 반환")
            return raw_candles

        self.logger.debug(f"빈 캔들 처리 시작: 첫청크={is_first_chunk}, api_start={api_start}, api_end={api_end}")

        try:
            detector = self.empty_candle_detector_factory(chunk_info.symbol, chunk_info.timeframe)

            # API 범위 정보 추출 (overlap 분석 결과에서)
            api_start = None
            api_end = None

            if chunk_info.has_overlap_info():
                overlap_result = getattr(chunk_info, 'overlap_result', None)
                if overlap_result and hasattr(overlap_result, 'api_start'):
                    api_start = overlap_result.api_start
                if overlap_result and hasattr(overlap_result, 'api_end'):
                    api_end = overlap_result.api_end

            # api_start/api_end가 없으면 청크 정보에서 추정
            if not api_start:
                api_start = chunk_info.to
            if not api_end:
                api_end = chunk_info.end

            # 빈 캔듡 처리 시작 로깅 (변수 정의 후)
            self.logger.debug(f"빈 캔듡 처리 시작: 첫청크={is_first_chunk}, api_start={api_start}, api_end={api_end}")

            # 🚀 Legacy 로직과 동일한 처리: 첫 청크는 무조건, 나머지는 조건부
            if is_first_chunk:
                # 첫 청크: api_end가 None이어도 무조건 빈 캔들 처리 수행
                self.logger.info(f"🚀 첫 청크 빈 캔들 처리 시작: api_start={api_start}, api_end={api_end} (api_end가 None이어도 처리)")

                processed_candles = detector.detect_and_fill_gaps(
                    raw_candles,
                    api_start=api_start,
                    api_end=api_end,
                    is_first_chunk=True  # 🚀 첫 청크 정보 전달 (api_start +1틱 추가 제어)
                )

                # 캔들 수 보정 로깅
                if len(processed_candles) != len(raw_candles):
                    empty_count = len(processed_candles) - len(raw_candles)
                    self.logger.info(f"빈 캔들 처리: 원본 {len(raw_candles)}개 + 빈 {empty_count}개 = 최종 {len(processed_candles)}개")

                return processed_candles

            else:
                # 나머지 청크: 조건부 빈 캔들 처리 (Legacy와 동일)
                should_process = self._should_process_empty_candles(raw_candles, api_end)
                self.logger.debug(f"🔍 나머지 청크 빈 캔들 처리 조건 확인: {should_process} (api_end={api_end})")

                if should_process:
                    self.logger.info(f"✅ 빈 캔들 처리 필요: 마지막캔들과 api_end 불일치")

                    processed_candles = detector.detect_and_fill_gaps(
                        raw_candles,
                        api_start=api_start,
                        api_end=api_end,
                        is_first_chunk=False
                    )

                    # 캔들 수 보정 로깅
                    if len(processed_candles) != len(raw_candles):
                        empty_count = len(processed_candles) - len(raw_candles)
                        self.logger.info(f"빈 캔들 처리: 원본 {len(raw_candles)}개 + 빈 {empty_count}개 = 최종 {len(processed_candles)}개")

                    return processed_candles
                else:
                    self.logger.info(f"❌ 빈 캔들 처리 건너뛰기: 마지막캔들과 api_end 일치 또는 조건 불충족 (api_end={api_end})")
                    return raw_candles

        except Exception as e:
            self.logger.warning(f"빈 캔들 처리 실패: {e}, 원본 데이터 반환")
            return raw_candles

    def _should_process_empty_candles(self, api_response: List[Dict[str, Any]], api_end: Optional[datetime]) -> bool:
        """API 응답의 마지막 캔들 시간과 api_end 비교하여 빈 캔들 처리 필요 여부 판단

        Args:
            api_response: 업비트 API 응답 리스트
            api_end: 예상되는 청크 종료 시간

        Returns:
            bool: 빈 캔들 처리가 필요하면 True, 아니면 False
        """
        if not api_response or not api_end:
            self.logger.debug("빈 캔들 처리 조건 확인: api_response 또는 api_end가 없음 → 처리 안 함")
            return False

        try:
            # 업비트 API는 내림차순이므로 마지막 요소가 가장 과거 캔들
            last_candle = api_response[-1]
            candle_time_utc = last_candle.get('candle_date_time_utc')

            if candle_time_utc and isinstance(candle_time_utc, str):
                # UTC 통일: TimeUtils를 통한 표준 정규화 (aware datetime 보장)
                parsed_time = datetime.fromisoformat(candle_time_utc)
                last_candle_time = TimeUtils.normalize_datetime_to_utc(parsed_time)

                # UTC 통일: 동일한 형식(aware datetime) 간 비교로 정확성 보장
                needs_processing = last_candle_time != api_end

                if needs_processing:
                    self.logger.debug(f"빈 캔들 처리 필요: 마지막캔들={last_candle_time} vs api_end={api_end}")
                else:
                    self.logger.debug(f"빈 캔들 처리 불필요: 마지막캔들={last_candle_time} == api_end={api_end}")

                return needs_processing

        except Exception as e:
            self.logger.warning(f"빈 캔들 처리 조건 확인 실패: {e} → 안전한 폴백으로 처리 안 함")
            return False

        self.logger.debug("빈 캔들 처리 조건 확인: 캔들 시간 파싱 실패 → 처리 안 함")
        return False

    def _normalize_candle_data(self, candles: List[Dict]) -> List[Dict]:
        """캔들 데이터 정규화"""
        try:
            normalized = []
            for candle in candles:
                # 기본 정규화: 필수 필드 확인 및 타입 변환
                normalized_candle = {
                    'candle_date_time_utc': candle.get('candle_date_time_utc'),
                    'candle_date_time_kst': candle.get('candle_date_time_kst'),
                    'opening_price': float(candle.get('opening_price', 0)),
                    'high_price': float(candle.get('high_price', 0)),
                    'low_price': float(candle.get('low_price', 0)),
                    'trade_price': float(candle.get('trade_price', 0)),
                    'timestamp': candle.get('timestamp', 0),
                    'candle_acc_trade_price': float(candle.get('candle_acc_trade_price', 0)),
                    'candle_acc_trade_volume': float(candle.get('candle_acc_trade_volume', 0)),
                    'prev_closing_price': (float(candle.get('prev_closing_price', 0))
                                           if candle.get('prev_closing_price') else None),
                    'change_price': float(candle.get('change_price', 0)) if candle.get('change_price') else None,
                    'change_rate': float(candle.get('change_rate', 0)) if candle.get('change_rate') else None,
                }

                # 추가 필드들도 그대로 유지 (빈 캔들 관련 등)
                for key, value in candle.items():
                    if key not in normalized_candle:
                        normalized_candle[key] = value

                normalized.append(normalized_candle)

            self.logger.debug(f"데이터 정규화 완료: {len(normalized)}개 캔들")
            return normalized

        except Exception as e:
            self.logger.error(f"데이터 정규화 실패: {e}")
            return candles  # 실패 시 원본 반환

    def _validate_processed_data(self, candles: List[Dict], chunk_info: ChunkInfo) -> ValidationResult:
        """처리된 데이터 최종 검증"""
        validation_messages = []
        has_critical_errors = False

        try:
            # 기본 데이터 존재 확인
            if not candles:
                validation_messages.append("처리된 캔들 데이터가 비어있음")
                has_critical_errors = True

            # 데이터 구조 검증
            for i, candle in enumerate(candles[:3]):  # 처음 3개만 검증
                if not isinstance(candle, dict):
                    validation_messages.append(f"처리된 캔들 {i}가 딕셔너리가 아님")
                    has_critical_errors = True
                    break

                # 가격 데이터 검증
                price_fields = ['opening_price', 'high_price', 'low_price', 'trade_price']
                for field in price_fields:
                    value = candle.get(field)
                    if value is None or (isinstance(value, (int, float)) and value < 0):
                        validation_messages.append(f"캔들 {i}의 {field} 값이 유효하지 않음: {value}")
                        # 가격이 음수인 것은 경고 수준 (빈 캔들일 수 있음)

        except Exception as e:
            validation_messages.append(f"처리된 데이터 검증 중 오류: {e}")
            has_critical_errors = True

        return ValidationResult(
            is_valid=not has_critical_errors,
            has_critical_errors=has_critical_errors,
            validation_messages=validation_messages,
            validation_time=datetime.now(timezone.utc)
        )

    def _validate_storage_result(self, saved_count: int, processed_data: ProcessedData) -> ValidationResult:
        """저장 결과 검증"""
        validation_messages = []
        has_critical_errors = False

        try:
            expected_count = len(processed_data.candles)

            if saved_count != expected_count:
                validation_messages.append(f"저장 개수 불일치: 예상={expected_count}, 실제={saved_count}")
                # 저장 개수가 다른 것은 중대 오류로 처리
                has_critical_errors = True

            if saved_count < 0:
                validation_messages.append(f"잘못된 저장 개수: {saved_count}")
                has_critical_errors = True

        except Exception as e:
            validation_messages.append(f"저장 결과 검증 중 오류: {e}")
            has_critical_errors = True

        return ValidationResult(
            is_valid=not has_critical_errors,
            has_critical_errors=has_critical_errors,
            validation_messages=validation_messages,
            validation_time=datetime.now(timezone.utc)
        )

    def _create_processing_metadata(self, chunk_info: ChunkInfo) -> Dict[str, Any]:
        """처리 메타데이터 생성"""
        return {
            'processed_at': datetime.now(timezone.utc),
            'chunk_id': chunk_info.chunk_id,
            'symbol': chunk_info.symbol,
            'timeframe': chunk_info.timeframe,
            'processor_version': 'v1.1',
            'has_overlap_optimization': chunk_info.has_overlap_info(),
            'overlap_strategy': getattr(chunk_info, 'overlap_status', None)
        }

    def _create_storage_metadata(self, chunk_info: ChunkInfo, saved_count: int) -> Dict[str, Any]:
        """저장 메타데이터 생성"""
        return {
            'storage_method': 'repository',
            'saved_at': datetime.now(timezone.utc),
            'chunk_id': chunk_info.chunk_id,
            'saved_count': saved_count,
            'symbol': chunk_info.symbol,
            'timeframe': chunk_info.timeframe,
            'processor_version': 'v1.1'
        }

    def _calculate_chunk_end_time(self, chunk_info: ChunkInfo) -> datetime:
        """청크 요청의 예상 종료 시점 계산"""
        ticks = -(chunk_info.count - 1)
        end_time = TimeUtils.get_time_by_ticks(chunk_info.to, chunk_info.timeframe, ticks)

        self.logger.debug(f"🔍 청크 경계 계산: to={chunk_info.to}, count={chunk_info.count}, "
                          f"ticks={ticks}, calculated_end={end_time}")

        return end_time

    def _calculate_api_count(self, start_time: datetime, end_time: datetime, timeframe: str) -> int:
        """API 요청에 필요한 캔들 개수 계산"""
        return TimeUtils.calculate_expected_count(start_time, end_time, timeframe)

    def _invalidate_cache(self):
        """필요시 캐시 무효화"""
        self._cache.clear()
        self.logger.debug("캐시 무효화 완료")

    def get_performance_summary(self) -> Dict[str, Any]:
        """성능 요약 정보 반환"""
        return self.performance_tracker.get_performance_report()
