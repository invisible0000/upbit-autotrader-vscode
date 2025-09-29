"""
API 연결 테스트 위젯

API 연결 상태 확인 및 테스트 기능을 제공하는 위젯

Phase 2 마이그레이션으로 생성됨:
- 기존: ApiKeyManagerSecure의 연결 테스트 부분
- 새로운: 독립적인 위젯으로 분리
"""

from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QPushButton,
                             QLabel, QGroupBox)
from PyQt6.QtCore import pyqtSignal, Qt

# Application Layer - Infrastructure 의존성 격리
from upbit_auto_trading.application.services.logging_application_service import IPresentationLogger

class ApiConnectionWidget(QWidget):
    """
    API 연결 테스트 위젯

    API 키 테스트 및 연결 상태 표시를 담당합니다.
    """

    # 시그널 정의
    test_requested = pyqtSignal()
    connection_status_changed = pyqtSignal(bool)  # connected

    def __init__(self, parent=None, logging_service: IPresentationLogger = None):
        """API 연결 위젯 초기화

        Args:
            parent: 부모 위젯
            logging_service: Application Layer 로깅 서비스
        """
        super().__init__(parent)
        self.setObjectName("widget-api-connection")

        # 로깅 설정 - DI 패턴 적용
        if logging_service:
            self.logger = logging_service.get_component_logger("ApiConnectionWidget")
        else:
            raise ValueError("ApiConnectionWidget에 logging_service가 주입되지 않았습니다")

        # 상태 관리
        self._is_connected = False
        self._last_test_result = ""

        self._setup_ui()
        self._connect_signals()

        self.logger.info("✅ API 연결 테스트 위젯 초기화 완료")

    def _setup_ui(self):
        """UI 설정"""
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(10)

        # 연결 상태 그룹
        connection_group = QGroupBox("API 연결 상태")
        connection_layout = QVBoxLayout(connection_group)

        # 상태 표시 레이블
        self.status_label = QLabel("상태: 미연결")
        self.status_label.setObjectName("label-connection-status")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        connection_layout.addWidget(self.status_label)

        # 테스트 결과 레이블
        self.result_label = QLabel("")
        self.result_label.setObjectName("label-test-result")
        self.result_label.setWordWrap(True)
        self.result_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        connection_layout.addWidget(self.result_label)

        # 테스트 버튼
        self.test_button = QPushButton("연결 테스트")
        self.test_button.setObjectName("button-test-connection")
        self.test_button.setEnabled(False)  # 기본적으로 비활성화
        connection_layout.addWidget(self.test_button)

        self.main_layout.addWidget(connection_group)

    def _connect_signals(self):
        """시그널 연결"""
        self.test_button.clicked.connect(self._on_test_clicked)

    def _on_test_clicked(self):
        """테스트 버튼 클릭 시 처리"""
        self.logger.info("🔧 API 연결 테스트 요청")
        self.test_requested.emit()

    def update_connection_status(self, connected: bool, message: str = ""):
        """연결 상태 업데이트"""
        self._is_connected = connected
        self._last_test_result = message

        if connected:
            self.status_label.setText("상태: ✅ 연결됨")
            self.status_label.setStyleSheet("color: green; font-weight: bold;")
            if message:
                self.result_label.setText(f"✅ {message}")
                self.result_label.setStyleSheet("color: green;")
        else:
            self.status_label.setText("상태: ❌ 연결 끊김")
            self.status_label.setStyleSheet("color: red; font-weight: bold;")
            if message:
                self.result_label.setText(f"❌ {message}")
                self.result_label.setStyleSheet("color: red;")

        self.connection_status_changed.emit(connected)
        self.logger.debug(f"연결 상태 업데이트: {'연결됨' if connected else '끊김'}")

    def set_test_button_enabled(self, enabled: bool):
        """테스트 버튼 활성화 상태 설정"""
        self.test_button.setEnabled(enabled)

    def set_test_button_tooltip(self, tooltip: str):
        """테스트 버튼 툴팁 설정"""
        self.test_button.setToolTip(tooltip)

    def clear_status(self):
        """상태 초기화"""
        self._is_connected = False
        self._last_test_result = ""
        self.status_label.setText("상태: 미연결")
        self.status_label.setStyleSheet("color: #666666;")  # 회색으로 표시
        self.result_label.setText("연결 테스트를 눌러 상태를 확인하세요")
        self.result_label.setStyleSheet("color: #666666; font-style: italic;")
        self.connection_status_changed.emit(False)
        self.logger.debug("연결 상태 초기화 완료")

    def is_connected(self) -> bool:
        """현재 연결 상태 반환"""
        return self._is_connected

    def get_last_test_result(self) -> str:
        """마지막 테스트 결과 반환"""
        return self._last_test_result
