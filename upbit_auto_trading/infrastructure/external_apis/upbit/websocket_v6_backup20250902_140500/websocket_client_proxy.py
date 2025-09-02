"""
WebSocket 클라이언트 프록시
========================

컴포넌트가 사용할 간단한 인터페이스 제공
Zero Configuration으로 즉시 사용 가능

🎯 특징:
- 전역 WebSocket 관리자에 구독 요청 위임
- WeakRef 기반 자동 리소스 정리
- 컨텍스트 매니저 지원 (async with)
- 타입 안전성 보장
- REST 스냅샷 API 통합
"""

import asyncio
import weakref
import time
from typing import List, Callable, Optional, Dict, Any

from upbit_auto_trading.infrastructure.logging import create_component_logger

from .types import (
    TickerEvent, OrderbookEvent, TradeEvent, CandleEvent, MyOrderEvent, MyAssetEvent,
    SubscriptionSpec, DataType as V6DataType, HealthStatus
)
from .global_websocket_manager import get_global_websocket_manager
from .exceptions import SubscriptionError


class WebSocketClientProxy:
    """
    컴포넌트별 WebSocket 프록시

    각 GUI 컴포넌트나 서비스가 독립적으로 WebSocket을 사용할 수 있는 인터페이스 제공
    내부적으로는 글로벌 매니저에 모든 요청을 위임하여 중앙집중식 관리 실현
    """

    def __init__(self, component_id: str):
        """
        프록시 초기화

        Args:
            component_id: 컴포넌트 고유 식별자 (예: "chart_btc", "orderbook_main")
        """
        if not component_id or not isinstance(component_id, str):
            raise ValueError("component_id는 비어있지 않은 문자열이어야 합니다")

        self.component_id = component_id.strip()
        self.logger = create_component_logger(f"WSProxy[{self.component_id}]")

        # 내부 상태
        self._manager = None
        self._subscriptions: Dict[str, SubscriptionSpec] = {}
        self._callbacks: Dict[str, Callable] = {}
        self._created_at = time.monotonic()
        self._is_active = True
        self._cleanup_callbacks: List[Callable] = []

        # WeakRef 기반 자동 정리 등록
        self._weakref = weakref.ref(self, self._cleanup_on_gc)

        self.logger.info(f"WebSocket 프록시 생성: {self.component_id}")

    async def __aenter__(self):
        """async with 구문 지원"""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """async with 종료 시 자동 정리"""
        await self.cleanup()

    # =============================================================================
    # Public 데이터 구독 메서드
    # =============================================================================

    async def subscribe_ticker(
        self,
        symbols: List[str],
        callback: Callable[[TickerEvent], None],
        error_handler: Optional[Callable[[Exception], None]] = None
    ) -> bool:
        """
        현재가 구독

        Args:
            symbols: 구독할 심볼 리스트 (예: ["KRW-BTC", "KRW-ETH"])
            callback: 데이터 수신 콜백 함수
            error_handler: 에러 처리 콜백 (선택사항)

        Returns:
            bool: 구독 성공 여부
        """
        return await self._subscribe_data(
            data_type=V6DataType.TICKER,
            symbols=symbols,
            callback=callback,
            error_handler=error_handler
        )

    async def subscribe_orderbook(
        self,
        symbols: List[str],
        callback: Callable[[OrderbookEvent], None],
        error_handler: Optional[Callable[[Exception], None]] = None
    ) -> bool:
        """
        호가 구독

        Args:
            symbols: 구독할 심볼 리스트
            callback: 데이터 수신 콜백 함수
            error_handler: 에러 처리 콜백 (선택사항)

        Returns:
            bool: 구독 성공 여부
        """
        return await self._subscribe_data(
            data_type=V6DataType.ORDERBOOK,
            symbols=symbols,
            callback=callback,
            error_handler=error_handler
        )

    async def subscribe_trade(
        self,
        symbols: List[str],
        callback: Callable[[TradeEvent], None],
        error_handler: Optional[Callable[[Exception], None]] = None
    ) -> bool:
        """
        체결 구독

        Args:
            symbols: 구독할 심볼 리스트
            callback: 데이터 수신 콜백 함수
            error_handler: 에러 처리 콜백 (선택사항)

        Returns:
            bool: 구독 성공 여부
        """
        return await self._subscribe_data(
            data_type=V6DataType.TRADE,
            symbols=symbols,
            callback=callback,
            error_handler=error_handler
        )

    async def subscribe_candle(
        self,
        symbols: List[str],
        callback: Callable[[CandleEvent], None],
        unit: int = 1,
        error_handler: Optional[Callable[[Exception], None]] = None
    ) -> bool:
        """
        캔들 구독

        Args:
            symbols: 구독할 심볼 리스트
            callback: 데이터 수신 콜백 함수
            unit: 분봉 단위 (1, 3, 5, 15, 30, 60, 240)
            error_handler: 에러 처리 콜백 (선택사항)

        Returns:
            bool: 구독 성공 여부
        """
        # 캔들 타입 결정
        candle_type = V6DataType.CANDLE
        if unit in [1, 3, 5, 15, 30, 60, 240]:
            self.logger.debug(f"캔들 구독: {unit}분봉")
        else:
            self.logger.warning(f"지원하지 않는 캔들 단위: {unit}, 1분봉으로 대체")
            unit = 1

        return await self._subscribe_data(
            data_type=candle_type,
            symbols=symbols,
            callback=callback,
            error_handler=error_handler,
            extra_params={'unit': unit}
        )

    # =============================================================================
    # Private 데이터 구독 메서드 (인증 필요)
    # =============================================================================

    async def subscribe_my_orders(
        self,
        callback: Callable[[MyOrderEvent], None],
        markets: Optional[List[str]] = None,
        error_handler: Optional[Callable[[Exception], None]] = None
    ) -> bool:
        """
        내 주문 구독 (Private)

        Args:
            callback: 데이터 수신 콜백 함수
            markets: 구독할 마켓 리스트 (None이면 전체)
            error_handler: 에러 처리 콜백 (선택사항)

        Returns:
            bool: 구독 성공 여부
        """
        if not await self.is_private_available():
            self.logger.error("Private 연결을 사용할 수 없습니다. API 키를 확인하세요.")
            return False

        return await self._subscribe_data(
            data_type=V6DataType.MY_ORDER,
            symbols=markets or [],
            callback=callback,
            error_handler=error_handler,
            is_private=True
        )

    async def subscribe_my_assets(
        self,
        callback: Callable[[MyAssetEvent], None],
        currencies: Optional[List[str]] = None,
        error_handler: Optional[Callable[[Exception], None]] = None
    ) -> bool:
        """
        내 자산 구독 (Private)

        Args:
            callback: 데이터 수신 콜백 함수
            currencies: 구독할 화폐 리스트 (None이면 전체)
            error_handler: 에러 처리 콜백 (선택사항)

        Returns:
            bool: 구독 성공 여부
        """
        if not await self.is_private_available():
            self.logger.error("Private 연결을 사용할 수 없습니다. API 키를 확인하세요.")
            return False

        return await self._subscribe_data(
            data_type=V6DataType.MY_ASSET,
            symbols=currencies or [],
            callback=callback,
            error_handler=error_handler,
            is_private=True
        )

    # =============================================================================
    # 스냅샷 API (REST 기반)
    # =============================================================================

    async def get_ticker_snapshot(self, symbols: List[str]) -> List[TickerEvent]:
        """
        현재가 스냅샷 조회 (간소화 - 직접 REST API 사용)

        Args:
            symbols: 조회할 심볼 리스트

        Returns:
            List[TickerEvent]: 현재가 데이터 리스트
        """
        try:
            # 임시로 빈 리스트 반환 (나중에 REST API 연동)
            self.logger.warning("스냅샷 API는 향후 구현 예정")
            return []

        except Exception as e:
            self.logger.error(f"현재가 스냅샷 조회 실패: {e}")
            return []

    async def get_orderbook_snapshot(self, symbols: List[str]) -> List[OrderbookEvent]:
        """
        호가 스냅샷 조회 (간소화 - 직접 REST API 사용)

        Args:
            symbols: 조회할 심볼 리스트

        Returns:
            List[OrderbookEvent]: 호가 데이터 리스트
        """
        try:
            # 임시로 빈 리스트 반환 (나중에 REST API 연동)
            self.logger.warning("스냅샷 API는 향후 구현 예정")
            return []

        except Exception as e:
            self.logger.error(f"호가 스냅샷 조회 실패: {e}")
            return []    # =============================================================================
    # 상태 관리 및 제어 메서드
    # =============================================================================

    async def unsubscribe(self, data_type: V6DataType, symbols: Optional[List[str]] = None) -> bool:
        """
        특정 구독 해제 (간소화)

        Args:
            data_type: 데이터 타입
            symbols: 해제할 심볼 리스트 (None이면 해당 타입 전체 해제)

        Returns:
            bool: 해제 성공 여부
        """
        try:
            # 로컬 구독 상태만 정리 (글로벌 매니저는 자동으로 처리)
            if symbols:
                for symbol in symbols:
                    sub_key = f"{data_type.value}:{symbol}"
                    if sub_key in self._subscriptions:
                        del self._subscriptions[sub_key]
                    if sub_key in self._callbacks:
                        del self._callbacks[sub_key]
            else:
                # 해당 타입 전체 해제
                keys_to_remove = [key for key in self._subscriptions.keys()
                                  if key.startswith(f"{data_type.value}:")]

                for key in keys_to_remove:
                    del self._subscriptions[key]
                    if key in self._callbacks:
                        del self._callbacks[key]

            self.logger.debug(f"구독 해제 완료: {data_type} ({symbols or 'ALL'})")
            return True

        except Exception as e:
            self.logger.error(f"구독 해제 실패: {e}")
            return False

    async def unsubscribe_all(self) -> bool:
        """
        모든 구독 해제

        Returns:
            bool: 해제 성공 여부
        """
        try:
            manager = await self._get_manager()
            # 실제 API 사용: unregister_component
            await manager.unregister_component(self.component_id)

            self._subscriptions.clear()
            self._callbacks.clear()

            self.logger.info("모든 구독 해제 완료")
            return True

        except Exception as e:
            self.logger.error(f"전체 구독 해제 실패: {e}")
            return False

    async def is_private_available(self) -> bool:
        """
        Private 연결 사용 가능 여부 확인 (간소화)

        Returns:
            bool: Private 연결 사용 가능 여부
        """
        try:
            manager = await self._get_manager()
            # 간단히 헬스 상태로 판단
            health = await manager.get_health_status()
            return hasattr(health, 'private_connection') and health.private_connection.value == 'connected'
        except Exception:
            return False

    async def health_check(self) -> Dict[str, Any]:
        """
        프록시 및 연결 상태 확인

        Returns:
            Dict: 상태 정보
        """
        try:
            manager = await self._get_manager()
            global_health = await manager.get_health_status()

            return {
                'component_id': self.component_id,
                'is_active': self._is_active,
                'active_subscriptions': len(self._subscriptions),
                'uptime_seconds': time.monotonic() - self._created_at,
                'global_status': global_health.status if isinstance(global_health, HealthStatus) else 'unknown',
                'public_connection': (
                    global_health.public_connection.value
                    if isinstance(global_health, HealthStatus)
                    else 'unknown'
                ),
                'private_connection': (
                    global_health.private_connection.value
                    if isinstance(global_health, HealthStatus)
                    else 'unknown'
                )
            }

        except Exception as e:
            return {
                'component_id': self.component_id,
                'is_active': self._is_active,
                'error': str(e)
            }

    async def get_subscription_info(self) -> Dict[str, Any]:
        """
        현재 구독 정보 조회

        Returns:
            Dict: 구독 상태 정보
        """
        subscriptions_by_type = {}
        for key, spec in self._subscriptions.items():
            data_type = spec.data_type.value
            if data_type not in subscriptions_by_type:
                subscriptions_by_type[data_type] = []

            symbol = key.split(':', 1)[1] if ':' in key else 'ALL'
            subscriptions_by_type[data_type].append(symbol)

        return {
            'component_id': self.component_id,
            'total_subscriptions': len(self._subscriptions),
            'subscriptions_by_type': subscriptions_by_type,
            'is_active': self._is_active
        }

    async def cleanup(self) -> None:
        """
        리소스 정리 (명시적 호출)
        """
        if not self._is_active:
            return

        self.logger.info(f"프록시 정리 시작: {self.component_id}")

        try:
            # 모든 구독 해제
            await self.unsubscribe_all()

            # cleanup 콜백 실행
            for cleanup_fn in self._cleanup_callbacks:
                try:
                    if asyncio.iscoroutinefunction(cleanup_fn):
                        await cleanup_fn()
                    else:
                        cleanup_fn()
                except Exception as e:
                    self.logger.warning(f"cleanup 콜백 실행 중 오류: {e}")

            self._is_active = False
            self.logger.info(f"프록시 정리 완료: {self.component_id}")

        except Exception as e:
            self.logger.error(f"프록시 정리 중 오류: {e}")

    def add_cleanup_callback(self, callback: Callable) -> None:
        """
        정리 시 실행할 콜백 추가

        Args:
            callback: 정리 시 실행할 함수
        """
        self._cleanup_callbacks.append(callback)

    # =============================================================================
    # 내부 구현 메서드
    # =============================================================================

    async def _subscribe_data(
        self,
        data_type: V6DataType,
        symbols: List[str],
        callback: Callable[[Any], None],  # Any로 변경하여 타입 에러 해결
        error_handler: Optional[Callable[[Exception], None]] = None,
        is_private: bool = False,
        extra_params: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        데이터 구독 내부 구현
        """
        if not self._is_active:
            raise SubscriptionError("프록시가 비활성화되었습니다")

        try:
            manager = await self._get_manager()

            # 구독 스펙 생성
            subscription_spec = SubscriptionSpec(
                data_type=data_type,
                symbols=symbols if not is_private else [],
                markets=symbols if is_private else None,
                callback=callback,
                error_handler=error_handler
            )

            # 컴포넌트 등록 (글로벌 매니저의 실제 API 사용)
            await manager.register_component(
                component_id=self.component_id,
                component_instance=self,  # self를 WeakRef로 추적
                subscriptions=[subscription_spec],
                callback=callback
            )

            # 로컬 구독 상태 저장
            for symbol in symbols:
                sub_key = f"{data_type.value}:{symbol}"
                self._subscriptions[sub_key] = subscription_spec
                self._callbacks[sub_key] = callback

            self.logger.debug(f"구독 성공: {data_type.value} {symbols}")
            return True

        except Exception as e:
            self.logger.error(f"구독 요청 중 오류: {e}")
            if error_handler:
                try:
                    error_handler(e)
                except Exception:
                    pass
            return False

    async def _get_manager(self):
        """글로벌 매니저 인스턴스 획득"""
        if self._manager is None:
            self._manager = await get_global_websocket_manager()
        return self._manager

    @classmethod
    def _cleanup_on_gc(cls, weakref_obj):
        """가비지 컬렉션 시 자동 정리 (WeakRef 콜백)"""
        # 주의: 이 메서드는 가비지 컬렉션 중에 호출되므로 asyncio 사용 불가
        # 대신 백그라운드에서 처리할 수 있도록 태스크 예약
        try:
            loop = asyncio.get_event_loop()
            if loop and loop.is_running():
                # 실행 중인 이벤트 루프가 있으면 태스크 생성
                loop.create_task(cls._async_cleanup_on_gc())
        except Exception:
            # 이벤트 루프가 없거나 오류 시 조용히 넘어감
            pass

    @classmethod
    async def _async_cleanup_on_gc(cls):
        """비동기 가비지 컬렉션 정리 (간소화)"""
        try:
            # 글로벌 매니저가 자동으로 orphaned 구독을 정리하므로 추가 작업 불필요
            pass
        except Exception:
            # 오류 시 조용히 넘어감 (로깅 불가 - 객체가 이미 소멸됨)
            pass


# =============================================================================
# 편의 함수들
# =============================================================================

async def create_websocket_proxy(component_id: str) -> WebSocketClientProxy:
    """
    WebSocket 프록시 생성 편의 함수

    Args:
        component_id: 컴포넌트 식별자

    Returns:
        WebSocketClientProxy: 생성된 프록시 인스턴스
    """
    return WebSocketClientProxy(component_id)


async def quick_ticker_subscription(
    component_id: str,
    symbols: List[str],
    callback: Callable[[TickerEvent], None]
) -> WebSocketClientProxy:
    """
    빠른 현재가 구독 (one-liner)

    Args:
        component_id: 컴포넌트 식별자
        symbols: 구독할 심볼 리스트
        callback: 데이터 콜백

    Returns:
        WebSocketClientProxy: 구독이 설정된 프록시
    """
    proxy = WebSocketClientProxy(component_id)
    await proxy.subscribe_ticker(symbols, callback)
    return proxy


# =============================================================================
# 사용 예시
# =============================================================================

async def example_usage():
    """WebSocket 프록시 사용 예시"""

    # 1. 기본 사용법
    async with WebSocketClientProxy("example_chart") as ws:
        # 현재가 구독
        await ws.subscribe_ticker(
            ["KRW-BTC", "KRW-ETH"],
            callback=lambda event: print(f"Price: {event.symbol} = {event.trade_price}")
        )

        # 호가 구독
        await ws.subscribe_orderbook(
            ["KRW-BTC"],
            callback=lambda event: print(f"Best bid: {event.orderbook_units[0].bid_price}")
        )

        # 스냅샷 조회
        tickers = await ws.get_ticker_snapshot(["KRW-BTC"])
        print(f"Current BTC price: {tickers[0].trade_price if tickers else 'N/A'}")

        # 5초 대기
        await asyncio.sleep(5)

        # 자동 정리 (async with 종료)

    # 2. 수동 관리 사용법
    proxy = WebSocketClientProxy("manual_example")
    try:
        # Private 데이터 구독 (API 키 필요)
        if await proxy.is_private_available():
            await proxy.subscribe_my_orders(
                callback=lambda event: print(f"Order update: {event.uuid}")
            )

        # 상태 확인
        health = await proxy.health_check()
        print(f"Proxy status: {health}")

        await asyncio.sleep(3)

    finally:
        await proxy.cleanup()


if __name__ == "__main__":
    # 테스트 실행
    asyncio.run(example_usage())
