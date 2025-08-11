"""
Profile Metadata Dialog
======================

프로파일 메타데이터 편집을 위한 다이얼로그
커스텀 프로파일 생성 시 이름, 설명, 태그 등의 메타데이터 입력

Features:
- 프로파일 이름 입력 및 검증
- 설명 텍스트 편집
- 태그 시스템 (쉼표 구분)
- 기반 프로파일 선택
- 실시간 입력 검증
"""

from typing import Optional, List, Dict, Any
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout, QWidget,
    QLineEdit, QTextEdit, QComboBox, QLabel, QPushButton,
    QGroupBox, QMessageBox
)
from PyQt6.QtGui import QFont
from datetime import datetime
import re

from upbit_auto_trading.infrastructure.logging import create_component_logger


logger = create_component_logger("ProfileMetadataDialog")


class ProfileMetadataDialog(QDialog):
    """
    프로파일 메타데이터 편집 다이얼로그

    새 커스텀 프로파일 생성 시 필요한 메타데이터를
    사용자로부터 입력받는 다이얼로그입니다.
    """

    def __init__(self, parent: Optional['QWidget'] = None, existing_profiles: Optional[List[str]] = None):
        super().__init__(parent)
        self.setObjectName("ProfileMetadataDialog")

        logger.info("📝 프로파일 메타데이터 다이얼로그 초기화 시작")

        # 기본 설정
        self.setWindowTitle("새 프로파일 생성")
        self.setModal(True)
        self.setMinimumSize(450, 400)
        self.setMaximumSize(600, 500)

        # 상태 관리
        self._existing_profiles = existing_profiles or []
        self._is_editing = False
        self._original_metadata: Optional[Dict[str, Any]] = None

        # UI 구성
        self._setup_ui()
        self._connect_signals()

        logger.info("✅ 프로파일 메타데이터 다이얼로그 초기화 완료")

    def _setup_ui(self) -> None:
        """UI 구성요소 설정"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        # 1. 기본 정보 섹션
        self._create_basic_info_section(layout)

        # 2. 상세 정보 섹션
        self._create_detail_info_section(layout)

        # 3. 고급 옵션 섹션
        self._create_advanced_options_section(layout)

        # 4. 버튼 섹션
        self._create_button_section(layout)

    def _create_basic_info_section(self, parent_layout: QVBoxLayout) -> None:
        """기본 정보 입력 섹션 생성"""
        group_box = QGroupBox("기본 정보")
        group_box.setObjectName("basic_info_group")

        form_layout = QFormLayout(group_box)
        form_layout.setFieldGrowthPolicy(QFormLayout.FieldGrowthPolicy.ExpandingFieldsGrow)

        # 프로파일 이름 입력
        self.name_input = QLineEdit()
        self.name_input.setObjectName("profile_name_input")
        self.name_input.setPlaceholderText("예: My Custom Settings")
        self.name_input.setMaxLength(50)

        # 이름 검증 레이블
        self.name_validation_label = QLabel("")
        self.name_validation_label.setObjectName("name_validation_label")

        # 파일명 미리보기 레이블
        self.filename_preview_label = QLabel("")
        self.filename_preview_label.setObjectName("filename_preview_label")
        font = QFont()
        font.setFamily("Consolas")
        font.setPointSize(9)
        self.filename_preview_label.setFont(font)

        form_layout.addRow("프로파일 이름:", self.name_input)
        form_layout.addRow("", self.name_validation_label)
        form_layout.addRow("생성될 파일명:", self.filename_preview_label)

        parent_layout.addWidget(group_box)

    def _create_detail_info_section(self, parent_layout: QVBoxLayout) -> None:
        """상세 정보 입력 섹션 생성"""
        group_box = QGroupBox("상세 정보")
        group_box.setObjectName("detail_info_group")

        form_layout = QFormLayout(group_box)
        form_layout.setFieldGrowthPolicy(QFormLayout.FieldGrowthPolicy.ExpandingFieldsGrow)

        # 설명 입력
        self.description_input = QTextEdit()
        self.description_input.setObjectName("profile_description_input")
        self.description_input.setPlaceholderText("이 프로파일의 용도나 특징을 설명해주세요...")
        self.description_input.setMaximumHeight(80)

        # 태그 입력
        self.tags_input = QLineEdit()
        self.tags_input.setObjectName("profile_tags_input")
        self.tags_input.setPlaceholderText("custom, debugging, experimental (쉼표로 구분)")

        form_layout.addRow("설명:", self.description_input)
        form_layout.addRow("태그:", self.tags_input)

        parent_layout.addWidget(group_box)

    def _create_advanced_options_section(self, parent_layout: QVBoxLayout) -> None:
        """고급 옵션 섹션 생성"""
        group_box = QGroupBox("고급 옵션")
        group_box.setObjectName("advanced_options_group")

        form_layout = QFormLayout(group_box)
        form_layout.setFieldGrowthPolicy(QFormLayout.FieldGrowthPolicy.ExpandingFieldsGrow)

        # 기반 프로파일 선택
        self.base_profile_combo = QComboBox()
        self.base_profile_combo.setObjectName("base_profile_combo")
        self.base_profile_combo.addItem("현재 설정", "current")

        # 기존 프로파일들을 기반으로 선택 옵션 추가
        for profile in self._existing_profiles:
            display_name = profile.replace('_', ' ').title()
            self.base_profile_combo.addItem(f"{display_name} 프로파일", profile)

        form_layout.addRow("기반 프로파일:", self.base_profile_combo)

        parent_layout.addWidget(group_box)

    def _create_button_section(self, parent_layout: QVBoxLayout) -> None:
        """버튼 섹션 생성"""
        # 확인 버튼
        self.ok_button = QPushButton("생성")
        self.ok_button.setObjectName("metadata_ok_button")

        # 취소 버튼
        self.cancel_button = QPushButton("취소")
        self.cancel_button.setObjectName("metadata_cancel_button")

        # 미리보기 버튼
        self.preview_button = QPushButton("미리보기")
        self.preview_button.setObjectName("metadata_preview_button")

        # 버튼 레이아웃
        button_layout = QHBoxLayout()
        button_layout.addWidget(self.preview_button)
        button_layout.addStretch()
        button_layout.addWidget(self.cancel_button)
        button_layout.addWidget(self.ok_button)

        parent_layout.addLayout(button_layout)

    def _connect_signals(self) -> None:
        """시그널 연결"""
        # 입력 필드 변경 시 실시간 검증
        self.name_input.textChanged.connect(self._on_name_input_changed)
        self.description_input.textChanged.connect(self._on_input_changed)
        self.tags_input.textChanged.connect(self._on_input_changed)

        # 버튼 시그널
        self.ok_button.clicked.connect(self._on_ok_clicked)
        self.cancel_button.clicked.connect(self._on_cancel_clicked)
        self.preview_button.clicked.connect(self._on_preview_clicked)

        # 다이얼로그 기본 시그널
        self.accepted.connect(self._on_accepted)
        self.rejected.connect(self._on_rejected)

    def _on_name_input_changed(self, text: str) -> None:
        """이름 입력 변경 이벤트"""
        self._validate_name_input(text)
        self._update_filename_preview(text)
        self._update_ok_button_state()

    def _on_input_changed(self) -> None:
        """일반 입력 변경 이벤트"""
        self._update_ok_button_state()

    def _validate_name_input(self, name: str) -> bool:
        """프로파일 이름 검증"""
        if not name.strip():
            self.name_validation_label.setText("❌ 프로파일 이름을 입력해주세요")
            self.name_validation_label.setObjectName("validation_error")
            return False

        if len(name.strip()) < 3:
            self.name_validation_label.setText("❌ 이름은 최소 3글자 이상이어야 합니다")
            self.name_validation_label.setObjectName("validation_error")
            return False

        # 파일명으로 사용할 수 없는 문자 검증
        invalid_chars = r'[<>:"/\\|?*]'
        if re.search(invalid_chars, name):
            self.name_validation_label.setText("❌ 파일명에 사용할 수 없는 문자가 포함되어 있습니다")
            self.name_validation_label.setObjectName("validation_error")
            return False

        # 중복 이름 검증 (기존 프로파일과 비교)
        generated_filename = self._generate_filename(name)
        if any(profile.startswith(generated_filename.replace('.yaml', '')) for profile in self._existing_profiles):
            self.name_validation_label.setText("⚠️ 비슷한 이름의 프로파일이 이미 존재합니다")
            self.name_validation_label.setObjectName("validation_warning")
            return True  # 경고이지만 생성은 허용

        # 검증 성공
        self.name_validation_label.setText("✅ 사용 가능한 이름입니다")
        self.name_validation_label.setObjectName("validation_success")
        return True

    def _update_filename_preview(self, name: str) -> None:
        """파일명 미리보기 업데이트"""
        if name.strip():
            filename = self._generate_filename(name)
            self.filename_preview_label.setText(f"📄 {filename}")
        else:
            self.filename_preview_label.setText("")

    def _generate_filename(self, name: str) -> str:
        """프로파일 이름으로부터 파일명 생성"""
        # 이름 정규화
        clean_name = re.sub(r'[<>:"/\\|?*]', '', name.strip())
        clean_name = re.sub(r'\s+', '_', clean_name)

        # 타임스탬프 추가
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        return f"Custom_{clean_name}_{timestamp}.yaml"

    def _update_ok_button_state(self) -> None:
        """확인 버튼 활성화 상태 업데이트"""
        name_valid = self._validate_name_input(self.name_input.text())
        has_name = bool(self.name_input.text().strip())

        self.ok_button.setEnabled(name_valid and has_name)

    def _on_ok_clicked(self) -> None:
        """확인 버튼 클릭 이벤트"""
        if self._validate_all_inputs():
            logger.info("프로파일 메타데이터 입력 완료")
            self.accept()

    def _on_cancel_clicked(self) -> None:
        """취소 버튼 클릭 이벤트"""
        logger.info("프로파일 메타데이터 입력 취소")
        self.reject()

    def _on_preview_clicked(self) -> None:
        """미리보기 버튼 클릭 이벤트"""
        metadata = self.get_metadata()

        preview_text = f"""
프로파일 미리보기
================

이름: {metadata['name']}
파일명: {self._generate_filename(metadata['name'])}
설명: {metadata['description'] or '(없음)'}
태그: {', '.join(metadata['tags']) if metadata['tags'] else '(없음)'}
기반: {metadata['created_from']}
생성 시간: {metadata['created_at']}
        """.strip()

        QMessageBox.information(self, "프로파일 미리보기", preview_text)

    def _on_accepted(self) -> None:
        """다이얼로그 승인 이벤트"""
        logger.info("프로파일 메타데이터 다이얼로그 승인됨")

    def _on_rejected(self) -> None:
        """다이얼로그 거부 이벤트"""
        logger.info("프로파일 메타데이터 다이얼로그 취소됨")

    def _validate_all_inputs(self) -> bool:
        """모든 입력값 검증"""
        if not self._validate_name_input(self.name_input.text()):
            QMessageBox.warning(self, "입력 오류", "프로파일 이름을 올바르게 입력해주세요.")
            self.name_input.setFocus()
            return False

        return True

    def get_profile_name(self) -> str:
        """입력된 프로파일 이름 반환"""
        return self.name_input.text().strip()

    def get_description(self) -> str:
        """입력된 설명 반환"""
        return self.description_input.toPlainText().strip()

    def get_tags(self) -> List[str]:
        """입력된 태그 목록 반환"""
        tags_text = self.tags_input.text().strip()
        if not tags_text:
            return []

        # 쉼표로 분할하고 정리
        tags = [tag.strip() for tag in tags_text.split(',')]
        return [tag for tag in tags if tag]  # 빈 태그 제거

    def get_base_profile(self) -> str:
        """선택된 기반 프로파일 반환"""
        return self.base_profile_combo.currentData() or "current"

    def get_generated_filename(self) -> str:
        """생성될 파일명 반환"""
        return self._generate_filename(self.get_profile_name())

    def get_metadata(self) -> Dict[str, Any]:
        """완성된 메타데이터 딕셔너리 반환"""
        return {
            'name': self.get_profile_name(),
            'description': self.get_description(),
            'tags': self.get_tags(),
            'created_from': self.get_base_profile(),
            'created_at': datetime.now().isoformat(),
            'profile_type': 'custom'
        }

    def set_initial_data(self, metadata: Dict[str, Any]) -> None:
        """
        초기 데이터 설정 (편집 모드용)

        Args:
            metadata: 기존 메타데이터
        """
        self._is_editing = True
        self._original_metadata = metadata.copy()

        self.setWindowTitle("프로파일 편집")
        self.ok_button.setText("수정")

        # 입력 필드에 기존 데이터 설정
        self.name_input.setText(metadata.get('name', ''))
        self.description_input.setText(metadata.get('description', ''))

        tags = metadata.get('tags', [])
        if tags:
            self.tags_input.setText(', '.join(tags))

        created_from = metadata.get('created_from', 'current')
        for i in range(self.base_profile_combo.count()):
            if self.base_profile_combo.itemData(i) == created_from:
                self.base_profile_combo.setCurrentIndex(i)
                break

        logger.info(f"편집 모드로 초기 데이터 설정 완료: {metadata.get('name', '')}")

    def is_editing_mode(self) -> bool:
        """편집 모드 여부 반환"""
        return self._is_editing

    def get_dialog_info(self) -> Dict[str, Any]:
        """다이얼로그 정보 반환 (디버깅용)"""
        return {
            'is_editing': self._is_editing,
            'existing_profiles_count': len(self._existing_profiles),
            'current_inputs': {
                'name': self.get_profile_name(),
                'description': self.get_description(),
                'tags': self.get_tags(),
                'base_profile': self.get_base_profile()
            },
            'validation_state': {
                'name_valid': self._validate_name_input(self.name_input.text()),
                'ok_button_enabled': self.ok_button.isEnabled()
            }
        }
