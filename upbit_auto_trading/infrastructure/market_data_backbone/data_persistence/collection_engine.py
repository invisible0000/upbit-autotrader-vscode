"""
데이터 수집 엔진 - 외부 API 통합 관리

기능:
1. 업비트 API 최적화 (200개 제한 기반)
2. 병렬 수집 및 배치 처리
3. 레이트 제한 준수 및 에러 처리
4. 중복 요청 제거 및 네트워크 효율성
"""

import asyncio
import time
from typing import List, Dict, Any
from datetime import datetime, timedelta
from dataclasses import dataclass

from upbit_auto_trading.infrastructure.logging import create_component_logger


@dataclass
class CollectionRequest:
    """수집 요청 정보"""
    symbol: str
    timeframe: str  # "1m", "5m", "1h", "1d" 등
    start_time: datetime
    end_time: datetime
    priority: int = 1  # 1=높음, 2=보통, 3=낮음


class APICollector:
    """API 수집 최적화"""

    def __init__(self, max_requests_per_second: float = 6.0):
        self.max_rps = max_requests_per_second  # 80% 안전 마진
        self.request_history = []
        self._logger = create_component_logger("APICollector")

    def can_make_request(self) -> bool:
        """레이트 제한 확인"""
        now = time.time()

        # 1초 이내 요청만 유지
        self.request_history = [
            req_time for req_time in self.request_history
            if now - req_time < 1.0
        ]

        return len(self.request_history) < self.max_rps

    def record_request(self) -> None:
        """요청 기록"""
        self.request_history.append(time.time())

    async def collect_candles(self, symbol: str, timeframe: str, count: int = 200) -> List[Dict[str, Any]]:
        """
        캔들 데이터 수집 (200개 제한 최적화)

        Args:
            symbol: 거래쌍 (예: "KRW-BTC")
            timeframe: 시간 단위 ("1", "5", "60" 등)
            count: 수집할 개수 (최대 200)
        """
        # 레이트 제한 대기
        while not self.can_make_request():
            await asyncio.sleep(0.1)

        self.record_request()

        try:
            # 실제 API 호출 시뮬레이션 (나중에 실제 구현으로 대체)
            await asyncio.sleep(0.1)  # 네트워크 지연 시뮬레이션

            # 모의 데이터 생성
            mock_data = []
            base_time = datetime.now()

            for i in range(min(count, 200)):
                timestamp = base_time - timedelta(minutes=i * int(timeframe))
                mock_data.append({
                    "timestamp": timestamp.isoformat(),
                    "opening_price": 50000000 + (i * 1000),
                    "high_price": 51000000 + (i * 1000),
                    "low_price": 49000000 + (i * 1000),
                    "trade_price": 50500000 + (i * 1000),
                    "candle_acc_trade_volume": 100.0 + i,
                    "candle_acc_trade_price": 5000000000 + (i * 1000000)
                })

            self._logger.debug(f"수집 완료: {symbol} {timeframe}분봉 {len(mock_data)}개")
            return mock_data

        except Exception as e:
            self._logger.error(f"수집 실패: {symbol} {timeframe}분봉 - {e}")
            raise


class RequestOptimizer:
    """요청 최적화 및 중복 제거"""

    def __init__(self):
        self.pending_requests = {}  # 중복 요청 추적
        self._logger = create_component_logger("RequestOptimizer")

    def deduplicate_requests(self, requests: List[CollectionRequest]) -> List[CollectionRequest]:
        """중복 요청 제거"""
        unique_requests = {}

        for request in requests:
            # 키 생성: symbol + timeframe + time_range
            key = f"{request.symbol}_{request.timeframe}_{request.start_time}_{request.end_time}"

            if key not in unique_requests:
                unique_requests[key] = request
            else:
                # 우선순위가 높은 것으로 대체
                if request.priority < unique_requests[key].priority:
                    unique_requests[key] = request

        deduplicated = list(unique_requests.values())
        removed_count = len(requests) - len(deduplicated)

        if removed_count > 0:
            self._logger.info(f"중복 요청 {removed_count}개 제거")

        return deduplicated

    def optimize_batch_size(self, requests: List[CollectionRequest]) -> List[List[CollectionRequest]]:
        """배치 크기 최적화"""
        # 우선순위별 정렬
        sorted_requests = sorted(requests, key=lambda x: (x.priority, x.symbol))

        # 심볼별 그룹화 (동일 심볼은 순차 처리가 효율적)
        symbol_groups = {}
        for request in sorted_requests:
            if request.symbol not in symbol_groups:
                symbol_groups[request.symbol] = []
            symbol_groups[request.symbol].append(request)

        # 배치 생성 (레이트 제한 고려)
        batches = []
        current_batch = []

        for symbol, symbol_requests in symbol_groups.items():
            for request in symbol_requests:
                current_batch.append(request)

                # 배치 크기 제한 (동시 요청 수 고려)
                if len(current_batch) >= 5:
                    batches.append(current_batch)
                    current_batch = []

        # 마지막 배치 추가
        if current_batch:
            batches.append(current_batch)

        self._logger.info(f"요청 최적화: {len(requests)}개 → {len(batches)}개 배치")
        return batches


class ErrorHandler:
    """에러 처리 및 재시도"""

    def __init__(self, max_retries: int = 3):
        self.max_retries = max_retries
        self.retry_delays = [1, 2, 5]  # 재시도 간격 (초)
        self._logger = create_component_logger("ErrorHandler")

    async def execute_with_retry(self, func, *args, **kwargs) -> Any:
        """재시도 로직을 포함한 함수 실행"""
        last_error = None

        for attempt in range(self.max_retries + 1):
            try:
                return await func(*args, **kwargs)

            except Exception as e:
                last_error = e

                if attempt < self.max_retries:
                    delay = self.retry_delays[min(attempt, len(self.retry_delays) - 1)]
                    self._logger.warning(f"시도 {attempt + 1} 실패, {delay}초 후 재시도: {e}")
                    await asyncio.sleep(delay)
                else:
                    self._logger.error(f"최대 재시도 횟수 초과: {e}")
                    raise last_error

        if last_error:
            raise last_error
        else:
            raise RuntimeError("알 수 없는 오류 발생")


class CollectionEngine:
    """데이터 수집 엔진 (통합 관리)"""

    def __init__(self):
        self.collector = APICollector()
        self.optimizer = RequestOptimizer()
        self.error_handler = ErrorHandler()
        self._logger = create_component_logger("CollectionEngine")

    async def collect_bulk_data(self, requests: List[CollectionRequest]) -> Dict[str, List[Dict[str, Any]]]:
        """
        대량 데이터 배치 수집

        Args:
            requests: 수집 요청 목록

        Returns:
            {symbol_timeframe: [candle_data...]}
        """
        self._logger.info(f"대량 수집 시작: {len(requests)}개 요청")

        # 1. 중복 제거 및 최적화
        optimized_requests = self.optimizer.deduplicate_requests(requests)
        batches = self.optimizer.optimize_batch_size(optimized_requests)

        results = {}

        # 2. 배치별 병렬 처리
        for batch_idx, batch in enumerate(batches):
            self._logger.debug(f"배치 {batch_idx + 1}/{len(batches)} 처리 중...")

            # 배치 내 병렬 실행
            tasks = []
            for request in batch:
                task = self.error_handler.execute_with_retry(
                    self.collector.collect_candles,
                    request.symbol,
                    request.timeframe,
                    200  # 최대 200개
                )
                tasks.append((request, task))

            # 병렬 실행 결과 수집
            for request, task in tasks:
                try:
                    data = await task
                    key = f"{request.symbol}_{request.timeframe}"
                    results[key] = data

                except Exception as e:
                    self._logger.error(f"수집 실패: {request.symbol} {request.timeframe} - {e}")
                    # 실패한 데이터는 빈 리스트로 처리
                    key = f"{request.symbol}_{request.timeframe}"
                    results[key] = []

            # 배치 간 간격 (레이트 제한 고려)
            if batch_idx < len(batches) - 1:
                await asyncio.sleep(0.2)

        self._logger.info(f"대량 수집 완료: {len(results)}개 결과")
        return results

    async def collect_single_timeframe(self, symbol: str, timeframe: str, days: int) -> List[Dict[str, Any]]:
        """
        단일 타임프레임 연속 수집 (200개 제한 극복)

        Args:
            symbol: 거래쌍
            timeframe: 시간 단위 (분 단위, "1", "5", "60" 등)
            days: 수집할 일수

        Returns:
            연속된 캔들 데이터
        """
        timeframe_minutes = int(timeframe)
        total_candles = (days * 24 * 60) // timeframe_minutes

        if total_candles <= 200:
            # 200개 이하면 1회 요청
            return await self.error_handler.execute_with_retry(
                self.collector.collect_candles,
                symbol, timeframe, total_candles
            )

        # 200개 초과 시 분할 수집
        all_data = []
        collected = 0

        while collected < total_candles:
            remaining = total_candles - collected
            batch_size = min(200, remaining)

            batch_data = await self.error_handler.execute_with_retry(
                self.collector.collect_candles,
                symbol, timeframe, batch_size
            )

            all_data.extend(batch_data)
            collected += len(batch_data)

            self._logger.debug(f"진행률: {collected}/{total_candles} ({collected / total_candles * 100:.1f}%)")

            # 중복 방지를 위한 시간 조정이 필요하지만,
            # 현재는 모의 구현이므로 생략

        self._logger.info(f"연속 수집 완료: {symbol} {timeframe}분봉 {len(all_data)}개")
        return all_data


# 팩토리 함수
def create_collection_engine() -> CollectionEngine:
    """수집 엔진 팩토리"""
    return CollectionEngine()
