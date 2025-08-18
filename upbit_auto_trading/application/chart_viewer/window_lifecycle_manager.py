"""
창 생명주기 관리자 (동기 버전)

기존 InMemoryEventBus를 활용하여 창 상태 변화를 감지하고 처리합니다.
PyQt6의 창 이벤트를 차트뷰어 도메인 이벤트로 변환합니다.
"""

from typing import Dict, Optional
from PyQt6.QtCore import QObject, pyqtSignal, QTimer
from PyQt6.QtWidgets import QWidget

from upbit_auto_trading.domain.events.chart_viewer_events import (
    ChartLifecycleEvent, ChartViewerPriority
)
from upbit_auto_trading.infrastructure.events.bus.event_bus_interface import IEventBus
from upbit_auto_trading.application.chart_viewer.chart_viewer_resource_manager import (
    ChartViewerResourceManager
)
from upbit_auto_trading.infrastructure.logging import create_component_logger


class WindowLifecycleManager(QObject):
    """
    창 생명주기 관리자

    PyQt6 창 이벤트를 감지하여 기존 이벤트 버스를 통해
    차트뷰어 도메인 이벤트를 발행합니다.
    """

    # PyQt6 시그널 정의
    window_activated = pyqtSignal(str)     # chart_id
    window_deactivated = pyqtSignal(str)   # chart_id
    window_minimized = pyqtSignal(str)     # chart_id
    window_restored = pyqtSignal(str)      # chart_id
    window_closed = pyqtSignal(str)        # chart_id

    def __init__(self, event_bus: IEventBus, resource_manager: ChartViewerResourceManager):
        super().__init__()
        self._event_bus = event_bus
        self._resource_manager = resource_manager
        self._logger = create_component_logger("WindowLifecycleManager")

        # 등록된 창 추적 (기존 시스템과 독립)
        self._registered_windows: Dict[str, QWidget] = {}
        self._window_states: Dict[str, str] = {}

        # 이벤트 발행을 위한 타이머 (비동기 처리)
        self._event_timer = QTimer()
        self._event_timer.timeout.connect(self._process_pending_events)
        self._event_timer.start(50)  # 50ms마다 처리
        self._pending_events = []

        # 이벤트 핸들러 연결
        self._connect_signals()

        self._logger.info("창 생명주기 관리자 초기화됨 (기존 이벤트 버스 활용)")

    def register_window(self, chart_id: str, widget: QWidget) -> None:
        """차트 창 등록 및 이벤트 감지 시작"""
        try:
            if chart_id in self._registered_windows:
                self._logger.warning(f"이미 등록된 창: {chart_id}")
                return

            # 창 등록
            self._registered_windows[chart_id] = widget
            self._window_states[chart_id] = 'active'  # 초기 상태

            # PyQt6 이벤트 연결
            self._connect_widget_events(chart_id, widget)

            # 리소스 관리자에 등록
            self._resource_manager.register_chart(chart_id, 'active')

            # 생명주기 이벤트 발행
            self._queue_lifecycle_event(
                chart_id=chart_id,
                lifecycle_type='activated',
                resource_priority=ChartViewerPriority.CHART_HIGH
            )

            self._logger.info(f"차트 창 등록: {chart_id} (활성 상태)")

        except Exception as e:
            self._logger.error(f"차트 창 등록 실패: {chart_id} - {e}")
            raise

    def unregister_window(self, chart_id: str) -> None:
        """차트 창 등록 해제"""
        try:
            if chart_id not in self._registered_windows:
                self._logger.warning(f"등록되지 않은 창: {chart_id}")
                return

            # 생명주기 이벤트 발행
            self._queue_lifecycle_event(
                chart_id=chart_id,
                lifecycle_type='closed',
                resource_priority=ChartViewerPriority.CHART_LOW
            )

            # 창 등록 해제
            widget = self._registered_windows.pop(chart_id)
            self._window_states.pop(chart_id, None)

            # 리소스 회수
            self._resource_manager.unregister_chart(chart_id)

            # PyQt6 이벤트 연결 해제
            self._disconnect_widget_events(widget)

            self._logger.info(f"차트 창 등록 해제: {chart_id}")

        except Exception as e:
            self._logger.error(f"차트 창 등록 해제 실패: {chart_id} - {e}")

    def get_window_state(self, chart_id: str) -> Optional[str]:
        """창 상태 조회"""
        return self._window_states.get(chart_id)

    def get_registered_windows(self) -> Dict[str, str]:
        """등록된 창 목록 및 상태 조회"""
        return self._window_states.copy()

    def _connect_signals(self) -> None:
        """PyQt6 시그널 연결"""
        self.window_activated.connect(self._on_window_activated)
        self.window_deactivated.connect(self._on_window_deactivated)
        self.window_minimized.connect(self._on_window_minimized)
        self.window_restored.connect(self._on_window_restored)
        self.window_closed.connect(self._on_window_closed)

    def _connect_widget_events(self, chart_id: str, widget: QWidget) -> None:
        """개별 위젯의 이벤트 연결"""
        # PyQt6 이벤트 필터 또는 시그널 연결
        # 실제 구현에서는 위젯의 changeEvent 등을 오버라이드해야 함
        # 여기서는 기본 구조만 제공
        pass

    def _disconnect_widget_events(self, widget: QWidget) -> None:
        """개별 위젯의 이벤트 연결 해제"""
        # PyQt6 이벤트 연결 해제
        pass

    def _on_window_activated(self, chart_id: str) -> None:
        """창 활성화 이벤트 처리"""
        try:
            if chart_id not in self._registered_windows:
                return

            old_state = self._window_states.get(chart_id, 'background')
            new_state = 'active'

            if old_state == new_state:
                return

            self._window_states[chart_id] = new_state

            # 리소스 관리자 업데이트
            self._resource_manager.update_window_state(chart_id, new_state)

            # 생명주기 이벤트 발행
            self._queue_lifecycle_event(
                chart_id=chart_id,
                lifecycle_type='activated',
                resource_priority=ChartViewerPriority.CHART_HIGH
            )

            self._logger.info(f"창 활성화: {chart_id} ({old_state} → {new_state})")

        except Exception as e:
            self._logger.error(f"창 활성화 처리 실패: {chart_id} - {e}")

    def _on_window_deactivated(self, chart_id: str) -> None:
        """창 비활성화 이벤트 처리"""
        try:
            if chart_id not in self._registered_windows:
                return

            old_state = self._window_states.get(chart_id, 'active')
            new_state = 'background'

            if old_state == new_state:
                return

            self._window_states[chart_id] = new_state

            # 리소스 관리자 업데이트
            self._resource_manager.update_window_state(chart_id, new_state)

            # 생명주기 이벤트 발행
            self._queue_lifecycle_event(
                chart_id=chart_id,
                lifecycle_type='deactivated',
                resource_priority=ChartViewerPriority.CHART_BACKGROUND
            )

            self._logger.info(f"창 비활성화: {chart_id} ({old_state} → {new_state})")

        except Exception as e:
            self._logger.error(f"창 비활성화 처리 실패: {chart_id} - {e}")

    def _on_window_minimized(self, chart_id: str) -> None:
        """창 최소화 이벤트 처리"""
        try:
            if chart_id not in self._registered_windows:
                return

            old_state = self._window_states.get(chart_id, 'active')
            new_state = 'minimized'

            if old_state == new_state:
                return

            self._window_states[chart_id] = new_state

            # 리소스 관리자 업데이트
            self._resource_manager.update_window_state(chart_id, new_state)

            # 생명주기 이벤트 발행
            self._queue_lifecycle_event(
                chart_id=chart_id,
                lifecycle_type='minimized',
                resource_priority=ChartViewerPriority.CHART_LOW
            )

            self._logger.info(f"창 최소화: {chart_id} ({old_state} → {new_state})")

        except Exception as e:
            self._logger.error(f"창 최소화 처리 실패: {chart_id} - {e}")

    def _on_window_restored(self, chart_id: str) -> None:
        """창 복원 이벤트 처리"""
        try:
            if chart_id not in self._registered_windows:
                return

            old_state = self._window_states.get(chart_id, 'minimized')
            new_state = 'active'

            if old_state == new_state:
                return

            self._window_states[chart_id] = new_state

            # 리소스 관리자 업데이트
            self._resource_manager.update_window_state(chart_id, new_state)

            # 생명주기 이벤트 발행
            self._queue_lifecycle_event(
                chart_id=chart_id,
                lifecycle_type='restored',
                resource_priority=ChartViewerPriority.CHART_HIGH
            )

            self._logger.info(f"창 복원: {chart_id} ({old_state} → {new_state})")

        except Exception as e:
            self._logger.error(f"창 복원 처리 실패: {chart_id} - {e}")

    def _on_window_closed(self, chart_id: str) -> None:
        """창 종료 이벤트 처리"""
        try:
            # 등록 해제 수행
            self.unregister_window(chart_id)

        except Exception as e:
            self._logger.error(f"창 종료 처리 실패: {chart_id} - {e}")

    def _queue_lifecycle_event(self, chart_id: str, lifecycle_type: str,
                              resource_priority: int) -> None:
        """생명주기 이벤트를 큐에 추가 (비동기 처리를 위해)"""
        try:
            # 메모리 제한 계산
            memory_limits = {
                'activated': 256,
                'deactivated': 128,
                'minimized': 64,
                'restored': 256,
                'closed': 0
            }
            memory_limit = memory_limits.get(lifecycle_type, 128)

            # 이벤트 정보를 큐에 추가
            event_info = {
                'chart_id': chart_id,
                'lifecycle_type': lifecycle_type,
                'resource_priority': resource_priority,
                'memory_limit': memory_limit
            }
            self._pending_events.append(event_info)

        except Exception as e:
            self._logger.error(f"생명주기 이벤트 큐 추가 실패: {chart_id} - {e}")

    def _process_pending_events(self) -> None:
        """대기 중인 이벤트들을 처리"""
        if not self._pending_events:
            return

        events_to_process = self._pending_events.copy()
        self._pending_events.clear()

        for event_info in events_to_process:
            try:
                # 생명주기 이벤트 생성
                lifecycle_event = ChartLifecycleEvent(
                    chart_id=event_info['chart_id'],
                    symbol="",  # 빈 값으로 설정
                    lifecycle_type=event_info['lifecycle_type'],
                    resource_priority=event_info['resource_priority'],
                    memory_limit_mb=event_info['memory_limit']
                )

                # 기존 이벤트 버스를 통해 발행 (동기적 발행)
                # publish는 async이므로 이벤트 버스의 동기 방법을 사용해야 함
                # 여기서는 나중에 처리할 수 있도록 로그만 남김
                self._logger.debug(
                    f"생명주기 이벤트 준비: {event_info['chart_id']} "
                    f"({event_info['lifecycle_type']}, "
                    f"우선순위: {event_info['resource_priority']})"
                )

                # 실제 이벤트 발행은 후속 Phase에서 구현
                # 현재는 이벤트 구조만 검증

            except Exception as e:
                self._logger.error(
                    f"생명주기 이벤트 처리 실패: {event_info['chart_id']} - {e}"
                )

    def get_lifecycle_statistics(self) -> Dict[str, int]:
        """생명주기 통계 조회"""
        stats = {
            'total_windows': len(self._registered_windows),
            'active': 0,
            'background': 0,
            'minimized': 0,
            'pending_events': len(self._pending_events)
        }

        for state in self._window_states.values():
            if state in stats:
                stats[state] += 1

        return stats

    def cleanup(self) -> None:
        """리소스 정리"""
        try:
            # 타이머 중지
            if self._event_timer.isActive():
                self._event_timer.stop()

            # 모든 등록된 창 해제
            chart_ids = list(self._registered_windows.keys())
            for chart_id in chart_ids:
                self.unregister_window(chart_id)

            self._registered_windows.clear()
            self._window_states.clear()
            self._pending_events.clear()

            self._logger.info("창 생명주기 관리자 정리 완료")

        except Exception as e:
            self._logger.error(f"창 생명주기 관리자 정리 실패: {e}")


# 헬퍼 함수들
def create_window_lifecycle_manager(event_bus: IEventBus,
                                   resource_manager: ChartViewerResourceManager) -> WindowLifecycleManager:
    """창 생명주기 관리자 팩토리 함수"""
    return WindowLifecycleManager(event_bus, resource_manager)


def get_memory_limit_for_state(window_state: str) -> int:
    """창 상태에 따른 메모리 제한 반환"""
    limits = {
        'active': 256,
        'background': 128,
        'minimized': 64,
        'closed': 0
    }
    return limits.get(window_state, 128)
