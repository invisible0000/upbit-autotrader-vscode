"""
창 생명주기 관리 프레젠터

차트뷰어 창의 활성화/비활성화 상태를 관리하고
리소스 사용량을 최적화하는 프레젠터입니다.

태스크 2.4: 호가창과 차트뷰의 독립적 리소스 관리 지원
"""

from typing import Optional, Dict, Any
from PyQt6.QtCore import QObject, pyqtSignal, QTimer
from PyQt6.QtWidgets import QWidget

from upbit_auto_trading.infrastructure.logging import create_component_logger
from upbit_auto_trading.application.chart_viewer.chart_viewer_resource_manager import ChartViewerResourceManager
from upbit_auto_trading.domain.events.chart_viewer_events import ChartViewerPriority


class WindowLifecyclePresenter(QObject):
    """
    창 생명주기 관리 프레젠터

    창 상태에 따른 리소스 관리:
    - 활성화: 우선순위 5 (실시간 업데이트)
    - 비활성화: 우선순위 8 (저빈도 업데이트)
    - 최소화: 우선순위 10 (최소 리소스)
    """

    # 시그널 정의
    state_changed = pyqtSignal(str)  # 상태 변경 시그널
    resource_optimized = pyqtSignal(float)  # 리소스 최적화 시그널 (절약률)

    def __init__(self, window: QWidget, parent: Optional[QObject] = None):
        """창 생명주기 프레젠터 초기화"""
        super().__init__(parent)

        self._logger = create_component_logger("WindowLifecyclePresenter")
        self._window = window

        # 상태 관리
        self._current_state = "active"
        self._previous_state = "active"
        self._state_history: list[str] = []

        # 차트 ID 생성 (창 식별용)
        self._chart_id = f"chart_window_{id(window)}"

        # 리소스 관리자
        self._resource_manager = ChartViewerResourceManager()

        # 초기 차트 등록
        self._resource_manager.register_chart(self._chart_id, "active")

        # 상태 감지 타이머
        self._state_monitor = QTimer()
        self._state_monitor.timeout.connect(self._check_window_state)
        self._state_monitor.start(1000)  # 1초마다 상태 확인

        # 창 이벤트 연결
        self._setup_window_events()

        self._logger.info("🔄 창 생명주기 프레젠터 초기화 완료")

    def _setup_window_events(self) -> None:
        """창 이벤트 설정"""
        # 창 활성화/비활성화 이벤트 모니터링을 위한 이벤트 필터 설치
        self._window.installEventFilter(self)

        self._logger.debug("창 이벤트 설정 완료")

    def eventFilter(self, obj, event) -> bool:
        """창 이벤트 필터"""
        from PyQt6.QtCore import QEvent

        if obj == self._window:
            if event.type() == QEvent.Type.WindowActivate:
                self._on_window_activated()
            elif event.type() == QEvent.Type.WindowDeactivate:
                self._on_window_deactivated()
            elif event.type() == QEvent.Type.WindowStateChange:
                self._on_window_state_changed()

        return super().eventFilter(obj, event)

    def _check_window_state(self) -> None:
        """창 상태 주기적 확인"""
        new_state = self._determine_current_state()

        if new_state != self._current_state:
            self._update_state(new_state)

    def _determine_current_state(self) -> str:
        """현재 창 상태 판단"""
        if not self._window.isVisible():
            return "hidden"

        if self._window.isMinimized():
            return "minimized"

        if self._window.isActiveWindow():
            return "active"

        return "inactive"

    def _update_state(self, new_state: str) -> None:
        """상태 업데이트"""
        self._previous_state = self._current_state
        self._current_state = new_state

        # 상태 기록
        self._state_history.append(new_state)
        if len(self._state_history) > 100:  # 최대 100개 기록 유지
            self._state_history.pop(0)

        # 리소스 우선순위 조정
        self._adjust_resource_priority()

        # 시그널 발송
        self.state_changed.emit(new_state)

        self._logger.info(f"🔄 창 상태 변경: {self._previous_state} → {new_state}")

    def _adjust_resource_priority(self) -> None:
        """상태에 따른 리소스 우선순위 조정 - 호가창 독립 지원"""
        # 상태 매핑 (ChartViewerResourceManager의 window_state와 일치)
        state_map = {
            "active": "active",
            "inactive": "background",
            "minimized": "minimized",
            "hidden": "minimized"  # hidden도 minimized로 처리
        }

        # 절약률 매핑
        saving_map = {
            "active": 0.0,
            "inactive": 0.5,
            "minimized": 0.9,
            "hidden": 0.95
        }

        # 호가창 전용 우선순위 매핑 (태스크 2.4)
        orderbook_priority_map = {
            "active": 5,     # ChartViewerPriority.ORDERBOOK_HIGH
            "inactive": 8,   # ChartViewerPriority.CHART_BACKGROUND
            "minimized": 10, # ChartViewerPriority.CHART_LOW
            "hidden": 10
        }

        resource_state = state_map.get(self._current_state, "background")
        saving_rate = saving_map.get(self._current_state, 0.5)
        orderbook_priority = orderbook_priority_map.get(self._current_state, 8)

        # 리소스 관리자에 창 상태 업데이트
        try:
            resource_info = self._resource_manager.update_window_state(self._chart_id, resource_state)
            if resource_info:
                priority = resource_info.priority_level
                self._logger.debug(
                    f"리소스 우선순위 조정: 차트={priority}, 호가창={orderbook_priority}, "
                    f"절약률={saving_rate:.1%}"
                )
            else:
                self._logger.warning(f"리소스 정보 업데이트 실패: {self._chart_id}")
        except Exception as e:
            self._logger.error(f"리소스 우선순위 조정 오류: {e}")

        # 절약률 시그널 발송
        self.resource_optimized.emit(saving_rate)

    def _on_window_activated(self) -> None:
        """창 활성화 처리"""
        self._logger.debug("창 활성화 이벤트")

        # 실시간 모드로 복원
        if self._current_state != "active":
            self._update_state("active")

    def _on_window_deactivated(self) -> None:
        """창 비활성화 처리"""
        self._logger.debug("창 비활성화 이벤트")

        # 저빈도 모드로 전환
        if self._current_state == "active":
            self._update_state("inactive")

    def _on_window_state_changed(self) -> None:
        """창 상태 변경 처리"""
        self._logger.debug("창 상태 변경 이벤트")

        # 즉시 상태 확인
        self._check_window_state()

    def get_current_state(self) -> str:
        """현재 상태 반환"""
        return self._current_state

    def get_state_history(self) -> list[str]:
        """상태 변경 기록 반환"""
        return self._state_history.copy()

    def force_state(self, state: str) -> None:
        """강제로 상태 설정 (테스트용)"""
        if state in ["active", "inactive", "minimized", "hidden"]:
            self._update_state(state)
            self._logger.debug(f"강제 상태 설정: {state}")
        else:
            self._logger.warning(f"유효하지 않은 상태: {state}")

    def get_resource_info(self) -> Dict[str, Any]:
        """현재 리소스 정보 반환"""
        priority_map = {
            "active": 5,
            "inactive": 8,
            "minimized": 10,
            "hidden": 10
        }

        saving_map = {
            "active": 0.0,
            "inactive": 0.5,
            "minimized": 0.9,
            "hidden": 0.95
        }

        return {
            "current_state": self._current_state,
            "previous_state": self._previous_state,
            "priority": priority_map.get(self._current_state, 8),
            "saving_rate": saving_map.get(self._current_state, 0.5),
            "state_changes": len(self._state_history),
            "visible": self._window.isVisible(),
            "minimized": self._window.isMinimized(),
            "active": self._window.isActiveWindow()
        }

    def start_monitoring(self) -> None:
        """모니터링 시작"""
        if not self._state_monitor.isActive():
            self._state_monitor.start(1000)
            self._logger.info("창 상태 모니터링 시작")

    def stop_monitoring(self) -> None:
        """모니터링 중지"""
        if self._state_monitor.isActive():
            self._state_monitor.stop()
            self._logger.info("창 상태 모니터링 중지")

    # 태스크 2.4: 호가창 전용 우선순위 관리 메서드들

    def get_orderbook_priority_info(self) -> Dict[str, Any]:
        """호가창 우선순위 정보 반환 (태스크 2.4 전용)"""
        state_priority_map = {
            "active": {
                "orderbook_priority": 5,  # ORDERBOOK_HIGH
                "chart_priority": 5,      # CHART_HIGH
                "memory_allocation": "256MB",
                "update_frequency": "실시간",
                "description": "호가창 실시간 업데이트, 최고 우선순위"
            },
            "inactive": {
                "orderbook_priority": 8,  # CHART_BACKGROUND
                "chart_priority": 8,
                "memory_allocation": "128MB",
                "update_frequency": "저빈도",
                "description": "호가창 백그라운드 모드, 중간 우선순위"
            },
            "minimized": {
                "orderbook_priority": 10,  # CHART_LOW
                "chart_priority": 10,
                "memory_allocation": "64MB",
                "update_frequency": "최소",
                "description": "호가창 최소 리소스, 최저 우선순위"
            }
        }

        current_info = state_priority_map.get(self._current_state, state_priority_map["minimized"])
        current_info["current_state"] = self._current_state
        current_info["chart_id"] = self._chart_id

        return current_info

    def is_orderbook_priority_high(self) -> bool:
        """호가창이 고우선순위 상태인지 확인"""
        return self._current_state == "active"

    def get_orderbook_resource_allocation(self) -> Dict[str, Any]:
        """호가창 리소스 할당 정보 반환"""
        allocation_map = {
            "active": {
                "cpu_priority": "high",
                "memory_mb": 256,
                "network_priority": "high",
                "update_interval_ms": 100,  # 100ms 실시간
                "websocket_priority": 5
            },
            "inactive": {
                "cpu_priority": "normal",
                "memory_mb": 128,
                "network_priority": "normal",
                "update_interval_ms": 1000,  # 1초
                "websocket_priority": 8
            },
            "minimized": {
                "cpu_priority": "low",
                "memory_mb": 64,
                "network_priority": "low",
                "update_interval_ms": 5000,  # 5초
                "websocket_priority": 10
            }
        }

        return allocation_map.get(self._current_state, allocation_map["minimized"])

    def cleanup(self) -> None:
        """리소스 정리"""
        self.stop_monitoring()
        self._window.removeEventFilter(self)

        # 차트 등록 해제
        if hasattr(self, '_chart_id'):
            self._resource_manager.unregister_chart(self._chart_id)

        self._logger.info("창 생명주기 프레젠터 정리 완료")
