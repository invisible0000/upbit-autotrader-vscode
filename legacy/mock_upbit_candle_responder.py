"""
MockUpbitCandleResponder - TimeUtils 기반 가짜 업비트 캔들 응답 생성기

실제 업비트 API 호출 없이 TimeUtils로 정확한 시간 계산을 통해
실제 응답과 동일한 형식의 Mock 캔들 데이터를 생성합니다.

Created: 2025-09-12
Purpose: 순차적 청크 처리 방식 테스트를 위한 Mock API
Features: 실제 업비트 응답 형식과 100% 동일, TimeUtils 완벽 연동
"""

from datetime import datetime, timezone, timedelta
from typing import List, Dict, Any, Optional
import random
from decimal import Decimal

from upbit_auto_trading.infrastructure.logging import create_component_logger
from upbit_auto_trading.infrastructure.market_data.candle.time_utils import TimeUtils

logger = create_component_logger("MockUpbitCandleResponder")


class MockUpbitCandleResponder:
    """
    TimeUtils 기반 가짜 업비트 캔들 응답 생성기

    특징:
    - 실제 API 호출 없이 TimeUtils로 시간 계산
    - 실제 업비트 응답 형식과 동일한 구조
    - 순차적 청크 테스트를 위한 완벽한 도구
    - KST/UTC 시간 변환 정확 처리
    - 가격 데이터는 현실적인 랜덤 생성
    """

    def __init__(self, seed: int = 42):
        """
        MockUpbitCandleResponder 초기화

        Args:
            seed: 랜덤 시드 (재현 가능한 테스트를 위해)
        """
        self.random = random.Random(seed)
        self.base_prices = {
            "KRW-BTC": 95_000_000,  # 9천5백만원
            "KRW-ETH": 4_200_000,   # 4백20만원
            "KRW-ADA": 580,         # 580원
            "KRW-DOT": 8_900,      # 8천9백원
        }
        logger.info("MockUpbitCandleResponder 초기화 완료 (seed={})".format(seed))

    def get_candles_minutes(
        self,
        market: str,
        unit: int = 1,
        count: int = 1,
        to: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        분봉 Mock 응답 생성

        Args:
            market: 마켓 코드 (예: 'KRW-BTC')
            unit: 분 단위 (1, 3, 5, 10, 15, 30, 60, 240)
            count: 캔들 개수 (1~200)
            to: 마지막 캔들 시각 (ISO 8601 형식)

        Returns:
            List[Dict]: 업비트 분봉 응답과 동일한 형식
        """
        timeframe = f"{unit}m"
        logger.debug(f"분봉 Mock 생성: {market} {timeframe}, count={count}, to={to}")

        return self._generate_candles(market, timeframe, count, to)

    def get_candles_hours(
        self,
        market: str,
        unit: int = 1,
        count: int = 1,
        to: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        시간봉 Mock 응답 생성

        Args:
            market: 마켓 코드
            unit: 시간 단위 (1, 4)
            count: 캔들 개수
            to: 마지막 캔들 시각

        Returns:
            List[Dict]: 업비트 시간봉 응답과 동일한 형식
        """
        timeframe = f"{unit}h"
        logger.debug(f"시간봉 Mock 생성: {market} {timeframe}, count={count}, to={to}")

        return self._generate_candles(market, timeframe, count, to)

    def get_candles_days(
        self,
        market: str,
        count: int = 1,
        to: Optional[str] = None,
        convertingPriceUnit: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        일봉 Mock 응답 생성

        Args:
            market: 마켓 코드
            count: 캔들 개수
            to: 마지막 캔들 시각
            convertingPriceUnit: 종가 변환 화폐 단위 (무시됨)

        Returns:
            List[Dict]: 업비트 일봉 응답과 동일한 형식
        """
        timeframe = "1d"
        logger.debug(f"일봉 Mock 생성: {market} {timeframe}, count={count}, to={to}")

        return self._generate_candles(market, timeframe, count, to)

    def get_candles_weeks(
        self,
        market: str,
        count: int = 1,
        to: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        주봉 Mock 응답 생성

        Args:
            market: 마켓 코드
            count: 캔들 개수
            to: 마지막 캔들 시각

        Returns:
            List[Dict]: 업비트 주봉 응답과 동일한 형식
        """
        timeframe = "1w"
        logger.debug(f"주봉 Mock 생성: {market} {timeframe}, count={count}, to={to}")

        return self._generate_candles(market, timeframe, count, to)

    def _generate_candles(
        self,
        market: str,
        timeframe: str,
        count: int,
        to: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        내부: TimeUtils 기반 캔들 데이터 생성

        Args:
            market: 마켓 코드
            timeframe: 타임프레임 (TimeUtils 형식)
            count: 캔들 개수
            to: 마지막 캔들 시각

        Returns:
            List[Dict]: 생성된 캔들 데이터 (업비트 형식)
        """
        # 1. 시작 시간 결정 (to가 없으면 현재 시간)
        if to is None:
            start_time = datetime.now(timezone.utc)
            logger.debug("to가 없어서 현재 시간 사용")
        else:
            # ISO 8601 문자열을 datetime으로 파싱
            try:
                start_time = datetime.fromisoformat(to.replace('Z', '+00:00'))
            except ValueError:
                # 업비트 형식 (2025-09-12T01:23:00) 처리
                start_time = datetime.fromisoformat(to).replace(tzinfo=timezone.utc)

        # 2. TimeUtils로 정렬된 시간 시퀀스 생성
        aligned_start = TimeUtils.align_to_candle_boundary(start_time, timeframe)
        time_sequence = []

        for i in range(count):
            candle_time = TimeUtils.get_aligned_time_by_ticks(
                base_time=aligned_start,
                timeframe=timeframe,
                tick_count=-i  # 과거 방향으로 생성
            )
            time_sequence.append(candle_time)

        # 3. 각 시간에 대해 캔들 데이터 생성
        candles = []
        base_price = self.base_prices.get(market, 50000)  # 기본값 5만원

        for i, candle_time in enumerate(time_sequence):
            candle_data = self._create_single_candle(
                market=market,
                candle_time=candle_time,
                timeframe=timeframe,
                base_price=base_price,
                index=i
            )
            candles.append(candle_data)

        logger.debug(f"✅ Mock 캔들 {len(candles)}개 생성 완료")
        return candles

    def _create_single_candle(
        self,
        market: str,
        candle_time: datetime,
        timeframe: str,
        base_price: int,
        index: int
    ) -> Dict[str, Any]:
        """
        단일 캔들 데이터 생성 (실제 업비트 응답 형식)

        Args:
            market: 마켓 코드
            candle_time: 캔들 시간 (UTC)
            timeframe: 타임프레임
            base_price: 기준 가격
            index: 캔들 인덱스 (가격 변동용)

        Returns:
            Dict: 업비트 캔들 응답 형식의 단일 캔들 데이터
        """
        # 가격 변동 (±5% 범위에서 랜덤)
        price_variation = 1 + (self.random.random() - 0.5) * 0.1  # ±5%
        current_price = int(base_price * price_variation)

        # OHLC 생성 (현실적인 관계 유지)
        high_variation = 1 + self.random.random() * 0.02  # +0~2%
        low_variation = 1 - self.random.random() * 0.02   # -0~2%

        opening_price = current_price
        high_price = int(current_price * high_variation)
        low_price = int(current_price * low_variation)
        trade_price = current_price  # 종가

        # 거래량 생성 (현실적인 범위)
        if "BTC" in market:
            volume = round(self.random.uniform(0.1, 50.0), 8)
            acc_trade_price = volume * trade_price
        else:
            volume = round(self.random.uniform(100, 50000), 8)
            acc_trade_price = volume * trade_price

        # KST 시간 계산 (UTC + 9시간)
        kst_time = candle_time + timedelta(hours=9)

        # timestamp (밀리초 Unix timestamp)
        timestamp = int(candle_time.timestamp() * 1000)

        # 타임프레임별 unit 설정
        unit_mapping = {
            "1m": 1, "3m": 3, "5m": 5, "10m": 10, "15m": 15, "30m": 30,
            "1h": 1, "4h": 4,
            "1d": 1, "1w": 1, "1M": 1
        }
        unit = unit_mapping.get(timeframe, 1)

        # 업비트 응답 형식과 동일한 구조
        candle_data = {
            "candle_date_time_utc": candle_time.strftime("%Y-%m-%dT%H:%M:%S"),
            "candle_date_time_kst": kst_time.strftime("%Y-%m-%dT%H:%M:%S"),
            "opening_price": float(opening_price),
            "high_price": float(high_price),
            "low_price": float(low_price),
            "trade_price": float(trade_price),
            "timestamp": timestamp,
            "candle_acc_trade_price": round(acc_trade_price, 8),
            "candle_acc_trade_volume": volume,
            "unit": unit
        }

        return candle_data

    def simulate_api_delay(self, min_ms: int = 10, max_ms: int = 100):
        """
        실제 API 지연 시뮬레이션 (선택적)

        Args:
            min_ms: 최소 지연 시간 (밀리초)
            max_ms: 최대 지연 시간 (밀리초)
        """
        import time
        delay_ms = self.random.uniform(min_ms, max_ms)
        time.sleep(delay_ms / 1000)
        logger.debug(f"API 지연 시뮬레이션: {delay_ms:.1f}ms")


# 편의 함수들
def create_mock_responder(seed: int = 42) -> MockUpbitCandleResponder:
    """Mock 응답기 생성 편의 함수"""
    return MockUpbitCandleResponder(seed=seed)


def test_mock_responder():
    """Mock 응답기 기본 테스트"""
    mock = create_mock_responder()

    print("🧪 MockUpbitCandleResponder 테스트")
    print("=" * 50)

    # 1분봉 테스트
    candles_1m = mock.get_candles_minutes("KRW-BTC", unit=1, count=5)
    print(f"1분봉 {len(candles_1m)}개 생성:")
    for i, candle in enumerate(candles_1m):
        print(f"  {i+1}. {candle['candle_date_time_utc']} - {candle['trade_price']:,.0f}원")

    # 일봉 테스트
    candles_1d = mock.get_candles_days("KRW-BTC", count=3)
    print(f"\n일봉 {len(candles_1d)}개 생성:")
    for i, candle in enumerate(candles_1d):
        print(f"  {i+1}. {candle['candle_date_time_utc']} - {candle['trade_price']:,.0f}원")

    print("\n✅ Mock 응답기 테스트 완료")


if __name__ == "__main__":
    test_mock_responder()
