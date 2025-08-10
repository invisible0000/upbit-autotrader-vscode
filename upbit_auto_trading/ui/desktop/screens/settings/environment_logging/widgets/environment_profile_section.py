"""
Environment Profile Section
===========================

환경 프로파일 관리 섹션 (좌측 6)
기존 EnvironmentProfileWidget을 재활용하여 구현

Features:
- Development/Testing/Production 환경 선택
- 환경별 프로파일 관리
- 현재 환경 상태 표시
- 환경 전환 기능
"""

from typing import Optional, List, Dict
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QFrame
)
from PyQt6.QtCore import pyqtSignal, Qt
from PyQt6.QtGui import QFont

from upbit_auto_trading.infrastructure.logging import create_component_logger
from .environment_profile_widget import EnvironmentProfileWidget


class EnvironmentProfileSection(QWidget):
    """
    환경 프로파일 관리 섹션

    기존 EnvironmentProfileWidget을 활용하여
    통합 탭의 좌측 섹션으로 구성
    """

    # 시그널 정의
    environment_switch_requested = pyqtSignal(str)  # 환경 전환 요청
    profile_create_requested = pyqtSignal(str)      # 프로파일 생성 요청
    profile_edit_requested = pyqtSignal(str, str)   # 프로파일 편집 요청
    profile_delete_requested = pyqtSignal(str)      # 프로파일 삭제 요청

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.setObjectName("EnvironmentProfileSection")

        # Infrastructure 로깅 초기화
        self._logger = create_component_logger("EnvironmentProfileSection")
        self._logger.info("🏢 환경 프로파일 섹션 초기화 시작")

        self._setup_ui()
        self._connect_signals()

        self._logger.info("✅ 환경 프로파일 섹션 초기화 완료")

    def _setup_ui(self):
        """UI 구성"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(8)

        # 섹션 제목
        self._create_section_header(layout)

        # 기존 환경 프로파일 위젯 활용
        self.profile_widget = EnvironmentProfileWidget()
        layout.addWidget(self.profile_widget)

    def _create_section_header(self, parent_layout: QVBoxLayout):
        """섹션 헤더 생성"""
        header_frame = QFrame()
        header_frame.setObjectName("section-header")
        header_layout = QVBoxLayout(header_frame)
        header_layout.setContentsMargins(8, 8, 8, 8)

        # 제목
        title_label = QLabel("🏢 환경 프로파일 관리")
        title_font = QFont()
        title_font.setPointSize(13)
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_label.setAlignment(Qt.AlignmentFlag.AlignLeft)
        header_layout.addWidget(title_label)

        # 설명
        desc_label = QLabel("Development, Testing, Production 환경을 관리합니다")
        desc_label.setStyleSheet("color: #666; font-size: 10px; margin-bottom: 4px;")
        header_layout.addWidget(desc_label)

        parent_layout.addWidget(header_frame)

        # 구분선
        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        line.setFrameShadow(QFrame.Shadow.Sunken)
        line.setStyleSheet("color: #ddd;")
        parent_layout.addWidget(line)

    def _connect_signals(self):
        """시그널 연결"""
        # 기존 위젯의 시그널을 상위로 전파
        self.profile_widget.environment_switch_requested.connect(
            self.environment_switch_requested.emit
        )
        self.profile_widget.profile_create_requested.connect(
            self.profile_create_requested.emit
        )
        self.profile_widget.profile_edit_requested.connect(
            self.profile_edit_requested.emit
        )
        self.profile_widget.profile_delete_requested.connect(
            self.profile_delete_requested.emit
        )

    # === 외부 API (위임 패턴) ===

    def set_current_environment(self, environment_name: str):
        """현재 환경 설정"""
        self.profile_widget.set_current_environment(environment_name)
        self._logger.info(f"📊 환경 설정: {environment_name}")

    def update_profiles(self, environment_name: str, profiles: List[Dict]):
        """프로파일 목록 업데이트"""
        self.profile_widget.update_profiles(environment_name, profiles)
        self._logger.info(f"📁 {environment_name} 프로파일 업데이트: {len(profiles)}개")

    def show_environment_switch_success(self, new_environment: str):
        """환경 전환 성공 알림"""
        self.profile_widget.show_environment_switch_success(new_environment)

    def show_environment_switch_error(self, error_message: str):
        """환경 전환 실패 알림"""
        self.profile_widget.show_environment_switch_error(error_message)

    def get_current_environment(self) -> str:
        """현재 환경 반환"""
        return self.profile_widget.get_current_environment()

    def enable_widgets(self, enabled: bool):
        """위젯 활성화/비활성화"""
        self.profile_widget.enable_widgets(enabled)
