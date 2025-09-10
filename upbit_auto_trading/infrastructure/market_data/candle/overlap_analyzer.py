"""
OverlapAnalyzer v5.0 - 5가지 상태 분류 분석 엔진
제안된 로직의 정확한 5개 상태 분류를 구현

핵심 목적: 겹침 상태를 5가지로 정확히 분류하여 API 요청 최적화
- NO_OVERLAP, COMPLETE_OVERLAP, PARTIAL_START, PARTIAL_MIDDLE_FRAGMENT, PARTIAL_MIDDLE_CONTINUOUS

설계 원칙:
- Repository 패턴 활용: DDD 계층 분리 준수
- 시간 중심 처리: target_start/target_end 기준 판단
- 성능 최적화: 단계별 조기 종료 로직
- 임시 검증: 개발 초기 안정성 확보 (안정화 후 제거)
"""

from datetime import datetime, timedelta
from typing import Optional

from upbit_auto_trading.domain.repositories.candle_repository_interface import CandleRepositoryInterface
from upbit_auto_trading.infrastructure.logging import create_component_logger
from .candle_models import OverlapStatus, OverlapResult, OverlapRequest

logger = create_component_logger("OverlapAnalyzer")


class OverlapAnalyzer:
    """
    OverlapAnalyzer v5.0 - 5가지 상태 분류 분석 엔진

    제안된 로직의 정확한 5개 상태 분류 구현:
    1. NO_OVERLAP: 겹침 없음
    2. COMPLETE_OVERLAP: 완전 겹침
    3. PARTIAL_START: 시작 겹침
    4. PARTIAL_MIDDLE_FRAGMENT: 중간 겹침 (파편)
    5. PARTIAL_MIDDLE_CONTINUOUS: 중간 겹침 (말단)

    성능 최적화: 단계별 조기 종료로 불필요한 쿼리 방지
    """

    def __init__(self, repository: CandleRepositoryInterface, time_utils, enable_validation: bool = True):
        """
        Args:
            repository: CandleRepositoryInterface 구현체
            time_utils: 시간 유틸리티 (타임프레임 초 계산용)
            enable_validation: 임시 검증 활성화 (개발 초기용, 안정화 후 False)
        """
        self.repository = repository
        self.time_utils = time_utils
        self.enable_validation = enable_validation
        logger.info("OverlapAnalyzer v5.0 초기화 완료 - 5가지 상태 분류 지원")

    async def analyze_overlap(self, request: OverlapRequest) -> OverlapResult:
        """
        제안된 5단계 겹침 분석 알고리즘

        성능 최적화: 단계별 조기 종료로 불필요한 쿼리 방지
        """
        # 0. 임시 검증 (개발 초기에만)
        if self.enable_validation:
            self._validate_request(request)

        logger.debug(f"겹침 분석 시작: {request.symbol} {request.timeframe} "
                    f"{request.target_start} ~ {request.target_end} ({request.target_count}개) [업비트 내림차순]")

        # 1. 겹침 없음 확인 (LIMIT 1 쿼리)
        has_data = await self.repository.has_any_data_in_range(
            request.symbol, request.timeframe,
            request.target_start, request.target_end
        )

        if not has_data:
            logger.debug("→ NO_OVERLAP: 범위 내 데이터 없음")
            return self._create_no_overlap_result(request)

        # 2. 완전성 확인 (COUNT 쿼리)
        is_complete = await self.repository.is_range_complete(
            request.symbol, request.timeframe,
            request.target_start, request.target_end, request.target_count
        )

        if is_complete:
            logger.debug("→ COMPLETE_OVERLAP: 완전한 데이터 존재")
            return self._create_complete_overlap_result(request)

        # 3. 일부 겹침 - 시작점 확인
        has_start = await self.has_data_in_start(
            request.symbol, request.timeframe, request.target_start
        )

        if has_start:
            # 3.1. 시작 겹침 처리
            logger.debug("→ 시작점에 데이터 존재: PARTIAL_START 처리")
            return await self._handle_start_overlap(request)
        else:
            # 3.2. 중간 겹침 처리
            logger.debug("→ 시작점에 데이터 없음: 중간 겹침 처리")
            return await self._handle_middle_overlap(request)

    # === 개발 초기 임시 검증 (안정화 후 제거) ===

    def _validate_request(self, request: OverlapRequest) -> None:
        """개발 초기 임시 검증 - 기능 안정화 후 제거 가능"""

        # 1. count 범위 검증
        if request.target_count <= 1:
            raise ValueError(f"count는 1보다 커야 합니다: {request.target_count}")

        if request.target_count > 200:
            raise ValueError(f"count는 200 이하여야 합니다: {request.target_count}")

        # 2. 시간 순서 검증 (업비트 내림차순: start > end)
        if request.target_start <= request.target_end:
            raise ValueError(
                f"업비트 내림차순: target_start가 target_end보다 커야 합니다: "
                f"{request.target_start} <= {request.target_end}"
            )

        # 3. 카운트 계산 일치성 검증
        expected_count = self.calculate_expected_count(
            request.target_start, request.target_end, request.timeframe
        )
        if expected_count != request.target_count:
            raise ValueError(
                f"시간 범위와 count가 일치하지 않습니다: "
                f"계산된 count={expected_count}, 요청 count={request.target_count}"
            )

    # === 시작점/중간점 겹침 처리 ===

    async def _handle_start_overlap(self, request: OverlapRequest) -> OverlapResult:
        """시작 겹침 처리 (PARTIAL_START)"""
        partial_end = await self.repository.find_last_continuous_time(
            request.symbol, request.timeframe, request.target_start, request.target_end
        )

        if partial_end and partial_end < request.target_end:
            dt_seconds = self.get_timeframe_dt(request.timeframe)
            api_start = partial_end + timedelta(seconds=dt_seconds)  # 다음 캔들부터 API 요청

            logger.debug(f"→ PARTIAL_START: DB({partial_end}~{request.target_start}) + API({request.target_end}~{api_start}) [업비트순]")
            return OverlapResult(
                status=OverlapStatus.PARTIAL_START,
                api_start=api_start,
                api_end=request.target_end,
                db_start=request.target_start,
                db_end=partial_end,
                partial_end=partial_end
            )
        else:
            # 예상치 못한 케이스 → 전체 API 요청
            logger.warning("예상치 못한 시작 겹침 케이스 → 폴백")
            return self._create_fallback_result(request)

    async def _handle_middle_overlap(self, request: OverlapRequest) -> OverlapResult:
        """중간 겹침 처리 (PARTIAL_MIDDLE_*)"""
        # 데이터 시작점 찾기
        partial_start = await self.find_data_start_in_range(
            request.symbol, request.timeframe,
            request.target_start, request.target_end
        )

        if not partial_start:
            # 데이터 시작점을 찾을 수 없음 → 전체 API 요청
            logger.warning("데이터 시작점 없음 → 폴백")
            return self._create_fallback_result(request)

        # 연속성 확인
        is_continuous = await self.is_continue_till_end(
            request.symbol, request.timeframe, partial_start, request.target_end
        )

        if is_continuous:
            # 말단 겹침 (PARTIAL_MIDDLE_CONTINUOUS)
            dt_seconds = self.get_timeframe_dt(request.timeframe)
            api_end = partial_start + timedelta(seconds=dt_seconds)  # 다음 캔들까지 API 요청

            logger.debug(f"→ PARTIAL_MIDDLE_CONTINUOUS: API({request.target_start}~{api_end}) + "
                         f"DB({partial_start}~{request.target_end}) [업비트순]")
            return OverlapResult(
                status=OverlapStatus.PARTIAL_MIDDLE_CONTINUOUS,
                api_start=request.target_start,
                api_end=api_end,
                db_start=partial_start,
                db_end=request.target_end,
                partial_start=partial_start
            )
        else:
            # 파편 겹침 (PARTIAL_MIDDLE_FRAGMENT)
            logger.debug(f"→ PARTIAL_MIDDLE_FRAGMENT: 2번째 gap 발견 → 전체 API 요청")
            return OverlapResult(
                status=OverlapStatus.PARTIAL_MIDDLE_FRAGMENT,
                api_start=request.target_start,
                api_end=request.target_end,
                db_start=None,
                db_end=None,
                partial_start=partial_start
            )

    # === 결과 생성 헬퍼 메서드들 ===

    def _create_no_overlap_result(self, request: OverlapRequest) -> OverlapResult:
        """겹침 없음 결과 생성"""
        return OverlapResult(
            status=OverlapStatus.NO_OVERLAP,
            api_start=request.target_start,
            api_end=request.target_end,
            db_start=None,
            db_end=None
        )

    def _create_complete_overlap_result(self, request: OverlapRequest) -> OverlapResult:
        """완전 겹침 결과 생성"""
        return OverlapResult(
            status=OverlapStatus.COMPLETE_OVERLAP,
            api_start=None,
            api_end=None,
            db_start=request.target_start,
            db_end=request.target_end
        )

    def _create_fallback_result(self, request: OverlapRequest) -> OverlapResult:
        """예상치 못한 케이스 → 전체 API 요청으로 폴백"""
        logger.warning("예상치 못한 케이스 → PARTIAL_MIDDLE_FRAGMENT 폴백")
        return OverlapResult(
            status=OverlapStatus.PARTIAL_MIDDLE_FRAGMENT,  # 안전한 폴백
            api_start=request.target_start,
            api_end=request.target_end,
            db_start=None,
            db_end=None
        )

    # === 보조 메서드들 ===

    async def has_data_in_start(self, symbol: str, timeframe: str, start_time: datetime) -> bool:
        """target_start에 데이터 존재 여부 확인 (특정 시점 정확 검사)"""
        return await self.repository.has_data_at_time(symbol, timeframe, start_time)

    async def find_data_start_in_range(self, symbol: str, timeframe: str,
                                      start_time: datetime, end_time: datetime) -> Optional[datetime]:
        """범위 내 데이터 시작점 찾기 (MAX 쿼리)

        업비트 서버 내림차순 특성: 최신 시간이 데이터의 '시작점'
        target_start ~ target_end 범위에서 candle_date_time_utc의 MAX 값 반환
        """
        return await self.repository.find_data_start_in_range(symbol, timeframe, start_time, end_time)

    async def is_continue_till_end(self, symbol: str, timeframe: str,
                                  start_time: datetime, end_time: datetime) -> bool:
        """start_time부터 end_time까지 연속성 확인 (안전한 범위 제한)"""
        return await self.repository.is_continue_till_end(symbol, timeframe, start_time, end_time)

    def get_timeframe_dt(self, timeframe: str) -> int:
        """타임프레임 → 초 단위 변환 (time_utils 연동)"""
        return self.time_utils.get_timeframe_seconds(timeframe)

    def calculate_expected_count(self, start_time: datetime, end_time: datetime, timeframe: str) -> int:
        """시간 범위 → 예상 캔들 개수 계산 (업비트 내림차순: start > end)"""
        dt_seconds = self.get_timeframe_dt(timeframe)
        time_diff = int((start_time - end_time).total_seconds())  # start > end이므로 start - end
        return (time_diff // dt_seconds) + 1

    # === 구 버전 호환성 유지 (deprecated) ===

    async def analyze(self, symbol: str, timeframe: str, start_time: datetime, count: int) -> dict:
        """구 버전 호환성 유지 (deprecated)

        새 코드는 analyze_overlap()을 사용하세요.
        """
        logger.warning("analyze() 메서드는 deprecated입니다. analyze_overlap()을 사용하세요.")

        end_time = start_time + timedelta(seconds=(count - 1) * self.get_timeframe_dt(timeframe))
        request = OverlapRequest(
            symbol=symbol,
            timeframe=timeframe,
            target_start=start_time,
            target_end=end_time,
            target_count=count
        )

        result = await self.analyze_overlap(request)

        # 구 버전 형식으로 변환
        return {
            "status": result.status.value,
            "connected_end": result.partial_end or result.db_end,
            "api_start": result.api_start,
            "api_end": result.api_end,
            "db_start": result.db_start,
            "db_end": result.db_end
        }
