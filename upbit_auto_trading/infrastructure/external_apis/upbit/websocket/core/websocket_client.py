"""
WebSocket v6.0 통합 클라이언트
===========================

사용자를 위한 유일한 WebSocket 인터페이스
- 내부 복잡성 완전 숨김
- 컨텍스트 매니저 지원
- 타입 안전성 보장
- WeakRef 자동 정리
"""

import asyncio
import weakref
import time
from typing import List, Callable, Optional, Dict, Any

from upbit_auto_trading.infrastructure.logging import create_component_logger

from .websocket_types import (
    TickerEvent, OrderbookEvent, TradeEvent, CandleEvent, MyOrderEvent, MyAssetEvent,
    SubscriptionSpec, DataType, HealthStatus, BaseWebSocketEvent
)
from .websocket_manager import get_websocket_manager


class WebSocketClient:
    """
    WebSocket v6.0 통합 클라이언트

    사용자가 사용할 유일한 WebSocket 인터페이스
    내부적으로 WebSocketManager에 모든 요청을 위임
    """

    def __init__(self, component_id: str):
        """
        클라이언트 초기화

        Args:
            component_id: 컴포넌트 고유 식별자 (예: "chart_btc", "orderbook_main")
        """
        if not component_id or not isinstance(component_id, str):
            raise ValueError("component_id는 비어있지 않은 문자열이어야 합니다")

        self.component_id = component_id.strip()
        self.logger = create_component_logger(f"WSClient[{self.component_id}]")

        # 내부 상태
        self._manager = None
        self._subscriptions: Dict[str, SubscriptionSpec] = {}
        self._callbacks: Dict[str, Callable] = {}
        self._created_at = time.time()
        self._is_active = True

        # WeakRef 기반 자동 정리
        self._weakref = weakref.ref(self, self._cleanup_on_gc)

        self.logger.info(f"WebSocket 클라이언트 생성: {self.component_id}")

    async def __aenter__(self):
        """async with 구문 지원"""
        await self._ensure_manager()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """async with 종료 시 자동 정리"""
        await self.cleanup()

    # ================================================================
    # Public 데이터 구독
    # ================================================================

    async def subscribe_ticker(
        self,
        symbols: List[str],
        callback: Callable[[TickerEvent], None]
    ) -> bool:
        """
        현재가 구독

        Args:
            symbols: 구독할 심볼 리스트 (예: ["KRW-BTC", "KRW-ETH"])
            callback: 데이터 수신 콜백 함수

        Returns:
            bool: 구독 성공 여부
        """
        return await self._subscribe_data(
            data_type=DataType.TICKER,
            symbols=symbols,
            callback=callback
        )

    async def subscribe_orderbook(
        self,
        symbols: List[str],
        callback: Callable[[OrderbookEvent], None]
    ) -> bool:
        """
        호가 구독

        Args:
            symbols: 구독할 심볼 리스트
            callback: 데이터 수신 콜백 함수

        Returns:
            bool: 구독 성공 여부
        """
        return await self._subscribe_data(
            data_type=DataType.ORDERBOOK,
            symbols=symbols,
            callback=callback
        )

    async def subscribe_trade(
        self,
        symbols: List[str],
        callback: Callable[[TradeEvent], None]
    ) -> bool:
        """
        체결 구독

        Args:
            symbols: 구독할 심볼 리스트
            callback: 데이터 수신 콜백 함수

        Returns:
            bool: 구독 성공 여부
        """
        return await self._subscribe_data(
            data_type=DataType.TRADE,
            symbols=symbols,
            callback=callback
        )

    async def subscribe_candle(
        self,
        symbols: List[str],
        callback: Callable[[CandleEvent], None],
        unit: str = "1m"
    ) -> bool:
        """
        캔들 구독

        Args:
            symbols: 구독할 심볼 리스트
            callback: 데이터 수신 콜백 함수
            unit: 캔들 단위 (1m, 5m, 15m, 30m, 60m, 240m)

        Returns:
            bool: 구독 성공 여부
        """
        # 캔들 타입 매핑
        candle_type_map = {
            "1m": DataType.CANDLE_1M,
            "3m": DataType.CANDLE_3M,
            "5m": DataType.CANDLE_5M,
            "10m": DataType.CANDLE_10M,
            "15m": DataType.CANDLE_15M,
            "30m": DataType.CANDLE_30M,
            "60m": DataType.CANDLE_60M,
            "240m": DataType.CANDLE_240M
        }

        data_type = candle_type_map.get(unit, DataType.CANDLE_1M)

        return await self._subscribe_data(
            data_type=data_type,
            symbols=symbols,
            callback=callback,
            unit=unit
        )

    # ================================================================
    # Private 데이터 구독 (인증 필요)
    # ================================================================

    async def subscribe_my_order(
        self,
        callback: Callable[[MyOrderEvent], None]
    ) -> bool:
        """
        내 주문 구독 (Private)

        Args:
            callback: 데이터 수신 콜백 함수

        Returns:
            bool: 구독 성공 여부
        """
        return await self._subscribe_data(
            data_type=DataType.MYORDER,
            symbols=[],  # Private 데이터는 심볼 불필요
            callback=callback
        )

    async def subscribe_my_asset(
        self,
        callback: Callable[[MyAssetEvent], None]
    ) -> bool:
        """
        내 자산 구독 (Private)

        Args:
            callback: 데이터 수신 콜백 함수

        Returns:
            bool: 구독 성공 여부
        """
        return await self._subscribe_data(
            data_type=DataType.MYASSET,
            symbols=[],  # Private 데이터는 심볼 불필요
            callback=callback
        )

    # ================================================================
    # 내부 구현
    # ================================================================

    async def _subscribe_data(
        self,
        data_type: DataType,
        symbols: List[str],
        callback: Any,  # 다양한 타입의 콜백을 받기 위해 Any 사용
        unit: Optional[str] = None
    ) -> bool:
        """내부 구독 처리"""
        try:
            await self._ensure_manager()

            # 구독 스펙 생성
            subscription_spec = SubscriptionSpec(
                data_type=data_type,
                symbols=symbols,
                unit=unit
            )

            # 구독 키 생성
            sub_key = f"{data_type.value}_{hash(tuple(symbols))}_{unit or ''}"

            # 기존 구독 확인
            if sub_key in self._subscriptions:
                self.logger.warning(f"이미 구독 중인 데이터: {sub_key}")
                return False

            # 구독 등록
            self._subscriptions[sub_key] = subscription_spec
            self._callbacks[sub_key] = callback

            # 매니저에 등록 (모든 구독을 한 번에 전달)
            await self._register_with_manager()

            self.logger.info(f"구독 성공: {data_type.value} {symbols}")
            return True

        except Exception as e:
            self.logger.error(f"구독 실패: {e}")
            return False

    async def _ensure_manager(self) -> None:
        """매니저 인스턴스 확보"""
        if not self._manager:
            self._manager = await get_websocket_manager()

    async def _register_with_manager(self) -> None:
        """매니저에 컴포넌트 등록"""
        if not self._manager:
            return

        # 모든 구독 스펙 수집
        all_subscriptions = list(self._subscriptions.values())

        if not all_subscriptions:
            return

        # 매니저에 등록
        await self._manager.register_component(
            component_id=self.component_id,
            component_ref=self,
            subscriptions=all_subscriptions
        )

    def _event_matches_subscription(self, event: BaseWebSocketEvent, spec: SubscriptionSpec) -> bool:
        """이벤트가 구독 스펙과 일치하는지 확인"""
        # 타입 확인
        if isinstance(event, TickerEvent) and spec.data_type == DataType.TICKER:
            return not spec.symbols or event.symbol in spec.symbols
        elif isinstance(event, OrderbookEvent) and spec.data_type == DataType.ORDERBOOK:
            return not spec.symbols or event.symbol in spec.symbols
        elif isinstance(event, TradeEvent) and spec.data_type == DataType.TRADE:
            return not spec.symbols or event.symbol in spec.symbols
        elif isinstance(event, CandleEvent) and spec.data_type.value.startswith("candle"):
            return not spec.symbols or event.symbol in spec.symbols
        elif isinstance(event, MyOrderEvent) and spec.data_type == DataType.MYORDER:
            return True  # Private 데이터는 심볼 필터링 없음
        elif isinstance(event, MyAssetEvent) and spec.data_type == DataType.MYASSET:
            return True  # Private 데이터는 심볼 필터링 없음

        return False

    # ================================================================
    # 상태 조회
    # ================================================================

    async def get_health_status(self) -> Optional[HealthStatus]:
        """WebSocket 연결 상태 조회"""
        try:
            await self._ensure_manager()
            if self._manager:
                return self._manager.get_health_status()
            return None
        except Exception as e:
            self.logger.error(f"상태 조회 실패: {e}")
            return None

    async def is_connected(self) -> bool:
        """연결 상태 확인"""
        try:
            status = await self.get_health_status()
            return status is not None and status.status == "healthy"
        except Exception:
            return False

    def get_subscription_count(self) -> int:
        """현재 구독 수"""
        return len(self._subscriptions)

    def get_subscribed_symbols(self) -> List[str]:
        """구독 중인 심볼 목록"""
        symbols = set()
        for spec in self._subscriptions.values():
            symbols.update(spec.symbols)
        return list(symbols)

    async def get_rate_limiter_status(self) -> Optional[Dict[str, Any]]:
        """Rate Limiter 상태 조회"""
        try:
            await self._ensure_manager()
            if self._manager and hasattr(self._manager, 'get_rate_limiter_status'):
                return self._manager.get_rate_limiter_status()
            return None
        except Exception as e:
            self.logger.error(f"Rate Limiter 상태 조회 실패: {e}")
            return None

    # ================================================================
    # 정리
    # ================================================================

    async def cleanup(self) -> None:
        """리소스 정리"""
        try:
            if not self._is_active:
                return

            self._is_active = False

            # 매니저에서 구독 해제
            if self._manager:
                await self._manager.unregister_component(self.component_id)

            # 내부 상태 정리
            self._subscriptions.clear()
            self._callbacks.clear()

            self.logger.info(f"WebSocket 클라이언트 정리 완료: {self.component_id}")

        except Exception as e:
            self.logger.error(f"정리 오류: {e}")

    def _cleanup_on_gc(self, weakref_obj) -> None:
        """GC 시 자동 정리 (WeakRef 콜백)"""
        # 비동기 정리를 위한 태스크 생성
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                loop.create_task(self.cleanup())
        except Exception:
            # 이벤트 루프가 없는 경우 무시
            pass

    @property
    def is_active(self) -> bool:
        """활성 상태 확인"""
        return self._is_active

    @property
    def uptime_seconds(self) -> float:
        """클라이언트 가동 시간"""
        return time.time() - self._created_at


# ================================================================
# 편의 함수
# ================================================================

def create_websocket_client(component_id: str) -> WebSocketClient:
    """WebSocket 클라이언트 생성 편의 함수"""
    return WebSocketClient(component_id)


async def quick_ticker_subscription(
    component_id: str,
    symbols: List[str],
    callback: Callable[[TickerEvent], None]
) -> WebSocketClient:
    """빠른 현재가 구독 설정"""
    client = WebSocketClient(component_id)
    await client.subscribe_ticker(symbols, callback)
    return client
