"""
Overlap Optimizer v4.0 - 업비트 특화 4단계 겹침 최적화 엔진

4단계 최적화 전략 (실제 데이터 수집 + 저장):
1. 시작점 200개 내 겹침 확인 → 200개 청크 요청 + INSERT OR IGNORE
2. 완전 겹침 확인 → 시작점 이동
3. 파편화 겹침 확인 → 연속된 끝부터 200개 요청
4. 연결된 끝 찾기 → 200개 청크 요청

API 호출 최적화 + 실제 데이터 수집 통합
"""

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import List, Optional, Tuple, Dict, Callable

from upbit_auto_trading.infrastructure.logging import create_component_logger
from upbit_auto_trading.infrastructure.market_data.candle.time_utils import TimeUtils


logger = create_component_logger("OverlapOptimizer")

# 업비트 API 제약사항
UPBIT_API_LIMIT = 200
UPBIT_RATE_LIMIT = 600  # req/min


@dataclass(frozen=True)
class ApiRequest:
    """업비트 API 요청 모델"""
    symbol: str
    timeframe: str
    start_time: datetime
    count: int
    target_start: datetime                     # 실제 목표 시작 시간
    expected_end: datetime                     # 예상 종료 시간
    next_start: Optional[datetime] = None      # 다음 요청 시작점
    remaining_count: int = 0                   # 남은 캔들 수
    delay_ms: float = 0.0                     # Rate Limit 지연시간

    def to_upbit_params(self) -> dict:
        """업비트 API 파라미터로 변환"""
        return {
            "market": self.symbol,
            "to": self.start_time.isoformat() + "Z",
            "count": self.count
        }


@dataclass(frozen=True)
class OptimizationStep:
    """최적화 단계 정보"""
    step_number: int                          # 단계 번호 (1-4)
    strategy: str                             # 적용된 전략
    start_time: datetime                      # 단계 시작 시간
    end_time: datetime                        # 단계 종료 시간
    api_request: Optional[ApiRequest]         # 생성된 API 요청
    db_operations: int                        # DB 작업 수 (INSERT 등)
    duration_ms: float                        # 단계 처리 시간
    candles_processed: int = 0                # 처리된 캔들 수


@dataclass(frozen=True)
class OptimizationResult:
    """4단계 최적화 결과"""
    symbol: str
    timeframe: str
    request_start: datetime
    request_end: datetime
    total_requested_candles: int

    api_requests: List[ApiRequest]             # 실제 API 요청 목록
    optimization_steps: List[OptimizationStep] # 단계별 최적화 과정
    total_api_calls: int                      # 총 API 호출 수
    total_candles_inserted: int               # 실제 삽입된 캔들 수
    total_duration_ms: float                  # 전체 처리 시간

    @property
    def efficiency_score(self) -> float:
        """최적화 효율성 점수 (캔들 수 / API 호출 수)"""
        return self.total_candles_inserted / max(self.total_api_calls, 1)

    @property
    def coverage_rate(self) -> float:
        """요청 대비 실제 수집률"""
        return self.total_candles_inserted / max(self.total_requested_candles, 1)


class UpbitOverlapOptimizer:
    """업비트 특화 4단계 겹침 최적화 엔진 (실제 데이터 수집)"""

    def __init__(self, repository, time_utils: TimeUtils, api_client: Callable):
        self.repository = repository
        self.time_utils = time_utils
        self.api_client = api_client  # 실제 업비트 API 클라이언트
        self._metrics = {
            "total_optimizations": 0,
            "total_api_calls": 0,
            "total_candles_collected": 0,
            "strategy_usage": {}
        }

    async def optimize_and_collect_candles(
        self,
        symbol: str,
        timeframe: str,
        start_time: datetime,
        end_time: datetime
    ) -> OptimizationResult:
        """4단계 최적화로 실제 캔들 데이터 수집 및 저장"""
        optimization_start = datetime.now()

        # 총 요청 캔들 수 계산
        timeframe_seconds = self.time_utils.get_timeframe_seconds(timeframe)
        total_seconds = (end_time - start_time).total_seconds()
        total_requested = int(total_seconds / timeframe_seconds) + 1

        logger.info(f"4단계 최적화 시작: {symbol} {timeframe} "
                   f"{start_time} ~ {end_time} ({total_requested}개 캔들)")

        # 4단계 최적화 실행
        api_requests = []
        optimization_steps = []
        total_candles_inserted = 0
        current_start = start_time

        step_number = 1
        while current_start < end_time:
            step_start_time = datetime.now()

            # 1단계: 시작점 200개 내 겹침 확인
            if self._check_start_overlap(symbol, timeframe, current_start):
                strategy = "START_OVERLAP"
                api_request, candles_inserted, next_start = await self._handle_start_overlap(
                    symbol, timeframe, current_start, end_time
                )

            # 2단계: 완전 겹침 확인
            elif self._check_complete_overlap(symbol, timeframe, current_start, end_time):
                strategy = "COMPLETE_OVERLAP"
                api_request, candles_inserted, next_start = await self._handle_complete_overlap(
                    symbol, timeframe, current_start, end_time
                )

            # 3단계: 파편화 겹침 확인
            elif self._check_fragmentation(symbol, timeframe, current_start, end_time):
                strategy = "FRAGMENTATION"
                api_request, candles_inserted, next_start = await self._handle_fragmentation(
                    symbol, timeframe, current_start, end_time
                )

            # 4단계: 연결된 끝 찾기 (기본 200개 요청)
            else:
                strategy = "CONNECTED_END"
                api_request, candles_inserted, next_start = await self._handle_connected_end(
                    symbol, timeframe, current_start, end_time
                )

            # 단계 기록
            step_duration = (datetime.now() - step_start_time).total_seconds() * 1000
            step = OptimizationStep(
                step_number=step_number,
                strategy=strategy,
                start_time=current_start,
                end_time=min(next_start, end_time),
                api_request=api_request,
                db_operations=1 if api_request else 0,
                duration_ms=step_duration,
                candles_processed=candles_inserted
            )

            optimization_steps.append(step)
            if api_request:
                api_requests.append(api_request)

            total_candles_inserted += candles_inserted
            current_start = next_start
            step_number += 1

            # 무한 루프 방지
            if step_number > 100:
                logger.warning(f"최적화 단계 수 초과: {step_number}, 중단")
                break

        # 최적화 결과 생성
        total_duration = (datetime.now() - optimization_start).total_seconds() * 1000

        result = OptimizationResult(
            symbol=symbol,
            timeframe=timeframe,
            request_start=start_time,
            request_end=end_time,
            total_requested_candles=total_requested,
            api_requests=api_requests,
            optimization_steps=optimization_steps,
            total_api_calls=len(api_requests),
            total_candles_inserted=total_candles_inserted,
            total_duration_ms=total_duration
        )

        # 통계 업데이트
        self._update_metrics(result)

        logger.info(f"4단계 최적화 완료: API {len(api_requests)}회, "
                   f"캔들 {total_candles_inserted}개 수집, "
                   f"효율성 {result.efficiency_score:.1f}")


    # ========== 4단계 최적화 메서드들 ==========

    def _check_start_overlap(self, symbol: str, timeframe: str, start_time: datetime) -> bool:
        """1단계: 시작점 200개 내 겹침 확인"""
        try:
            table_name = f"candles_{symbol.replace('-', '_')}_{timeframe}"
            timeframe_seconds = self.time_utils.get_timeframe_seconds(timeframe)
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

        except Exception as e:
            logger.error(f"시작점 겹침 확인 실패: {e}")
            return False

    async def _handle_start_overlap(
        self,
        symbol: str,
        timeframe: str,
        start_time: datetime,
        end_time: datetime
    ) -> Tuple[Optional[ApiRequest], int, datetime]:
        """1단계 처리: 시작점 -1부터 200개 요청 후 INSERT"""
        timeframe_seconds = self.time_utils.get_timeframe_seconds(timeframe)

        # 시작점 -1부터 요청 (업비트 특성: 시작점 배제)
        api_start = start_time - timedelta(seconds=timeframe_seconds)
        api_count = min(UPBIT_API_LIMIT,
                       int((end_time - start_time).total_seconds() / timeframe_seconds) + 2)

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
        try:
            table_name = f"candles_{symbol.replace('-', '_')}_{timeframe}"
            timeframe_seconds = self.time_utils.get_timeframe_seconds(timeframe)

            # 200개 범위 내에서 완전 겹침 확인
            chunk_end = min(
                end_time,
                start_time + timedelta(seconds=timeframe_seconds * (UPBIT_API_LIMIT - 1))
            )

            # 예상 캔들 수
            expected_count = int((chunk_end - start_time).total_seconds() / timeframe_seconds) + 1

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

        except Exception as e:
            logger.error(f"완전 겹침 확인 실패: {e}")
            return False

    async def _handle_complete_overlap(
        self,
        symbol: str,
        timeframe: str,
        start_time: datetime,
        end_time: datetime
    ) -> Tuple[Optional[ApiRequest], int, datetime]:
        """2단계 처리: 완전 겹침 시 시작점 이동"""
        timeframe_seconds = self.time_utils.get_timeframe_seconds(timeframe)

        # 200개만큼 시작점 이동
        next_start = start_time + timedelta(seconds=timeframe_seconds * UPBIT_API_LIMIT)
        if next_start >= end_time:
            next_start = end_time

        logger.info(f"2단계 처리: {symbol} 완전 겹침으로 API 호출 생략, 시작점 이동")

        return None, 0, next_start  # API 호출 없음

    def _check_fragmentation(
        self,
        symbol: str,
        timeframe: str,
        start_time: datetime,
        end_time: datetime
    ) -> bool:
        """3단계: 파편화 겹침 확인"""
        try:
            table_name = f"candles_{symbol.replace('-', '_')}_{timeframe}"
            timeframe_seconds = self.time_utils.get_timeframe_seconds(timeframe)

            # 200개 범위 내 파편화 확인
            chunk_end = min(
                end_time,
                start_time + timedelta(seconds=timeframe_seconds * (UPBIT_API_LIMIT - 1))
            )

            fragmentation_query = f"""
            WITH gaps AS (
                SELECT
                    candle_date_time_utc,
                    LAG(candle_date_time_utc) OVER (ORDER BY candle_date_time_utc) as prev_time,
                    (julianday(candle_date_time_utc) -
                     julianday(LAG(candle_date_time_utc) OVER (ORDER BY candle_date_time_utc))
                    ) * 86400 as gap_seconds
                FROM {table_name}
                WHERE candle_date_time_utc BETWEEN ? AND ?
                ORDER BY candle_date_time_utc
            )
            SELECT COUNT(CASE WHEN gap_seconds > ? THEN 1 END) as significant_gaps
            FROM gaps
            WHERE prev_time IS NOT NULL
            """

            result = self.repository._execute_query(
                fragmentation_query,
                (start_time.isoformat(), chunk_end.isoformat(), timeframe_seconds * 1.5)
            )

            gap_count = result[0][0] if result else 0
            has_fragmentation = gap_count >= 2

            logger.debug(f"파편화 확인: {symbol} {timeframe} 간격={gap_count}, 파편화={has_fragmentation}")

            return has_fragmentation

        except Exception as e:
            logger.error(f"파편화 확인 실패: {e}")
            return False

    async def _handle_fragmentation(
        self,
        symbol: str,
        timeframe: str,
        start_time: datetime,
        end_time: datetime
    ) -> Tuple[Optional[ApiRequest], int, datetime]:
        """3단계 처리: 연속된 끝부터 200개 요청"""
        # 연속된 끝 찾기
        connected_end = self._find_connected_end(symbol, timeframe, start_time, end_time)

        if connected_end and connected_end > start_time:
            # 연속된 끝부터 요청 시작
            api_start_time = connected_end
        else:
            # 연속된 끝이 없으면 원래 시작점부터
            api_start_time = start_time

        timeframe_seconds = self.time_utils.get_timeframe_seconds(timeframe)
        api_count = min(UPBIT_API_LIMIT,
                       int((end_time - api_start_time).total_seconds() / timeframe_seconds) + 1)

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

        logger.info(f"3단계 처리 완료: {symbol} 파편화 구간, 캔들 {candles_inserted}개")

        return api_request, candles_inserted, next_start

    def _find_connected_end(
        self,
        symbol: str,
        timeframe: str,
        start_time: datetime,
        end_time: datetime
    ) -> Optional[datetime]:
        """연결된 끝 찾기 (공통 메서드)"""
        try:
            table_name = f"candles_{symbol.replace('-', '_')}_{timeframe}"
            timeframe_seconds = self.time_utils.get_timeframe_seconds(timeframe)

            connected_end_query = f"""
            WITH numbered_candles AS (
                SELECT
                    candle_date_time_utc,
                    ROW_NUMBER() OVER (ORDER BY candle_date_time_utc) as row_num,
                    datetime(?, '+' || (ROW_NUMBER() OVER (ORDER BY candle_date_time_utc) - 1) *
                             {timeframe_seconds} || ' seconds') as expected_time
                FROM {table_name}
                WHERE candle_date_time_utc >= ?
                    AND candle_date_time_utc <= ?
                ORDER BY candle_date_time_utc
                LIMIT {UPBIT_API_LIMIT}
            )
            SELECT candle_date_time_utc
            FROM numbered_candles
            WHERE candle_date_time_utc = expected_time
            ORDER BY candle_date_time_utc DESC
            LIMIT 1
            """

            chunk_end = min(
                end_time,
                start_time + timedelta(seconds=timeframe_seconds * (UPBIT_API_LIMIT - 1))
            )

            result = self.repository._execute_query(
                connected_end_query,
                (start_time.isoformat(), start_time.isoformat(), chunk_end.isoformat())
            )

            if result:
                connected_end_str = result[0][0]
                connected_end = datetime.fromisoformat(connected_end_str.replace('Z', '+00:00'))
                logger.debug(f"연결된 끝 발견: {symbol} {timeframe} -> {connected_end}")
                return connected_end

            return None

        except Exception as e:
            logger.error(f"연결된 끝 찾기 실패: {e}")
            return None

    async def _handle_connected_end(
        self,
        symbol: str,
        timeframe: str,
        start_time: datetime,
        end_time: datetime
    ) -> Tuple[Optional[ApiRequest], int, datetime]:
        """4단계 처리: 기본 200개 청크 요청"""
        timeframe_seconds = self.time_utils.get_timeframe_seconds(timeframe)

        # 시작점 -1부터 200개 요청
        api_start = start_time - timedelta(seconds=timeframe_seconds)
        api_count = min(UPBIT_API_LIMIT,
                       int((end_time - start_time).total_seconds() / timeframe_seconds) + 2)

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
