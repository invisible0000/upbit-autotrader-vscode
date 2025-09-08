"""
업비트 자동매매 시스템 - Overlap Optimizer v4.0 (Practical Implementation)

실용 중심 겹침 최적화 엔진:
- 200개 청크 기본 전략 (API 호출 비용 최소화)
- 4단계 최적화: START_OVERLAP → COMPLETE_OVERLAP → FRAGMENTATION → CONNECTED_END
- 실제 데이터 수집 및 INSERT OR IGNORE 저장
- 비용 중심 접근: 요청 횟수 > 데이터 용량
"""

from datetime import datetime, timedelta
from typing import List, Optional, Tuple, Dict, Any
from dataclasses import dataclass, field
from upbit_auto_trading.infrastructure.logging import create_component_logger

logger = create_component_logger("OverlapOptimizer")

# 업비트 API 제한
UPBIT_API_LIMIT = 200


@dataclass(frozen=True)
class ApiRequest:
    """API 요청 정보"""
    symbol: str
    timeframe: str
    start_time: datetime
    count: int
    target_start: datetime
    expected_end: datetime

    def to_upbit_params(self) -> Dict[str, Any]:
        """업비트 API 파라미터로 변환"""
        return {
            "market": self.symbol,
            "to": self.start_time.isoformat(),
            "count": self.count
        }


@dataclass(frozen=True)
class OptimizationStep:
    """최적화 단계 정보"""
    step_number: int
    strategy: str  # START_OVERLAP, COMPLETE_OVERLAP, FRAGMENTATION, CONNECTED_END
    symbol: str
    timeframe: str
    start_time: datetime
    end_time: datetime
    api_request: Optional[ApiRequest]
    candles_inserted: int
    next_start: datetime


@dataclass(frozen=True)
class FragmentationResult:
    """파편화 확인 결과"""
    has_fragmentation: bool
    gap_count: int
    first_gap_position: Optional[datetime]  # 첫 번째 끊어짐 위치 (연결된 끝 찾기에서 재사용)
    threshold_seconds: float  # 사용된 임계값 (디버깅용)


@dataclass(frozen=True)
class OptimizationResult:
    """4단계 최적화 결과"""
    symbol: str
    timeframe: str
    original_start: datetime
    original_end: datetime
    optimization_steps: List[OptimizationStep] = field(default_factory=list)
    total_api_calls: int = 0
    total_candles_inserted: int = 0
    completion_status: str = "completed"  # completed, partial, failed


class OverlapOptimizer:
    """업비트 겹침 최적화기 v4.0 - 실용 구현"""

    def __init__(self, repository, time_utils, api_client):
        """
        Args:
            repository: 캔들 데이터 저장소
            time_utils: 시간 유틸리티
            api_client: 업비트 API 클라이언트 (async)
        """
        self.repository = repository
        self.time_utils = time_utils
        self.api_client = api_client

        # 핵심 메트릭만 유지 (간소화)
        self._metrics = {
            "total_optimizations": 0,
            "total_api_calls": 0,
            "total_candles_collected": 0,
            "strategy_usage": {}
        }

        # timeframe 캐시 (성능 최적화)
        self._timeframe_cache = {}

        logger.info("업비트 겹침 최적화기 v4.0 초기화 완료 (실용 구현)")

    def _get_timeframe_seconds(self, timeframe: str) -> int:
        """timeframe 초 변환 (캐싱)"""
        if timeframe not in self._timeframe_cache:
            self._timeframe_cache[timeframe] = self.time_utils.get_timeframe_seconds(timeframe)
        return self._timeframe_cache[timeframe]

    def _get_fragmentation_threshold(self, timeframe: str) -> float:
        """적응형 파편화 임계값 계산

        Args:
            timeframe: 타임프레임 (1s, 1m, 5m, 15m, 1h, 4h, 1d, 1w, 1M, 1y)

        Returns:
            float: timeframe의 1.5배 임계값 (초 단위)

        Examples:
            1s → 1.5초, 1m → 90초, 5m → 450초
        """
        timeframe_seconds = self._get_timeframe_seconds(timeframe)
        threshold = timeframe_seconds * 1.5

        logger.debug(f"적응형 임계값 계산: {timeframe} → {timeframe_seconds}s × 1.5 = {threshold}s")

        return threshold

    async def optimize_and_collect_candles(
        self,
        symbol: str,
        timeframe: str,
        start_time: datetime,
        end_time: datetime
    ) -> OptimizationResult:
        """4단계 최적화로 캔들 데이터 수집"""
        logger.info(f"4단계 최적화 시작: {symbol} {timeframe} "
                    f"{start_time} ~ {end_time}")

        result = OptimizationResult(
            symbol=symbol,
            timeframe=timeframe,
            original_start=start_time,
            original_end=end_time
        )

        try:
            # 4단계 순차 처리
            current_start = start_time
            step_number = 1
            optimization_steps = []
            total_api_calls = 0
            total_candles = 0

            while current_start < end_time:
                # 1단계: 시작점 겹침 확인
                if self._check_start_overlap(symbol, timeframe, current_start):
                    api_request, candles_inserted, next_start = await self._handle_start_overlap(
                        symbol, timeframe, current_start, end_time
                    )
                    strategy = "START_OVERLAP"

                # 2단계: 완전 겹침 확인
                elif self._check_complete_overlap(symbol, timeframe, current_start, end_time):
                    api_request, candles_inserted, next_start = await self._handle_complete_overlap(
                        symbol, timeframe, current_start, end_time
                    )
                    strategy = "COMPLETE_OVERLAP"

                # 3단계: 파편화 확인 (최적화된 결과 재사용)
                fragmentation_result = self._check_fragmentation_with_position(
                    symbol, timeframe, current_start, end_time
                )
                if fragmentation_result.has_fragmentation:
                    api_request, candles_inserted, next_start = await self._handle_fragmentation(
                        symbol, timeframe, current_start, end_time, fragmentation_result
                    )
                    strategy = "FRAGMENTATION"

                # 4단계: 기본 처리 (연결된 끝)
                else:
                    api_request, candles_inserted, next_start = await self._handle_connected_end(
                        symbol, timeframe, current_start, end_time
                    )
                    strategy = "CONNECTED_END"

                # 단계 기록
                step = OptimizationStep(
                    step_number=step_number,
                    strategy=strategy,
                    symbol=symbol,
                    timeframe=timeframe,
                    start_time=current_start,
                    end_time=min(end_time, next_start),
                    api_request=api_request,
                    candles_inserted=candles_inserted,
                    next_start=next_start
                )
                optimization_steps.append(step)

                # 통계 업데이트
                if api_request:
                    total_api_calls += 1
                total_candles += candles_inserted

                # 다음 단계 준비
                current_start = next_start
                step_number += 1

                # 무한 루프 방지 (최대 1000단계)
                if step_number > 1000:
                    logger.warning(f"최대 단계 수 초과: {symbol} {timeframe}")
                    break

            # 결과 생성
            result = OptimizationResult(
                symbol=symbol,
                timeframe=timeframe,
                original_start=start_time,
                original_end=end_time,
                optimization_steps=optimization_steps,
                total_api_calls=total_api_calls,
                total_candles_inserted=total_candles,
                completion_status="completed"
            )

            # 메트릭 업데이트
            self._update_metrics(result)

            logger.info(f"4단계 최적화 완료: {symbol} {timeframe} "
                        f"단계={len(optimization_steps)}, API={total_api_calls}회, "
                        f"캔들={total_candles}개")

            return result

        except Exception as e:
            logger.error(f"4단계 최적화 실패: {symbol} {timeframe} - {e}")

            return OptimizationResult(
                symbol=symbol,
                timeframe=timeframe,
                original_start=start_time,
                original_end=end_time,
                optimization_steps=[],
                total_api_calls=0,
                total_candles_inserted=0,
                completion_status="failed"
            )

    # ========== 4단계 최적화 메서드들 ==========

    def _check_start_overlap(self, symbol: str, timeframe: str, start_time: datetime) -> bool:
        """1단계: 시작점 200개 내 겹침 확인"""
        table_name = f"candles_{symbol.replace('-', '_')}_{timeframe}"
        timeframe_seconds = self._get_timeframe_seconds(timeframe)
        end_time = start_time + timedelta(seconds=timeframe_seconds * (UPBIT_API_LIMIT - 1))

        overlap_query = f"""
        SELECT 1 FROM {table_name}
        WHERE candle_date_time_utc BETWEEN ? AND ?
        LIMIT 1
        """

        result = self.repository._execute_query(
            overlap_query,
            (start_time.isoformat(), end_time.isoformat())
        )

        has_overlap = len(result) > 0
        logger.debug(f"시작점 겹침 확인: {symbol} {timeframe} -> {has_overlap}")

        return has_overlap

    async def _handle_start_overlap(
        self,
        symbol: str,
        timeframe: str,
        start_time: datetime,
        end_time: datetime
    ) -> Tuple[Optional[ApiRequest], int, datetime]:
        """1단계 처리: 시작점 -1부터 200개 요청 후 INSERT"""
        timeframe_seconds = self._get_timeframe_seconds(timeframe)

        # 시작점 -1부터 요청 (업비트 특성: 시작점 배제)
        api_start = start_time - timedelta(seconds=timeframe_seconds)

        # TimeUtils를 활용한 정확한 캔들 개수 계산
        base_count = self.time_utils.calculate_candle_count(start_time, end_time, timeframe)

        # 버퍼는 200개 제한 내에서만 적용 (API 호출 횟수 증가 방지)
        if base_count >= UPBIT_API_LIMIT:
            api_count = UPBIT_API_LIMIT  # 200개 정확히 요청
        else:
            api_count = min(UPBIT_API_LIMIT, base_count + 2)  # +2: 소량 요청시에만 버퍼 적용

        api_request = ApiRequest(
            symbol=symbol,
            timeframe=timeframe,
            start_time=api_start,
            count=api_count,
            target_start=start_time,
            expected_end=start_time + timedelta(seconds=timeframe_seconds * (api_count - 1))
        )

        # 실제 API 호출 및 데이터 저장
        candles_data = await self.api_client(**api_request.to_upbit_params())
        candles_inserted = await self.repository.save_candles(symbol, timeframe, candles_data)

        # 다음 시작점 계산
        next_start = start_time + timedelta(seconds=timeframe_seconds * UPBIT_API_LIMIT)
        if next_start >= end_time:
            next_start = end_time

        logger.info(f"1단계 처리 완료: {symbol} API 1회, 캔들 {candles_inserted}개")

        return api_request, candles_inserted, next_start

    def _check_complete_overlap(
        self,
        symbol: str,
        timeframe: str,
        start_time: datetime,
        end_time: datetime
    ) -> bool:
        """2단계: 완전 겹침 확인"""
        table_name = f"candles_{symbol.replace('-', '_')}_{timeframe}"
        timeframe_seconds = self._get_timeframe_seconds(timeframe)

        # 200개 범위 내에서 완전 겹침 확인
        chunk_end = min(
            end_time,
            start_time + timedelta(seconds=timeframe_seconds * (UPBIT_API_LIMIT - 1))
        )

        # TimeUtils를 활용한 정확한 예상 캔들 수 계산
        expected_count = self.time_utils.calculate_candle_count(start_time, chunk_end, timeframe)

        count_query = f"""
        SELECT COUNT(*) FROM {table_name}
        WHERE candle_date_time_utc BETWEEN ? AND ?
        """

        result = self.repository._execute_query(
            count_query,
            (start_time.isoformat(), chunk_end.isoformat())
        )

        actual_count = result[0][0] if result else 0
        is_complete = actual_count >= expected_count

        logger.debug(f"완전 겹침 확인: {symbol} {timeframe} "
                     f"실제={actual_count}, 예상={expected_count}, 완전={is_complete}")

        return is_complete

    async def _handle_complete_overlap(
        self,
        symbol: str,
        timeframe: str,
        start_time: datetime,
        end_time: datetime
    ) -> Tuple[Optional[ApiRequest], int, datetime]:
        """2단계 처리: 완전 겹침 시 시작점 이동"""
        timeframe_seconds = self._get_timeframe_seconds(timeframe)

        # 200개만큼 시작점 이동
        next_start = start_time + timedelta(seconds=timeframe_seconds * UPBIT_API_LIMIT)
        if next_start >= end_time:
            next_start = end_time

        logger.info(f"2단계 처리: {symbol} 완전 겹침으로 API 호출 생략, 시작점 이동")

        return None, 0, next_start  # API 호출 없음

    def _check_fragmentation_with_position(
        self,
        symbol: str,
        timeframe: str,
        start_time: datetime,
        end_time: datetime
    ) -> FragmentationResult:
        """3단계: 파편화 확인 + 첫 번째 끊어짐 위치 반환"""
        table_name = f"candles_{symbol.replace('-', '_')}_{timeframe}"
        timeframe_seconds = self._get_timeframe_seconds(timeframe)

        # 200개 범위 내 파편화 확인
        chunk_end = min(
            end_time,
            start_time + timedelta(seconds=timeframe_seconds * (UPBIT_API_LIMIT - 1))
        )

        # 적응형 임계값 사용
        fragmentation_threshold = self._get_fragmentation_threshold(timeframe)

        # 조기 종료 + 첫 번째 끊어짐 위치 반환 쿼리
        optimized_fragmentation_query = f"""
        WITH gaps AS (
            SELECT
                candle_date_time_utc,
                LAG(timestamp) OVER (ORDER BY timestamp) as prev_timestamp,
                timestamp - LAG(timestamp) OVER (ORDER BY timestamp) as gap_seconds
            FROM {table_name}
            WHERE candle_date_time_utc BETWEEN ? AND ?
            ORDER BY timestamp
        ),
        significant_gaps AS (
            SELECT
                candle_date_time_utc,
                gap_seconds,
                ROW_NUMBER() OVER (ORDER BY candle_date_time_utc) as gap_rank
            FROM gaps
            WHERE prev_timestamp IS NOT NULL AND gap_seconds > ?
            LIMIT 2  -- 조기 종료: 최대 2개만 확인
        )
        SELECT
            COUNT(*) as gap_count,
            MIN(CASE WHEN gap_rank = 1 THEN candle_date_time_utc END) as first_gap_position
        FROM significant_gaps
        """

        result = self.repository._execute_query(
            optimized_fragmentation_query,
            (start_time.isoformat(), chunk_end.isoformat(), fragmentation_threshold)
        )

        if result and len(result) > 0:
            gap_count = result[0][0] or 0
            first_gap_str = result[0][1] if len(result[0]) > 1 else None

            # 첫 번째 끊어짐 위치 파싱
            first_gap_position = None
            if first_gap_str:
                first_gap_position = datetime.fromisoformat(first_gap_str.replace('Z', '+00:00'))

            has_fragmentation = gap_count >= 2

            fragmentation_result = FragmentationResult(
                has_fragmentation=has_fragmentation,
                gap_count=gap_count,
                first_gap_position=first_gap_position,
                threshold_seconds=fragmentation_threshold
            )

            logger.debug(f"파편화 확인: {symbol} {timeframe} "
                         f"간격={gap_count}, 파편화={has_fragmentation}, "
                         f"첫 끊어짐={first_gap_position}")

            return fragmentation_result

        # 결과가 없는 경우
        return FragmentationResult(
            has_fragmentation=False,
            gap_count=0,
            first_gap_position=None,
            threshold_seconds=fragmentation_threshold
        )

    async def _handle_fragmentation(
        self,
        symbol: str,
        timeframe: str,
        start_time: datetime,
        end_time: datetime,
        fragmentation_result: FragmentationResult
    ) -> Tuple[Optional[ApiRequest], int, datetime]:
        """3단계 처리 최적화: FragmentationResult 재사용으로 연속된 끝부터 200개 요청"""

        # 최적화된 연결된 끝 찾기 (중복 계산 제거)
        connected_end = self._find_connected_end(
            fragmentation_result, symbol, timeframe, start_time, end_time
        )

        if connected_end and connected_end > start_time:
            # 연결된 끝부터 요청 시작
            api_start_time = connected_end
        else:
            # 연결된 끝이 없으면 원래 시작점부터
            api_start_time = start_time

        timeframe_seconds = self._get_timeframe_seconds(timeframe)

        # TimeUtils를 활용한 정확한 캔들 개수 계산
        base_count = self.time_utils.calculate_candle_count(api_start_time, end_time, timeframe)

        # 버퍼는 200개 제한 내에서만 적용 (API 호출 횟수 증가 방지)
        if base_count >= UPBIT_API_LIMIT:
            api_count = UPBIT_API_LIMIT  # 200개 정확히 요청
        else:
            api_count = min(UPBIT_API_LIMIT, base_count + 1)  # +1: 소량 요청시에만 안전 버퍼

        api_request = ApiRequest(
            symbol=symbol,
            timeframe=timeframe,
            start_time=api_start_time,
            count=api_count,
            target_start=api_start_time,
            expected_end=api_start_time + timedelta(seconds=timeframe_seconds * (api_count - 1))
        )

        # 실제 API 호출 및 INSERT OR IGNORE
        candles_data = await self.api_client(**api_request.to_upbit_params())
        candles_inserted = await self.repository.save_candles(symbol, timeframe, candles_data)

        # 다음 시작점
        next_start = api_start_time + timedelta(seconds=timeframe_seconds * UPBIT_API_LIMIT)
        if next_start >= end_time:
            next_start = end_time

        logger.info(f"3단계 최적화 완료: {symbol} 파편화 구간, 캔들 {candles_inserted}개")

        return api_request, candles_inserted, next_start

    def _find_connected_end(
        self,
        fragmentation_result: FragmentationResult,
        symbol: str,
        timeframe: str,
        start_time: datetime,
        end_time: datetime
    ) -> Optional[datetime]:
        """연결된 끝 찾기 최적화 - FragmentationResult 재사용"""

        # 파편화가 없으면 전체 구간이 연결되어 있음
        if not fragmentation_result.has_fragmentation:
            logger.debug(f"연결된 끝 최적화: {symbol} {timeframe} - 파편화 없음, 전체 연결")
            return end_time

        # 첫 번째 끊어짐 위치가 있으면 그 직전까지가 연결된 구간
        if fragmentation_result.first_gap_position:
            timeframe_seconds = self._get_timeframe_seconds(timeframe)
            # 첫 번째 끊어짐 직전이 연결된 끝
            connected_end = fragmentation_result.first_gap_position - timedelta(seconds=timeframe_seconds)

            logger.debug(f"연결된 끝 최적화: {symbol} {timeframe} - "
                         f"첫 끊어짐={fragmentation_result.first_gap_position}, "
                         f"연결끝={connected_end}")

            return connected_end if connected_end >= start_time else None

        # 파편화는 있지만 첫 번째 위치가 없는 경우 (예외 상황)
        raise ValueError(f"파편화 있으나 위치 정보 없음: {symbol} {timeframe}")

    async def _handle_connected_end(
        self,
        symbol: str,
        timeframe: str,
        start_time: datetime,
        end_time: datetime
    ) -> Tuple[Optional[ApiRequest], int, datetime]:
        """4단계 처리: 기본 200개 청크 요청"""
        timeframe_seconds = self._get_timeframe_seconds(timeframe)

        # 시작점 -1부터 200개 요청
        api_start = start_time - timedelta(seconds=timeframe_seconds)

        # TimeUtils를 활용한 정확한 캔들 개수 계산
        base_count = self.time_utils.calculate_candle_count(start_time, end_time, timeframe)

        # 버퍼는 200개 제한 내에서만 적용 (API 호출 횟수 증가 방지)
        if base_count >= UPBIT_API_LIMIT:
            api_count = UPBIT_API_LIMIT  # 200개 정확히 요청
        else:
            api_count = min(UPBIT_API_LIMIT, base_count + 2)  # +2: 소량 요청시에만 버퍼 적용

        api_request = ApiRequest(
            symbol=symbol,
            timeframe=timeframe,
            start_time=api_start,
            count=api_count,
            target_start=start_time,
            expected_end=start_time + timedelta(seconds=timeframe_seconds * (api_count - 1))
        )

        # 실제 API 호출 및 INSERT OR IGNORE
        candles_data = await self.api_client(**api_request.to_upbit_params())
        candles_inserted = await self.repository.save_candles(symbol, timeframe, candles_data)

        # 다음 시작점
        next_start = start_time + timedelta(seconds=timeframe_seconds * UPBIT_API_LIMIT)
        if next_start >= end_time:
            next_start = end_time

        logger.info(f"4단계 처리 완료: {symbol} 기본 청크, 캔들 {candles_inserted}개")

        return api_request, candles_inserted, next_start

    def _update_metrics(self, result: OptimizationResult) -> None:
        """통계 업데이트"""
        self._metrics["total_optimizations"] += 1
        self._metrics["total_api_calls"] += result.total_api_calls
        self._metrics["total_candles_collected"] += result.total_candles_inserted

        # 전략별 사용 통계
        for step in result.optimization_steps:
            strategy = step.strategy
            if strategy not in self._metrics["strategy_usage"]:
                self._metrics["strategy_usage"][strategy] = 0
            self._metrics["strategy_usage"][strategy] += 1

    def get_optimization_metrics(self) -> Dict:
        """최적화 성능 지표 반환"""
        return self._metrics.copy()

    def reset_metrics(self) -> None:
        """성능 지표 초기화"""
        self._metrics = {
            "total_optimizations": 0,
            "total_api_calls": 0,
            "total_candles_collected": 0,
            "strategy_usage": {}
        }
        logger.info("최적화 성능 지표 초기화됨")
