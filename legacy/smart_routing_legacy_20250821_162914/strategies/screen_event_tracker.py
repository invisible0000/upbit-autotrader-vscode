"""
PyQt6 UI와 WebSocket 자원 관리 연동

화면 생명주기 이벤트를 자동으로 감지하여
WebSocket 구독을 최적화합니다.
"""

import asyncio
from typing import Dict, List, Optional, Set
from PyQt6.QtCore import QObject, pyqtSignal, QTimer
from PyQt6.QtWidgets import QWidget

from upbit_auto_trading.infrastructure.logging import create_component_logger
from upbit_auto_trading.infrastructure.external_apis.upbit.upbit_websocket_quotation_client import WebSocketDataType
from .ui_aware_websocket_manager import (
    UIAwareWebSocketManager,
    ScreenType,
    SubscriptionPriority
)


class ScreenEventTracker(QObject):
    """화면 이벤트 추적기

    PyQt6 윈도우/위젯의 생명주기 이벤트를 감지하여
    WebSocket 자원 관리자에게 알림을 전달합니다.
    """

    # 시그널 정의
    screen_opened = pyqtSignal(str, str, list, list)  # screen_name, screen_type, symbols, data_types
    screen_closed = pyqtSignal(str)                   # screen_name
    symbol_changed = pyqtSignal(str, list, list)     # screen_name, old_symbols, new_symbols

    def __init__(self, websocket_manager: UIAwareWebSocketManager):
        super().__init__()
        self.logger = create_component_logger("ScreenEventTracker")
        self.websocket_manager = websocket_manager

        # 추적 중인 화면들
        self.tracked_screens: Dict[str, QWidget] = {}
        self.screen_configs: Dict[str, Dict] = {}

        # 시그널 연결
        self.screen_opened.connect(self._on_screen_opened)
        self.screen_closed.connect(self._on_screen_closed)
        self.symbol_changed.connect(self._on_symbol_changed)

    def register_screen(
        self,
        screen_name: str,
        widget: QWidget,
        screen_type: ScreenType,
        symbols: List[str],
        data_types: List[WebSocketDataType],
        priority: SubscriptionPriority = SubscriptionPriority.EXCLUSIVE
    ):
        """화면 등록 및 이벤트 추적 시작"""

        self.logger.info(f"📋 화면 등록: {screen_name} ({screen_type.value})")

        # 화면 설정 저장
        self.screen_configs[screen_name] = {
            'screen_type': screen_type,
            'symbols': symbols.copy(),
            'data_types': data_types.copy(),
            'priority': priority,
            'widget': widget
        }

        # 이벤트 연결
        self._connect_widget_events(screen_name, widget)

        # 즉시 화면 열림 이벤트 발생 (이미 표시된 경우)
        if widget.isVisible():
            self.screen_opened.emit(
                screen_name,
                screen_type.value,
                symbols,
                [dt.value for dt in data_types]
            )

    def unregister_screen(self, screen_name: str):
        """화면 등록 해제"""

        if screen_name in self.tracked_screens:
            self.screen_closed.emit(screen_name)
            del self.tracked_screens[screen_name]

        if screen_name in self.screen_configs:
            del self.screen_configs[screen_name]

        self.logger.info(f"📋 화면 등록 해제: {screen_name}")

    def update_screen_symbols(self, screen_name: str, new_symbols: List[str]):
        """화면의 구독 심볼 업데이트"""

        if screen_name not in self.screen_configs:
            self.logger.warning(f"⚠️ 미등록 화면: {screen_name}")
            return

        config = self.screen_configs[screen_name]
        old_symbols = config['symbols'].copy()
        config['symbols'] = new_symbols.copy()

        self.symbol_changed.emit(screen_name, old_symbols, new_symbols)
        self.logger.info(f"🔄 {screen_name}: 심볼 업데이트 {old_symbols} → {new_symbols}")

    def get_active_screens(self) -> Set[str]:
        """현재 활성 화면 목록"""

        active = set()

        for screen_name, config in self.screen_configs.items():
            widget = config['widget']
            if widget and widget.isVisible():
                active.add(screen_name)

        return active

    def _connect_widget_events(self, screen_name: str, widget: QWidget):
        """위젯 이벤트 연결"""

        self.tracked_screens[screen_name] = widget

        # showEvent 오버라이드
        original_show_event = widget.showEvent
        def enhanced_show_event(event):
            original_show_event(event)
            self._on_widget_shown(screen_name)

        widget.showEvent = enhanced_show_event

        # closeEvent 오버라이드
        original_close_event = widget.closeEvent
        def enhanced_close_event(event):
            self._on_widget_closed(screen_name)
            original_close_event(event)

        widget.closeEvent = enhanced_close_event

        # hideEvent 오버라이드 (최소화 등)
        original_hide_event = widget.hideEvent
        def enhanced_hide_event(event):
            self._on_widget_hidden(screen_name)
            original_hide_event(event)

        widget.hideEvent = enhanced_hide_event

    def _on_widget_shown(self, screen_name: str):
        """위젯이 표시될 때"""

        if screen_name in self.screen_configs:
            config = self.screen_configs[screen_name]
            self.screen_opened.emit(
                screen_name,
                config['screen_type'].value,
                config['symbols'],
                [dt.value for dt in config['data_types']]
            )

    def _on_widget_closed(self, screen_name: str):
        """위젯이 닫힐 때"""

        self.screen_closed.emit(screen_name)

    def _on_widget_hidden(self, screen_name: str):
        """위젯이 숨겨질 때 (최소화 등)"""

        # 완전히 닫힌 게 아니면 구독은 유지
        # 필요에 따라 임시 일시정지 로직 추가 가능
        self.logger.debug(f"📱 화면 숨김: {screen_name}")

    def _on_screen_opened(self, screen_name: str, screen_type: str, symbols: List[str], data_types: List[str]):
        """화면 열림 이벤트 처리"""

        asyncio.create_task(self._handle_screen_opened(screen_name, screen_type, symbols, data_types))

    def _on_screen_closed(self, screen_name: str):
        """화면 닫힘 이벤트 처리"""

        asyncio.create_task(self._handle_screen_closed(screen_name))

    def _on_symbol_changed(self, screen_name: str, old_symbols: List[str], new_symbols: List[str]):
        """심볼 변경 이벤트 처리"""

        if screen_name in self.screen_configs:
            config = self.screen_configs[screen_name]
            data_types = config['data_types']

            asyncio.create_task(self._handle_symbol_changed(
                screen_name, old_symbols, new_symbols, data_types
            ))

    async def _handle_screen_opened(self, screen_name: str, screen_type: str, symbols: List[str], data_types: List[str]):
        """화면 열림 비동기 처리"""

        try:
            config = self.screen_configs.get(screen_name, {})
            priority = config.get('priority', SubscriptionPriority.EXCLUSIVE)

            screen_type_enum = ScreenType(screen_type)
            data_types_enum = [WebSocketDataType(dt) for dt in data_types]

            await self.websocket_manager.on_screen_opened(
                screen_name, screen_type_enum, symbols, data_types_enum, priority
            )

        except Exception as e:
            self.logger.error(f"❌ 화면 열림 처리 오류: {e}")

    async def _handle_screen_closed(self, screen_name: str):
        """화면 닫힘 비동기 처리"""

        try:
            await self.websocket_manager.on_screen_closed(screen_name)

        except Exception as e:
            self.logger.error(f"❌ 화면 닫힘 처리 오류: {e}")

    async def _handle_symbol_changed(self, screen_name: str, old_symbols: List[str], new_symbols: List[str], data_types: List[WebSocketDataType]):
        """심볼 변경 비동기 처리"""

        try:
            await self.websocket_manager.on_symbol_changed(
                screen_name, old_symbols, new_symbols, data_types
            )

        except Exception as e:
            self.logger.error(f"❌ 심볼 변경 처리 오류: {e}")


class WebSocketResourceMonitor(QObject):
    """WebSocket 자원 모니터링 위젯"""

    # 시그널 정의
    resource_updated = pyqtSignal(dict)  # 자원 사용량 업데이트
    optimization_needed = pyqtSignal(list)  # 최적화 권장사항

    def __init__(self, websocket_manager: UIAwareWebSocketManager):
        super().__init__()
        self.logger = create_component_logger("WebSocketResourceMonitor")
        self.websocket_manager = websocket_manager

        # 모니터링 타이머 (30초마다)
        self.monitor_timer = QTimer()
        self.monitor_timer.timeout.connect(self._update_metrics)
        self.monitor_timer.start(30000)  # 30초

    def get_current_usage(self) -> Dict:
        """현재 자원 사용량 조회"""

        return self.websocket_manager.get_resource_usage()

    def get_recommendations(self) -> List[str]:
        """최적화 권장사항 조회"""

        return self.websocket_manager.get_optimization_recommendations()

    def _update_metrics(self):
        """메트릭 업데이트"""

        try:
            # 자원 사용량 업데이트
            usage = self.get_current_usage()
            self.resource_updated.emit(usage)

            # 최적화 권장사항 확인
            recommendations = self.get_recommendations()
            if recommendations:
                self.optimization_needed.emit(recommendations)

        except Exception as e:
            self.logger.error(f"❌ 메트릭 업데이트 오류: {e}")


# 편의 함수들

def create_chart_view_tracker(
    websocket_manager: UIAwareWebSocketManager,
    chart_widget: QWidget,
    initial_symbol: str = "KRW-BTC"
) -> ScreenEventTracker:
    """차트뷰용 이벤트 추적기 생성"""

    tracker = ScreenEventTracker(websocket_manager)

    # 차트뷰 화면 등록
    tracker.register_screen(
        screen_name="chartview",
        widget=chart_widget,
        screen_type=ScreenType.ON_DEMAND,
        symbols=[initial_symbol],
        data_types=[WebSocketDataType.TICKER, WebSocketDataType.ORDERBOOK],
        priority=SubscriptionPriority.EXCLUSIVE
    )

    return tracker


def create_dashboard_tracker(
    websocket_manager: UIAwareWebSocketManager,
    dashboard_widget: QWidget,
    krw_symbols: List[str]
) -> ScreenEventTracker:
    """대시보드용 이벤트 추적기 생성"""

    tracker = ScreenEventTracker(websocket_manager)

    # 대시보드 화면 등록 (공유 구독 사용)
    tracker.register_screen(
        screen_name="dashboard",
        widget=dashboard_widget,
        screen_type=ScreenType.ON_DEMAND,
        symbols=krw_symbols,
        data_types=[WebSocketDataType.TICKER],
        priority=SubscriptionPriority.SHARED
    )

    return tracker


def create_trading_tracker(
    websocket_manager: UIAwareWebSocketManager,
    trading_widget: QWidget,
    portfolio_symbols: List[str]
) -> ScreenEventTracker:
    """실시간 거래용 이벤트 추적기 생성"""

    tracker = ScreenEventTracker(websocket_manager)

    # 실시간 거래 화면 등록 (Critical - 항상 유지)
    tracker.register_screen(
        screen_name="trading",
        widget=trading_widget,
        screen_type=ScreenType.CRITICAL,
        symbols=portfolio_symbols,
        data_types=[WebSocketDataType.TICKER, WebSocketDataType.TRADE],
        priority=SubscriptionPriority.CRITICAL
    )

    return tracker
