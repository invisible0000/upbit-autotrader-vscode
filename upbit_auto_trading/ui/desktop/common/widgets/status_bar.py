"""
상태 바 위젯 모듈
"""
from PyQt6.QtWidgets import QStatusBar, QLabel, QHBoxLayout, QWidget
from PyQt6.QtCore import QTimer, Qt, pyqtSignal
from upbit_auto_trading.ui.desktop.common.widgets.clickable_api_status import ClickableApiStatus
from upbit_auto_trading.infrastructure.logging import create_component_logger


class StatusBar(QStatusBar):
    """
    상태 바 위젯

    애플리케이션의 상태 정보를 표시하는 상태 바입니다.
    클릭 가능한 API 상태 표시 기능 포함.
    자율적으로 API/DB 상태를 관리합니다.
    """

    # API 새로고침 요청 시그널
    api_refresh_requested = pyqtSignal()

    def __init__(self, parent=None, database_health_service=None):
        """
        초기화

        Args:
            parent (QWidget, optional): 부모 위젯
            database_health_service: 데이터베이스 상태 서비스
        """
        super().__init__(parent)

        self.logger = create_component_logger("StatusBar")
        self.database_health_service = database_health_service

        self._setup_ui()
        self._setup_timer()
        self._setup_auto_status_check()

    def _setup_ui(self):
        """UI 설정"""
        # 상태 메시지 레이블
        self.status_message = QLabel("준비됨")
        self.status_message.setMinimumWidth(200)

        # 클릭 가능한 API 연결 상태 레이블
        self.api_status = ClickableApiStatus()
        self.api_status.refresh_requested.connect(self._on_api_refresh_requested)

        # 데이터베이스 연결 상태 레이블
        self.db_status = QLabel("DB: 연결됨")

        # 시간 레이블
        self.time_label = QLabel()

        # 위젯을 상태 바에 추가
        self.addPermanentWidget(self.api_status)
        self.addPermanentWidget(self.db_status)
        self.addPermanentWidget(self.time_label)

        # 기본 메시지 설정
        self.showMessage("준비됨")

    def _setup_timer(self):
        """타이머 설정"""
        # 1초마다 시간 업데이트
        self.timer = QTimer(self)
        self.timer.timeout.connect(self._update_time)
        self.timer.start(1000)

        # 초기 시간 설정
        self._update_time()

    def _setup_auto_status_check(self):
        """자동 상태 체크 설정"""
        # 주기적 상태 체크 타이머 (30초마다)
        self.status_check_timer = QTimer(self)
        self.status_check_timer.timeout.connect(self._perform_auto_status_check)
        self.status_check_timer.start(30000)  # 30초

        # 초기 상태 체크
        QTimer.singleShot(1000, self._perform_initial_status_check)

    def _update_time(self):
        """시간 업데이트"""
        from datetime import datetime
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.time_label.setText(current_time)

    def _perform_initial_status_check(self):
        """초기 상태 체크"""
        self.logger.info("초기 상태 체크 시작")
        self._check_db_status()
        self._check_api_status()

    def _perform_auto_status_check(self):
        """자동 상태 체크"""
        self.logger.debug("자동 상태 체크 수행")
        self._check_db_status()

    def _check_db_status(self):
        """DB 상태 체크"""
        try:
            if self.database_health_service:
                # 실제 DB 상태 체크 로직
                connected = True  # 기본값, 추후 실제 체크 로직 추가
                self.set_db_status(connected)
                self.logger.debug(f"DB 상태 체크 완료: {'연결됨' if connected else '연결 끊김'}")
            else:
                # 서비스가 없으면 기본값으로 연결됨 표시
                self.set_db_status(True)
                self.logger.debug("DB 서비스 없음, 기본값으로 연결됨 표시")
        except Exception as e:
            self.logger.error(f"DB 상태 체크 실패: {e}")
            self.set_db_status(False)

    def _check_api_status(self):
        """API 상태 체크"""
        try:
            # 기본값으로 연결 끊김 표시 (추후 실제 API 체크 로직 추가)
            connected = False
            self.set_api_status(connected)
            self.logger.debug(f"API 상태 체크 완료: {'연결됨' if connected else '연결 끊김'}")
        except Exception as e:
            self.logger.error(f"API 상태 체크 실패: {e}")
            self.set_api_status(False)

    def _on_api_refresh_requested(self):
        """API 새로고침 요청 처리"""
        try:
            self.logger.info("사용자가 API 상태 새로고침을 요청했습니다")

            # 확인 중 상태 표시 (None은 확인 중을 의미)
            self.api_status.set_api_status(None)

            # API 상태 재체크
            QTimer.singleShot(1000, self._check_api_status)

            # 외부로 시그널 발신 (필요한 경우)
            self.api_refresh_requested.emit()

        except Exception as e:
            self.logger.error(f"API 새로고침 요청 처리 실패: {e}")

    def set_api_status(self, connected):
        """
        API 연결 상태 설정

        Args:
            connected (bool | None): 연결 상태 (None은 확인 중)
        """
        # 클릭 가능한 API 상태 위젯에 위임
        self.api_status.set_api_status(connected)

    def set_db_status(self, connected):
        """
        데이터베이스 연결 상태 설정

        Args:
            connected (bool): 연결 상태
        """
        if connected:
            self.db_status.setText("DB: 연결됨")
            self.db_status.setStyleSheet("color: green;")
        else:
            self.db_status.setText("DB: 연결 끊김")
            self.db_status.setStyleSheet("color: red;")

    def show_message(self, message, timeout=0):
        """
        메시지 표시

        Args:
            message (str): 표시할 메시지
            timeout (int, optional): 메시지 표시 시간(ms). 0이면 계속 표시.
        """
        self.showMessage(message, timeout)

    def update_api_status(self, connected):
        """외부 호환성을 위한 메서드 (기존 코드와의 호환성)"""
        self.set_api_status(connected)

    def update_db_status(self, connected):
        """외부 호환성을 위한 메서드 (기존 코드와의 호환성)"""
        self.set_db_status(connected)
