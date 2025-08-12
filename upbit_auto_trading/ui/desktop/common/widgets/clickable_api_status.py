"""
클릭 가능한 API 상태 위젯

상태바에서 API 연결 상태를 표시하고 클릭으로 수동 새로고침이 가능한 위젯
"""

from PyQt6.QtWidgets import QLabel
from PyQt6.QtCore import QTimer, pyqtSignal, Qt
from PyQt6.QtGui import QMouseEvent, QCursor
from upbit_auto_trading.infrastructure.logging import create_component_logger

class ClickableApiStatus(QLabel):
    """
    클릭 가능한 API 상태 레이블

    - 좌클릭: API 상태 새로고침 요청
    - 10초 쿨다운: 연속 클릭 방지
    - 시각적 피드백: 상태별 색상 변경
    """

    # 시그널 정의
    refresh_requested = pyqtSignal()  # API 새로고침 요청 시그널

    def __init__(self, cooldown_seconds: int = 10, parent=None):
        """
        초기화

        Args:
            cooldown_seconds (int): 쿨다운 시간 (초)
            parent: 부모 위젯
        """
        super().__init__(parent)

        self.cooldown_seconds = cooldown_seconds
        self.is_enabled = True
        self.remaining_time = 0

        # 로깅 설정
        self.logger = create_component_logger("ClickableApiStatus")

        # UI 설정
        self._setup_ui()

        # 쿨다운 타이머 설정
        self._setup_timer()

        # 초기 상태
        self.set_api_status(None)  # 확인 중 상태

    def _setup_ui(self) -> None:
        """UI 초기 설정"""
        self.setMinimumWidth(120)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.setObjectName("clickable-api-status")

        # 기본 툴팁
        self._update_tooltip()

    def _setup_timer(self) -> None:
        """쿨다운 타이머 설정"""
        self.cooldown_timer = QTimer(self)
        self.cooldown_timer.timeout.connect(self._on_cooldown_tick)

    def _update_tooltip(self) -> None:
        """툴팁 업데이트"""
        if self.is_enabled:
            self.setToolTip(
                "클릭하여 API 연결 상태를 새로고침합니다.\n"
                "• 실시간 연결 테스트 수행\n"
                "• 3회 연속 실패 시 자동 감지"
            )
        else:
            self.setToolTip(
                f"쿨다운 중입니다. {self.remaining_time}초 후에 다시 시도하세요.\n"
                "너무 빈번한 API 호출을 방지하기 위한 대기 시간입니다."
            )

    def set_api_status(self, connected: bool = None) -> None:
        """
        API 연결 상태 설정

        Args:
            connected (bool, optional): 연결 상태. None이면 확인 중
        """
        if connected is True:
            self.setText("API: 연결됨")
            self.setStyleSheet("""
                QLabel#clickable-api-status {
                    color: #4CAF50;
                    font-weight: bold;
                    padding: 2px 8px;
                    border: 1px solid #4CAF50;
                    border-radius: 3px;
                    background-color: rgba(76, 175, 80, 0.1);
                }
                QLabel#clickable-api-status:hover {
                    background-color: rgba(76, 175, 80, 0.2);
                }
            """)
        elif connected is False:
            self.setText("API: 연결 끊김")
            self.setStyleSheet("""
                QLabel#clickable-api-status {
                    color: #F44336;
                    font-weight: bold;
                    padding: 2px 8px;
                    border: 1px solid #F44336;
                    border-radius: 3px;
                    background-color: rgba(244, 67, 54, 0.1);
                }
                QLabel#clickable-api-status:hover {
                    background-color: rgba(244, 67, 54, 0.2);
                }
            """)
        else:
            # 확인 중 상태
            self.setText("API: 확인 중...")
            self.setStyleSheet("""
                QLabel#clickable-api-status {
                    color: #FF9800;
                    font-weight: bold;
                    padding: 2px 8px;
                    border: 1px solid #FF9800;
                    border-radius: 3px;
                    background-color: rgba(255, 152, 0, 0.1);
                }
                QLabel#clickable-api-status:hover {
                    background-color: rgba(255, 152, 0, 0.2);
                }
            """)

        self.logger.debug(f"API 상태 업데이트: {connected}")

    def mousePressEvent(self, event: QMouseEvent) -> None:
        """마우스 클릭 이벤트 처리"""
        if (event.button() == Qt.MouseButton.LeftButton and
                self.is_enabled):

            self.logger.info("API 상태 새로고침 요청")
            self.refresh_requested.emit()
            self.start_cooldown()

        super().mousePressEvent(event)

    def start_cooldown(self) -> None:
        """쿨다운 시작"""
        if not self.is_enabled:
            return

        self.is_enabled = False
        self.remaining_time = self.cooldown_seconds

        # 쿨다운 시각적 표시
        self._update_cooldown_display()

        # 1초마다 업데이트
        self.cooldown_timer.start(1000)

        # 마우스 커서 변경
        self.setCursor(QCursor(Qt.CursorShape.ForbiddenCursor))

        self.logger.debug(f"쿨다운 시작: {self.cooldown_seconds}초")

    def _on_cooldown_tick(self) -> None:
        """쿨다운 타이머 틱"""
        self.remaining_time -= 1

        if self.remaining_time <= 0:
            self._end_cooldown()
        else:
            self._update_cooldown_display()
            self._update_tooltip()

    def _update_cooldown_display(self) -> None:
        """쿨다운 상태 표시 업데이트"""
        if self.remaining_time > 0:
            original_text = self.text().split(" (")[0]  # 기존 쿨다운 텍스트 제거
            self.setText(f"{original_text} ({self.remaining_time}초 대기)")

            # 쿨다운 중 스타일
            self.setStyleSheet("""
                QLabel#clickable-api-status {
                    color: #9E9E9E;
                    font-weight: normal;
                    padding: 2px 8px;
                    border: 1px solid #9E9E9E;
                    border-radius: 3px;
                    background-color: rgba(158, 158, 158, 0.1);
                }
            """)

    def _end_cooldown(self) -> None:
        """쿨다운 종료"""
        self.cooldown_timer.stop()
        self.is_enabled = True
        self.remaining_time = 0

        # 텍스트에서 쿨다운 표시 제거
        original_text = self.text().split(" (")[0]
        self.setText(original_text)

        # 마우스 커서 복원
        self.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))

        # 툴팁 업데이트
        self._update_tooltip()

        # API 상태에 따른 스타일 복원
        if "연결됨" in self.text():
            self.set_api_status(True)
        elif "연결 끊김" in self.text():
            self.set_api_status(False)
        else:
            self.set_api_status(None)

        self.logger.debug("쿨다운 종료")

    def reset_cooldown(self) -> None:
        """쿨다운 강제 리셋 (테스트용)"""
        if self.cooldown_timer.isActive():
            self.cooldown_timer.stop()
        self._end_cooldown()
        self.logger.debug("쿨다운 강제 리셋")

    def get_remaining_cooldown(self) -> int:
        """남은 쿨다운 시간 반환"""
        return self.remaining_time if not self.is_enabled else 0

    def is_cooldown_active(self) -> bool:
        """쿨다운 활성 상태 확인"""
        return not self.is_enabled
