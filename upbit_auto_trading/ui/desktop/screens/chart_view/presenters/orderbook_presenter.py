"""
호가창 프레젠터 - Presentation Layer

UI와 비즈니스 로직 사이의 연결을 담당합니다.
- 이벤트 처리 (QAsync 기반)
- 데이터 변환
- UI 상태 관리
"""

from typing import Optional, Dict, Any
from PyQt6.QtCore import QObject, QTimer, pyqtSignal
from qasync import asyncSlot

from upbit_auto_trading.infrastructure.logging import create_component_logger
from upbit_auto_trading.application.use_cases.orderbook_management_use_case import OrderbookManagementUseCase
from upbit_auto_trading.infrastructure.events.bus.in_memory_event_bus import InMemoryEventBus
from upbit_auto_trading.domain.events.chart_viewer_events import WebSocketOrderbookUpdateEvent


class OrderbookPresenter(QObject):
    """호가창 프레젠터"""

    # 시그널 정의
    data_updated = pyqtSignal(dict)  # 데이터 업데이트
    status_changed = pyqtSignal(dict)  # 상태 변경
    error_occurred = pyqtSignal(str)  # 오류 발생

    def __init__(self, event_bus: Optional[InMemoryEventBus] = None):
        """프레젠터 초기화"""
        super().__init__()
        self._logger = create_component_logger("OrderbookPresenter")
        self._event_bus = event_bus

        # UseCase
        self._use_case = OrderbookManagementUseCase(event_bus)
        self._use_case.set_update_callback(self._on_data_updated)
        self._use_case.set_status_callback(self._on_status_changed)

        # 타이머 (백업 갱신용)
        self._backup_timer = QTimer(self)
        self._backup_timer.timeout.connect(self._backup_refresh)
        self._backup_timer.start(15000)  # 15초마다 백업 갱신

        # UseCase 시그널 연결 (QAsync 기반)
        self._use_case.symbol_changed.connect(self._on_symbol_changed)
        self._use_case.data_loaded.connect(self._on_data_updated)
        self._use_case.status_updated.connect(self._on_status_changed)

        # WebSocket 이벤트 구독
        if self._event_bus:
            self._event_bus.subscribe(WebSocketOrderbookUpdateEvent, self._on_websocket_update)

    @asyncSlot(str)
    async def change_symbol(self, symbol: str) -> bool:
        """심볼 변경 요청 - QAsync 기반으로 안전하게"""
        try:
            success = await self._use_case.change_symbol(symbol)
            if not success:
                self.error_occurred.emit(f"심볼 변경 실패: {symbol}")
            return success
        except Exception as e:
            self._logger.error(f"심볼 변경 오류: {e}")
            self.error_occurred.emit(f"심볼 변경 오류: {str(e)}")
            return False

    def change_symbol_sync(self, symbol: str) -> bool:
        """심볼 변경 요청 (동기 호출용)"""
        try:
            return self._use_case.change_symbol_sync(symbol)
        except Exception as e:
            self._logger.error(f"동기 심볼 변경 오류: {e}")
            self.error_occurred.emit(f"심볼 변경 오류: {str(e)}")
            return False

    # 호환성을 위한 async 버전 제거하고 동기 래퍼만 유지
    async def change_symbol_async(self, symbol: str) -> bool:
        """심볼 변경 요청 (async 호환성)"""
        return await self.change_symbol(symbol)

    def refresh_data(self) -> None:
        """데이터 수동 갱신"""
        try:
            self._use_case.load_current_data()
        except Exception as e:
            self._logger.error(f"데이터 갱신 오류: {e}")
            self.error_occurred.emit(f"데이터 갱신 오류: {str(e)}")

    def get_current_symbol(self) -> str:
        """현재 심볼 반환"""
        return self._use_case.get_current_symbol()

    def get_connection_status(self) -> Dict[str, Any]:
        """연결 상태 정보"""
        return self._use_case.get_connection_status()

    def enable_auto_refresh(self, enable: bool = True) -> None:
        """자동 갱신 활성화/비활성화"""
        self._use_case.enable_auto_refresh(enable)

        if enable:
            self._backup_timer.start(15000)
        else:
            self._backup_timer.stop()

    def _on_symbol_changed(self, old_symbol: str, new_symbol: str) -> None:
        """심볼 변경 완료 시그널 핸들러"""
        self._logger.info(f"📈 심볼 변경 완료: {old_symbol} → {new_symbol}")

    def _on_data_updated(self, data: Dict[str, Any]) -> None:
        """데이터 업데이트 콜백"""
        self.data_updated.emit(data)

    def _on_status_changed(self, status: Dict[str, Any]) -> None:
        """상태 변경 콜백"""
        self.status_changed.emit(status)

    def _on_websocket_update(self, event: WebSocketOrderbookUpdateEvent) -> None:
        """WebSocket 호가창 업데이트 이벤트 처리"""
        try:
            # 현재 심볼과 일치하는지 확인
            if event.symbol != self._use_case.get_current_symbol():
                return

            # 실시간 데이터로 변환
            websocket_data = {
                "symbol": event.symbol,
                "asks": event.orderbook_data.get("asks", []),
                "bids": event.orderbook_data.get("bids", []),
                "timestamp": event.orderbook_data.get("timestamp", ""),
                "market": event.symbol.split("-")[0],
                "source": "websocket",
                "spread_percent": event.spread_percent
            }

            # 데이터 업데이트 시그널 발생
            self.data_updated.emit(websocket_data)

            self._logger.debug(f"WebSocket 호가 업데이트: {event.symbol}")

        except Exception as e:
            self._logger.error(f"WebSocket 이벤트 처리 오류: {e}")
            self.error_occurred.emit(f"WebSocket 오류: {str(e)}")

    def _backup_refresh(self) -> None:
        """백업 갱신 (WebSocket 보완용)"""
        try:
            if self._use_case.is_websocket_available():
                # WebSocket 연결됨 - 가벼운 백업 갱신
                self._logger.debug("🔄 WebSocket 백업 갱신")
            else:
                # WebSocket 미연결 - 전체 갱신
                self._logger.debug("🔄 REST 전체 갱신")

            self._use_case.load_current_data()

        except Exception as e:
            self._logger.error(f"백업 갱신 오류: {e}")

    def cleanup(self) -> None:
        """리소스 정리"""
        if self._backup_timer.isActive():
            self._backup_timer.stop()

        self._logger.info("OrderbookPresenter 리소스 정리 완료")
