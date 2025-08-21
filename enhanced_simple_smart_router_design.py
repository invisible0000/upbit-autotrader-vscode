"""
Enhanced Simple Smart Router with Time Continuity Support
시간 연속성을 지원하는 향상된 Simple Smart Router 설계안
"""

from typing import List, Dict, Any, Optional, Union
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum

class ContinuityMode(Enum):
    """연속성 모드"""
    LATEST = "latest"           # 최신 데이터부터 (기본)
    FROM_TIME = "from_time"     # 지정 시간부터
    CONTINUOUS = "continuous"   # 시간 연속성 보장


@dataclass
class CandleRequest:
    """캔들 요청 사양"""
    symbol: str
    interval: str
    count: int

    # 🆕 시간 연속성 옵션
    continuity_mode: ContinuityMode = ContinuityMode.LATEST
    start_time: Optional[str] = None  # "2024-01-01T00:00:00"
    end_time: Optional[str] = None    # 종료 시간 (선택적)

    # 배치 처리 옵션
    auto_batch: bool = True           # 자동 배치 처리
    batch_size: int = 200            # 배치 크기
    batch_delay: float = 0.1         # 배치간 딜레이


class EnhancedSimpleSmartRouter:
    """시간 연속성을 지원하는 향상된 Simple Smart Router"""

    def __init__(self):
        self.api_client = None  # 실제 API 클라이언트

    async def get_candles_continuous(self, request: CandleRequest) -> List[Dict[str, Any]]:
        """시간 연속성을 보장하는 캔들 조회"""

        if request.continuity_mode == ContinuityMode.LATEST:
            return await self._get_latest_candles(request)
        elif request.continuity_mode == ContinuityMode.FROM_TIME:
            return await self._get_candles_from_time(request)
        elif request.continuity_mode == ContinuityMode.CONTINUOUS:
            return await self._get_continuous_candles(request)

    async def _get_continuous_candles(self, request: CandleRequest) -> List[Dict[str, Any]]:
        """완전한 시간 연속성을 보장하는 캔들 조회"""

        if not request.start_time:
            # 시작 시간이 없으면 현재부터 과거로
            end_time = datetime.now()
            start_time = end_time - timedelta(minutes=request.count)
            request.start_time = start_time.isoformat()

        all_candles = []
        current_to = request.end_time  # 최신부터 역순으로
        remaining_count = request.count

        while remaining_count > 0:
            batch_count = min(request.batch_size, remaining_count)

            # 배치 조회
            batch_candles = await self._fetch_candle_batch(
                symbol=request.symbol,
                interval=request.interval,
                count=batch_count,
                to=current_to
            )

            if not batch_candles:
                break

            # 시간 연속성 검증
            validated_candles = self._validate_batch_continuity(
                batch_candles, all_candles, request.start_time
            )

            all_candles.extend(validated_candles)
            remaining_count -= len(validated_candles)

            # 다음 배치의 시작 시간 설정 (마지막 캔들의 이전 시간)
            if validated_candles:
                last_candle_time = validated_candles[-1]['candle_date_time_kst']
                current_to = self._get_previous_candle_time(last_candle_time, request.interval)

            # 시작 시간에 도달하면 중단
            if self._reached_start_time(current_to, request.start_time):
                break

            await asyncio.sleep(request.batch_delay)

        # 시간순 정렬 (최신순 → 시간순)
        return sorted(all_candles, key=lambda x: x['candle_date_time_kst'])

    def _validate_batch_continuity(self, batch_candles: List[Dict],
                                   existing_candles: List[Dict],
                                   start_time: str) -> List[Dict]:
        """배치 시간 연속성 검증 및 필터링"""

        if not existing_candles:
            return batch_candles

        # 기존 캔들의 마지막 시간
        last_existing_time = existing_candles[-1]['candle_date_time_kst']

        validated = []
        for candle in batch_candles:
            candle_time = candle['candle_date_time_kst']

            # 중복 시간 제거
            if candle_time <= last_existing_time:
                continue

            # 시작 시간 이전 제거
            if candle_time < start_time:
                break

            validated.append(candle)

        return validated

    def _get_previous_candle_time(self, current_time: str, interval: str) -> str:
        """이전 캔들 시간 계산"""
        dt = datetime.fromisoformat(current_time.replace('T', ' '))

        # 인터벌에 따른 시간 차이
        interval_minutes = self._parse_interval_minutes(interval)
        previous_dt = dt - timedelta(minutes=interval_minutes)

        return previous_dt.strftime('%Y-%m-%dT%H:%M:%S')

    def _parse_interval_minutes(self, interval: str) -> int:
        """인터벌을 분으로 변환"""
        if interval.endswith('m'):
            return int(interval[:-1])
        elif interval.endswith('h'):
            return int(interval[:-1]) * 60
        elif interval.endswith('d'):
            return int(interval[:-1]) * 24 * 60
        else:
            return 1  # 기본 1분


# 🎯 사용 예시
async def usage_examples():
    """향상된 Smart Router 사용 예시"""

    router = EnhancedSimpleSmartRouter()

    # 1. 기본 사용 (기존과 동일)
    request_basic = CandleRequest(
        symbol="KRW-BTC",
        interval="1m",
        count=200
    )
    candles = await router.get_candles_continuous(request_basic)

    # 2. 시간 연속성 보장 (2000개)
    request_continuous = CandleRequest(
        symbol="KRW-BTC",
        interval="1m",
        count=2000,
        continuity_mode=ContinuityMode.CONTINUOUS,
        start_time="2024-08-20T00:00:00"  # 시작 시간 지정
    )
    continuous_candles = await router.get_candles_continuous(request_continuous)

    # 3. 특정 시간부터 수집
    request_from_time = CandleRequest(
        symbol="KRW-ETH",
        interval="5m",
        count=1000,
        continuity_mode=ContinuityMode.FROM_TIME,
        start_time="2024-08-15T09:00:00",
        end_time="2024-08-20T18:00:00"
    )
    time_range_candles = await router.get_candles_continuous(request_from_time)


# 🔧 SimpleSmartRouter 인터페이스 확장 예시
class SimpleSmartRouterEnhanced:
    """기존 SimpleSmartRouter에 추가할 메서드들"""

    async def get_candles_from_time(self, symbol: str, interval: str,
                                    start_time: str, count: int = 2000) -> List[Dict[str, Any]]:
        """지정 시간부터 연속된 캔들 조회 (편의 메서드)"""
        request = CandleRequest(
            symbol=symbol,
            interval=interval,
            count=count,
            continuity_mode=ContinuityMode.CONTINUOUS,
            start_time=start_time
        )
        return await self.get_candles_continuous(request)

    async def get_large_dataset(self, symbol: str, interval: str,
                                count: int, ensure_continuity: bool = True) -> List[Dict[str, Any]]:
        """대용량 데이터셋 조회 (시간 연속성 옵션)"""
        mode = ContinuityMode.CONTINUOUS if ensure_continuity else ContinuityMode.LATEST

        request = CandleRequest(
            symbol=symbol,
            interval=interval,
            count=count,
            continuity_mode=mode
        )
        return await self.get_candles_continuous(request)


# 📝 API 설계 요약
"""
기존: router.get_candles("KRW-BTC", "1m", 2000)  # 중복 가능성
새로운: router.get_candles_from_time("KRW-BTC", "1m", "2024-08-20T00:00:00", 2000)  # 연속성 보장

또는:
request = CandleRequest(
    symbol="KRW-BTC",
    interval="1m",
    count=2000,
    continuity_mode=ContinuityMode.CONTINUOUS,
    start_time="2024-08-20T00:00:00"
)
candles = await router.get_candles_continuous(request)
"""
