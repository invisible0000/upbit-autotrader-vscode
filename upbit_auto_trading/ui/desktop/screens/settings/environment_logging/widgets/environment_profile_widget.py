"""
Environment Profile Management Widget

환경별 데이터베이스 프로파일 및 환경변수 관리를 위한 전용 UI 위젯입니다.
ConfigProfileService와 연동되어 기본/커스텀 프로파일을 관리합니다.

Features:
- 기본 프로파일 (development/production/testing) 전환
- 커스텀 프로파일 저장/로드/삭제
- 프로파일 미리보기 및 정보 표시
- 환경별 로깅 환경변수 관리
- 실시간 프로파일 스위칭
- MVP 패턴 완전 적용
"""

import os
from typing import List, Dict, Optional
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QButtonGroup, QRadioButton,
    QFrame, QMessageBox, QComboBox, QGroupBox,
    QGridLayout, QCheckBox, QLineEdit, QTabWidget,
    QDialog, QTextEdit, QDialogButtonBox
)
from PyQt6.QtCore import pyqtSignal, QTimer
from PyQt6.QtGui import QFont

from upbit_auto_trading.infrastructure.logging import create_component_logger
from upbit_auto_trading.application.services.config_profile_service import ConfigProfileService


class CustomProfileSaveDialog(QDialog):
    """커스텀 프로파일 저장 다이얼로그"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("커스텀 프로파일 저장")
        self.setModal(True)
        self.setFixedSize(400, 200)

        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)

        # 프로파일명 입력
        name_layout = QHBoxLayout()
        name_layout.addWidget(QLabel("프로파일명:"))
        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText("영문, 숫자, _ 만 사용 가능")
        name_layout.addWidget(self.name_edit)
        layout.addLayout(name_layout)

        # 설명 입력
        desc_layout = QVBoxLayout()
        desc_layout.addWidget(QLabel("설명 (선택사항):"))
        self.desc_edit = QTextEdit()
        self.desc_edit.setMaximumHeight(80)
        self.desc_edit.setPlaceholderText("프로파일에 대한 설명을 입력하세요...")
        desc_layout.addWidget(self.desc_edit)
        layout.addLayout(desc_layout)

        # 버튼
        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)

    def get_profile_name(self) -> str:
        return self.name_edit.text().strip()

    def get_description(self) -> str:
        return self.desc_edit.toPlainText().strip()


class EnvironmentProfileWidget(QWidget):
    """
    환경 프로파일 관리 위젯

    Development/Testing/Production 환경별 프로파일과
    사용자 커스텀 프로파일을 관리합니다.
    ConfigProfileService와 완전히 연동됩니다.
    """

    # 시그널 정의
    environment_switch_requested = pyqtSignal(str)  # 환경 전환 요청 (environment_name)
    profile_create_requested = pyqtSignal(str)      # 프로파일 생성 요청 (environment_name)
    profile_edit_requested = pyqtSignal(str, str)   # 프로파일 편집 요청 (environment, profile_id)
    profile_delete_requested = pyqtSignal(str)      # 프로파일 삭제 요청 (profile_id)
    profile_switched = pyqtSignal(str)              # 프로파일 스위칭 완료 (profile_name)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("widget-environment-profile")
        self._logger = create_component_logger("EnvironmentProfileWidget")

        # ConfigProfileService 초기화
        self._profile_service = ConfigProfileService()

        # 현재 상태 - 시스템 환경변수 우선
        self._current_environment = self._detect_system_environment()
        self._current_profile = None
        self._available_profiles = []

        # 환경 정보 업데이트 (기본 프로파일명에 맞춤)
        self._environments = {
            "development": {
                "icon": "🛠️",
                "color": "#4CAF50",
                "description": "개발 및 테스트용 환경",
                "details": "실제 거래 없음, 로그 상세 출력, 디버깅 기능 활성화",
            },
            "testing": {
                "icon": "🧪",
                "color": "#FF9800",
                "description": "전략 검증 및 백테스팅 환경",
                "details": "시뮬레이션 모드, 성능 측정, 안정성 검증",
            },
            "production": {
                "icon": "🚀",
                "color": "#F44336",
                "description": "실제 거래 환경",
                "details": "실거래 모드, 최적화된 성능, 안전장치 활성화",
            }
        }

        self._setup_ui()
        self._connect_signals()
        self._load_available_profiles()

        # 시스템 환경에 맞는 프로파일 자동 적용
        self._auto_apply_system_profile()

        self._logger.info("🏢 환경 프로파일 위젯 초기화 완료")

    def _setup_ui(self):
        """UI 구성 - 환경 선택 + 프로파일 관리"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(8)

        # 현재 환경 표시
        self._create_current_environment_section(layout)

        # 구분선
        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        line.setFrameShadow(QFrame.Shadow.Sunken)
        layout.addWidget(line)

        # 프로파일 선택 섹션 (기본 + 커스텀)
        self._create_profile_selection_section(layout)

        # 구분선
        line2 = QFrame()
        line2.setFrameShape(QFrame.Shape.HLine)
        line2.setFrameShadow(QFrame.Shadow.Sunken)
        layout.addWidget(line2)

        # 커스텀 프로파일 관리 섹션
        self._create_custom_profile_management_section(layout)

        layout.addStretch()

    def _load_available_profiles(self):
        """사용 가능한 프로파일 목록 로드"""
        try:
            self._available_profiles = self._profile_service.get_available_profiles()
            self._logger.info(f"📋 사용 가능한 프로파일 로드: {len(self._available_profiles)}개")
            self._update_profile_combo()
        except Exception as e:
            self._logger.error(f"❌ 프로파일 목록 로드 실패: {e}")
            self._available_profiles = []

    def _update_profile_combo(self):
        """프로파일 콤보박스 업데이트"""
        if hasattr(self, 'profile_combo'):
            self.profile_combo.clear()

            # 기본 프로파일과 커스텀 프로파일 분리 표시
            basic_profiles = [p for p in self._available_profiles if not p.startswith('custom_')]
            custom_profiles = [p for p in self._available_profiles if p.startswith('custom_')]

            # 기본 프로파일 추가
            if basic_profiles:
                for profile in sorted(basic_profiles):
                    display_name = profile.capitalize()
                    self.profile_combo.addItem(f"🏢 {display_name}", profile)

            # 구분선 추가 (커스텀 프로파일이 있는 경우)
            if custom_profiles and basic_profiles:
                self.profile_combo.insertSeparator(self.profile_combo.count())

            # 커스텀 프로파일 추가
            if custom_profiles:
                for profile in sorted(custom_profiles):
                    display_name = profile.replace('custom_', '').replace('_', ' ').title()
                    self.profile_combo.addItem(f"👤 {display_name}", profile)

            # 현재 프로파일 선택
            current_profile = self._profile_service.get_current_profile()
            if current_profile:
                for i in range(self.profile_combo.count()):
                    if self.profile_combo.itemData(i) == current_profile:
                        self.profile_combo.setCurrentIndex(i)
                        break

    def _create_current_environment_section(self, parent_layout):
        """현재 프로파일 상태 표시 섹션"""
        current_label = QLabel("🎯 현재 활성 프로파일")
        current_font = QFont()
        current_font.setBold(True)
        current_label.setFont(current_font)
        parent_layout.addWidget(current_label)

        # 현재 프로파일 표시
        self.current_profile_display = QLabel()
        self.current_profile_display.setObjectName("label-current-profile")
        self._update_current_profile_display()
        parent_layout.addWidget(self.current_profile_display)

    def _create_profile_selection_section(self, parent_layout):
        """프로파일 선택 섹션"""
        selection_label = QLabel("📋 프로파일 선택")
        selection_font = QFont()
        selection_font.setBold(True)
        selection_label.setFont(selection_font)
        parent_layout.addWidget(selection_label)

        # 프로파일 선택 콤보박스
        profile_layout = QHBoxLayout()

        self.profile_combo = QComboBox()
        self.profile_combo.setObjectName("combo-profiles")
        self.profile_combo.setMinimumHeight(35)
        profile_layout.addWidget(self.profile_combo, 3)

        # 프로파일 전환 버튼
        self.switch_profile_btn = QPushButton("🔄 전환")
        self.switch_profile_btn.setObjectName("button-switch-profile")
        self.switch_profile_btn.setMinimumHeight(35)
        self.switch_profile_btn.setStyleSheet("""
            QPushButton {
                background-color: #2196F3;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 8px 16px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #1976D2;
            }
            QPushButton:disabled {
                background-color: #cccccc;
                color: #666666;
            }
        """)
        profile_layout.addWidget(self.switch_profile_btn, 1)

        parent_layout.addLayout(profile_layout)

        # 프로파일 미리보기 영역
        self.profile_preview_frame = QFrame()
        self.profile_preview_frame.setObjectName("profile-preview")
        self.profile_preview_frame.setFrameStyle(QFrame.Shape.Box)
        self.profile_preview_frame.setStyleSheet("""
            QFrame#profile-preview {
                border: 1px solid #ddd;
                border-radius: 6px;
                background-color: #f9f9f9;
                padding: 8px;
                margin: 4px 0;
            }
        """)

        preview_layout = QVBoxLayout(self.profile_preview_frame)
        preview_layout.setContentsMargins(12, 8, 12, 8)

        self.profile_preview_label = QLabel("프로파일을 선택하면 설정 미리보기가 표시됩니다.")
        self.profile_preview_label.setStyleSheet("color: #666; font-size: 10px;")
        preview_layout.addWidget(self.profile_preview_label)

        parent_layout.addWidget(self.profile_preview_frame)

    def _create_custom_profile_management_section(self, parent_layout):
        """커스텀 프로파일 관리 섹션"""
        management_label = QLabel("👤 커스텀 프로파일 관리")
        management_font = QFont()
        management_font.setBold(True)
        management_label.setFont(management_font)
        parent_layout.addWidget(management_label)

        # 관리 버튼들
        button_layout = QHBoxLayout()

        self.save_current_btn = QPushButton("💾 현재 설정 저장")
        self.save_current_btn.setObjectName("button-save-current")
        self.save_current_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 8px 12px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
        """)

        self.delete_profile_btn = QPushButton("🗑️ 삭제")
        self.delete_profile_btn.setObjectName("button-delete-profile")
        self.delete_profile_btn.setStyleSheet("""
            QPushButton {
                background-color: #f44336;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 8px 12px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #d32f2f;
            }
        """)

        self.refresh_profiles_btn = QPushButton("🔄 새로고침")
        self.refresh_profiles_btn.setObjectName("button-refresh-profiles")
        self.refresh_profiles_btn.setStyleSheet("""
            QPushButton {
                background-color: #FF9800;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 8px 12px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #F57C00;
            }
        """)

        button_layout.addWidget(self.save_current_btn)
        button_layout.addWidget(self.delete_profile_btn)
        button_layout.addWidget(self.refresh_profiles_btn)
        button_layout.addStretch()

        parent_layout.addLayout(button_layout)

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
        # 프로파일 선택 변경 감지
        self.profile_combo.currentTextChanged.connect(self._on_profile_selection_changed)

        # 프로파일 전환 버튼
        self.switch_profile_btn.clicked.connect(self._on_switch_profile_clicked)

        # 커스텀 프로파일 관리 버튼들
        self.save_current_btn.clicked.connect(self._on_save_current_clicked)
        self.delete_profile_btn.clicked.connect(self._on_delete_profile_clicked)
        self.refresh_profiles_btn.clicked.connect(self._on_refresh_profiles_clicked)

    def _on_profile_selection_changed(self, text):
        """프로파일 선택 변경 처리"""
        if not text:
            return

        # 선택된 프로파일의 실제 이름 조회
        current_index = self.profile_combo.currentIndex()
        if current_index >= 0:
            profile_name = self.profile_combo.itemData(current_index)
            if profile_name:
                self._show_profile_preview(profile_name)

                # 현재 프로파일과 다르면 전환 버튼 활성화
                current_profile = self._profile_service.get_current_profile()
                self.switch_profile_btn.setEnabled(profile_name != current_profile)

    def _show_profile_preview(self, profile_name: str):
        """프로파일 미리보기 표시"""
        try:
            # 프로파일 정보 및 설정 미리보기
            profile_info = self._profile_service.get_profile_info(profile_name)
            preview_settings = self._profile_service.preview_profile_changes(profile_name)

            preview_html = f"""
            <div style='padding: 8px; margin: 4px 0;'>
                <div style='font-weight: bold; color: #333; margin-bottom: 6px;'>
                    📄 {profile_info.get('name', profile_name)} 프로파일
                </div>
                <div style='font-size: 10px; color: #666; margin-bottom: 8px;'>
                    {profile_info.get('description', '설명 없음')}
                </div>
                <div style='font-size: 9px; color: #888;'>
                    <b>적용될 설정:</b><br/>
            """

            if preview_settings:
                for key, value in preview_settings.items():
                    display_key = key.replace('UPBIT_', '').replace('_', ' ').title()
                    preview_html += f"• {display_key}: {value}<br/>"
            else:
                preview_html += "• 설정 정보 없음<br/>"

            preview_html += "</div></div>"

            self.profile_preview_label.setText(preview_html)
            self.profile_preview_label.setWordWrap(True)

        except Exception as e:
            self._logger.warning(f"⚠️ 프로파일 미리보기 실패: {e}")
            self.profile_preview_label.setText(f"미리보기를 불러올 수 없습니다: {str(e)}")

    def _on_switch_profile_clicked(self):
        """프로파일 전환 버튼 클릭 처리"""
        current_index = self.profile_combo.currentIndex()
        if current_index < 0:
            return

        profile_name = self.profile_combo.itemData(current_index)
        if not profile_name:
            return

        # 확인 다이얼로그
        reply = QMessageBox.question(
            self,
            "프로파일 전환 확인",
            f"환경 설정을 '{profile_name}' 프로파일로 전환하시겠습니까?\n\n"
            f"⚠️ 현재 환경변수 설정이 변경됩니다.\n"
            f"계속하시겠습니까?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            self._switch_to_profile(profile_name)

    def _switch_to_profile(self, profile_name: str):
        """실제 프로파일 전환 수행"""
        try:
            self._logger.info(f"🔄 프로파일 전환 시작: {profile_name}")

            # ConfigProfileService를 통한 프로파일 전환
            result = self._profile_service.switch_profile(profile_name)

            if result.success:
                self._logger.info(f"✅ 프로파일 전환 성공: {profile_name}")

                # UI 업데이트
                self._current_profile = profile_name
                self._update_current_profile_display()
                self.switch_profile_btn.setEnabled(False)

                # 성공 메시지
                QMessageBox.information(
                    self,
                    "프로파일 전환 완료",
                    f"프로파일이 '{profile_name}'로 성공적으로 전환되었습니다.\n\n"
                    f"적용된 환경변수: {len(result.env_vars_applied)}개"
                )

                # 시그널 발송
                self.profile_switched.emit(profile_name)

            else:
                # 실패 메시지
                error_msg = '\n'.join(result.errors) if result.errors else "알 수 없는 오류"
                QMessageBox.critical(
                    self,
                    "프로파일 전환 실패",
                    f"프로파일 전환 중 오류가 발생했습니다:\n\n{error_msg}"
                )

        except Exception as e:
            self._logger.error(f"❌ 프로파일 전환 중 예외 발생: {e}")
            QMessageBox.critical(
                self,
                "프로파일 전환 오류",
                f"프로파일 전환 중 예상치 못한 오류가 발생했습니다:\n\n{str(e)}"
            )

    def _on_save_current_clicked(self):
        """현재 설정 저장 버튼 클릭 처리"""
        dialog = CustomProfileSaveDialog(self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            profile_name = dialog.get_profile_name()
            description = dialog.get_description()

            if self._save_current_as_profile(profile_name, description):
                QMessageBox.information(
                    self,
                    "프로파일 저장 완료",
                    f"현재 설정이 '{profile_name}' 프로파일로 저장되었습니다."
                )
                self._load_available_profiles()  # 목록 새로고침

    def _save_current_as_profile(self, profile_name: str, description: str) -> bool:
        """현재 설정을 커스텀 프로파일로 저장"""
        try:
            success = self._profile_service.save_current_as_profile(profile_name, description)
            if success:
                self._logger.info(f"💾 커스텀 프로파일 저장 성공: {profile_name}")
            else:
                self._logger.error(f"❌ 커스텀 프로파일 저장 실패: {profile_name}")
            return success
        except Exception as e:
            self._logger.error(f"❌ 커스텀 프로파일 저장 중 예외: {e}")
            return False

    def _on_delete_profile_clicked(self):
        """프로파일 삭제 버튼 클릭 처리"""
        current_index = self.profile_combo.currentIndex()
        if current_index < 0:
            return

        profile_name = self.profile_combo.itemData(current_index)
        if not profile_name or not profile_name.startswith('custom_'):
            QMessageBox.warning(
                self,
                "삭제 불가",
                "기본 프로파일은 삭제할 수 없습니다.\n커스텀 프로파일만 삭제 가능합니다."
            )
            return

        # 삭제 확인
        reply = QMessageBox.question(
            self,
            "프로파일 삭제 확인",
            f"프로파일 '{profile_name}'을 삭제하시겠습니까?\n\n"
            f"⚠️ 이 작업은 취소할 수 없습니다.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            if self._profile_service.delete_custom_profile(profile_name):
                QMessageBox.information(
                    self,
                    "프로파일 삭제 완료",
                    f"프로파일 '{profile_name}'이 삭제되었습니다."
                )
                self._load_available_profiles()  # 목록 새로고침
            else:
                QMessageBox.critical(
                    self,
                    "프로파일 삭제 실패",
                    f"프로파일 '{profile_name}' 삭제 중 오류가 발생했습니다."
                )

    def _on_refresh_profiles_clicked(self):
        """프로파일 목록 새로고침"""
        self._load_available_profiles()
        self._logger.info("🔄 프로파일 목록 새로고침 완료")

    def _update_current_profile_display(self):
        """현재 프로파일 표시 업데이트"""
        current_profile = self._profile_service.get_current_profile()
        ui_state = self._profile_service.get_ui_state()

        if not current_profile:
            status_html = """
            <div style='padding: 12px; border-radius: 8px; background-color: #ffa72620;
                        border-left: 4px solid #FF9800; margin: 4px 0;'>
                <div style='font-size: 14px; font-weight: bold; color: #FF9800; margin-bottom: 4px;'>
                    ⚠️ 프로파일 미설정
                </div>
                <div style='font-size: 11px; color: #666;'>
                    프로파일을 선택하여 환경 설정을 관리하세요.
                </div>
            </div>
            """
        else:
            # 프로파일 정보 조회
            profile_info = self._profile_service.get_profile_info(current_profile)
            profile_type = profile_info.get('type', 'unknown')

            if profile_type == 'built-in':
                icon = "🏢"
                color = "#2196F3"
                type_text = "기본 프로파일"
            else:
                icon = "👤"
                color = "#4CAF50"
                type_text = "커스텀 프로파일"

            status_html = f"""
            <div style='padding: 12px; border-radius: 8px; background-color: {color}20;
                        border-left: 4px solid {color}; margin: 4px 0;'>
                <div style='font-size: 14px; font-weight: bold; color: {color}; margin-bottom: 4px;'>
                    {icon} {profile_info.get('name', current_profile)} ({type_text})
                </div>
                <div style='font-size: 11px; color: #666; margin-bottom: 2px;'>
                    {profile_info.get('description', '설명 없음')}
                </div>
                <div style='font-size: 10px; color: #888;'>
                    로그레벨: {ui_state.get('log_level', 'N/A')} |
                    컨텍스트: {ui_state.get('log_context', 'N/A')} |
                    스코프: {ui_state.get('log_scope', 'N/A')}
                </div>
            </div>
            """

        self.current_profile_display.setText(status_html)
        self.current_profile_display.setWordWrap(True)

    # === 외부 API (Presenter에서 호출) ===

    def set_current_environment(self, environment_name: str):
        """현재 환경 설정 (호환성 유지)"""
        # 기존 환경 개념을 프로파일로 매핑
        if environment_name.lower() in ['development', 'testing', 'production']:
            profile_name = environment_name.lower()
            try:
                result = self._profile_service.switch_profile(profile_name)
                if result.success:
                    self._current_environment = environment_name.lower()
                    self._current_profile = profile_name
                    self._update_current_profile_display()
                    self._update_profile_combo()
                    self._logger.info(f"� 환경 설정됨: {environment_name}")
                else:
                    self._logger.error(f"❌ 환경 설정 실패: {environment_name}")
            except Exception as e:
                self._logger.error(f"❌ 환경 설정 중 예외: {e}")

    def update_profiles(self, environment_name: str, profiles: List[Dict]):
        """프로파일 목록 업데이트 (호환성 유지)"""
        # 기존 인터페이스 호환성을 위해 유지
        self._load_available_profiles()
        self._logger.info(f"📁 프로파일 목록 업데이트 완료")

    def show_environment_switch_success(self, new_environment: str):
        """환경 전환 성공 알림 (호환성 유지)"""
        QMessageBox.information(
            self,
            "환경 전환 완료",
            f"환경이 '{new_environment}'로 성공적으로 전환되었습니다."
        )

    def show_environment_switch_error(self, error_message: str):
        """환경 전환 실패 알림 (호환성 유지)"""
        QMessageBox.critical(
            self,
            "환경 전환 실패",
            f"환경 전환 중 오류가 발생했습니다:\n\n{error_message}"
        )

    def get_current_environment(self) -> str:
        """현재 환경 반환 (호환성 유지)"""
        return self._current_environment or "development"

    def _detect_system_environment(self) -> str:
        """시스템 환경변수에서 초기 환경 감지

        Returns:
            str: 감지된 환경명 (development, production, testing)
        """
        # 1. UPBIT_ENVIRONMENT 환경변수 확인
        env_var = os.getenv('UPBIT_ENVIRONMENT')
        if env_var and env_var.lower() in ['development', 'production', 'testing']:
            self._logger.info(f"🔍 시스템 환경변수에서 환경 감지: {env_var}")
            return env_var.lower()

        # 2. UPBIT_LOG_CONTEXT 환경변수 확인 (Infrastructure Layer가 설정한 경우)
        log_context = os.getenv('UPBIT_LOG_CONTEXT')
        if log_context and log_context.lower() in ['development', 'production', 'testing']:
            self._logger.info(f"🔍 로그 컨텍스트에서 환경 감지: {log_context}")
            return log_context.lower()

        # 3. 기본값
        self._logger.info("🔍 환경변수 없음 - 기본 development 환경 사용")
        return "development"

    def _auto_apply_system_profile(self):
        """시스템 환경에 맞는 프로파일 자동 적용"""
        try:
            detected_env = self._current_environment

            # 기본 프로파일명 매핑
            profile_mapping = {
                'development': 'development',
                'production': 'production',
                'testing': 'testing'
            }

            target_profile = profile_mapping.get(detected_env)
            if target_profile:
                self._logger.info(f"🚀 시스템 환경 {detected_env}에 맞는 프로파일 {target_profile} 자동 적용 시작")

                # 프로파일 전환 (UI 업데이트 포함)
                success = self._switch_to_profile(target_profile)

                if success:
                    self._logger.info(f"✅ 시스템 프로파일 자동 적용 완료: {target_profile}")
                else:
                    self._logger.warning(f"⚠️ 시스템 프로파일 자동 적용 실패: {target_profile}")
            else:
                self._logger.warning(f"⚠️ 알 수 없는 시스템 환경: {detected_env}")

        except Exception as e:
            self._logger.error(f"❌ 시스템 프로파일 자동 적용 중 오류: {e}")

    def get_current_profile(self) -> Optional[str]:
        """현재 프로파일 반환"""
        return self._current_profile

    def enable_widgets(self, enabled: bool):
        """위젯 활성화/비활성화"""
        self.switch_profile_btn.setEnabled(enabled)
        self.save_current_btn.setEnabled(enabled)
        self.delete_profile_btn.setEnabled(enabled)
        self.refresh_profiles_btn.setEnabled(enabled)
        self.profile_combo.setEnabled(enabled)

    def refresh_profiles(self):
        """프로파일 목록 새로고침 (외부 호출용)"""
        self._load_available_profiles()
