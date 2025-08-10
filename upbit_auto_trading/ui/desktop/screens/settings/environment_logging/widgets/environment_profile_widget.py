"""
Environment Profile Management Widget

환경별 데이터베이스 프로파일 및 환경변수 관리를 위한 전용 UI 위젯입니다.
이미 구현된 DatabaseProfileManagementUseCase와 연동되어
Development/Testing/Production 환경을 관리합니다.

Features:
- 환경별 프로파일 표시 및 전환
- 환경별 로깅 환경변수 관리 (구현됨)
- 환경별 거래/API 설정 관리 (미구현)
- 프로파일 생성/편집/삭제
- 환경 전환 시 안전성 검증
- MVP 패턴 완전 적용
"""

import os
from typing import List, Dict
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QButtonGroup, QRadioButton,
    QFrame, QMessageBox, QComboBox, QGroupBox,
    QGridLayout, QCheckBox, QLineEdit, QTabWidget
)
from PyQt6.QtCore import pyqtSignal
from PyQt6.QtGui import QFont

from upbit_auto_trading.infrastructure.logging import create_component_logger


class EnvironmentProfileWidget(QWidget):
    """
    환경 프로파일 관리 위젯

    Development/Testing/Production 환경별 데이터베이스 프로파일을 관리합니다.
    이미 구현된 DatabaseProfileManagementUseCase와 완전히 연동됩니다.
    """

    # 시그널 정의
    environment_switch_requested = pyqtSignal(str)  # 환경 전환 요청 (environment_name)
    profile_create_requested = pyqtSignal(str)      # 프로파일 생성 요청 (environment_name)
    profile_edit_requested = pyqtSignal(str, str)   # 프로파일 편집 요청 (environment, profile_id)
    profile_delete_requested = pyqtSignal(str)      # 프로파일 삭제 요청 (profile_id)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("widget-environment-profile")
        self._logger = create_component_logger("EnvironmentProfileWidget")

        # 현재 상태
        self._current_environment = "Development"  # 기본값
        self._environments = {
            "Development": {
                "icon": "🛠️",
                "color": "#4CAF50",
                "description": "개발 및 테스트용 환경",
                "details": "실제 거래 없음, 로그 상세 출력, 디버깅 기능 활성화",
                "profiles": []
            },
            "Testing": {
                "icon": "🧪",
                "color": "#FF9800",
                "description": "전략 검증 및 백테스팅 환경",
                "details": "시뮬레이션 모드, 성능 측정, 안정성 검증",
                "profiles": []
            },
            "Production": {
                "icon": "🚀",
                "color": "#F44336",
                "description": "실제 거래 환경",
                "details": "실거래 모드, 최적화된 성능, 안전장치 활성화",
                "profiles": []
            }
        }

        self._setup_ui()
        self._connect_signals()

        self._logger.info("🏢 환경 프로파일 위젯 초기화 완료")

    def _setup_ui(self):
        """UI 구성 - 환경 선택 + 프로파일 관리"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(8)

        # 제목 제거 - 그룹박스에서 이미 표시됨

        # 현재 환경 표시
        self._create_current_environment_section(layout)

        # 구분선
        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        line.setFrameShadow(QFrame.Shadow.Sunken)
        layout.addWidget(line)

        # 환경 선택 섹션
        self._create_environment_selection_section(layout)

        # 구분선
        line2 = QFrame()
        line2.setFrameShape(QFrame.Shape.HLine)
        line2.setFrameShadow(QFrame.Shadow.Sunken)
        layout.addWidget(line2)

        # 프로파일 관리 섹션
        self._create_profile_management_section(layout)

        layout.addStretch()

    def _create_current_environment_section(self, parent_layout):
        """현재 환경 표시 섹션"""
        current_label = QLabel("📊 현재 환경")
        current_font = QFont()
        current_font.setBold(True)
        current_label.setFont(current_font)
        parent_layout.addWidget(current_label)

        # 현재 환경 표시
        self.current_env_display = QLabel()
        self.current_env_display.setObjectName("label-current-environment")
        self._update_current_environment_display()
        parent_layout.addWidget(self.current_env_display)

    def _create_environment_selection_section(self, parent_layout):
        """환경 선택 섹션 - 개선된 UI"""
        selection_label = QLabel("🔄 환경 전환")
        selection_font = QFont()
        selection_font.setBold(True)
        selection_label.setFont(selection_font)
        parent_layout.addWidget(selection_label)

        # 환경 선택 카드들
        env_cards_layout = QVBoxLayout()
        self.env_button_group = QButtonGroup(self)

        for i, (env_name, env_data) in enumerate(self._environments.items()):
            # 환경 카드 컨테이너
            card_frame = QFrame()
            card_frame.setObjectName(f"env-card-{env_name.lower()}")
            card_frame.setFrameStyle(QFrame.Shape.Box)
            card_frame.setStyleSheet(f"""
                QFrame#env-card-{env_name.lower()} {{
                    border: 2px solid #ddd;
                    border-radius: 8px;
                    padding: 8px;
                    margin: 2px;
                }}
                QFrame#env-card-{env_name.lower()}:hover {{
                    border-color: {env_data['color']};
                    background-color: rgba(76, 175, 80, 0.1);
                }}
            """)

            card_layout = QHBoxLayout(card_frame)
            card_layout.setContentsMargins(12, 8, 12, 8)

            # 라디오 버튼
            radio_btn = QRadioButton()
            radio_btn.setObjectName(f"radio-env-{env_name.lower()}")

            # 기본값으로 Development 선택
            if env_name == self._current_environment:
                radio_btn.setChecked(True)
                card_frame.setStyleSheet(f"""
                    QFrame#env-card-{env_name.lower()} {{
                        border: 2px solid {env_data['color']};
                        border-radius: 8px;
                        padding: 8px;
                        margin: 2px;
                        background-color: rgba(76, 175, 80, 0.2);
                    }}
                """)

            self.env_button_group.addButton(radio_btn, i)
            card_layout.addWidget(radio_btn)

            # 아이콘
            icon_label = QLabel(env_data['icon'])
            icon_label.setStyleSheet("font-size: 20px; margin-right: 8px;")
            card_layout.addWidget(icon_label)

            # 환경 정보
            info_layout = QVBoxLayout()
            info_layout.setSpacing(2)

            # 환경 이름
            name_label = QLabel(env_name)
            name_font = QFont()
            name_font.setBold(True)
            name_font.setPointSize(12)
            name_label.setFont(name_font)
            name_label.setStyleSheet(f"color: {env_data['color']};")
            info_layout.addWidget(name_label)

            # 환경 설명
            desc_label = QLabel(env_data['description'])
            desc_label.setStyleSheet("font-size: 10px; color: #666;")
            info_layout.addWidget(desc_label)

            # 상세 정보
            details_label = QLabel(env_data['details'])
            details_label.setStyleSheet("font-size: 9px; color: #888;")
            details_label.setWordWrap(True)
            info_layout.addWidget(details_label)

            card_layout.addLayout(info_layout)
            card_layout.addStretch()

            env_cards_layout.addWidget(card_frame)

        parent_layout.addLayout(env_cards_layout)

        # 환경 전환 버튼
        switch_layout = QHBoxLayout()
        self.switch_env_btn = QPushButton("🔄 선택한 환경으로 전환")
        self.switch_env_btn.setObjectName("button-switch-environment")
        self.switch_env_btn.setEnabled(False)  # 다른 환경 선택 시 활성화
        self.switch_env_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 8px 16px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
            QPushButton:disabled {
                background-color: #cccccc;
                color: #666666;
            }
        """)
        switch_layout.addWidget(self.switch_env_btn)
        switch_layout.addStretch()
        parent_layout.addLayout(switch_layout)

    def _create_profile_management_section(self, parent_layout):
        """프로파일 관리 섹션"""
        management_label = QLabel("📁 프로파일 관리")
        management_font = QFont()
        management_font.setBold(True)
        management_label.setFont(management_font)
        parent_layout.addWidget(management_label)

        # 프로파일 목록 (현재는 간단하게)
        self.profile_combo = QComboBox()
        self.profile_combo.setObjectName("combo-profiles")
        parent_layout.addWidget(self.profile_combo)

        # 관리 버튼들
        button_layout = QHBoxLayout()

        self.create_profile_btn = QPushButton("➕ 새 프로파일")
        self.create_profile_btn.setObjectName("button-create-profile")

        self.edit_profile_btn = QPushButton("✏️ 편집")
        self.edit_profile_btn.setObjectName("button-edit-profile")

        self.delete_profile_btn = QPushButton("🗑️ 삭제")
        self.delete_profile_btn.setObjectName("button-delete-profile")

        button_layout.addWidget(self.create_profile_btn)
        button_layout.addWidget(self.edit_profile_btn)
        button_layout.addWidget(self.delete_profile_btn)
        button_layout.addStretch()

        parent_layout.addLayout(button_layout)

    def _connect_signals(self):
        """시그널 연결"""
        # 환경 선택 변경 감지
        self.env_button_group.buttonClicked.connect(self._on_environment_selection_changed)

        # 환경 전환 버튼
        self.switch_env_btn.clicked.connect(self._on_switch_environment_clicked)

        # 프로파일 관리 버튼들
        self.create_profile_btn.clicked.connect(self._on_create_profile_clicked)
        self.edit_profile_btn.clicked.connect(self._on_edit_profile_clicked)
        self.delete_profile_btn.clicked.connect(self._on_delete_profile_clicked)

    def _update_current_environment_display(self):
        """현재 환경 표시 업데이트 - 향상된 시각적 표시"""
        env_data = self._environments[self._current_environment]

        # 환경별 배경색과 스타일 적용
        status_html = f"""
        <div style='padding: 12px; border-radius: 8px; background-color: {env_data['color']}20;
                    border-left: 4px solid {env_data['color']}; margin: 4px 0;'>
            <div style='font-size: 16px; font-weight: bold; color: {env_data['color']}; margin-bottom: 4px;'>
                {env_data['icon']} {self._current_environment} 환경 활성
            </div>
            <div style='font-size: 12px; color: #666; margin-bottom: 2px;'>
                {env_data['description']}
            </div>
            <div style='font-size: 10px; color: #888;'>
                {env_data['details']}
            </div>
        </div>
        """

        self.current_env_display.setText(status_html)
        self.current_env_display.setWordWrap(True)

    def _on_environment_selection_changed(self, button):
        """환경 선택 변경 처리"""
        # 버튼 그룹에서 현재 선택된 버튼의 ID로 환경 확인
        button_id = self.env_button_group.id(button)
        environment_names = list(self._environments.keys())

        if 0 <= button_id < len(environment_names):
            selected_env = environment_names[button_id]
        else:
            self._logger.warning(f"⚠️ 잘못된 환경 선택 ID: {button_id}")
            return

        # 현재 환경과 다르면 전환 버튼 활성화
        if selected_env != self._current_environment:
            self.switch_env_btn.setEnabled(True)
            self.switch_env_btn.setText(f"🔄 {selected_env}로 전환")
        else:
            self.switch_env_btn.setEnabled(False)
            self.switch_env_btn.setText("🔄 환경 전환")

        self._logger.info(f"🔄 환경 선택 변경: {selected_env}")

    def _on_switch_environment_clicked(self):
        """환경 전환 버튼 클릭 처리"""
        # 선택된 환경 확인
        checked_button = self.env_button_group.checkedButton()
        if not checked_button:
            return

        # 버튼 ID로 환경명 확인
        button_id = self.env_button_group.id(checked_button)
        environment_names = list(self._environments.keys())

        if 0 <= button_id < len(environment_names):
            selected_env = environment_names[button_id]
        else:
            self._logger.warning(f"⚠️ 잘못된 환경 전환 요청 ID: {button_id}")
            return

        # 확인 다이얼로그
        reply = QMessageBox.question(
            self,
            "환경 전환 확인",
            f"데이터베이스 환경을 '{selected_env}'로 전환하시겠습니까?\n\n"
            f"⚠️ 이 작업은 전체 시스템에 영향을 줄 수 있습니다.\n"
            f"계속하시겠습니까?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            self._logger.info(f"🔄 환경 전환 요청: {self._current_environment} → {selected_env}")
            self.environment_switch_requested.emit(selected_env)
        else:
            # 취소 시 원래 환경으로 라디오 버튼 복원
            for i, (env_name, _) in enumerate(self._environments.items()):
                if env_name == self._current_environment:
                    button = self.env_button_group.button(i)
                    if button:
                        button.setChecked(True)
                    break
            self.switch_env_btn.setEnabled(False)
            self.switch_env_btn.setText("🔄 환경 전환")

    def _on_create_profile_clicked(self):
        """프로파일 생성 버튼 클릭 처리"""
        self._logger.info(f"➕ 프로파일 생성 요청: {self._current_environment}")
        self.profile_create_requested.emit(self._current_environment)

    def _on_edit_profile_clicked(self):
        """프로파일 편집 버튼 클릭 처리"""
        current_profile = self.profile_combo.currentText()
        if current_profile:
            self._logger.info(f"✏️ 프로파일 편집 요청: {current_profile}")
            # 실제로는 profile_id를 사용해야 하지만, 현재는 이름으로 대체
            self.profile_edit_requested.emit(self._current_environment, current_profile)

    def _on_delete_profile_clicked(self):
        """프로파일 삭제 버튼 클릭 처리"""
        current_profile = self.profile_combo.currentText()
        if current_profile:
            reply = QMessageBox.question(
                self,
                "프로파일 삭제 확인",
                f"프로파일 '{current_profile}'을 삭제하시겠습니까?\n\n"
                f"⚠️ 이 작업은 취소할 수 없습니다.",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No
            )

            if reply == QMessageBox.StandardButton.Yes:
                self._logger.info(f"🗑️ 프로파일 삭제 요청: {current_profile}")
                self.profile_delete_requested.emit(current_profile)

    # === 외부 API (Presenter에서 호출) ===

    def set_current_environment(self, environment_name: str):
        """현재 환경 설정"""
        if environment_name in self._environments:
            self._current_environment = environment_name
            self._update_current_environment_display()

            # 라디오 버튼도 업데이트
            for i, (env_name, _) in enumerate(self._environments.items()):
                if env_name == environment_name:
                    button = self.env_button_group.button(i)
                    if button:
                        button.setChecked(True)
                    break

            # 전환 버튼 비활성화
            self.switch_env_btn.setEnabled(False)
            self.switch_env_btn.setText("🔄 환경 전환")

            self._logger.info(f"📊 현재 환경 설정됨: {environment_name}")

    def update_profiles(self, environment_name: str, profiles: List[Dict]):
        """특정 환경의 프로파일 목록 업데이트"""
        if environment_name in self._environments:
            self._environments[environment_name]["profiles"] = profiles

            # 현재 환경이면 콤보박스 업데이트
            if environment_name == self._current_environment:
                self.profile_combo.clear()
                for profile in profiles:
                    profile_name = profile.get('profile_name', 'Unknown')
                    self.profile_combo.addItem(profile_name)

            self._logger.info(f"📁 {environment_name} 프로파일 목록 업데이트: {len(profiles)}개")

    def show_environment_switch_success(self, new_environment: str):
        """환경 전환 성공 알림"""
        QMessageBox.information(
            self,
            "환경 전환 완료",
            f"데이터베이스 환경이 '{new_environment}'로 성공적으로 전환되었습니다."
        )

    def show_environment_switch_error(self, error_message: str):
        """환경 전환 실패 알림"""
        QMessageBox.critical(
            self,
            "환경 전환 실패",
            f"환경 전환 중 오류가 발생했습니다:\n\n{error_message}"
        )

    def get_current_environment(self) -> str:
        """현재 환경 반환"""
        return self._current_environment

    def enable_widgets(self, enabled: bool):
        """위젯 활성화/비활성화"""
        self.switch_env_btn.setEnabled(enabled)
        self.create_profile_btn.setEnabled(enabled)
        self.edit_profile_btn.setEnabled(enabled)
        self.delete_profile_btn.setEnabled(enabled)

        for button in self.env_button_group.buttons():
            button.setEnabled(enabled)
