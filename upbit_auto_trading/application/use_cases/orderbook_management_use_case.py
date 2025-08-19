"""
호가창 관리 UseCase - Application Layer

호가창 관련 비즈니스 로직을 담당합니다.
- 심볼 변경 관리
- 데이터 소스 선택 (WebSocket vs REST)
- 실시간 업데이트 제어
- QTimer 기반 안정적인 갱신 (asyncio 문제 해결)
"""

from typing import Optional, Dict, Any, Callable
from PyQt6.QtCore import QTimer, QObject

from upbit_auto_trading.infrastructure.logging import create_component_logger
from upbit_auto_trading.infrastructure.services.orderbook_data_service import OrderbookDataService
from upbit_auto_trading.infrastructure.events.bus.in_memory_event_bus import InMemoryEventBus


class OrderbookManagementUseCase(QObject):
    """호가창 관리 UseCase - QTimer 기반 안정화"""

    def __init__(self, event_bus: Optional[InMemoryEventBus] = None):
        """UseCase 초기화"""
        super().__init__()
        self._logger = create_component_logger("OrderbookManagementUseCase")
        self._data_service = OrderbookDataService(event_bus)

        # 현재 상태
        self._current_symbol = "KRW-BTC"
        self._auto_refresh_enabled = True
        self._refresh_interval = 3000  # 3초

        # 콜백
        self._update_callback: Optional[Callable[[Dict[str, Any]], None]] = None
        self._status_callback: Optional[Callable[[Dict[str, Any]], None]] = None

        # 심볼 변경 지연 타이머 (asyncio 대신 QTimer 사용)
        self._symbol_change_timer = QTimer(self)
        self._symbol_change_timer.setSingleShot(True)
        self._symbol_change_timer.timeout.connect(self._complete_symbol_change)

        # 대기 중인 심볼 변경
        self._pending_symbol: Optional[str] = None

    def set_update_callback(self, callback: Callable[[Dict[str, Any]], None]) -> None:
        """데이터 업데이트 콜백 설정"""
        self._update_callback = callback

    def set_status_callback(self, callback: Callable[[Dict[str, Any]], None]) -> None:
        """상태 업데이트 콜백 설정"""
        self._status_callback = callback

    def change_symbol(self, symbol: str) -> bool:
        """심볼 변경 - QTimer 기반으로 안전하게 처리"""
        if symbol == self._current_symbol:
            return True

        try:
            self._logger.info(f"🔄 심볼 변경 시작: {self._current_symbol} → {symbol}")

            # 기존 구독 해제 (스레드 방식)
            if self._current_symbol:
                self._data_service.unsubscribe_symbol_threaded(self._current_symbol)

            # 새 심볼 설정
            old_symbol = self._current_symbol
            self._current_symbol = symbol
            self._pending_symbol = symbol

            # 즉시 REST 데이터 로드 (논블로킹)
            rest_data = self._data_service.load_rest_orderbook(symbol)
            if rest_data and self._update_callback:
                self._update_callback(rest_data)

            # WebSocket 구독을 지연 처리 (500ms 후)
            self._symbol_change_timer.start(500)

            # 상태 업데이트
            self._notify_status_change()

            self._logger.info(f"✅ 심볼 변경 완료: {old_symbol} → {symbol}")
            return True

        except Exception as e:
            self._logger.error(f"❌ 심볼 변경 실패: {symbol} - {e}")
            return False

    def _complete_symbol_change(self) -> None:
        """심볼 변경 완료 처리 (WebSocket 구독)"""
        if not self._pending_symbol:
            return

        def on_websocket_subscribed(success: bool):
            """WebSocket 구독 완료 콜백"""
            if success:
                self._logger.info(f"✅ WebSocket 구독 완료: {self._pending_symbol}")
            else:
                self._logger.warning(f"⚠️ WebSocket 구독 실패: {self._pending_symbol}")

            # 상태 업데이트
            self._notify_status_change()
            self._pending_symbol = None

        # WebSocket 구독 시도 (스레드 방식)
        self._data_service.subscribe_symbol_threaded(self._pending_symbol, on_websocket_subscribed)

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
            "refresh_interval": self._refresh_interval,
            "pending_symbol": self._pending_symbol is not None
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

    def refresh_data(self) -> None:
        """데이터 수동 갱신 - QTimer 기반으로 안전하게"""
        if self._current_symbol:
            self.load_current_data()

    # 호환성을 위한 async 메서드 (내부적으로 동기 방식 사용)
    async def change_symbol_async(self, symbol: str) -> bool:
        """심볼 변경 (async 호환성)"""
        return self.change_symbol(symbol)

    async def refresh_data_async(self) -> None:
        """데이터 갱신 (async 호환성)"""
        self.refresh_data()
