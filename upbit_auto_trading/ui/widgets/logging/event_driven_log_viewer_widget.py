"""
Event-Driven 로그 뷰어 위젯 - QAsync 통합 버전
격리 이벤트 루프 패턴을 QAsync 통합 패턴으로 전환
"""

import asyncio
from typing import Dict, List, Optional, Any
from datetime import datetime

# QAsync 통합 imports
try:
    from qasync import asyncSlot
    QASYNC_AVAILABLE = True
except ImportError:
    QASYNC_AVAILABLE = False

    def asyncSlot(*args):
        def decorator(func):
            return func
        return decorator


from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QTextEdit, QComboBox, QLineEdit, QLabel, QCheckBox,
    QFrame
)
from PyQt6.QtCore import QTimer, pyqtSignal, pyqtSlot
from PyQt6.QtGui import QFont, QTextCursor

from upbit_auto_trading.infrastructure.logging import create_component_logger
from upbit_auto_trading.infrastructure.events.logging_events import (
    LogMessageEvent, LogLevel, LogFilterChangedEvent, LogViewerStateChangedEvent
)
from upbit_auto_trading.infrastructure.events.event_system_initializer import EventSystemInitializer
from upbit_auto_trading.infrastructure.events.bus.event_bus_interface import IEventBus
from upbit_auto_trading.infrastructure.database.database_manager import DatabaseManager


class EventDrivenLogViewerWidget(QWidget):
    """Event-Driven Architecture 기반 로그 뷰어 위젯"""

    # PyQt6 신호들 (UI 스레드 안전성 보장)
    log_message_received = pyqtSignal(dict)  # 로그 메시지 수신 신호
    filter_changed = pyqtSignal(str, str, bool)  # 필터 변경 신호

    def __init__(self, db_manager: DatabaseManager, parent=None):
        super().__init__(parent)
        self.db_manager = db_manager
        self.logger = create_component_logger("EventDrivenLogViewerWidget")

        # Event System 초기화
        self.event_bus: Optional[IEventBus] = None
        self.domain_publisher = None
        self._event_subscription_ids: List[str] = []

        # 로그 메시지 저장소 (메모리 캐시)
        self.log_messages: List[Dict[str, Any]] = []
        self.filtered_messages: List[Dict[str, Any]] = []
        self.max_messages = 10000  # 최대 메시지 수

        # 필터 상태
        self.filters = {
            'level': None,
            'logger': '',
            'search_text': '',
            'show_debug': True,
            'show_info': True,
            'show_warning': True,
            'show_error': True,
            'show_critical': True
        }

        # 뷰어 상태
        self.auto_scroll = True
        self.is_paused = False

        # UI 컴포넌트 생성
        self._init_ui()

        # PyQt6 신호 연결
        self._connect_signals()

        # Event System 비동기 초기화
        self._setup_event_system()

        self.logger.info("Event-Driven 로그 뷰어 위젯 초기화 완료")

    def _init_ui(self):
        """UI 컴포넌트 초기화"""
        layout = QVBoxLayout(self)

        # 필터 컨트롤 패널
        filter_panel = self._create_filter_panel()
        layout.addWidget(filter_panel)

        # 로그 텍스트 영역
        self.log_text_edit = QTextEdit()
        self.log_text_edit.setReadOnly(True)
        self.log_text_edit.setFont(QFont("Consolas", 9))
        layout.addWidget(self.log_text_edit)

        # 하단 컨트롤 패널
        control_panel = self._create_control_panel()
        layout.addWidget(control_panel)

        # 레이아웃 비율 설정
        layout.setStretch(1, 1)  # 로그 텍스트 영역이 대부분 공간 차지

    def _create_filter_panel(self) -> QFrame:
        """필터 컨트롤 패널 생성"""
        frame = QFrame()
        frame.setFrameStyle(QFrame.Shape.Box)
        layout = QHBoxLayout(frame)

        # 로그 레벨 필터
        layout.addWidget(QLabel("레벨:"))
        self.level_combo = QComboBox()
        self.level_combo.addItems(["모든 레벨", "DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"])
        layout.addWidget(self.level_combo)

        # 로거 이름 필터
        layout.addWidget(QLabel("로거:"))
        self.logger_filter = QLineEdit()
        self.logger_filter.setPlaceholderText("로거 이름으로 필터...")
        layout.addWidget(self.logger_filter)

        # 검색 텍스트 필터
        layout.addWidget(QLabel("검색:"))
        self.search_filter = QLineEdit()
        self.search_filter.setPlaceholderText("메시지 내용으로 검색...")
        layout.addWidget(self.search_filter)

        # 레벨별 체크박스
        level_checkboxes_layout = QHBoxLayout()
        self.level_checkboxes = {}
        for level in ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]:
            checkbox = QCheckBox(level)
            checkbox.setChecked(True)
            self.level_checkboxes[level] = checkbox
            level_checkboxes_layout.addWidget(checkbox)

        layout.addLayout(level_checkboxes_layout)
        layout.addStretch()

        return frame

    def _create_control_panel(self) -> QFrame:
        """하단 컨트롤 패널 생성"""
        frame = QFrame()
        layout = QHBoxLayout(frame)

        # 자동 스크롤 체크박스
        self.auto_scroll_checkbox = QCheckBox("자동 스크롤")
        self.auto_scroll_checkbox.setChecked(True)
        layout.addWidget(self.auto_scroll_checkbox)

        # 일시정지 버튼
        self.pause_button = QPushButton("일시정지")
        self.pause_button.setCheckable(True)
        layout.addWidget(self.pause_button)

        # 클리어 버튼
        self.clear_button = QPushButton("클리어")
        layout.addWidget(self.clear_button)

        # 내보내기 버튼
        self.export_button = QPushButton("내보내기")
        layout.addWidget(self.export_button)

        # 통계 라벨
        self.stats_label = QLabel("메시지: 0")
        layout.addWidget(self.stats_label)

        layout.addStretch()

        return frame

    def _connect_signals(self):
        """PyQt6 신호 연결"""
        # 내부 신호 연결
        self.log_message_received.connect(self._on_log_message_received)
        self.filter_changed.connect(self._on_filter_changed)

        # UI 컨트롤 신호 연결
        self.level_combo.currentTextChanged.connect(
            lambda text: self._emit_filter_changed('level', text, text != "모든 레벨")
        )
        self.logger_filter.textChanged.connect(
            lambda text: self._emit_filter_changed('logger', text, bool(text))
        )
        self.search_filter.textChanged.connect(
            lambda text: self._emit_filter_changed('search_text', text, bool(text))
        )

        # 레벨 체크박스 연결
        for level, checkbox in self.level_checkboxes.items():
            checkbox.toggled.connect(
                lambda checked, l=level: self._emit_filter_changed(f'show_{l.lower()}', checked, True)
            )

        # 컨트롤 버튼 연결
        self.auto_scroll_checkbox.toggled.connect(self._on_auto_scroll_changed)
        self.pause_button.toggled.connect(self._on_pause_toggled)
        self.clear_button.clicked.connect(self._on_clear_clicked)
        self.export_button.clicked.connect(self._on_export_clicked)

    def _setup_event_system(self):
        """Event System 비동기 초기화"""
        # QAsync 환경에서 비동기 초기화
        QTimer.singleShot(0, self._trigger_async_setup)

    @asyncSlot()
    async def _trigger_async_setup(self):
        """QAsync 통합 Event System 설정"""
        try:
            if not QASYNC_AVAILABLE:
                self.logger.error("QAsync가 설치되지 않았습니다")
                return

            # 간단한 Event System 생성 (비동기 초기화 없음)
            self.event_bus, self.domain_publisher = EventSystemInitializer.create_simple_event_system(
                self.db_manager
            )

            # 이벤트 구독 설정
            self._subscribe_to_events()

            # 🎯 핵심 변경: 격리 루프 대신 직접 await
            await self.event_bus.start()

            self.logger.info("Event System 초기화 및 시작 완료 (QAsync 모드)")

        except Exception as e:
            self.logger.error(f"Event System 초기화 실패: {e}")

    def _subscribe_to_events(self):
        """이벤트 구독 설정"""
        if not self.event_bus:
            return

        try:
            # 로그 메시지 이벤트 구독
            subscription_id = self.event_bus.subscribe(
                event_type="logging.message",
                handler=self._handle_log_message_event,
                priority=1  # 높은 우선순위
            )
            self._event_subscription_ids.append(subscription_id)

            # 로그 필터 변경 이벤트 구독
            subscription_id = self.event_bus.subscribe(
                event_type="ui.log_filter_changed",
                handler=self._handle_filter_changed_event,
                priority=2
            )
            self._event_subscription_ids.append(subscription_id)

            self.logger.info(f"이벤트 구독 완료: {len(self._event_subscription_ids)}개 구독")

        except Exception as e:
            self.logger.error(f"이벤트 구독 실패: {e}")

    def _handle_log_message_event(self, event_data: Dict[str, Any]) -> None:
        """로그 메시지 이벤트 처리"""
        try:
            # 이벤트 데이터에서 로그 정보 추출
            message_data = {
                'timestamp': event_data.get('occurred_at', datetime.now().isoformat()),
                'level': event_data.get('data', {}).get('level', 'INFO'),
                'logger_name': event_data.get('data', {}).get('logger_name', 'Unknown'),
                'message': event_data.get('data', {}).get('message', ''),
                'module_name': event_data.get('data', {}).get('module_name'),
                'function_name': event_data.get('data', {}).get('function_name'),
                'line_number': event_data.get('data', {}).get('line_number'),
                'thread_name': event_data.get('data', {}).get('thread_name'),
                'tags': event_data.get('data', {}).get('tags', {}),
                'extra_data': event_data.get('data', {}).get('extra_data', {})
            }

            # UI 스레드로 신호 전송
            self.log_message_received.emit(message_data)

        except Exception as e:
            # Event 처리 실패는 로깅하지 않음 (무한 루프 방지)
            pass

    def _handle_filter_changed_event(self, event_data: Dict[str, Any]) -> None:
        """필터 변경 이벤트 처리"""
        try:
            data = event_data.get('data', {})
            filter_type = data.get('filter_type', '')
            filter_value = data.get('filter_value', '')
            is_active = data.get('is_active', False)

            # UI 스레드로 신호 전송
            self.filter_changed.emit(filter_type, str(filter_value), is_active)

        except Exception as e:
            self.logger.error(f"필터 변경 이벤트 처리 실패: {e}")

    @pyqtSlot(dict)
    def _on_log_message_received(self, message_data: Dict[str, Any]):
        """로그 메시지 수신 처리 (UI 스레드)"""
        if self.is_paused:
            return

        # 메시지 저장
        self.log_messages.append(message_data)

        # 최대 메시지 수 제한
        if len(self.log_messages) > self.max_messages:
            self.log_messages = self.log_messages[-self.max_messages:]

        # 필터링 적용
        self._apply_filters()

        # UI 업데이트
        self._update_log_display()
        self._update_stats()

    @pyqtSlot(str, str, bool)
    def _on_filter_changed(self, filter_type: str, filter_value: str, is_active: bool):
        """필터 변경 처리 (UI 스레드)"""
        # 필터 상태 업데이트
        if filter_type == 'level':
            self.filters['level'] = filter_value if is_active else None
        elif filter_type in ['logger', 'search_text']:
            self.filters[filter_type] = filter_value
        elif filter_type.startswith('show_'):
            self.filters[filter_type] = filter_value == 'True' or filter_value is True

        # 필터 재적용
        self._apply_filters()
        self._update_log_display()

    def _emit_filter_changed(self, filter_type: str, filter_value: Any, is_active: bool):
        """필터 변경 이벤트 발행"""
        try:
            if self.event_bus:
                # LogFilterChangedEvent 생성 및 발행
                event = LogFilterChangedEvent(
                    filter_type=filter_type,
                    filter_value=filter_value,
                    is_active=is_active
                )

                # 이벤트 발행 (비동기)
                asyncio.create_task(self.event_bus.publish(event.to_dict()))

        except Exception as e:
            self.logger.error(f"필터 변경 이벤트 발행 실패: {e}")

    def _apply_filters(self):
        """현재 필터 설정에 따라 메시지 필터링"""
        self.filtered_messages = []

        for message in self.log_messages:
            if self._message_passes_filter(message):
                self.filtered_messages.append(message)

    def _message_passes_filter(self, message: Dict[str, Any]) -> bool:
        """메시지가 현재 필터를 통과하는지 확인"""
        # 레벨 필터
        level = message.get('level', 'INFO')
        if not self.filters.get(f'show_{level.lower()}', True):
            return False

        # 특정 레벨 필터
        if self.filters.get('level') and self.filters['level'] != level:
            return False

        # 로거 이름 필터
        logger_filter = self.filters.get('logger', '').strip()
        if logger_filter:
            logger_name = message.get('logger_name', '').lower()
            if logger_filter.lower() not in logger_name:
                return False

        # 검색 텍스트 필터
        search_filter = self.filters.get('search_text', '').strip()
        if search_filter:
            message_text = message.get('message', '').lower()
            if search_filter.lower() not in message_text:
                return False

        return True

    def _update_log_display(self):
        """로그 디스플레이 업데이트"""
        if not self.filtered_messages:
            return

        # 새 메시지만 추가 (성능 최적화)
        current_line_count = self.log_text_edit.document().lineCount()
        new_messages = self.filtered_messages[current_line_count-1:] if current_line_count > 1 else self.filtered_messages

        cursor = self.log_text_edit.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.End)

        for message in new_messages:
            formatted_message = self._format_log_message(message)
            cursor.insertText(formatted_message + '\n')

        # 자동 스크롤
        if self.auto_scroll:
            self.log_text_edit.ensureCursorVisible()

    def _format_log_message(self, message: Dict[str, Any]) -> str:
        """로그 메시지 포맷팅"""
        timestamp = message.get('timestamp', '')
        if '.' in timestamp:
            timestamp = timestamp.split('.')[0]  # 마이크로초 제거

        level = message.get('level', 'INFO')
        logger_name = message.get('logger_name', 'Unknown')
        text = message.get('message', '')

        # 모듈/함수 정보가 있으면 추가
        location = ""
        if message.get('module_name') and message.get('function_name'):
            location = f" [{message['module_name']}.{message['function_name']}:{message.get('line_number', '?')}]"

        return f"{timestamp} [{level:8}] {logger_name}{location}: {text}"

    def _update_stats(self):
        """통계 정보 업데이트"""
        total_messages = len(self.log_messages)
        filtered_messages = len(self.filtered_messages)

        if total_messages == filtered_messages:
            stats_text = f"메시지: {total_messages}"
        else:
            stats_text = f"메시지: {filtered_messages}/{total_messages}"

        self.stats_label.setText(stats_text)

    def _on_auto_scroll_changed(self, checked: bool):
        """자동 스크롤 설정 변경"""
        self.auto_scroll = checked

        # 상태 변경 이벤트 발행
        self._emit_viewer_state_changed("auto_scroll_changed", str(not checked), str(checked))

    def _on_pause_toggled(self, checked: bool):
        """일시정지 토글"""
        self.is_paused = checked
        self.pause_button.setText("재시작" if checked else "일시정지")

        # 상태 변경 이벤트 발행
        self._emit_viewer_state_changed("pause_toggled", str(not checked), str(checked))

    def _on_clear_clicked(self):
        """로그 클리어"""
        self.log_messages.clear()
        self.filtered_messages.clear()
        self.log_text_edit.clear()
        self._update_stats()

        # 상태 변경 이벤트 발행
        self._emit_viewer_state_changed("log_cleared", None, None)

    def _on_export_clicked(self):
        """로그 내보내기"""
        # TODO: 파일 저장 다이얼로그 구현
        self.logger.info("로그 내보내기 기능 준비 중...")

        # 상태 변경 이벤트 발행
        self._emit_viewer_state_changed("export_requested", None, None)

    def _emit_viewer_state_changed(self, state_change: str, previous_state: Optional[str], new_state: Optional[str]):
        """뷰어 상태 변경 이벤트 발행"""
        try:
            if self.event_bus:
                event = LogViewerStateChangedEvent(
                    viewer_id="main_log_viewer",
                    state_change=state_change,
                    previous_state=previous_state,
                    new_state=new_state
                )

                # 이벤트 발행 (비동기)
                asyncio.create_task(self.event_bus.publish(event.to_dict()))

        except Exception as e:
            self.logger.error(f"뷰어 상태 변경 이벤트 발행 실패: {e}")

    def closeEvent(self, event):
        """위젯 종료 시 정리"""
        try:
            # 이벤트 구독 해제
            if self.event_bus and self._event_subscription_ids:
                for subscription_id in self._event_subscription_ids:
                    asyncio.create_task(self.event_bus.unsubscribe(subscription_id))

            # Event System 종료
            if self.event_bus:
                asyncio.create_task(
                    EventSystemInitializer.shutdown_event_system(self.event_bus, timeout=5.0)
                )

            self.logger.info("Event-Driven 로그 뷰어 위젯 정리 완료")

        except Exception as e:
            self.logger.error(f"위젯 정리 실패: {e}")

        super().closeEvent(event)

# Event Handler 함수들 (독립적으로 사용 가능)
def create_log_message_event_from_log_record(record) -> LogMessageEvent:
    """Python logging.LogRecord에서 LogMessageEvent 생성"""
    try:
        level_mapping = {
            'DEBUG': LogLevel.DEBUG,
            'INFO': LogLevel.INFO,
            'WARNING': LogLevel.WARNING,
            'ERROR': LogLevel.ERROR,
            'CRITICAL': LogLevel.CRITICAL
        }

        return LogMessageEvent(
            message=record.getMessage(),
            level=level_mapping.get(record.levelname, LogLevel.INFO),
            logger_name=record.name,
            module_name=getattr(record, 'module', None),
            function_name=record.funcName,
            line_number=record.lineno,
            thread_name=getattr(record, 'threadName', None),
            process_id=getattr(record, 'process', None),
            tags={},
            extra_data=getattr(record, '__dict__', {})
        )

    except Exception as e:
        # Fallback event
        return LogMessageEvent(
            message=str(record),
            level=LogLevel.INFO,
            logger_name="unknown",
            tags={"error": "event_creation_failed", "original_error": str(e)}
        )
