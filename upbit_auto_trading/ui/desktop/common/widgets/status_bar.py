"""
상태 바 위젯 모듈
"""
from PyQt6.QtWidgets import QStatusBar, QLabel, QHBoxLayout, QWidget
from PyQt6.QtCore import QTimer, Qt, pyqtSignal
from upbit_auto_trading.ui.desktop.common.widgets.clickable_api_status import ClickableApiStatus


class StatusBar(QStatusBar):
    """
    상태 바 위젯

    애플리케이션의 상태 정보를 표시하는 상태 바입니다.
    클릭 가능한 API 상태 표시 기능 포함.
    """

    # API 새로고침 요청 시그널
    api_refresh_requested = pyqtSignal()

    def __init__(self, parent=None):
        """
        초기화

        Args:
            parent (QWidget, optional): 부모 위젯
        """
        super().__init__(parent)

        self._setup_ui()
        self._setup_timer()

    def _setup_ui(self):
        """UI 설정"""
        # 상태 메시지 레이블
        self.status_message = QLabel("준비됨")
        self.status_message.setMinimumWidth(200)

        # 클릭 가능한 API 연결 상태 레이블
        self.api_status = ClickableApiStatus()
        self.api_status.refresh_requested.connect(self.api_refresh_requested.emit)

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

    def _update_time(self):
        """시간 업데이트"""
        from datetime import datetime
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.time_label.setText(current_time)

    def set_api_status(self, connected):
        """
        API 연결 상태 설정

        Args:
            connected (bool): 연결 상태
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
