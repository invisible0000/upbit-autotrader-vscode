"""
간소화된 WebSocket 클라이언트 프록시 v2
=====================================

데이터 풀 매니저를 사용하는 새로운 아키텍처
복잡한 콜백 시스템 대신 간단한 데이터 요청/응답 모델

특징:
- 콜백 없는 Pull 모델
- 중앙집중식 데이터 관리
- 클라이언트는 관심사만 등록
- 필요할 때 최신 데이터 요청
"""

from typing import List, Optional, Dict, Any, Set
from upbit_auto_trading.infrastructure.logging import create_component_logger

from .types import DataType, TickerEvent, OrderbookEvent, TradeEvent, CandleEvent
from .data_pool_manager import DataPoolManager
from .global_websocket_manager import get_global_websocket_manager


class SimpleWebSocketClient:
    """
    간소화된 WebSocket 클라이언트

    콜백 없는 Pull 모델로 WebSocket 데이터 사용
    """

    def __init__(self, client_id: str):
        """
        클라이언트 초기화

        Args:
            client_id: 클라이언트 고유 식별자
        """
        if not client_id or not isinstance(client_id, str):
            raise ValueError("client_id는 비어있지 않은 문자열이어야 합니다")

        self.client_id = client_id.strip()
        self.logger = create_component_logger(f"SimpleWSClient[{self.client_id}]")

        # 상태 관리
        self._is_active = False
        self._registered_interests: Set[DataType] = set()
        self._registered_symbols: Set[str] = set()

        # 관리자 참조 (lazy loading)
        self._manager = None
        self._data_pool = None

        self.logger.info(f"간소화된 WebSocket 클라이언트 생성: {client_id}")

    async def __aenter__(self):
        """async with 구문 지원"""
        await self._initialize()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """async with 종료 시 자동 정리"""
        await self.cleanup()

    async def _initialize(self) -> None:
        """클라이언트 초기화"""
        if self._is_active:
            return

        # 전역 관리자 가져오기
        self._manager = await get_global_websocket_manager()
        self._data_pool = self._manager.data_pool_manager  # 새로 추가될 속성

        self._is_active = True
        self.logger.info("클라이언트 초기화 완료")

    # =============================================================================
    # 관심사 등록 API (구독 대신)
    # =============================================================================

    async def register_interest(
        self,
        data_types: List[DataType],
        symbols: List[str]
    ) -> bool:
        """
        관심 데이터 등록

        Args:
            data_types: 관심 데이터 타입들
            symbols: 관심 심볼들

        Returns:
            bool: 등록 성공 여부
        """
        try:
            await self._initialize()

            data_type_set = set(data_types)
            symbol_set = set(symbols)

            # 데이터 풀에 관심사 등록
            changes = self._data_pool.register_client_interest(
                client_id=self.client_id,
                data_types=data_type_set,
                symbols=symbol_set
            )

            # 로컬 상태 업데이트
            self._registered_interests = data_type_set
            self._registered_symbols = symbol_set

            # 전역 관리자에 구독 변경 알림
            if changes:
                await self._notify_subscription_changes(changes)

            self.logger.info(f"관심사 등록: {len(data_types)}개 타입, {len(symbols)}개 심볼")
            return True

        except Exception as e:
            self.logger.error(f"관심사 등록 실패: {e}")
            return False

    async def unregister_interest(self) -> bool:
        """
        모든 관심사 해제

        Returns:
            bool: 해제 성공 여부
        """
        try:
            if not self._is_active or not self._data_pool:
                return True

            # 데이터 풀에서 관심사 해제
            changes = self._data_pool.unregister_client_interest(self.client_id)

            # 로컬 상태 초기화
            self._registered_interests.clear()
            self._registered_symbols.clear()

            # 전역 관리자에 구독 변경 알림
            if changes:
                await self._notify_subscription_changes(changes)

            self.logger.info("모든 관심사 해제 완료")
            return True

        except Exception as e:
            self.logger.error(f"관심사 해제 실패: {e}")
            return False

    async def _notify_subscription_changes(self, changes: Dict[DataType, Set[str]]) -> None:
        """구독 변경사항을 전역 관리자에 알림"""
        # TODO: 전역 관리자의 실제 WebSocket 구독 업데이트
        # self._manager.update_subscriptions(changes)
        self.logger.debug(f"구독 변경 알림: {len(changes)}개 타입")

    # =============================================================================
    # 데이터 조회 API (Pull 모델)
    # =============================================================================

    async def get_ticker_data(self, symbols: Optional[List[str]] = None) -> Dict[str, TickerEvent]:
        """
        최신 티커 데이터 조회

        Args:
            symbols: 조회할 심볼들 (None이면 등록된 모든 심볼)

        Returns:
            Dict[str, TickerEvent]: 심볼별 티커 데이터
        """
        if not await self._ensure_initialized():
            return {}

        raw_data = self._data_pool.get_latest_data(
            client_id=self.client_id,
            data_type=DataType.TICKER,
            symbols=symbols
        )

        # 타입 안전성 보장
        return {k: v for k, v in raw_data.items() if isinstance(v, TickerEvent)}

    async def get_orderbook_data(self, symbols: Optional[List[str]] = None) -> Dict[str, OrderbookEvent]:
        """
        최신 오더북 데이터 조회

        Args:
            symbols: 조회할 심볼들

        Returns:
            Dict[str, OrderbookEvent]: 심볼별 오더북 데이터
        """
        if not await self._ensure_initialized():
            return {}

        raw_data = self._data_pool.get_latest_data(
            client_id=self.client_id,
            data_type=DataType.ORDERBOOK,
            symbols=symbols
        )

        return {k: v for k, v in raw_data.items() if isinstance(v, OrderbookEvent)}

    async def get_trade_data(self, symbols: Optional[List[str]] = None) -> Dict[str, TradeEvent]:
        """
        최신 체결 데이터 조회

        Args:
            symbols: 조회할 심볼들

        Returns:
            Dict[str, TradeEvent]: 심볼별 체결 데이터
        """
        if not await self._ensure_initialized():
            return {}

        raw_data = self._data_pool.get_latest_data(
            client_id=self.client_id,
            data_type=DataType.TRADE,
            symbols=symbols
        )

        return {k: v for k, v in raw_data.items() if isinstance(v, TradeEvent)}

    async def get_candle_data(
        self,
        symbols: Optional[List[str]] = None,
        unit: int = 1
    ) -> Dict[str, CandleEvent]:
        """
        최신 캔들 데이터 조회

        Args:
            symbols: 조회할 심볼들
            unit: 캔들 단위 (0, 1, 3, 5, 15, 30, 60, 240)

        Returns:
            Dict[str, CandleEvent]: 심볼별 캔들 데이터
        """
        if not await self._ensure_initialized():
            return {}

        # 캔들 타입 결정
        candle_type = {
            0: DataType.CANDLE_1S,  # 1초봉
            1: DataType.CANDLE_1M,
            3: DataType.CANDLE_3M,
            5: DataType.CANDLE_5M,
            15: DataType.CANDLE_15M,
            30: DataType.CANDLE_30M,
            60: DataType.CANDLE_60M,
            240: DataType.CANDLE_240M,
        }.get(unit, DataType.CANDLE_1M)

        raw_data = self._data_pool.get_latest_data(
            client_id=self.client_id,
            data_type=candle_type,
            symbols=symbols
        )

        return {k: v for k, v in raw_data.items() if isinstance(v, CandleEvent)}

    # =============================================================================
    # 히스토리 데이터 조회
    # =============================================================================

    async def get_ticker_history(
        self,
        symbol: str,
        limit: int = 100
    ) -> List[TickerEvent]:
        """
        티커 히스토리 조회

        Args:
            symbol: 심볼
            limit: 최대 조회 개수

        Returns:
            List[TickerEvent]: 티커 히스토리
        """
        if not await self._ensure_initialized():
            return []

        raw_data = self._data_pool.get_data_history(
            client_id=self.client_id,
            data_type=DataType.TICKER,
            symbol=symbol,
            limit=limit
        )

        return [event for event in raw_data if isinstance(event, TickerEvent)]

    # =============================================================================
    # 편의 메서드
    # =============================================================================

    async def get_latest_price(self, symbol: str) -> Optional[float]:
        """
        심볼의 최신 가격 조회

        Args:
            symbol: 심볼 (예: "KRW-BTC")

        Returns:
            Optional[float]: 최신 가격 (없으면 None)
        """
        ticker_data = await self.get_ticker_data([symbol])

        if symbol in ticker_data:
            return float(ticker_data[symbol].trade_price)
        return None

    async def get_multiple_prices(self, symbols: List[str]) -> Dict[str, float]:
        """
        여러 심볼의 최신 가격 일괄 조회

        Args:
            symbols: 심볼 리스트

        Returns:
            Dict[str, float]: 심볼별 최신 가격
        """
        ticker_data = await self.get_ticker_data(symbols)

        return {
            symbol: float(event.trade_price)
            for symbol, event in ticker_data.items()
        }

    # =============================================================================
    # 상태 조회
    # =============================================================================

    async def get_registration_status(self) -> Dict[str, Any]:
        """등록 상태 조회"""
        return {
            'client_id': self.client_id,
            'is_active': self._is_active,
            'registered_data_types': [dt.value for dt in self._registered_interests],
            'registered_symbols': list(self._registered_symbols),
            'total_symbols': len(self._registered_symbols)
        }

    async def is_symbol_available(self, symbol: str) -> bool:
        """심볼 데이터 이용 가능 여부 확인"""
        if not await self._ensure_initialized():
            return False

        ticker_data = await self.get_ticker_data([symbol])
        return symbol in ticker_data

    # =============================================================================
    # 내부 메서드
    # =============================================================================

    async def _ensure_initialized(self) -> bool:
        """초기화 확인"""
        if not self._is_active:
            await self._initialize()
        return self._is_active and self._data_pool is not None

    async def cleanup(self) -> None:
        """리소스 정리"""
        if not self._is_active:
            return

        self.logger.info(f"클라이언트 정리 시작: {self.client_id}")

        try:
            # 관심사 해제
            await self.unregister_interest()

            self._is_active = False
            self.logger.info(f"클라이언트 정리 완료: {self.client_id}")

        except Exception as e:
            self.logger.error(f"클라이언트 정리 중 오류: {e}")


# =============================================================================
# 편의 함수들
# =============================================================================

async def create_simple_websocket_client(client_id: str) -> SimpleWebSocketClient:
    """
    간소화된 WebSocket 클라이언트 생성

    Args:
        client_id: 클라이언트 식별자

    Returns:
        SimpleWebSocketClient: 초기화된 클라이언트
    """
    client = SimpleWebSocketClient(client_id)
    await client._initialize()
    return client


async def quick_price_check(symbols: List[str]) -> Dict[str, float]:
    """
    빠른 가격 체크 (일회성 사용)

    Args:
        symbols: 심볼 리스트

    Returns:
        Dict[str, float]: 심볼별 최신 가격
    """
    async with SimpleWebSocketClient("quick_check") as client:
        # 티커 관심사 등록
        await client.register_interest([DataType.TICKER], symbols)

        # 잠시 대기 (데이터 수신 대기)
        import asyncio
        await asyncio.sleep(0.1)

        # 가격 조회
        return await client.get_multiple_prices(symbols)


# =============================================================================
# 사용 예시
# =============================================================================

async def example_usage():
    """간소화된 클라이언트 사용 예시"""

    # 클라이언트 생성 및 관심사 등록
    async with SimpleWebSocketClient("chart_main") as client:
        # 관심 데이터 등록
        await client.register_interest(
            data_types=[DataType.TICKER, DataType.ORDERBOOK],
            symbols=["KRW-BTC", "KRW-ETH", "KRW-XRP"]
        )

        # 잠시 대기 (데이터 축적)
        import asyncio
        await asyncio.sleep(1.0)

        # 최신 가격 조회
        prices = await client.get_multiple_prices(["KRW-BTC", "KRW-ETH"])
        print(f"최신 가격: {prices}")

        # 오더북 조회
        orderbooks = await client.get_orderbook_data(["KRW-BTC"])
        print(f"오더북: {len(orderbooks)}개")

        # 히스토리 조회
        history = await client.get_ticker_history("KRW-BTC", limit=10)
        print(f"히스토리: {len(history)}개")


if __name__ == "__main__":
    import asyncio
    asyncio.run(example_usage())
