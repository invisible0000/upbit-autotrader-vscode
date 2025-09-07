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
class OptimizationResult:
    """4단계 최적화 결과"""
    symbol: str
    timeframe: str
    original_start: datetime
    original_end: datetime
    optimization_steps: List[OptimizationStep] = field(default_factory=list)
    total_api_calls: int = 0
    total_candles_inserted: int = 0
    processing_time_ms: float = 0.0
    completion_status: str = "completed"  # completed, partial, failed


class UpbitOverlapOptimizer:
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

        # 성능 메트릭
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

    async def optimize_and_collect_candles(
        self,
        symbol: str,
        timeframe: str,
        start_time: datetime,
        end_time: datetime
    ) -> OptimizationResult:
        """4단계 최적화로 캔들 데이터 수집"""
        optimization_start = datetime.now()
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

                # 3단계: 파편화 확인
                elif self._check_fragmentation(symbol, timeframe, current_start, end_time):
                    api_request, candles_inserted, next_start = await self._handle_fragmentation(
                        symbol, timeframe, current_start, end_time
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
            processing_time = (datetime.now() - optimization_start).total_seconds() * 1000
            result = OptimizationResult(
                symbol=symbol,
                timeframe=timeframe,
                original_start=start_time,
                original_end=end_time,
                optimization_steps=optimization_steps,
                total_api_calls=total_api_calls,
                total_candles_inserted=total_candles,
                processing_time_ms=processing_time,
                completion_status="completed"
            )

            # 메트릭 업데이트
            self._update_metrics(result)

            logger.info(f"4단계 최적화 완료: {symbol} {timeframe} "
                       f"단계={len(optimization_steps)}, API={total_api_calls}회, "
                       f"캔들={total_candles}개, 시간={processing_time:.1f}ms")

            return result

        except Exception as e:
            processing_time = (datetime.now() - optimization_start).total_seconds() * 1000
            logger.error(f"4단계 최적화 실패: {symbol} {timeframe} - {e}")

            return OptimizationResult(
                symbol=symbol,
                timeframe=timeframe,
                original_start=start_time,
                original_end=end_time,
                optimization_steps=[],
                total_api_calls=0,
                total_candles_inserted=0,
                processing_time_ms=processing_time,
                completion_status="failed"
            )

    # ========== 4단계 최적화 메서드들 ==========

    def _check_start_overlap(self, symbol: str, timeframe: str, start_time: datetime) -> bool:
        """1단계: 시작점 200개 내 겹침 확인"""
        try:
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
        timeframe_seconds = self._get_timeframe_seconds(timeframe)

        # 시작점 -1부터 요청 (업비트 특성: 시작점 배제)
        api_start = start_time - timedelta(seconds=timeframe_seconds)

        # TimeUtils를 활용한 정확한 캔들 개수 계산
        base_count = self.time_utils.calculate_candle_count(start_time, end_time, timeframe)
        api_count = min(UPBIT_API_LIMIT, base_count + 2)  # +2: 업비트 API 특성 고려 버퍼

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
        timeframe_seconds = self._get_timeframe_seconds(timeframe)

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
            timeframe_seconds = self._get_timeframe_seconds(timeframe)

            # 200개 범위 내 파편화 확인
            chunk_end = min(
                end_time,
                start_time + timedelta(seconds=timeframe_seconds * (UPBIT_API_LIMIT - 1))
            )

            fragmentation_query = f"""
            WITH gaps AS (
                SELECT
                    candle_date_time_utc,
                    LAG(timestamp) OVER (ORDER BY timestamp) as prev_timestamp,
                    timestamp - LAG(timestamp) OVER (ORDER BY timestamp) as gap_seconds
                FROM {table_name}
                WHERE candle_date_time_utc BETWEEN ? AND ?
                ORDER BY timestamp
            )
            SELECT COUNT(CASE WHEN gap_seconds > ? THEN 1 END) as significant_gaps
            FROM gaps
            WHERE prev_timestamp IS NOT NULL
            """

            # 파편화 임계값: timeframe의 1.5배 (유연한 기준)
            fragmentation_threshold = timeframe_seconds * 1.5

            result = self.repository._execute_query(
                fragmentation_query,
                (start_time.isoformat(), chunk_end.isoformat(), fragmentation_threshold)
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

        timeframe_seconds = self._get_timeframe_seconds(timeframe)

        # TimeUtils를 활용한 정확한 캔들 개수 계산
        base_count = self.time_utils.calculate_candle_count(api_start_time, end_time, timeframe)
        api_count = min(UPBIT_API_LIMIT, base_count + 1)  # +1: 안전 버퍼

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
            timeframe_seconds = self._get_timeframe_seconds(timeframe)

            connected_end_query = f"""
            WITH numbered_candles AS (
                SELECT
                    candle_date_time_utc,
                    timestamp,
                    ROW_NUMBER() OVER (ORDER BY timestamp) as row_num,
                    ? + (ROW_NUMBER() OVER (ORDER BY timestamp) - 1) * {timeframe_seconds} as expected_timestamp
                FROM {table_name}
                WHERE candle_date_time_utc >= ?
                    AND candle_date_time_utc <= ?
                ORDER BY timestamp
                LIMIT {UPBIT_API_LIMIT}
            )
            SELECT candle_date_time_utc
            FROM numbered_candles
            WHERE timestamp = expected_timestamp
            ORDER BY timestamp DESC
            LIMIT 1
            """

            chunk_end = min(
                end_time,
                start_time + timedelta(seconds=timeframe_seconds * (UPBIT_API_LIMIT - 1))
            )

            # timestamp 기반 쿼리를 위한 파라미터 준비
            start_timestamp = int(start_time.timestamp())

            result = self.repository._execute_query(
                connected_end_query,
                (start_timestamp, start_time.isoformat(), chunk_end.isoformat())
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
        timeframe_seconds = self._get_timeframe_seconds(timeframe)

        # 시작점 -1부터 200개 요청
        api_start = start_time - timedelta(seconds=timeframe_seconds)

        # TimeUtils를 활용한 정확한 캔들 개수 계산
        base_count = self.time_utils.calculate_candle_count(start_time, end_time, timeframe)
        api_count = min(UPBIT_API_LIMIT, base_count + 2)  # +2: 업비트 API 특성 고려 버퍼

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
