"""
클릭 가능한 데이터베이스 상태 위젯

StatusBar에서 DB 연결 상태를 표시하고 클릭으로 수동 새로고침이 가능한 위젯
API 상태와 유사한 구조로 구현되었습니다.
"""

from PyQt6.QtWidgets import QLabel
from PyQt6.QtCore import QTimer, pyqtSignal, Qt
from PyQt6.QtGui import QMouseEvent, QCursor
from upbit_auto_trading.infrastructure.logging import create_component_logger


class ClickableDatabaseStatus(QLabel):
    """
    클릭 가능한 데이터베이스 상태 레이블

    - 좌클릭: DB 상태 새로고침 요청
    - 쿨다운: 연속 클릭 방지
    - 시각적 피드백: 상태별 색상 변경
    """

    # 시그널 정의
    refresh_requested = pyqtSignal()  # DB 새로고침 요청 시그널

    def __init__(self, cooldown_seconds: int = 30, parent=None):
        """
        초기화

        Args:
            cooldown_seconds (int): 쿨다운 시간 (초) - API보다 길게
            parent: 부모 위젯
        """
        super().__init__(parent)

        self.cooldown_seconds = cooldown_seconds
        self.is_enabled = True
        self.remaining_time = 0

        # 로깅 설정
        self.logger = create_component_logger("ClickableDatabaseStatus")

        # UI 설정
        self._setup_ui()

        # 쿨다운 타이머 설정
        self._setup_timer()

        # 초기 상태
        self.set_db_status(None)  # 확인 중 상태

    def _setup_ui(self) -> None:
        """UI 초기 설정"""
        self.setMinimumWidth(150)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.setObjectName("clickable-db-status")

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
                "클릭하여 데이터베이스 연결 상태를 새로고침합니다.\n"
                "• 프로그램 시작 시 자동 검증\n"
                "• 설정 변경 시 자동 검증\n"
                "• 수동 새로고침 가능\n"
                "\n"
                "⚠️ 주의: 너무 빈번한 확인은 성능에 영향을 줄 수 있습니다."
            )
        else:
            self.setToolTip(
                f"쿨다운 중입니다. {self.remaining_time}초 후에 다시 시도하세요.\n"
                "데이터베이스 부하를 방지하기 위한 대기 시간입니다.\n"
                "\n"
                "DB 상태 확인은 안전한 시점에만 수행됩니다:\n"
                "• 프로그램 시작 시\n"
                "• 설정 변경 시\n"
                "• 확실한 문제 감지 시"
            )

    def set_db_status(self, connected: bool = None, status_text: str = None) -> None:
        """
        DB 연결 상태 설정

        Args:
            connected (bool, optional): 연결 상태. None이면 확인 중
            status_text (str, optional): 표시할 텍스트
        """
        if connected is True:
            display_text = status_text or "DB: 연결됨"
            self.setText(display_text)
            self.setStyleSheet("""
                QLabel#clickable-db-status {
                    color: #4CAF50;
                    font-weight: bold;
                    padding: 2px 8px;
                    border: 1px solid #4CAF50;
                    border-radius: 3px;
                    background-color: rgba(76, 175, 80, 0.1);
                }
                QLabel#clickable-db-status:hover {
                    background-color: rgba(76, 175, 80, 0.2);
                }
            """)
        elif connected is False:
            display_text = status_text or "DB: 연결 끊김"
            self.setText(display_text)

            # 상태에 따른 색상 선택
            if "치명적" in display_text:
                # 치명적 상태 - 빨간색
                color = "#D32F2F"
                bg_color = "rgba(211, 47, 47, 0.1)"
                hover_color = "rgba(211, 47, 47, 0.2)"
            elif "오류" in display_text or "실패" in display_text:
                # 오류 상태 - 주황색
                color = "#F57C00"
                bg_color = "rgba(245, 124, 0, 0.1)"
                hover_color = "rgba(245, 124, 0, 0.2)"
            elif "경고" in display_text:
                # 경고 상태 - 노란색
                color = "#FBC02D"
                bg_color = "rgba(251, 192, 45, 0.1)"
                hover_color = "rgba(251, 192, 45, 0.2)"
            else:
                # 기본 연결 끊김 - 빨간색
                color = "#F44336"
                bg_color = "rgba(244, 67, 54, 0.1)"
                hover_color = "rgba(244, 67, 54, 0.2)"

            self.setStyleSheet(f"""
                QLabel#clickable-db-status {{
                    color: {color};
                    font-weight: bold;
                    padding: 2px 8px;
                    border: 1px solid {color};
                    border-radius: 3px;
                    background-color: {bg_color};
                }}
                QLabel#clickable-db-status:hover {{
                    background-color: {hover_color};
                }}
            """)
        else:
            # 확인 중 상태
            display_text = status_text or "DB: 확인 중..."
            self.setText(display_text)
            self.setStyleSheet("""
                QLabel#clickable-db-status {
                    color: #FF9800;
                    font-weight: bold;
                    padding: 2px 8px;
                    border: 1px solid #FF9800;
                    border-radius: 3px;
                    background-color: rgba(255, 152, 0, 0.1);
                }
                QLabel#clickable-db-status:hover {
                    background-color: rgba(255, 152, 0, 0.2);
                }
            """)

        self.logger.debug(f"DB 상태 업데이트: {connected} - {display_text}")

    def mousePressEvent(self, event: QMouseEvent) -> None:
        """마우스 클릭 이벤트 처리"""
        if (event.button() == Qt.MouseButton.LeftButton and
                self.is_enabled):

            self.logger.info("DB 상태 새로고침 요청")
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
                QLabel#clickable-db-status {
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

        # 상태에 따른 스타일 복원
        if "연결됨" in self.text():
            self.set_db_status(True, self.text())
        elif any(word in self.text() for word in ["연결 끊김", "오류", "치명적", "경고", "실패"]):
            self.set_db_status(False, self.text())
        else:
            self.set_db_status(None, self.text())

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

    def set_detailed_tooltip(self, tooltip_text: str) -> None:
        """상세 툴팁 설정 (Presenter에서 호출)"""
        if self.is_enabled:
            self.setToolTip(tooltip_text)
        else:
            # 쿨다운 중에는 쿨다운 메시지 유지
            self._update_tooltip()

```
