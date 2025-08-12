"""
Database Status Widget

데이터베이스 상태를 표시하는 전용 UI 위젯입니다.
MVP 패턴에 따라 Presenter로부터 상태 정보를 받아 표시합니다.

Features:
- 실시간 데이터베이스 상태 표시
- 연결 상태, 응답 시간, 파일 크기 등
- 테마 시스템 완전 통합
- 상태별 색상 및 아이콘 표시
- DB 재연결 및 새로고침 기능
"""

from typing import Dict, Any, Optional
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QFrame, QProgressBar, QPushButton
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont

from upbit_auto_trading.infrastructure.logging import create_component_logger

class DatabaseStatusWidget(QWidget):
    """
    데이터베이스 상태 표시 위젯

    각 데이터베이스의 실시간 상태를 시각적으로 표시합니다.
    """

    # 상태 클릭 시그널 (상세 정보 요청)
    status_clicked = pyqtSignal(str)  # database_type
    # 재연결 요청 시그널
    refresh_requested = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("widget-database-status")
        self._logger = create_component_logger("DatabaseStatusWidget")

        self._database_labels = {}
        self._status_data = {}

        self._setup_ui()

    def _setup_ui(self):
        """UI 구성 - 새로고침 버튼 추가"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(6)

        # 새로고침 버튼 추가
        refresh_button = QPushButton("🔄 상태 새로고침")
        refresh_button.setObjectName("button-refresh-status")
        refresh_button.clicked.connect(self.refresh_requested.emit)
        layout.addWidget(refresh_button)

        # 구분선
        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        line.setFrameShadow(QFrame.Shadow.Sunken)
        layout.addWidget(line)

        # 데이터베이스별 상태 표시
        db_types = [
            ("settings", "⚙️ Settings"),
            ("strategies", "📈 Strategies"),
            ("market_data", "📊 Market Data")
        ]

        for db_type, display_name in db_types:
            status_frame = self._create_status_frame(db_type, display_name)
            layout.addWidget(status_frame)

        layout.addStretch()

    def _create_status_frame(self, db_type: str, display_name: str) -> QFrame:
        """개별 데이터베이스 상태 프레임 생성"""
        frame = QFrame()
        frame.setObjectName(f"frame-db-status-{db_type}")
        frame.setFrameStyle(QFrame.Shape.StyledPanel)
        frame.setCursor(Qt.CursorShape.PointingHandCursor)

        layout = QVBoxLayout(frame)
        layout.setContentsMargins(8, 6, 8, 6)
        layout.setSpacing(4)

        # 데이터베이스 이름
        name_label = QLabel(display_name)
        name_font = QFont()
        name_font.setBold(True)
        name_label.setFont(name_font)
        layout.addWidget(name_label)

        # 상태 정보 라벨
        status_label = QLabel("상태 확인 중...")
        status_label.setObjectName(f"label-status-{db_type}")
        layout.addWidget(status_label)

        # 상세 정보 라벨
        detail_label = QLabel("")
        detail_label.setObjectName(f"label-detail-{db_type}")
        layout.addWidget(detail_label)

        # 프레임 클릭 이벤트 - 올바른 시그니처 사용
        def on_frame_click(a0):
            self.status_clicked.emit(db_type)
        frame.mousePressEvent = on_frame_click

        # 라벨 참조 저장
        self._database_labels[db_type] = {
            'frame': frame,
            'status': status_label,
            'detail': detail_label
        }

        return frame

    def update_status(self, status_data: Dict[str, Any]) -> None:
        """
        상태 정보 업데이트

        Args:
            status_data: 데이터베이스별 상태 정보
        """
        try:
            self._status_data = status_data

            for db_type, labels in self._database_labels.items():
                if db_type in status_data:
                    db_status = status_data[db_type]
                    self._update_database_status(db_type, db_status, labels)
                else:
                    self._update_database_status(db_type, None, labels)

        except Exception as e:
            self._logger.error(f"❌ 상태 업데이트 실패: {e}")

    def _update_database_status(self, db_type: str, db_status: Optional[Dict[str, Any]],
                                labels: Dict[str, Any]) -> None:
        """개별 데이터베이스 상태 업데이트 - 상세 정보 포함"""
        frame = labels['frame']
        status_label = labels['status']
        detail_label = labels['detail']

        if db_status is None:
            # 상태 정보 없음
            status_label.setText("❓ 상태 불명")
            detail_label.setText("정보 없음")
            frame.setStyleSheet(f"#frame-db-status-{db_type} {{ background-color: #f0f0f0; }}")
            return

        is_healthy = db_status.get('is_healthy', False)
        response_time = db_status.get('response_time_ms', 0)
        file_size_mb = db_status.get('file_size_mb', 0)
        error_message = db_status.get('error_message', '')
        table_count = db_status.get('table_count', 0)
        last_check = db_status.get('last_check_time', '')
        has_secure_keys = db_status.get('has_secure_keys', False)

        if is_healthy:
            # 정상 상태 - 상세 정보 표시
            status_label.setText("✅ 정상 연결")

            # 테이블 정보와 보안 키 상태 포함
            detail_parts = [
                f"{response_time:.1f}ms",
                f"{file_size_mb:.1f}MB",
                f"{table_count}개 테이블"
            ]

            if db_type == 'settings':
                # 암호화 키 상태를 더 명확하게 표시
                if has_secure_keys:
                    detail_parts.append("🔐 암호키있음")
                else:
                    detail_parts.append("⚠️ 암호키없음")  # 실제 암호화 키가 없는 상태

            if last_check:
                detail_parts.append(f"검사: {last_check}")

            detail_label.setText(" | ".join(detail_parts))
            frame.setStyleSheet(f"#frame-db-status-{db_type} {{ background-color: #e8f5e8; }}")
        else:
            # 오류 상태 - 더 명확한 에러 표시
            status_label.setText("❌ 연결 실패")

            # 에러 유형별 상세 정보
            if "테이블이 없음" in error_message and db_type == 'market_data':
                # Market Data DB는 아직 개발되지 않았으므로 특별 처리
                status_label.setText("⏳ 개발 예정")
                detail_label.setText("시장 데이터 수집 기능 개발 예정")
                frame.setStyleSheet(f"#frame-db-status-{db_type} {{ background-color: #fff3cd; }}")  # 경고 색상
            elif "secure_keys" in error_message:
                detail_label.setText("보안 키 테이블 누락 - DB 교체 필요")
                frame.setStyleSheet(f"#frame-db-status-{db_type} {{ background-color: #ffeaea; }}")
            elif "파일" in error_message or "File" in error_message:
                detail_label.setText("DB 파일 손상 - 백업에서 복원 필요")
                frame.setStyleSheet(f"#frame-db-status-{db_type} {{ background-color: #ffeaea; }}")
            else:
                detail_label.setText(error_message or "연결 실패")
                frame.setStyleSheet(f"#frame-db-status-{db_type} {{ background-color: #ffeaea; }}")

    def get_status_data(self) -> Dict[str, Any]:
        """현재 상태 데이터 반환"""
        return self._status_data.copy()

    def clear_status(self) -> None:
        """상태 정보 초기화"""
        for db_type, labels in self._database_labels.items():
            labels['status'].setText("상태 확인 중...")
            labels['detail'].setText("")
            labels['frame'].setStyleSheet("")

        self._status_data.clear()

class DatabaseProgressWidget(QWidget):
    """
    데이터베이스 작업 진행상황 표시 위젯

    백업, 복원, 검증 등의 작업 진행상황을 표시합니다.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("widget-database-progress")
        self._logger = create_component_logger("DatabaseProgressWidget")

        self._setup_ui()
        self.setVisible(False)  # 기본적으로 숨김

    def _setup_ui(self):
        """UI 구성"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 8, 10, 8)
        layout.setSpacing(6)

        # 작업 상태 라벨
        self.status_label = QLabel("작업 중...")
        status_font = QFont()
        status_font.setBold(True)
        self.status_label.setFont(status_font)
        layout.addWidget(self.status_label)

        # 진행바
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        layout.addWidget(self.progress_bar)

        # 상세 메시지 라벨
        self.detail_label = QLabel("")
        layout.addWidget(self.detail_label)

    def show_progress(self, message: str = "작업 진행 중...") -> None:
        """진행상황 표시"""
        self.status_label.setText(message)
        self.progress_bar.setRange(0, 0)  # 무한 진행바
        self.detail_label.setText("")
        self.setVisible(True)

    def update_progress(self, percentage: int, message: str = "") -> None:
        """진행률 업데이트"""
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(percentage)

        if message:
            self.detail_label.setText(message)

    def hide_progress(self) -> None:
        """진행상황 숨김"""
        self.setVisible(False)
        self.progress_bar.setValue(0)
        self.status_label.setText("작업 중...")
        self.detail_label.setText("")

    def set_error_state(self, error_message: str) -> None:
        """에러 상태 표시"""
        self.status_label.setText("❌ 작업 실패")
        self.detail_label.setText(error_message)
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)

    def set_success_state(self, success_message: str) -> None:
        """성공 상태 표시"""
        self.status_label.setText("✅ 작업 완료")
        self.detail_label.setText(success_message)
        self.progress_bar.setValue(100)
