"""
Profile Selector Section Widget
==============================

프로파일 선택 및 관리를 위한 섹션 위젯
좌우 분할 레이아웃의 좌측 전체를 담당하여 프로파일 선택, 정보 표시, 액션 버튼 제공

Features:
- 퀵 환경 버튼 통합
- 프로파일 콤보박스 (메타데이터 표시명 지원)
- 현재 프로파일 정보 미리보기
- 프로파일 관리 액션 버튼들
- 실시간 상태 동기화
"""

from typing import Optional, Dict, Any
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QComboBox, QLabel,
    QPushButton, QFrame, QTextEdit, QGroupBox
)
from PyQt6.QtCore import pyqtSignal
from PyQt6.QtGui import QFont

from upbit_auto_trading.infrastructure.logging import create_component_logger
from .quick_environment_buttons import QuickEnvironmentButtons


logger = create_component_logger("ProfileSelectorSection")


class ProfileSelectorSection(QWidget):
    """
    프로파일 선택기 섹션 위젯

    좌우 분할 레이아웃의 좌측(1/3 영역)을 담당하여
    프로파일 선택 및 관리 기능을 통합 제공합니다.
    """

    # 시그널 정의
    profile_selected = pyqtSignal(str)                    # 프로파일 선택
    environment_quick_switch = pyqtSignal(str)            # 퀵 환경 전환
    profile_apply_requested = pyqtSignal(str)             # 프로파일 적용 요청
    custom_save_requested = pyqtSignal()                  # 커스텀 저장 요청
    profile_delete_requested = pyqtSignal(str)            # 프로파일 삭제 요청

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.setObjectName("ProfileSelectorSection")

        logger.info("📂 프로파일 선택기 섹션 초기화 시작")

        # 상태 관리
        self._current_profile = ""
        self._current_environment = ""
        self._profiles_data: Dict[str, Dict[str, Any]] = {}

        # UI 구성
        self._setup_ui()
        self._connect_signals()

        logger.info("✅ 프로파일 선택기 섹션 초기화 완료")

    def _setup_ui(self) -> None:
        """UI 구성요소 설정"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(15)

        # 1. 퀵 환경 버튼 섹션
        self._create_quick_environment_section(layout)

        # 2. 프로파일 선택 섹션
        self._create_profile_selection_section(layout)

        # 3. 프로파일 정보 미리보기 섹션
        self._create_profile_preview_section(layout)

        # 4. 액션 버튼 섹션
        self._create_action_buttons_section(layout)

        # 공간 확장
        layout.addStretch()

    def _create_quick_environment_section(self, parent_layout: QVBoxLayout) -> None:
        """퀵 환경 버튼 섹션 생성"""
        # 그룹박스로 감싸기
        group_box = QGroupBox("빠른 환경 전환")
        group_box.setObjectName("quick_env_group")

        group_layout = QVBoxLayout(group_box)
        group_layout.setContentsMargins(10, 10, 10, 10)

        # 퀵 환경 버튼 위젯 추가
        self.quick_env_buttons = QuickEnvironmentButtons()
        group_layout.addWidget(self.quick_env_buttons)

        parent_layout.addWidget(group_box)

    def _create_profile_selection_section(self, parent_layout: QVBoxLayout) -> None:
        """프로파일 선택 섹션 생성"""
        # 그룹박스로 감싸기
        group_box = QGroupBox("프로파일 선택")
        group_box.setObjectName("profile_selection_group")

        group_layout = QVBoxLayout(group_box)
        group_layout.setContentsMargins(10, 10, 10, 10)
        group_layout.setSpacing(8)

        # 프로파일 콤보박스
        profile_label = QLabel("사용할 프로파일:")
        profile_label.setObjectName("profile_selection_label")

        self.profile_combo = QComboBox()
        self.profile_combo.setObjectName("profile_selection_combo")
        self.profile_combo.setMinimumHeight(30)

        group_layout.addWidget(profile_label)
        group_layout.addWidget(self.profile_combo)

        parent_layout.addWidget(group_box)

    def _create_profile_preview_section(self, parent_layout: QVBoxLayout) -> None:
        """프로파일 정보 미리보기 섹션 생성"""
        # 그룹박스로 감싸기
        group_box = QGroupBox("프로파일 정보")
        group_box.setObjectName("profile_preview_group")

        group_layout = QVBoxLayout(group_box)
        group_layout.setContentsMargins(10, 10, 10, 10)
        group_layout.setSpacing(8)

        # 프로파일 이름 표시
        self.profile_name_label = QLabel("선택된 프로파일이 없습니다")
        self.profile_name_label.setObjectName("profile_name_display")
        font = QFont()
        font.setBold(True)
        font.setPointSize(11)
        self.profile_name_label.setFont(font)

        # 프로파일 설명 표시
        self.profile_description_label = QLabel("")
        self.profile_description_label.setObjectName("profile_description_display")
        self.profile_description_label.setWordWrap(True)

        # 프로파일 태그 표시
        self.profile_tags_label = QLabel("")
        self.profile_tags_label.setObjectName("profile_tags_display")

        # 프로파일 생성 정보
        self.profile_info_label = QLabel("")
        self.profile_info_label.setObjectName("profile_info_display")

        # 미니 YAML 미리보기 (선택적)
        self.yaml_preview = QTextEdit()
        self.yaml_preview.setObjectName("yaml_mini_preview")
        self.yaml_preview.setMaximumHeight(80)
        self.yaml_preview.setReadOnly(True)
        font = QFont("Consolas", 8)
        font.setStyleHint(QFont.StyleHint.Monospace)
        self.yaml_preview.setFont(font)

        group_layout.addWidget(self.profile_name_label)
        group_layout.addWidget(self.profile_description_label)
        group_layout.addWidget(self.profile_tags_label)
        group_layout.addWidget(self.profile_info_label)
        group_layout.addWidget(QLabel("YAML 미리보기:"))
        group_layout.addWidget(self.yaml_preview)

        parent_layout.addWidget(group_box)

    def _create_action_buttons_section(self, parent_layout: QVBoxLayout) -> None:
        """액션 버튼 섹션 생성"""
        # 그룹박스로 감싸기
        group_box = QGroupBox("프로파일 관리")
        group_box.setObjectName("profile_actions_group")

        group_layout = QVBoxLayout(group_box)
        group_layout.setContentsMargins(10, 10, 10, 10)
        group_layout.setSpacing(8)

        # 프로파일 적용 버튼
        self.apply_button = QPushButton("🚀 프로파일 적용")
        self.apply_button.setObjectName("profile_apply_button")
        self.apply_button.setMinimumHeight(35)

        # 커스텀 저장 버튼
        self.save_custom_button = QPushButton("💾 현재 설정으로 저장")
        self.save_custom_button.setObjectName("profile_save_custom_button")
        self.save_custom_button.setMinimumHeight(30)

        # 프로파일 삭제 버튼
        self.delete_button = QPushButton("🗑️ 프로파일 삭제")
        self.delete_button.setObjectName("profile_delete_button")
        self.delete_button.setMinimumHeight(30)

        # 새로 고침 버튼
        self.refresh_button = QPushButton("🔄 목록 새로 고침")
        self.refresh_button.setObjectName("profile_refresh_button")
        self.refresh_button.setMinimumHeight(30)

        group_layout.addWidget(self.apply_button)
        group_layout.addWidget(self.save_custom_button)

        # 구분선
        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.HLine)
        separator.setFrameShadow(QFrame.Shadow.Sunken)
        group_layout.addWidget(separator)

        group_layout.addWidget(self.delete_button)
        group_layout.addWidget(self.refresh_button)

        parent_layout.addWidget(group_box)

    def _connect_signals(self) -> None:
        """시그널 연결"""
        # 퀵 환경 버튼 시그널
        self.quick_env_buttons.environment_selected.connect(self._on_environment_selected)

        # 프로파일 콤보박스 시그널
        self.profile_combo.currentTextChanged.connect(self._on_profile_combo_changed)

        # 액션 버튼 시그널
        self.apply_button.clicked.connect(self._on_apply_button_clicked)
        self.save_custom_button.clicked.connect(self._on_save_custom_button_clicked)
        self.delete_button.clicked.connect(self._on_delete_button_clicked)
        self.refresh_button.clicked.connect(self._on_refresh_button_clicked)

    def _on_environment_selected(self, env_key: str) -> None:
        """퀵 환경 버튼 선택 이벤트 처리"""
        logger.info(f"퀵 환경 선택됨: {env_key}")

        self._current_environment = env_key

        # 환경에 해당하는 기본 프로파일 자동 선택
        default_profile = self._get_default_profile_for_environment(env_key)
        if default_profile:
            self._select_profile_in_combo(default_profile)

        # 시그널 발송
        self.environment_quick_switch.emit(env_key)

    def _on_profile_combo_changed(self, profile_display_name: str) -> None:
        """프로파일 콤보박스 변경 이벤트 처리"""
        if not profile_display_name:
            return

        # 표시명에서 실제 프로파일명 추출
        profile_name = self._extract_profile_name_from_display(profile_display_name)

        if profile_name != self._current_profile:
            logger.info(f"프로파일 선택됨: {profile_name}")

            self._current_profile = profile_name
            self._update_profile_preview(profile_name)

            # 시그널 발송
            self.profile_selected.emit(profile_name)

    def _on_apply_button_clicked(self) -> None:
        """프로파일 적용 버튼 클릭 이벤트"""
        if self._current_profile:
            logger.info(f"프로파일 적용 요청: {self._current_profile}")
            self.profile_apply_requested.emit(self._current_profile)

    def _on_save_custom_button_clicked(self) -> None:
        """커스텀 저장 버튼 클릭 이벤트"""
        logger.info("커스텀 프로파일 저장 요청")
        self.custom_save_requested.emit()

    def _on_delete_button_clicked(self) -> None:
        """삭제 버튼 클릭 이벤트"""
        if self._current_profile:
            logger.info(f"프로파일 삭제 요청: {self._current_profile}")
            self.profile_delete_requested.emit(self._current_profile)

    def _on_refresh_button_clicked(self) -> None:
        """새로 고침 버튼 클릭 이벤트"""
        logger.info("프로파일 목록 새로 고침 요청")
        self.refresh_profiles()

    def load_profiles(self, profiles_data: Dict[str, Dict[str, Any]]) -> None:
        """
        프로파일 데이터 로드

        Args:
            profiles_data: 프로파일명 -> 프로파일 정보 딕셔너리
        """
        logger.info(f"프로파일 데이터 로드 중: {len(profiles_data)}개")

        self._profiles_data = profiles_data
        self._update_profile_combo()

    def _update_profile_combo(self) -> None:
        """프로파일 콤보박스 업데이트"""
        self.profile_combo.clear()

        for profile_name, profile_data in self._profiles_data.items():
            display_name = self._get_profile_display_name(profile_name, profile_data)
            self.profile_combo.addItem(display_name)

        logger.debug(f"프로파일 콤보박스 업데이트 완료: {self.profile_combo.count()}개 항목")

    def _get_profile_display_name(self, profile_name: str, profile_data: Dict[str, Any]) -> str:
        """프로파일 표시명 생성"""
        metadata = profile_data.get('metadata', {})

        # 메타데이터에서 사용자 정의 이름 확인
        display_name = metadata.get('name', profile_name)
        profile_type = metadata.get('profile_type', 'unknown')

        # 타입별 아이콘 추가
        if profile_type == 'built-in':
            icon = "🔧"  # 기본 프로파일
        elif profile_type == 'custom':
            icon = "⚙️"  # 커스텀 프로파일
        else:
            icon = "📄"  # 알 수 없는 타입

        return f"{icon} {display_name} ({profile_name})"

    def _extract_profile_name_from_display(self, display_name: str) -> str:
        """표시명에서 실제 프로파일명 추출"""
        # "🔧 Development Settings (development)" → "development"
        if '(' in display_name and display_name.endswith(')'):
            start = display_name.rfind('(') + 1
            end = display_name.rfind(')')
            return display_name[start:end].strip()

        return display_name  # 파싱 실패 시 전체 문자열 반환

    def _get_default_profile_for_environment(self, env_key: str) -> Optional[str]:
        """환경에 대응하는 기본 프로파일명 반환"""
        # 환경 키와 동일한 이름의 프로파일이 있는지 확인
        if env_key in self._profiles_data:
            return env_key

        # 환경 매핑 테이블 (확장 가능)
        environment_mapping = {
            'development': ['development', 'dev', 'debug'],
            'testing': ['testing', 'test', 'staging'],
            'production': ['production', 'prod', 'live']
        }

        possible_names = environment_mapping.get(env_key, [env_key])
        for name in possible_names:
            if name in self._profiles_data:
                return name

        return None

    def _select_profile_in_combo(self, profile_name: str) -> None:
        """콤보박스에서 특정 프로파일 선택"""
        for i in range(self.profile_combo.count()):
            item_text = self.profile_combo.itemText(i)
            extracted_name = self._extract_profile_name_from_display(item_text)
            if extracted_name == profile_name:
                self.profile_combo.setCurrentIndex(i)
                break

    def _update_profile_preview(self, profile_name: str) -> None:
        """프로파일 미리보기 정보 업데이트"""
        if profile_name not in self._profiles_data:
            self._clear_profile_preview()
            return

        profile_data = self._profiles_data[profile_name]
        metadata = profile_data.get('metadata', {})

        # 프로파일 이름 표시
        display_name = metadata.get('name', profile_name)
        self.profile_name_label.setText(f"📄 {display_name}")

        # 설명 표시
        description = metadata.get('description', '설명이 없습니다.')
        self.profile_description_label.setText(description)

        # 태그 표시
        tags = metadata.get('tags', [])
        if tags:
            tags_text = ', '.join([f"#{tag}" for tag in tags])
            self.profile_tags_label.setText(f"태그: {tags_text}")
        else:
            self.profile_tags_label.setText("태그: 없음")

        # 생성 정보 표시
        created_at = metadata.get('created_at', '')
        created_from = metadata.get('created_from', '')
        if created_at and created_from:
            self.profile_info_label.setText(f"생성: {created_at} (기반: {created_from})")
        else:
            self.profile_info_label.setText("생성 정보: 없음")

        # YAML 미리보기
        yaml_content = profile_data.get('content', '')
        if yaml_content:
            # 처음 5줄만 표시
            preview_lines = yaml_content.split('\n')[:5]
            preview_text = '\n'.join(preview_lines)
            if len(yaml_content.split('\n')) > 5:
                preview_text += '\n...'
            self.yaml_preview.setText(preview_text)
        else:
            self.yaml_preview.setText("# YAML 내용을 로드할 수 없습니다")

        # 버튼 상태 업데이트
        self._update_button_states(profile_name)

    def _clear_profile_preview(self) -> None:
        """프로파일 미리보기 정보 초기화"""
        self.profile_name_label.setText("선택된 프로파일이 없습니다")
        self.profile_description_label.setText("")
        self.profile_tags_label.setText("")
        self.profile_info_label.setText("")
        self.yaml_preview.setText("")

        # 버튼 비활성화
        self.apply_button.setEnabled(False)
        self.delete_button.setEnabled(False)

    def _update_button_states(self, profile_name: str) -> None:
        """버튼 활성화 상태 업데이트"""
        if not profile_name or profile_name not in self._profiles_data:
            self.apply_button.setEnabled(False)
            self.delete_button.setEnabled(False)
            return

        profile_data = self._profiles_data[profile_name]
        metadata = profile_data.get('metadata', {})
        profile_type = metadata.get('profile_type', 'unknown')

        # 적용 버튼은 항상 활성화
        self.apply_button.setEnabled(True)

        # 삭제 버튼은 커스텀 프로파일만 활성화
        self.delete_button.setEnabled(profile_type == 'custom')

    def set_active_profile(self, profile_name: str) -> None:
        """외부에서 활성 프로파일 설정"""
        if profile_name in self._profiles_data:
            self._select_profile_in_combo(profile_name)
            self._current_profile = profile_name
            logger.info(f"외부에서 활성 프로파일 설정: {profile_name}")

    def set_active_environment(self, env_key: str) -> None:
        """외부에서 활성 환경 설정"""
        self.quick_env_buttons.set_active_environment(env_key)
        self._current_environment = env_key

    def refresh_profiles(self) -> None:
        """프로파일 목록 새로 고침 (외부에서 데이터 다시 로드 필요)"""
        logger.info("프로파일 목록 새로 고침 시작")
        # 실제 새로 고침은 상위 컴포넌트에서 처리
        # 여기서는 현재 상태만 초기화

    def get_current_selection(self) -> Dict[str, str]:
        """현재 선택 상태 반환"""
        return {
            'profile': self._current_profile,
            'environment': self._current_environment
        }

    def get_selector_info(self) -> Dict[str, Any]:
        """선택기 위젯 정보 반환 (디버깅용)"""
        return {
            'current_profile': self._current_profile,
            'current_environment': self._current_environment,
            'total_profiles': len(self._profiles_data),
            'combo_items': self.profile_combo.count(),
            'button_states': {
                'apply': self.apply_button.isEnabled(),
                'delete': self.delete_button.isEnabled(),
                'save_custom': self.save_custom_button.isEnabled(),
                'refresh': self.refresh_button.isEnabled()
            }
        }
