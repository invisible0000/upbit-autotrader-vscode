"""
데이터베이스 작업 진행 상황 위젯

실제 로그 출력과 명확한 진행바를 포함한 작업 진행 상황 전용 위젯입니다.
DatabaseSettingsView에서 분리되어 독립적으로 관리됩니다.
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QProgressBar,
    QTextEdit, QGroupBox
)
from PyQt6.QtCore import pyqtSignal, QTimer
from PyQt6.QtGui import QFont

# Application Layer - Infrastructure 의존성 격리

class DatabaseTaskProgressWidget(QWidget):
    """
    데이터베이스 작업 진행 상황 위젯

    실제 로그 출력과 명확한 진행바를 표시하는 전용 위젯입니다.
    """

    # 작업 완료 시그널
    task_completed = pyqtSignal(bool)  # success

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("widget-database-task-progress")

        # 로깅 초기화
        # Application Layer 로깅 서비스 사용 (폴백: None)
        self.logger = None

        # 내부 상태
        self._current_task = ""
        self._log_buffer = []
        self._max_log_lines = 10  # 최대 로그 라인 수

        # UI 설정
        self._setup_ui()

        # 기본 상태로 설정
        self.reset_progress()

        self.logger.debug("✅ 데이터베이스 작업 진행 상황 위젯 초기화 완료")

    def _setup_ui(self):
        """UI 구성"""
        # 메인 그룹박스
        self.group_box = QGroupBox("⏳ 작업 진행 상황")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.group_box)

        # 그룹박스 내부 레이아웃
        group_layout = QVBoxLayout(self.group_box)
        group_layout.setContentsMargins(10, 10, 10, 10)
        group_layout.setSpacing(8)

        # 현재 작업 타이틀 라벨 (고정 높이)
        self.task_label = QLabel("대기 중...")
        self.task_label.setObjectName("label-current-task")
        task_font = QFont()
        task_font.setBold(True)
        task_font.setPointSize(10)
        self.task_label.setFont(task_font)
        self.task_label.setFixedHeight(18)  # 고정 높이로 설정
        self.task_label.setStyleSheet("""
            QLabel {
                color: #2c3e50;
                padding: 2px 0px;
            }
        """)
        group_layout.addWidget(self.task_label)

        # 진행바 (고정 높이, 위로 정렬)
        self.progress_bar = QProgressBar()
        self.progress_bar.setObjectName("progress-bar-database-task")
        self.progress_bar.setMinimum(0)
        self.progress_bar.setMaximum(100)
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(True)
        self.progress_bar.setFixedHeight(22)  # 고정 높이
        self.progress_bar.setFormat("준비됨")
        group_layout.addWidget(self.progress_bar)

        # 작업 로그 텍스트 영역 (확장 가능하게 크기 증가)
        self.log_text = QTextEdit()
        self.log_text.setObjectName("text-task-logs")
        self.log_text.setMinimumHeight(80)  # 최소 높이 증가
        self.log_text.setMaximumHeight(300)  # 최대 높이 크게 증가
        self.log_text.setReadOnly(True)
        log_font = QFont()
        log_font.setFamily("Consolas, Monaco, monospace")
        log_font.setPointSize(9)
        self.log_text.setFont(log_font)
        self.log_text.setStyleSheet("""
            QTextEdit {
                background-color: #f8f9fa;
                border: 1px solid #dee2e6;
                border-radius: 4px;
                padding: 6px;
                line-height: 1.4;
            }
        """)
        group_layout.addWidget(self.log_text)

    def start_task(self, task_name: str) -> None:
        """작업 시작"""
        try:
            self._current_task = task_name
            self.task_label.setText(f"진행 중: {task_name}")
            self.progress_bar.setValue(0)
            self.progress_bar.setFormat("시작 중... (0%)")

            # 로그 초기화 및 시작 메시지 추가
            self._log_buffer.clear()
            self._add_log_entry(f"🚀 작업 시작: {task_name}")

            self.logger.info(f"📋 작업 시작: {task_name}")

        except Exception as e:
            self.logger.error(f"❌ 작업 시작 실패: {e}")

    def update_progress(self, progress: int, message: str = "") -> None:
        """진행 상황 업데이트"""
        try:
            # 진행바 업데이트
            progress = max(0, min(100, progress))  # 0-100 범위로 제한
            self.progress_bar.setValue(progress)

            # 메시지가 있으면 진행바 텍스트 업데이트
            if message:
                self.progress_bar.setFormat(f"{message} ({progress}%)")
                self._add_log_entry(f"📊 {message}")
            else:
                self.progress_bar.setFormat(f"{progress}%")

            self.logger.debug(f"📊 진행 상황 업데이트: {progress}% - {message}")

        except Exception as e:
            self.logger.error(f"❌ 진행 상황 업데이트 실패: {e}")

    def complete_task(self, success: bool = True, message: str = "") -> None:
        """작업 완료"""
        try:
            if success:
                self.progress_bar.setValue(100)
                self.progress_bar.setFormat("완료 (100%)")
                self.task_label.setText(f"완료: {self._current_task}")

                completion_msg = message or "작업이 성공적으로 완료되었습니다"
                self._add_log_entry(f"✅ {completion_msg}")

                self.logger.info(f"✅ 작업 완료: {self._current_task}")

                # 3초 후 자동으로 기본 상태로 돌아감
                QTimer.singleShot(3000, self.reset_progress)

            else:
                self.progress_bar.setValue(0)
                self.progress_bar.setFormat("실패")
                self.task_label.setText(f"실패: {self._current_task}")

                error_msg = message or "작업 중 오류가 발생했습니다"
                self._add_log_entry(f"❌ {error_msg}")

                self.logger.warning(f"❌ 작업 실패: {self._current_task}")

                # 5초 후 자동으로 기본 상태로 돌아감
                QTimer.singleShot(5000, self.reset_progress)

            # 작업 완료 시그널 발생
            self.task_completed.emit(success)

        except Exception as e:
            self.logger.error(f"❌ 작업 완료 처리 실패: {e}")

    def reset_progress(self) -> None:
        """기본 상태로 초기화"""
        try:
            self._current_task = ""
            self.task_label.setText("대기 중...")
            self.progress_bar.setValue(0)
            self.progress_bar.setFormat("준비됨")

            # 로그는 지우지 않고 준비 메시지만 추가
            self._add_log_entry("💤 대기 상태")

            self.logger.debug("🔄 진행 상황 위젯 초기화 완료")

        except Exception as e:
            self.logger.error(f"❌ 진행 상황 초기화 실패: {e}")

    def add_log_message(self, message: str) -> None:
        """외부에서 로그 메시지 추가"""
        try:
            self._add_log_entry(message)
            self.logger.debug(f"📝 외부 로그 추가: {message}")
        except Exception as e:
            self.logger.error(f"❌ 외부 로그 추가 실패: {e}")

    def _add_log_entry(self, message: str) -> None:
        """로그 항목 추가 (내부용)"""
        try:
            from datetime import datetime

            # 타임스탬프 추가
            timestamp = datetime.now().strftime("%H:%M:%S")
            log_entry = f"[{timestamp}] {message}"

            # 버퍼에 추가
            self._log_buffer.append(log_entry)

            # 최대 라인 수 제한
            if len(self._log_buffer) > self._max_log_lines:
                self._log_buffer = self._log_buffer[-self._max_log_lines:]

            # 텍스트 영역 업데이트
            self.log_text.setPlainText("\n".join(self._log_buffer))

            # 스크롤을 맨 아래로
            cursor = self.log_text.textCursor()
            cursor.movePosition(cursor.MoveOperation.End)
            self.log_text.setTextCursor(cursor)

        except Exception as e:
            self.logger.error(f"❌ 로그 항목 추가 실패: {e}")

    def get_current_task(self) -> str:
        """현재 작업 이름 반환"""
        return self._current_task

    def is_task_running(self) -> bool:
        """작업이 실행 중인지 확인"""
        return bool(self._current_task) and self.progress_bar.value() < 100
