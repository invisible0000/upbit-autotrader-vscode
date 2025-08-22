"""
캔들 데이터 대용량 요청 자동 분할 시스템

🎯 실제 업비트 API 테스트 기반 리팩터링 (2025-01-22)
- 캔들 API: 200개 제한 + 단일 심볼만 → 분할 필요
- 티커 API: 100개+ 심볼 한번에 처리 가능 → 분할 불필요 (RequestSplitter 범위 외)
- 호가 API: 20개+ 심볼 한번에 처리 가능 → 분할 불필요 (RequestSplitter 범위 외)

캔들 요청의 API 제한사항을 고려하여 필요한 경우에만 분할하고
효율적인 처리 계획을 수립합니다.
"""

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import List, Optional, Tuple
from enum import Enum

from upbit_auto_trading.infrastructure.logging import create_component_logger


logger = create_component_logger("RequestSplitter")


class SplitStrategy(Enum):
    """분할 전략 - 캔들 데이터 전용"""
    TIME_BASED = "time_based"  # 시간 기반 분할 (캔들 데이터)
    COUNT_BASED = "count_based"  # 개수 기반 분할


@dataclass(frozen=True)
class SplitRequest:
    """분할된 캔들 요청 정보"""
    original_id: str
    split_index: int
    total_splits: int
    symbol: str
    timeframe: Optional[str] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    count: Optional[int] = None
    strategy: SplitStrategy = SplitStrategy.COUNT_BASED

    @property
    def split_id(self) -> str:
        """분할된 요청의 고유 ID"""
        return f"{self.original_id}_split_{self.split_index}"


class RequestSplitter:
    """캔들 데이터 요청 자동 분할기 - 실제 업비트 API 제한 기준"""

    # 🎯 실제 API 테스트 결과: 캔들만 분할 필요
    MAX_CANDLES_PER_REQUEST = 200       # 캔들: 200개 제한 (확인됨)
    # 티커, 호가는 다중 심볼 완전 지원 → 분할 불필요    # 타임프레임별 1개 캔들 당 시간 간격
    TIMEFRAME_INTERVALS = {
        "1m": timedelta(minutes=1),
        "3m": timedelta(minutes=3),
        "5m": timedelta(minutes=5),
        "15m": timedelta(minutes=15),
        "30m": timedelta(minutes=30),
        "1h": timedelta(hours=1),
        "4h": timedelta(hours=4),
        "1d": timedelta(days=1),
        "1w": timedelta(weeks=1),
        "1M": timedelta(days=30),  # 대략적인 월 간격
    }

    def __init__(self):
        self.logger = logger

    def should_split_candle_request(
        self,
        symbol: str,
        timeframe: str,
        count: Optional[int] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None
    ) -> bool:
        """캔들 요청 분할 필요성 판단"""

        # count 기반 요청 분할 검사
        if count and count > self.MAX_CANDLES_PER_REQUEST:
            self.logger.debug(
                f"Count-based split needed: {count} > {self.MAX_CANDLES_PER_REQUEST}",
                extra={"symbol": symbol, "timeframe": timeframe}
            )
            return True

        # 시간 범위 기반 요청 분할 검사 (200개 기준 통일)
        if start_time and end_time:
            period = end_time - start_time
            interval = self.TIMEFRAME_INTERVALS.get(timeframe)

            if interval:
                # 요청된 기간에 포함되는 예상 캔들 수 계산
                estimated_candles = int(period.total_seconds() / interval.total_seconds())

                if estimated_candles > self.MAX_CANDLES_PER_REQUEST:
                    self.logger.debug(
                        f"Time-based split needed: {estimated_candles} candles > {self.MAX_CANDLES_PER_REQUEST}",
                        extra={"symbol": symbol, "timeframe": timeframe, "period": str(period)}
                    )
                    return True

        return False

    def split_candle_request(
        self,
        request_id: str,
        symbol: str,
        timeframe: str,
        count: Optional[int] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None
    ) -> List[SplitRequest]:
        """캔들 요청을 분할"""

        if not self.should_split_candle_request(symbol, timeframe, count, start_time, end_time):
            # 분할 불필요한 경우 원본 요청 그대로 반환
            return [SplitRequest(
                original_id=request_id,
                split_index=0,
                total_splits=1,
                symbol=symbol,
                timeframe=timeframe,
                count=count,
                start_time=start_time,
                end_time=end_time,
                strategy=SplitStrategy.COUNT_BASED
            )]

        splits = []

        # Count 기반 분할
        if count and count > self.MAX_CANDLES_PER_REQUEST:
            splits = self._split_by_count(
                request_id, symbol, timeframe, count, start_time, end_time
            )

        # 시간 기반 분할
        elif start_time and end_time:
            splits = self._split_by_time(
                request_id, symbol, timeframe, start_time, end_time
            )

        self.logger.info(
            f"Split candle request into {len(splits)} parts",
            extra={
                "original_id": request_id,
                "symbol": symbol,
                "timeframe": timeframe,
                "total_splits": len(splits)
            }
        )

        return splits

    def _split_by_count(
        self,
        request_id: str,
        symbol: str,
        timeframe: str,
        count: int,
        start_time: Optional[datetime],
        end_time: Optional[datetime]
    ) -> List[SplitRequest]:
        """개수 기반 분할"""

        splits = []
        chunk_size = self.MAX_CANDLES_PER_REQUEST
        total_chunks = (count + chunk_size - 1) // chunk_size

        for i in range(total_chunks):
            split_count = min(chunk_size, count - i * chunk_size)

            splits.append(SplitRequest(
                original_id=request_id,
                split_index=i,
                total_splits=total_chunks,
                symbol=symbol,
                timeframe=timeframe,
                count=split_count,
                start_time=start_time,
                end_time=end_time,
                strategy=SplitStrategy.COUNT_BASED
            ))

        return splits

    def _split_by_time(
        self,
        request_id: str,
        symbol: str,
        timeframe: str,
        start_time: datetime,
        end_time: datetime
    ) -> List[SplitRequest]:
        """시간 기반 분할 - 200개 캔들 기준 통일"""

        splits = []
        interval = self.TIMEFRAME_INTERVALS.get(timeframe)

        if not interval:
            # 알 수 없는 타임프레임인 경우 기본값 사용
            self.logger.warning(f"Unknown timeframe: {timeframe}, using default split")
            return [SplitRequest(
                original_id=request_id,
                split_index=0,
                total_splits=1,
                symbol=symbol,
                timeframe=timeframe,
                start_time=start_time,
                end_time=end_time,
                strategy=SplitStrategy.TIME_BASED
            )]

        # 200개 캔들에 해당하는 시간 기간 계산
        max_period = interval * self.MAX_CANDLES_PER_REQUEST

        current_start = start_time
        split_index = 0

        # 전체 기간을 200개 캔들 단위로 나누어 분할
        temp_splits = []
        while current_start < end_time:
            current_end = min(current_start + max_period, end_time)

            temp_splits.append((current_start, current_end))
            current_start = current_end

            # 무한 루프 방지
            if len(temp_splits) > 1000:
                self.logger.warning(
                    "Too many time splits (>1000), limiting to prevent issues",
                    extra={"symbol": symbol, "timeframe": timeframe}
                )
                break

        total_splits = len(temp_splits)

        for split_start, split_end in temp_splits:
            splits.append(SplitRequest(
                original_id=request_id,
                split_index=split_index,
                total_splits=total_splits,
                symbol=symbol,
                timeframe=timeframe,
                start_time=split_start,
                end_time=split_end,
                strategy=SplitStrategy.TIME_BASED
            ))
            split_index += 1

        return splits

    def estimate_split_performance(
        self,
        splits: List[SplitRequest]
    ) -> Tuple[float, int]:
        """분할 성능 추정"""

        if not splits:
            return 0.0, 0

        # 분할 수에 따른 예상 처리 시간 (병렬 처리 고려)
        base_time_per_request = 0.5  # 기본 500ms per request
        parallel_factor = min(len(splits), 5)  # 최대 5개 병렬 처리

        estimated_time = (len(splits) / parallel_factor) * base_time_per_request
        total_api_calls = len(splits)

        return estimated_time, total_api_calls
