"""
호가창 관리 UseCase - Application Layer

호가창 관련 비즈니스 로직을 담당합니다.
- 심볼 변경 관리
- 데이터 소스 선택 (WebSocket vs REST)
- 실시간 업데이트 제어
"""

import asyncio
from typing import Optional, Dict, Any, Callable

from upbit_auto_trading.infrastructure.logging import create_component_logger
from upbit_auto_trading.infrastructure.services.orderbook_data_service import OrderbookDataService
from upbit_auto_trading.infrastructure.events.bus.in_memory_event_bus import InMemoryEventBus


class OrderbookManagementUseCase:
    """호가창 관리 UseCase"""

    def __init__(self, event_bus: Optional[InMemoryEventBus] = None):
        """UseCase 초기화"""
        self._logger = create_component_logger("OrderbookManagementUseCase")
        self._data_service = OrderbookDataService(event_bus)

        # 현재 상태
        self._current_symbol = "KRW-BTC"
        self._auto_refresh_enabled = True
        self._refresh_interval = 3000  # 3초

        # 콜백
        self._update_callback: Optional[Callable[[Dict[str, Any]], None]] = None
        self._status_callback: Optional[Callable[[Dict[str, Any]], None]] = None

    def set_update_callback(self, callback: Callable[[Dict[str, Any]], None]) -> None:
        """데이터 업데이트 콜백 설정"""
        self._update_callback = callback

    def set_status_callback(self, callback: Callable[[Dict[str, Any]], None]) -> None:
        """상태 업데이트 콜백 설정"""
        self._status_callback = callback

    async def change_symbol(self, symbol: str) -> bool:
        """심볼 변경"""
        if symbol == self._current_symbol:
            return True

        try:
            # 기존 구독 해제
            if self._current_symbol:
                await self._data_service.unsubscribe_symbol(self._current_symbol)

            # 새 심볼 구독
            old_symbol = self._current_symbol
            self._current_symbol = symbol

            # WebSocket 구독 시도
            websocket_success = await self._data_service.subscribe_symbol(symbol)

            # 즉시 REST 데이터 로드
            rest_data = self._data_service.load_rest_orderbook(symbol)
            if rest_data and self._update_callback:
                self._update_callback(rest_data)

            # 상태 업데이트
            self._notify_status_change()

            self._logger.info(f"심볼 변경: {old_symbol} → {symbol} (WebSocket: {websocket_success})")
            return True

        except Exception as e:
            self._logger.error(f"심볼 변경 실패: {symbol} - {e}")
            return False

    def load_current_data(self) -> Optional[Dict[str, Any]]:
        """현재 심볼의 데이터 로드 (REST)"""
        data = self._data_service.load_rest_orderbook(self._current_symbol)
        if data and self._update_callback:
            self._update_callback(data)
        return data

    def get_connection_status(self) -> Dict[str, Any]:
        """연결 상태 정보"""
        base_status = self._data_service.get_connection_status()
        base_status.update({
            "auto_refresh_enabled": self._auto_refresh_enabled,
            "refresh_interval": self._refresh_interval
        })
        return base_status

    def enable_auto_refresh(self, enable: bool = True) -> None:
        """자동 갱신 활성화/비활성화"""
        self._auto_refresh_enabled = enable
        self._notify_status_change()

    def set_refresh_interval(self, interval_ms: int) -> None:
        """갱신 주기 설정"""
        self._refresh_interval = interval_ms
        self._notify_status_change()

    def is_websocket_available(self) -> bool:
        """WebSocket 사용 가능 여부"""
        return self._data_service.is_websocket_connected()

    def get_current_symbol(self) -> str:
        """현재 심볼 반환"""
        return self._current_symbol

    def _notify_status_change(self) -> None:
        """상태 변경 알림"""
        if self._status_callback:
            status = self.get_connection_status()
            self._status_callback(status)

    async def refresh_data(self) -> None:
        """데이터 수동 갱신"""
        if self._current_symbol:
            self.load_current_data()
