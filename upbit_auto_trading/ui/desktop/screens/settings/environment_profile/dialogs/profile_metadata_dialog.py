"""
Profile Metadata Dialog
======================

프로파일 메타데이터 편집을 위한 다이얼로그 구현
사용자가 프로파일의 이름, 설명, 태그 등을 편집할 수 있는 폼을 제공

Features:
- 메타데이터 폼 구성
- 입력 유효성 검증
- 프로파일에 메타데이터 적용
- 사용자 친화적 인터페이스

Author: AI Assistant
Created: 2025-08-11
Task: 4.2.3
"""

from typing import Optional
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout,
    QLineEdit, QTextEdit, QListWidget, QListWidgetItem, QPushButton,
    QLabel, QGroupBox, QWidget,
    QScrollArea, QMessageBox
)
from PyQt6.QtCore import Qt, pyqtSignal

from upbit_auto_trading.infrastructure.logging import create_component_logger
from .profile_metadata import ProfileMetadata

logger = create_component_logger("ProfileMetadataDialog")

class ProfileMetadataDialog(QDialog):
    """
    프로파일 메타데이터 편집 다이얼로그

    사용자가 프로파일의 메타데이터(이름, 설명, 태그 등)을
    편집할 수 있는 모달 다이얼로그를 제공합니다.
    """

    # 시그널 정의
    metadata_applied = pyqtSignal(str, object)  # (profile_name, metadata)

    def __init__(self, profile_name: str, metadata: Optional[ProfileMetadata] = None, parent=None):
        super().__init__(parent)

        self.profile_name = profile_name
        self.metadata = metadata or ProfileMetadata()
        self.is_custom_profile = self._check_if_custom_profile()

        # UI 요소들
        self.name_edit = None
        self.description_edit = None
        self.created_from_label = None
        self.tags_list = None
        self.tag_input = None
        self.add_tag_btn = None
        self.remove_tag_btn = None

        self._setup_dialog()
        self._setup_metadata_form()
        self._setup_buttons()
        self._populate_form()
        self._apply_styles()

        logger.info(f"📝 프로파일 메타데이터 다이얼로그 초기화: {profile_name}")

    def _setup_dialog(self):
        """다이얼로그 기본 설정"""
        self.setWindowTitle(f"프로파일 메타데이터 편집 - {self.profile_name}")
        self.setModal(True)
        self.setMinimumSize(500, 600)
        self.resize(600, 700)

        # 메인 레이아웃
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(16)
        main_layout.setContentsMargins(20, 20, 20, 20)

        # 스크롤 영역 설정
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)

        # 스크롤 컨텐츠 위젯
        content_widget = QWidget()
        self.content_layout = QVBoxLayout(content_widget)
        self.content_layout.setSpacing(16)

        scroll_area.setWidget(content_widget)
        main_layout.addWidget(scroll_area)

        self.setLayout(main_layout)

    def _setup_metadata_form(self):
        """메타데이터 편집 폼 구성"""
        try:
            # === 기본 정보 그룹 ===
            basic_group = QGroupBox("기본 정보")
            basic_layout = QFormLayout(basic_group)
            basic_layout.setSpacing(12)

            # 프로파일명 표시 (읽기 전용)
            profile_name_label = QLabel(self.profile_name)
            profile_name_label.setStyleSheet("font-weight: bold; color: #2c3e50;")
            basic_layout.addRow("프로파일:", profile_name_label)

            # 표시명 입력
            self.name_edit = QLineEdit()
            self.name_edit.setPlaceholderText("프로파일의 표시명을 입력하세요")
            self.name_edit.setMaxLength(100)
            basic_layout.addRow("표시명:", self.name_edit)

            # 설명 입력
            self.description_edit = QTextEdit()
            self.description_edit.setPlaceholderText("프로파일에 대한 설명을 입력하세요")
            self.description_edit.setMaximumHeight(100)
            basic_layout.addRow("설명:", self.description_edit)

            # 생성 정보 (읽기 전용)
            if self.metadata.created_from:
                self.created_from_label = QLabel(f"기반 환경: {self.metadata.created_from}")
                self.created_from_label.setStyleSheet("color: #7f8c8d;")
                basic_layout.addRow("생성 정보:", self.created_from_label)

            # 생성일 표시
            if self.metadata.created_at:
                created_at_label = QLabel(self.metadata.created_at)
                created_at_label.setStyleSheet("color: #7f8c8d;")
                basic_layout.addRow("생성일:", created_at_label)

            self.content_layout.addWidget(basic_group)

            # === 태그 관리 그룹 ===
            self._setup_tags_group()

            logger.debug("✅ 메타데이터 폼 구성 완료")

        except Exception as e:
            logger.error(f"❌ 메타데이터 폼 구성 실패: {e}")
            raise

    def _setup_tags_group(self):
        """태그 관리 그룹 설정"""
        try:
            tags_group = QGroupBox("태그 관리")
            tags_layout = QVBoxLayout(tags_group)

            # 태그 입력 영역
            tag_input_layout = QHBoxLayout()

            self.tag_input = QLineEdit()
            self.tag_input.setPlaceholderText("새 태그를 입력하세요")
            self.tag_input.setMaxLength(50)
            self.tag_input.returnPressed.connect(self._add_tag)

            self.add_tag_btn = QPushButton("추가")
            self.add_tag_btn.clicked.connect(self._add_tag)
            self.add_tag_btn.setFixedWidth(60)

            tag_input_layout.addWidget(QLabel("새 태그:"))
            tag_input_layout.addWidget(self.tag_input)
            tag_input_layout.addWidget(self.add_tag_btn)

            tags_layout.addLayout(tag_input_layout)

            # 태그 목록
            tags_list_layout = QHBoxLayout()

            self.tags_list = QListWidget()
            self.tags_list.setMaximumHeight(150)
            self.tags_list.setSelectionMode(QListWidget.SelectionMode.SingleSelection)

            # 태그 관리 버튼들
            tag_buttons_layout = QVBoxLayout()

            self.remove_tag_btn = QPushButton("선택 삭제")
            self.remove_tag_btn.clicked.connect(self._remove_tag)

            clear_tags_btn = QPushButton("모두 삭제")
            clear_tags_btn.clicked.connect(self._clear_tags)

            tag_buttons_layout.addWidget(self.remove_tag_btn)
            tag_buttons_layout.addWidget(clear_tags_btn)
            tag_buttons_layout.addStretch()

            tags_list_layout.addWidget(self.tags_list)
            tags_list_layout.addLayout(tag_buttons_layout)

            tags_layout.addLayout(tags_list_layout)

            # 태그 도움말
            help_label = QLabel("💡 태그는 프로파일을 분류하고 검색하는 데 도움이 됩니다")
            help_label.setStyleSheet("color: #7f8c8d; font-size: 12px;")
            tags_layout.addWidget(help_label)

            self.content_layout.addWidget(tags_group)

        except Exception as e:
            logger.error(f"❌ 태그 그룹 설정 실패: {e}")
            raise

    def _setup_buttons(self):
        """버튼 영역 설정"""
        try:
            # 버튼 레이아웃
            button_layout = QHBoxLayout()
            button_layout.addStretch()

            # 취소 버튼
            cancel_btn = QPushButton("취소")
            cancel_btn.clicked.connect(self.reject)
            cancel_btn.setFixedSize(80, 32)

            # 적용 버튼
            apply_btn = QPushButton("적용")
            apply_btn.clicked.connect(self._apply_metadata)
            apply_btn.setDefault(True)
            apply_btn.setFixedSize(80, 32)

            button_layout.addWidget(cancel_btn)
            button_layout.addWidget(apply_btn)

            self.layout().addLayout(button_layout)

        except Exception as e:
            logger.error(f"❌ 버튼 설정 실패: {e}")
            raise

    def _populate_form(self):
        """폼에 기존 메타데이터 데이터 채우기"""
        try:
            if self.metadata:
                # 기본 정보
                if self.metadata.name:
                    self.name_edit.setText(self.metadata.name)

                if self.metadata.description:
                    self.description_edit.setPlainText(self.metadata.description)

                # 태그 목록
                for tag in self.metadata.tags:
                    self._add_tag_to_list(tag)

            logger.debug("✅ 폼 데이터 채우기 완료")

        except Exception as e:
            logger.error(f"❌ 폼 데이터 채우기 실패: {e}")

    def _add_tag(self):
        """새 태그 추가"""
        try:
            tag_text = self.tag_input.text().strip()
            if not tag_text:
                return

            # 중복 확인
            for i in range(self.tags_list.count()):
                item = self.tags_list.item(i)
                if item.text() == tag_text:
                    QMessageBox.warning(self, "중복 태그", f"'{tag_text}' 태그가 이미 존재합니다.")
                    return

            # 태그 길이 검증
            if len(tag_text) > 50:
                QMessageBox.warning(self, "태그 길이", "태그는 50자를 초과할 수 없습니다.")
                return

            # 태그 추가
            self._add_tag_to_list(tag_text)
            self.tag_input.clear()

            logger.debug(f"🏷️ 태그 추가: {tag_text}")

        except Exception as e:
            logger.error(f"❌ 태그 추가 실패: {e}")

    def _add_tag_to_list(self, tag_text: str):
        """태그를 목록에 추가"""
        try:
            item = QListWidgetItem(tag_text)
            self.tags_list.addItem(item)

        except Exception as e:
            logger.error(f"❌ 태그 목록 추가 실패: {e}")

    def _remove_tag(self):
        """선택된 태그 제거"""
        try:
            current_item = self.tags_list.currentItem()
            if current_item:
                tag_text = current_item.text()
                self.tags_list.takeItem(self.tags_list.row(current_item))
                logger.debug(f"🗑️ 태그 제거: {tag_text}")

        except Exception as e:
            logger.error(f"❌ 태그 제거 실패: {e}")

    def _clear_tags(self):
        """모든 태그 제거"""
        try:
            reply = QMessageBox.question(
                self, "태그 삭제", "모든 태그를 삭제하시겠습니까?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )

            if reply == QMessageBox.StandardButton.Yes:
                self.tags_list.clear()
                logger.debug("🗑️ 모든 태그 제거")

        except Exception as e:
            logger.error(f"❌ 태그 전체 삭제 실패: {e}")

    def _validate_metadata_input(self) -> tuple[bool, str]:
        """메타데이터 입력 유효성 검증"""
        try:
            # 표시명 검증
            name = self.name_edit.text().strip()
            if not name:
                return False, "표시명은 필수 입력 항목입니다."

            if len(name) > 100:
                return False, "표시명은 100자를 초과할 수 없습니다."

            # 설명 검증
            description = self.description_edit.toPlainText().strip()
            if len(description) > 500:
                return False, "설명은 500자를 초과할 수 없습니다."

            # 태그 검증
            tags = []
            for i in range(self.tags_list.count()):
                item = self.tags_list.item(i)
                tag = item.text().strip()
                if not tag:
                    return False, "빈 태그는 허용되지 않습니다."
                if len(tag) > 50:
                    return False, f"태그 '{tag}'는 50자를 초과할 수 없습니다."
                tags.append(tag)

            return True, "유효한 입력입니다."

        except Exception as e:
            logger.error(f"❌ 입력 검증 실패: {e}")
            return False, f"입력 검증 중 오류 발생: {e}"

    def _apply_metadata_to_profile(self, profile_name: str) -> bool:
        """프로파일에 메타데이터 적용"""
        try:
            # 입력 검증
            is_valid, error_msg = self._validate_metadata_input()
            if not is_valid:
                QMessageBox.warning(self, "입력 오류", error_msg)
                return False

            # 메타데이터 객체 생성
            updated_metadata = ProfileMetadata(
                name=self.name_edit.text().strip(),
                description=self.description_edit.toPlainText().strip(),
                created_at=self.metadata.created_at,
                created_from=self.metadata.created_from
            )

            # 태그 수집
            for i in range(self.tags_list.count()):
                item = self.tags_list.item(i)
                updated_metadata.add_tag(item.text().strip())

            # 메타데이터 유효성 최종 검증
            is_valid, error_msg = updated_metadata.validate()
            if not is_valid:
                QMessageBox.warning(self, "메타데이터 오류", error_msg)
                return False

            # 시그널 발생
            self.metadata_applied.emit(profile_name, updated_metadata)

            logger.info(f"✅ 메타데이터 적용 완료: {profile_name}")
            return True

        except Exception as e:
            logger.error(f"❌ 메타데이터 적용 실패: {e}")
            QMessageBox.critical(self, "적용 실패", f"메타데이터 적용 중 오류가 발생했습니다:\n{e}")
            return False

    def _apply_metadata(self):
        """메타데이터 적용 버튼 핸들러"""
        try:
            success = self._apply_metadata_to_profile(self.profile_name)
            if success:
                self.accept()

        except Exception as e:
            logger.error(f"❌ 메타데이터 적용 핸들러 실패: {e}")

    def _check_if_custom_profile(self) -> bool:
        """커스텀 프로파일 여부 확인"""
        try:
            system_profiles = ['development', 'production', 'testing', 'staging']
            return self.profile_name not in system_profiles

        except Exception as e:
            logger.warning(f"⚠️ 커스텀 프로파일 확인 실패: {e}")
            return False

    def _apply_styles(self):
        """다이얼로그 스타일 적용"""
        try:
            # 전체 다이얼로그 스타일
            self.setStyleSheet("""
                QDialog {
                    background-color: #f8f9fa;
                }

                QGroupBox {
                    font-weight: bold;
                    border: 2px solid #dee2e6;
                    border-radius: 8px;
                    margin-top: 12px;
                    padding-top: 8px;
                    background-color: white;
                }

                QGroupBox::title {
                    subcontrol-origin: margin;
                    left: 16px;
                    padding: 0 8px 0 8px;
                    color: #495057;
                }

                QLineEdit, QTextEdit {
                    border: 2px solid #e9ecef;
                    border-radius: 6px;
                    padding: 8px;
                    font-size: 13px;
                    background-color: white;
                }

                QLineEdit:focus, QTextEdit:focus {
                    border-color: #007bff;
                }

                QListWidget {
                    border: 2px solid #e9ecef;
                    border-radius: 6px;
                    background-color: white;
                }

                QPushButton {
                    background-color: #007bff;
                    color: white;
                    border: none;
                    border-radius: 6px;
                    padding: 8px 16px;
                    font-weight: bold;
                }

                QPushButton:hover {
                    background-color: #0056b3;
                }

                QPushButton:pressed {
                    background-color: #004085;
                }
            """)

        except Exception as e:
            logger.warning(f"⚠️ 스타일 적용 실패: {e}")
