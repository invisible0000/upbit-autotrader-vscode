#!/usr/bin/env python3
"""
조건 생성기 다이얼로그 (위젯 기반 MVP)
================================

깔끔한 MVP 패턴으로 재구현된 조건 생성기 다이얼로그입니다.
모든 비즈니스 로직은 Presenter에서 처리하고, 다이얼로그는 순수한 View 역할만 합니다.

주요 특징:
- 위젯 기반 모듈러 아키텍처
- DB 연동 변수 정의 시스템
- 실시간 호환성 검증
- 조건 미리보기 및 검증

작성자: Assistant
일시: 2025-01-27
"""

import sys
from typing import Dict, Any, TYPE_CHECKING

# PyQt6 핵심 임포트
try:
    from PyQt6.QtWidgets import (
        QApplication, QDialog, QVBoxLayout, QHBoxLayout,
        QLabel, QLineEdit, QDialogButtonBox, QGroupBox,
        QMessageBox
    )
    from PyQt6.QtCore import pyqtSignal
    PYQT_AVAILABLE = True
except ImportError:
    PYQT_AVAILABLE = False
    if TYPE_CHECKING:
        from PyQt6.QtCore import pyqtSignal

# 위젯 임포트 (가용성 확인)
try:
    from .widgets import (
        VariableSelectionWidget,
        ConditionInputWidget,
        CompatibilityWidget,
        ConditionPreviewWidget
    )
    WIDGETS_AVAILABLE = True
except ImportError:
    WIDGETS_AVAILABLE = False
    if TYPE_CHECKING:
        from .widgets import (
            VariableSelectionWidget, ConditionInputWidget,
            CompatibilityWidget, ConditionPreviewWidget
        )

# 프레젠터 임포트
try:
    from .condition_builder_presenter import ConditionBuilderPresenter
    PRESENTER_AVAILABLE = True
except ImportError:
    PRESENTER_AVAILABLE = False
    if TYPE_CHECKING:
        from .condition_builder_presenter import ConditionBuilderPresenter

# 로깅
try:
    from upbit_auto_trading.utils.logging_config import get_logger
    logger = get_logger(__name__)
except ImportError:
    import logging
    logger = logging.getLogger(__name__)


class ConditionBuilderDialog(QDialog):
    """위젯 기반 MVP 조건 생성기 다이얼로그

    순수한 View 역할만 수행하며, 모든 비즈니스 로직은 Presenter에 위임합니다.
    """

    # 시그널 정의
    condition_created = pyqtSignal(dict)
    condition_updated = pyqtSignal(dict)
    edit_mode_changed = pyqtSignal(bool)

    def __init__(self, parent=None):
        """다이얼로그 초기화"""
        super().__init__(parent)

        # 상태 변수 초기화
        self.edit_mode = False
        self.edit_condition_id = None
        self.condition_data = {}

        # 위젯 참조 초기화
        self.variable_widget = None
        self.input_widget = None
        self.compatibility_widget = None
        self.preview_widget = None

        # 조건 정보 UI
        self.condition_name_input = None
        self.condition_desc_input = None

        # 프레젠터 초기화
        self.presenter = None
        if PRESENTER_AVAILABLE:
            try:
                self.presenter = ConditionBuilderPresenter()
                self._connect_presenter_signals()
                logger.info("ConditionBuilderPresenter 초기화 완료")
            except Exception as e:
                logger.error(f"Presenter 초기화 실패: {e}")

        # UI 초기화
        self.init_ui()

        logger.info("ConditionBuilderDialog 초기화 완료")

    def _connect_presenter_signals(self):
        """프레젠터 시그널 연결"""
        if not self.presenter:
            return

        self.presenter.condition_ready.connect(self._on_condition_ready)
        self.presenter.validation_error.connect(self._show_validation_error)
        self.presenter.edit_mode_changed.connect(self._on_edit_mode_changed)

    def init_ui(self):
        """UI 초기화"""
        self.setWindowTitle("🎯 조건 생성기 (위젯 기반)")
        self.setModal(True)
        self.setMinimumSize(600, 700)
        self.resize(600, 700)

        # 메인 레이아웃
        layout = QVBoxLayout()
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(12)

        # 위젯들 생성 및 배치
        if WIDGETS_AVAILABLE:
            self._create_widgets(layout)
        else:
            self._create_fallback_ui(layout)

        # 조건 정보 입력 섹션
        self._create_condition_info_section(layout)

        # 다이얼로그 버튼
        button_box = self._create_button_box()
        layout.addWidget(button_box)

        self.setLayout(layout)

        # Presenter에 위젯 참조 설정
        if self.presenter and WIDGETS_AVAILABLE:
            self.presenter.set_widgets(
                self.variable_widget,
                self.input_widget,
                self.compatibility_widget,
                self.preview_widget
            )

    def _create_widgets(self, layout):
        """기능별 위젯들 생성 및 배치"""
        try:
            # 1. 변수 선택 위젯
            self.variable_widget = VariableSelectionWidget()
            layout.addWidget(self.variable_widget)

            # 2. 조건 입력 위젯
            self.input_widget = ConditionInputWidget()
            layout.addWidget(self.input_widget)

            # 3. 호환성 검증 위젯
            self.compatibility_widget = CompatibilityWidget()
            layout.addWidget(self.compatibility_widget)

            # 4. 조건 미리보기 위젯
            self.preview_widget = ConditionPreviewWidget()
            layout.addWidget(self.preview_widget)

            logger.info("모든 위젯 생성 완료")

        except Exception as e:
            logger.error(f"위젯 생성 실패: {e}")
            self._create_fallback_ui(layout)

    def _create_fallback_ui(self, layout):
        """위젯을 사용할 수 없을 때의 대체 UI"""
        fallback_label = QLabel("⚠️ 위젯을 로드할 수 없습니다.\n\n기본 UI로 전환됩니다.")
        fallback_label.setStyleSheet("""
            QLabel {
                background-color: #fff3cd;
                border: 1px solid #ffeaa7;
                padding: 20px;
                border-radius: 8px;
                color: #856404;
                font-size: 14px;
                text-align: center;
            }
        """)
        layout.addWidget(fallback_label)

    def _create_condition_info_section(self, layout):
        """조건 정보 입력 섹션 생성"""
        group = QGroupBox("📝 조건 정보")
        group_layout = QVBoxLayout()

        # 조건 이름
        name_layout = QHBoxLayout()
        name_layout.addWidget(QLabel("조건 이름:"))

        self.condition_name_input = QLineEdit()
        self.condition_name_input.setPlaceholderText("조건의 이름을 입력하세요")
        name_layout.addWidget(self.condition_name_input)

        group_layout.addLayout(name_layout)

        # 설명
        desc_layout = QHBoxLayout()
        desc_layout.addWidget(QLabel("설명:"))

        self.condition_desc_input = QLineEdit()
        self.condition_desc_input.setPlaceholderText("조건에 대한 설명을 입력하세요 (선택사항)")
        desc_layout.addWidget(self.condition_desc_input)

        group_layout.addLayout(desc_layout)

        group.setLayout(group_layout)
        layout.addWidget(group)

    def _create_button_box(self):
        """다이얼로그 버튼 박스 생성"""
        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )

        # 버튼 스타일링
        ok_button = button_box.button(QDialogButtonBox.StandardButton.Ok)
        if ok_button:
            ok_button.setText("✅ 조건 저장")

        cancel_button = button_box.button(QDialogButtonBox.StandardButton.Cancel)
        if cancel_button:
            cancel_button.setText("❌ 취소")

        # 시그널 연결
        button_box.accepted.connect(self.accept_condition)
        button_box.rejected.connect(self.reject)

        return button_box

    # === 이벤트 핸들러 ===

    def accept_condition(self):
        """조건 승인 처리"""
        try:
            # 필수 입력 검증
            if not self.condition_name_input.text().strip():
                QMessageBox.warning(self, "입력 오류", "조건 이름을 입력해주세요.")
                return

            # Presenter에게 조건 생성/수정 요청
            if self.presenter:
                condition_info = {
                    'name': self.condition_name_input.text().strip(),
                    'description': self.condition_desc_input.text().strip()
                }

                if self.edit_mode:
                    self.presenter.update_condition(self.edit_condition_id, condition_info)
                else:
                    self.presenter.create_condition(condition_info)
            else:
                # Presenter가 없는 경우 직접 처리
                self._handle_condition_without_presenter()

        except Exception as e:
            logger.error(f"조건 승인 처리 실패: {e}")
            QMessageBox.critical(self, "오류", f"조건 처리 중 오류가 발생했습니다: {str(e)}")

    def _handle_condition_without_presenter(self):
        """Presenter 없이 조건 처리"""
        condition_data = {
            'id': self.edit_condition_id or f"condition_{int(self._get_timestamp())}",
            'name': self.condition_name_input.text().strip(),
            'description': self.condition_desc_input.text().strip(),
            'created_at': self._get_timestamp(),
            'edit_mode': self.edit_mode
        }

        self.condition_data = condition_data

        if self.edit_mode:
            self.condition_updated.emit(condition_data)
        else:
            self.condition_created.emit(condition_data)

        self.accept()

    def _get_timestamp(self) -> float:
        """현재 타임스탬프 반환"""
        from datetime import datetime
        return datetime.now().timestamp()

    # === 프레젠터 시그널 핸들러 ===

    def _on_condition_ready(self, condition_data: Dict[str, Any]):
        """조건 생성/수정 완료 시 호출"""
        self.condition_data = condition_data

        if self.edit_mode:
            self.condition_updated.emit(condition_data)
            logger.info(f"조건 수정 완료: {condition_data.get('name', 'Unknown')}")
        else:
            self.condition_created.emit(condition_data)
            logger.info(f"조건 생성 완료: {condition_data.get('name', 'Unknown')}")

        self.accept()

    def _show_validation_error(self, error_message: str):
        """검증 오류 표시"""
        QMessageBox.warning(self, "검증 오류", error_message)

    def _on_edit_mode_changed(self, is_edit_mode: bool):
        """편집 모드 변경 시 호출"""
        self.edit_mode = is_edit_mode

        if is_edit_mode:
            self.setWindowTitle("🔧 조건 수정")
        else:
            self.setWindowTitle("🎯 조건 생성기 (위젯 기반)")

        self.edit_mode_changed.emit(is_edit_mode)

    # === 공개 API ===

    def get_condition_data(self) -> Dict[str, Any]:
        """생성/수정된 조건 데이터 반환"""
        return getattr(self, 'condition_data', {})

    def set_edit_mode(self, condition_data: Dict[str, Any]):
        """편집 모드로 전환"""
        try:
            self.edit_mode = True
            self.edit_condition_id = condition_data.get('id')

            # UI에 기존 데이터 로드
            if condition_data.get('name'):
                self.condition_name_input.setText(condition_data['name'])
            if condition_data.get('description'):
                self.condition_desc_input.setText(condition_data['description'])

            # Presenter에게 편집 모드 설정
            if self.presenter:
                self.presenter.set_edit_mode(condition_data)

            self.setWindowTitle(f"🔧 조건 수정: {condition_data.get('name', '알 수 없음')}")
            self.edit_mode_changed.emit(True)

            logger.info(f"편집 모드 활성화: {condition_data.get('name', 'Unknown')}")

        except Exception as e:
            logger.error(f"편집 모드 설정 실패: {e}")

    def reset_to_create_mode(self):
        """생성 모드로 초기화"""
        self.edit_mode = False
        self.edit_condition_id = None

        # UI 초기화
        if self.condition_name_input:
            self.condition_name_input.clear()
        if self.condition_desc_input:
            self.condition_desc_input.clear()

        # Presenter 초기화
        if self.presenter:
            self.presenter.reset_to_create_mode()

        self.setWindowTitle("🎯 조건 생성기 (위젯 기반)")
        self.edit_mode_changed.emit(False)

        logger.info("생성 모드로 초기화")


# === 독립 실행 코드 ===

def main():
    """독립 실행용 메인 함수"""
    print("🚀 ConditionBuilderDialog (위젯 기반 MVP) 독립 실행 시작!")

    if not PYQT_AVAILABLE:
        print("❌ PyQt6가 설치되지 않았습니다.")
        return

    app = QApplication(sys.argv)

    # 다이얼로그 생성
    dialog = ConditionBuilderDialog()

    # 테스트용 시그널 연결
    def on_condition_created(condition_data):
        print(f"✅ 조건 생성됨: {condition_data}")

    def on_condition_updated(condition_data):
        print(f"🔧 조건 수정됨: {condition_data}")

    def on_edit_mode_changed(is_edit_mode):
        print(f"🔄 편집 모드 변경: {is_edit_mode}")

    dialog.condition_created.connect(on_condition_created)
    dialog.condition_updated.connect(on_condition_updated)
    dialog.edit_mode_changed.connect(on_edit_mode_changed)

    # 다이얼로그 실행
    result = dialog.exec()

    if result == QDialog.DialogCode.Accepted:
        condition_data = dialog.get_condition_data()
        print(f"💾 최종 조건 데이터: {condition_data}")
    else:
        print("❌ 다이얼로그 취소됨")

    print("🔚 프로그램 종료!")


if __name__ == "__main__":
    main()
