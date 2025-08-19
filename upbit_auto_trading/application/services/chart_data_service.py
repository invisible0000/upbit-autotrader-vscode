"""
차트 데이터 관리 애플리케이션 서비스 - Application Layer

DDD Application 계층:
- 차트 데이터 요청 및 조작
- 테스트 데이터 생성
- 실시간 업데이트 처리
- 백엔드 시스템 연동

Domain 서비스와 Infrastructure 계층 조율
"""

from typing import List, Optional, Protocol
from datetime import datetime, timedelta
import numpy as np

from upbit_auto_trading.infrastructure.logging import create_component_logger
from upbit_auto_trading.infrastructure.chart_viewer.db_integration_layer import CandleData
from upbit_auto_trading.domain.services.chart_state_service import (
    ChartStateService,
    ChartViewState,
    ChartPerformanceMetrics
)


class ChartDataRepository(Protocol):
    """차트 데이터 저장소 인터페이스"""

    async def get_candles(
        self,
        symbol: str,
        timeframe: str,
        count: int
    ) -> List[CandleData]:
        """캔들 데이터 조회"""
        ...

    async def get_latest_candle(
        self,
        symbol: str,
        timeframe: str
    ) -> Optional[CandleData]:
        """최신 캔들 조회"""
        ...


class RealtimeDataService(Protocol):
    """실시간 데이터 서비스 인터페이스"""

    async def subscribe_candle_updates(
        self,
        symbol: str,
        timeframe: str,
        callback
    ) -> None:
        """캔들 업데이트 구독"""
        ...

    async def unsubscribe_candle_updates(
        self,
        symbol: str,
        timeframe: str
    ) -> None:
        """캔들 업데이트 구독 해제"""
        ...


class ChartDataApplicationService:
    """
    차트 데이터 관리 애플리케이션 서비스

    핵심 책임:
    - 차트 데이터 CRUD 오케스트레이션
    - 테스트 데이터 생성
    - 실시간 데이터 구독 관리
    - 성능 모니터링
    """

    def __init__(
        self,
        chart_state_service: ChartStateService,
        data_repository: Optional[ChartDataRepository] = None,
        realtime_service: Optional[RealtimeDataService] = None
    ):
        self._logger = create_component_logger("ChartDataApplicationService")
        self._chart_state = chart_state_service
        self._data_repository = data_repository
        self._realtime_service = realtime_service

        # 실시간 구독 상태
        self._subscriptions: dict[str, bool] = {}

    async def initialize_chart(
        self,
        symbol: str,
        timeframe: str,
        initial_count: int = 200
    ) -> ChartViewState:
        """
        차트 초기화

        Args:
            symbol: 심볼 (예: "KRW-BTC")
            timeframe: 타임프레임 (예: "1m")
            initial_count: 초기 로드할 캔들 개수

        Returns:
            초기화된 차트 상태
        """
        self._logger.info(f"차트 초기화: {symbol} {timeframe} ({initial_count}개)")

        # 차트 상태 초기화
        state = self._chart_state.initialize_state(symbol, timeframe)

        try:
            # 초기 데이터 로드
            if self._data_repository:
                candles = await self._data_repository.get_candles(
                    symbol, timeframe, initial_count
                )
            else:
                # 테스트 데이터 생성
                candles = self._generate_test_data(symbol, timeframe, initial_count)

            # 상태 업데이트
            if candles:
                state = self._chart_state.update_candle_data(candles)
                self._logger.info(f"✅ 초기 데이터 로드 완료: {len(candles)}개")

            # 실시간 구독 시작
            await self._start_realtime_subscription(symbol, timeframe)

            return state

        except Exception as e:
            self._logger.error(f"차트 초기화 실패: {e}")
            raise

    async def change_symbol(self, symbol: str) -> ChartViewState:
        """심볼 변경"""
        current_state = self._chart_state.get_current_state()
        if not current_state:
            raise ValueError("차트가 초기화되지 않음")

        self._logger.info(f"심볼 변경: {current_state.symbol} → {symbol}")

        # 기존 구독 해제
        await self._stop_realtime_subscription(
            current_state.symbol,
            current_state.timeframe
        )

        # 새 심볼로 초기화
        return await self.initialize_chart(symbol, current_state.timeframe)

    async def change_timeframe(self, timeframe: str) -> ChartViewState:
        """타임프레임 변경"""
        current_state = self._chart_state.get_current_state()
        if not current_state:
            raise ValueError("차트가 초기화되지 않음")

        self._logger.info(f"타임프레임 변경: {current_state.timeframe} → {timeframe}")

        # 기존 구독 해제
        await self._stop_realtime_subscription(
            current_state.symbol,
            current_state.timeframe
        )

        # 새 타임프레임으로 초기화
        return await self.initialize_chart(current_state.symbol, timeframe)

    def update_zoom(self, zoom_factor: float, center_index: Optional[int] = None) -> ChartViewState:
        """줌 변경"""
        return self._chart_state.change_zoom(zoom_factor, center_index)

    def toggle_auto_scroll(self, enabled: bool) -> ChartViewState:
        """자동 스크롤 토글"""
        return self._chart_state.toggle_auto_scroll(enabled)

    def get_current_state(self) -> Optional[ChartViewState]:
        """현재 차트 상태 반환"""
        return self._chart_state.get_current_state()

    def get_visible_candles(self) -> List[CandleData]:
        """현재 표시 중인 캔들 데이터 반환"""
        return self._chart_state.get_visible_candles()

    def get_performance_metrics(self) -> ChartPerformanceMetrics:
        """성능 메트릭스 반환"""
        return self._chart_state.calculate_performance_metrics()

    async def refresh_data(self) -> ChartViewState:
        """데이터 새로고침"""
        current_state = self._chart_state.get_current_state()
        if not current_state:
            raise ValueError("차트가 초기화되지 않음")

        self._logger.info("데이터 새로고침")

        try:
            if self._data_repository:
                candles = await self._data_repository.get_candles(
                    current_state.symbol,
                    current_state.timeframe,
                    200  # 기본 200개
                )
            else:
                # 테스트 데이터 재생성
                candles = self._generate_test_data(
                    current_state.symbol,
                    current_state.timeframe,
                    200
                )

            if candles:
                return self._chart_state.update_candle_data(candles)

            return current_state

        except Exception as e:
            self._logger.error(f"데이터 새로고침 실패: {e}")
            raise

    async def _start_realtime_subscription(self, symbol: str, timeframe: str) -> None:
        """실시간 구독 시작"""
        subscription_key = f"{symbol}:{timeframe}"

        if self._realtime_service and subscription_key not in self._subscriptions:
            try:
                await self._realtime_service.subscribe_candle_updates(
                    symbol,
                    timeframe,
                    self._on_realtime_candle_update
                )
                self._subscriptions[subscription_key] = True
                self._logger.debug(f"실시간 구독 시작: {subscription_key}")
            except Exception as e:
                self._logger.warning(f"실시간 구독 실패: {e}")

    async def _stop_realtime_subscription(self, symbol: str, timeframe: str) -> None:
        """실시간 구독 해제"""
        subscription_key = f"{symbol}:{timeframe}"

        if self._realtime_service and subscription_key in self._subscriptions:
            try:
                await self._realtime_service.unsubscribe_candle_updates(
                    symbol,
                    timeframe
                )
                del self._subscriptions[subscription_key]
                self._logger.debug(f"실시간 구독 해제: {subscription_key}")
            except Exception as e:
                self._logger.warning(f"실시간 구독 해제 실패: {e}")

    def _on_realtime_candle_update(self, candle: CandleData) -> None:
        """실시간 캔들 업데이트 콜백"""
        try:
            current_state = self._chart_state.get_current_state()
            if not current_state:
                return

            # 심볼/타임프레임 일치 확인
            if (candle.symbol != current_state.symbol or
                candle.timeframe != current_state.timeframe):
                return

            # 기존 데이터와 비교
            candle_data = self._chart_state.get_candle_data()

            if not candle_data:
                # 첫 번째 캔들
                self._chart_state.add_realtime_candle(candle)
            elif candle.timestamp > candle_data[-1].timestamp:
                # 새로운 캔들
                self._chart_state.add_realtime_candle(candle)
            else:
                # 기존 캔들 업데이트
                self._chart_state.update_last_candle(candle)

        except Exception as e:
            self._logger.error(f"실시간 캔들 업데이트 처리 실패: {e}")

    def _generate_test_data(
        self,
        symbol: str,
        timeframe: str,
        count: int
    ) -> List[CandleData]:
        """테스트 데이터 생성"""
        self._logger.info(f"테스트 데이터 생성: {symbol} {timeframe} {count}개")

        # 타임프레임에 따른 시간 간격
        timeframe_minutes = {
            "1m": 1, "3m": 3, "5m": 5, "15m": 15, "30m": 30,
            "1h": 60, "4h": 240, "1d": 1440, "1w": 10080, "1M": 43200
        }

        interval_minutes = timeframe_minutes.get(timeframe, 1)

        # 현재 시간부터 역순으로 생성
        end_time = datetime.now()
        base_price = 45000000  # 기본 가격 (4500만원)

        candles = []
        for i in range(count):
            candle_time = end_time - timedelta(minutes=interval_minutes * (count - 1 - i))

            # 가격 변동 시뮬레이션 (랜덤 워크)
            price_change = np.random.normal(0, base_price * 0.01)  # 1% 변동
            base_price = max(base_price + price_change, base_price * 0.8)

            # OHLC 생성
            open_price = base_price
            high_price = open_price + abs(np.random.normal(0, base_price * 0.005))
            low_price = open_price - abs(np.random.normal(0, base_price * 0.005))
            close_price = open_price + np.random.normal(0, base_price * 0.008)

            # high, low 보정
            high_price = max(high_price, open_price, close_price)
            low_price = min(low_price, open_price, close_price)

            volume = np.random.uniform(0.1, 2.0)  # 0.1~2.0 BTC

            candle = CandleData(
                symbol=symbol,
                timestamp=candle_time,
                timeframe=timeframe,
                open_price=open_price,
                high_price=high_price,
                low_price=low_price,
                close_price=close_price,
                volume=volume,
                quote_volume=volume * close_price,
                trade_count=int(np.random.uniform(50, 200))
            )

            candles.append(candle)

        return candles

    async def cleanup(self) -> None:
        """리소스 정리"""
        self._logger.info("차트 데이터 서비스 정리")

        # 모든 실시간 구독 해제
        for subscription_key in list(self._subscriptions.keys()):
            symbol, timeframe = subscription_key.split(":")
            await self._stop_realtime_subscription(symbol, timeframe)

        self._subscriptions.clear()
