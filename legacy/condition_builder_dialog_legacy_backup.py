#!/usr/bin/env python3
"""
조건 빌더 다이얼로그 - 위젯 기반 MVP 패턴

TriggerBuilder와 StrategyMaker에서 공통으로 사용하는 모달 형태의 조건 생성 다이얼로그입니다.
위젯 분리 및 MVP 패턴을 적용하여 리팩토링된 버전입니다.

Architecture: Widget-based MVP Pattern
- View: ConditionBuilderDialog (Passive View - 이 클래스)
- Presenter: ConditionBuilderPresenter
- Widgets: VariableSelectionWidget, ConditionInputWidget, etc.
"""

import sys
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QMessageBox,
    QLineEdit, QApplication, QDialogButtonBox
)
from PyQt6.QtCore import pyqtSignal
from typing import Dict, Any

from upbit_auto_trading.infrastructure.logging import create_component_logger

# 위젯 및 프레젠터 import
try:
    from .widgets import (
        VariableSelectionWidget, ConditionInputWidget,
        CompatibilityWidget, ConditionPreviewWidget
    )
    from .condition_builder_presenter import ConditionBuilderPresenter
    WIDGETS_AVAILABLE = True
except ImportError as e:
    print(f"⚠️ 위젯 import 실패: {e}")
    WIDGETS_AVAILABLE = False

# 공통 컴포넌트 import
try:
    from upbit_auto_trading.ui.desktop.common.components import StyledLineEdit
    STYLED_COMPONENTS_AVAILABLE = True
except ImportError:
    StyledLineEdit = QLineEdit
    STYLED_COMPONENTS_AVAILABLE = False


class ConditionBuilderDialog(QDialog):
    """조건 빌더 다이얼로그 - 위젯 기반 MVP 패턴

    위젯 분리 및 MVP 패턴을 적용한 리팩토링된 조건 생성 다이얼로그입니다.

    Architecture:
        - Passive View: UI 이벤트만 처리, 비즈니스 로직은 Presenter에 위임
        - Widget-based: 기능별로 분리된 독립적인 위젯들 사용
        - MVP Pattern: Presenter가 비즈니스 로직과 위젯 간 조정 담당

    Signals:
        condition_created: 새 조건이 생성되었을 때 발생
        condition_updated: 기존 조건이 수정되었을 때 발생
    """

    # 시그널 정의 (Presenter에서 전달받음)
    condition_created = pyqtSignal(dict)  # 조건 생성 완료
    condition_updated = pyqtSignal(dict)  # 조건 수정 완료

    def __init__(self, parent=None):
        """다이얼로그 초기화"""
        super().__init__(parent)
        self.logger = create_component_logger("ConditionBuilderDialog")

        # MVP: Presenter 초기화
        self.presenter = None
        if WIDGETS_AVAILABLE:
            self.presenter = ConditionBuilderPresenter()
            self._connect_presenter_signals()

        # UI 상태
        self.condition_data = {}  # 최종 반환 데이터

        # 위젯 참조
        self.variable_widget = None
        self.input_widget = None
        self.compatibility_widget = None
        self.preview_widget = None

        # 조건 정보 입력 필드
        self.condition_name_input = None
        self.condition_desc_input = None

        # UI 초기화
        self.init_ui()
        self.logger.info("조건 빌더 다이얼로그 (위젯 기반) 초기화 완료")

    def _connect_presenter_signals(self):
        """Presenter 시그널 연결"""
        if not self.presenter:
            return

        # Presenter → View 시그널 연결
        self.presenter.condition_created.connect(self._on_condition_created)
        self.presenter.condition_updated.connect(self._on_condition_updated)
        self.presenter.validation_error.connect(self._show_validation_error)
        self.presenter.edit_mode_changed.connect(self._on_edit_mode_changed)

    def init_ui(self):
        """UI 초기화 - 위젯 기반"""
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

            # 4. 미리보기 위젯
            self.preview_widget = ConditionPreviewWidget()
            layout.addWidget(self.preview_widget)

            self.logger.info("모든 위젯 생성 완료")

        except Exception as e:
            self.logger.error(f"위젯 생성 실패: {e}")
            self._create_fallback_ui(layout)

    def _create_fallback_ui(self, layout):
        """위젯이 없을 때 폴백 UI"""
        fallback_label = QLabel("⚠️ 위젯을 로드할 수 없습니다. 기본 UI로 동작합니다.")
        fallback_label.setStyleSheet("color: orange; padding: 10px; background: #fff3cd; border-radius: 4px;")
        layout.addWidget(fallback_label)

    def _create_condition_info_section(self, layout):
        """조건 정보 입력 섹션 생성"""
        # 조건 이름 입력
        name_layout = QHBoxLayout()
        name_layout.addWidget(QLabel("조건 이름:"))

        self.condition_name_input = StyledLineEdit()
        self.condition_name_input.setPlaceholderText("조건의 이름을 입력하세요")
        name_layout.addWidget(self.condition_name_input)

        layout.addLayout(name_layout)

        # 설명 입력
        desc_layout = QHBoxLayout()
        desc_layout.addWidget(QLabel("설명:"))

        self.condition_desc_input = StyledLineEdit()
        self.condition_desc_input.setPlaceholderText("조건에 대한 설명을 입력하세요 (선택사항)")
        desc_layout.addWidget(self.condition_desc_input)

        layout.addLayout(desc_layout)

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
        button_box.accepted.connect(self._handle_accept)
        button_box.rejected.connect(self.reject)

        return button_box

    # === 이벤트 핸들러 (Passive View) ===

    def _handle_accept(self):
        """확인 버튼 클릭 처리 - Presenter에 위임"""
        if not self.presenter:
            self._fallback_accept()
            return

        # Presenter에게 조건 생성 요청
        condition_name = self.condition_name_input.text().strip()
        condition_desc = self.condition_desc_input.text().strip()

        self.presenter.handle_condition_creation(condition_name, condition_desc)

    def _fallback_accept(self):
        """Presenter가 없을 때 폴백 처리"""
        if not self.condition_name_input.text().strip():
            QMessageBox.warning(self, "입력 오류", "조건 이름을 입력해주세요.")
            return

        # 기본 조건 데이터 생성
        self.condition_data = {
            'name': self.condition_name_input.text().strip(),
            'description': self.condition_desc_input.text().strip(),
            'fallback_mode': True
        }

        self.condition_created.emit(self.condition_data)
        self.accept()

    # === Presenter → View 시그널 핸들러 ===

    def _on_condition_created(self, condition_data: Dict[str, Any]):
        """조건 생성 완료 처리"""
        self.condition_data = condition_data
        self.condition_created.emit(condition_data)
        self.accept()
        self.logger.info(f"조건 생성 완료: {condition_data.get('name', 'Unknown')}")

    def _on_condition_updated(self, condition_data: Dict[str, Any]):
        """조건 수정 완료 처리"""
        self.condition_data = condition_data
        self.condition_updated.emit(condition_data)
        self.accept()
        self.logger.info(f"조건 수정 완료: {condition_data.get('name', 'Unknown')}")

    def _show_validation_error(self, error_message: str):
        """검증 오류 표시"""
        QMessageBox.warning(self, "검증 오류", error_message)

    def _on_edit_mode_changed(self, edit_mode: bool):
        """편집 모드 변경 처리"""
        if edit_mode:
            self.setWindowTitle("🔧 조건 수정 (위젯 기반)")
        else:
            self.setWindowTitle("🎯 조건 생성기 (위젯 기반)")

    # === 공개 API ===

    def get_condition_data(self) -> Dict[str, Any]:
        """생성/수정된 조건 데이터 반환"""
        return self.condition_data.copy()

    def set_edit_mode(self, condition_data: Dict[str, Any]):
        """편집 모드로 전환"""
        if self.presenter:
            self.presenter.set_edit_mode(condition_data)

        # UI에 기존 데이터 로드
        if condition_data.get('name'):
            self.condition_name_input.setText(condition_data['name'])
        if condition_data.get('description'):
            self.condition_desc_input.setText(condition_data['description'])

    def reset_to_create_mode(self):
        """생성 모드로 초기화"""
        if self.presenter:
            self.presenter.reset_to_create_mode()

        # UI 초기화
        self.condition_name_input.clear()
        self.condition_desc_input.clear()

    def create_content_widget(self):
        """조건 빌더 컨텐츠 위젯 생성"""
        content_widget = QDialog()  # 내부 컨테이너
        content_layout = QVBoxLayout()
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(8)

        # 1. 변수 선택 섹션
        self.create_variable_section(content_layout)

        # 2. 비교 설정 섹션
        self.create_comparison_section(content_layout)

        # 3. 외부 변수 설정 섹션
        self.create_external_variable_section(content_layout)

        # 4. 조건 정보 섹션
        self.create_info_section(content_layout)

        # 5. 미리보기 섹션
        self.create_preview_section(content_layout)

        content_widget.setLayout(content_layout)
        return content_widget

    def create_variable_section(self, layout):
        """변수 선택 섹션 생성"""
        group = StyledGroupBox("📊 1단계: 변수 선택")
        group.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        group_layout = QVBoxLayout()
        group_layout.setContentsMargins(8, 8, 8, 8)
        group_layout.setSpacing(6)

        # 범주 + 변수 선택을 한 줄로
        category_var_layout = QHBoxLayout()

        # 범주 선택
        category_var_layout.addWidget(QLabel("범주:"))

        self.category_combo = StyledComboBox()
        self.category_combo.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        self.category_combo.setFixedHeight(28)

        # DB 기반 카테고리 로드 (컴포넌트가 있을 때)
        if self.variable_definitions:
            try:
                category_variables = self.variable_definitions.get_category_variables()
                for category in category_variables.keys():
                    # 카테고리 아이콘 추가
                    icon_map = {
                        "trend": "📈", "momentum": "⚡", "volatility": "🔥",
                        "volume": "📦", "price": "💰", "indicator": "📊"
                    }
                    icon = icon_map.get(category, "🔹")
                    self.category_combo.addItem(f"{icon} {category.title()}", category)
                self.logger.info(f"DB에서 {len(category_variables)}개 카테고리 로드 완료")
            except Exception as e:
                self.logger.error(f"카테고리 로드 실패: {e}")
                # 폴백: 기본 카테고리
                self.category_combo.addItems(["trend", "momentum", "volatility", "volume", "price"])
        else:
            # 기본 카테고리 추가 (컴포넌트가 없을 때 폴백)
            self.category_combo.addItems(["trend", "momentum", "volatility", "volume", "price"])

        category_var_layout.addWidget(self.category_combo)

        # 변수 선택
        category_var_layout.addWidget(QLabel("변수:"))

        self.variable_combo = StyledComboBox()
        self.variable_combo.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        self.variable_combo.setFixedHeight(28)

        # DB 기반 변수 로드 (초기화 시 자동 로드)
        # 하드코딩된 변수 목록 제거됨 - DB에서 동적 로드

        category_var_layout.addWidget(self.variable_combo)

        group_layout.addLayout(category_var_layout)

        # 변수 정보 표시 라벨
        self.variable_info_label = QLabel("변수를 선택하면 정보가 표시됩니다.")
        self.variable_info_label.setWordWrap(True)
        self.variable_info_label.setStyleSheet("color: #666; font-size: 11px; margin: 5px 0;")
        group_layout.addWidget(self.variable_info_label)

        group.setLayout(group_layout)
        layout.addWidget(group)

    def create_comparison_section(self, layout):
        """비교 설정 섹션 생성"""
        group = StyledGroupBox("⚖️ 2단계: 비교 설정")
        group_layout = QVBoxLayout()
        group_layout.setContentsMargins(8, 8, 8, 8)
        group_layout.setSpacing(6)

        # 비교 연산자 선택
        operator_layout = QHBoxLayout()
        operator_layout.addWidget(QLabel("연산자:"))

        self.operator_combo = StyledComboBox()
        self.operator_combo.addItems([">", ">=", "<", "<=", "==", "!="])
        self.operator_combo.setFixedHeight(28)
        operator_layout.addWidget(self.operator_combo)

        operator_layout.addStretch()
        group_layout.addLayout(operator_layout)

        group.setLayout(group_layout)
        layout.addWidget(group)

    def create_external_variable_section(self, layout):
        """외부 변수 설정 섹션 생성"""
        group = StyledGroupBox("🔗 3단계: 비교 대상")
        group_layout = QVBoxLayout()
        group_layout.setContentsMargins(8, 8, 8, 8)
        group_layout.setSpacing(6)

        # 비교 방식 선택 (고정값 vs 다른 변수)
        comparison_type_layout = QHBoxLayout()
        comparison_type_layout.addWidget(QLabel("비교 방식:"))

        self.comparison_type_combo = StyledComboBox()
        self.comparison_type_combo.addItems(["고정값", "다른 변수"])
        self.comparison_type_combo.setFixedHeight(28)
        comparison_type_layout.addWidget(self.comparison_type_combo)

        comparison_type_layout.addStretch()
        group_layout.addLayout(comparison_type_layout)

        # 고정값 입력
        fixed_value_layout = QHBoxLayout()
        fixed_value_layout.addWidget(QLabel("값:"))

        self.fixed_value_input = StyledLineEdit()
        self.fixed_value_input.setPlaceholderText("비교할 값을 입력하세요 (예: 30, 1.5)")
        fixed_value_layout.addWidget(self.fixed_value_input)

        group_layout.addLayout(fixed_value_layout)

        # 호환성 상태 표시 라벨 (다른 변수 선택 시)
        self.compatibility_status_label = QLabel()
        self.compatibility_status_label.setWordWrap(True)
        self.compatibility_status_label.setStyleSheet("""
            QLabel {
                background-color: #f8f9fa;
                border: 1px solid #dee2e6;
                padding: 8px;
                border-radius: 4px;
                margin: 5px 0;
                font-size: 11px;
            }
        """)
        self.compatibility_status_label.hide()  # 초기에는 숨김
        group_layout.addWidget(self.compatibility_status_label)

        group.setLayout(group_layout)
        layout.addWidget(group)

    def create_info_section(self, layout):
        """조건 정보 섹션 생성"""
        group = StyledGroupBox("📝 4단계: 조건 정보")
        group_layout = QVBoxLayout()
        group_layout.setContentsMargins(8, 8, 8, 8)
        group_layout.setSpacing(6)

        # 조건 이름 입력
        name_layout = QHBoxLayout()
        name_layout.addWidget(QLabel("조건 이름:"))

        self.condition_name_input = StyledLineEdit()
        self.condition_name_input.setPlaceholderText("조건의 이름을 입력하세요")
        name_layout.addWidget(self.condition_name_input)

        group_layout.addLayout(name_layout)

        # 설명 입력
        desc_layout = QHBoxLayout()
        desc_layout.addWidget(QLabel("설명:"))

        self.condition_desc_input = StyledLineEdit()
        self.condition_desc_input.setPlaceholderText("조건에 대한 설명을 입력하세요 (선택사항)")
        desc_layout.addWidget(self.condition_desc_input)

        group_layout.addLayout(desc_layout)

        group.setLayout(group_layout)
        layout.addWidget(group)

    def create_preview_section(self, layout):
        """미리보기 섹션 생성"""
        group = StyledGroupBox("👁️ 5단계: 미리보기")
        group_layout = QVBoxLayout()
        group_layout.setContentsMargins(8, 8, 8, 8)
        group_layout.setSpacing(6)

        # 미리보기 텍스트
        self.preview_label = QLabel("조건을 설정하면 미리보기가 표시됩니다.")
        self.preview_label.setWordWrap(True)
        self.preview_label.setStyleSheet("""
            QLabel {
                background-color: #f8f9fa;
                border: 1px solid #dee2e6;
                padding: 10px;
                border-radius: 4px;
                font-family: 'Courier New', monospace;
                color: #495057;
            }
        """)
        group_layout.addWidget(self.preview_label)

        group.setLayout(group_layout)
        layout.addWidget(group)

    def create_button_box(self):
        """다이얼로그 버튼 박스 생성"""
        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )

        # 버튼 텍스트 한글화 및 스타일 개선
        ok_button = button_box.button(QDialogButtonBox.StandardButton.Ok)
        if ok_button:
            ok_button.setText("✅ 조건 저장")
            ok_button.setStyleSheet("""
                QPushButton {
                    background-color: #28a745;
                    color: white;
                    border: none;
                    padding: 8px 16px;
                    border-radius: 4px;
                    font-weight: bold;
                }
                QPushButton:hover {
                    background-color: #218838;
                }
                QPushButton:disabled {
                    background-color: #6c757d;
                }
            """)

        cancel_button = button_box.button(QDialogButtonBox.StandardButton.Cancel)
        if cancel_button:
            cancel_button.setText("❌ 취소")
            cancel_button.setStyleSheet("""
                QPushButton {
                    background-color: #6c757d;
                    color: white;
                    border: none;
                    padding: 8px 16px;
                    border-radius: 4px;
                }
                QPushButton:hover {
                    background-color: #5a6268;
                }
            """)

        # 시그널 연결
        button_box.accepted.connect(self.accept_condition)
        button_box.rejected.connect(self.reject)

        return button_box    # === 이벤트 핸들러 ===

    def accept_condition(self):
        """조건 승인 - 데이터 검증 후 다이얼로그 닫기"""
        try:
            # 필수 데이터 검증
            if not self.condition_name_input.text().strip():
                QMessageBox.warning(self, "입력 오류", "조건 이름을 입력해주세요.")
                return

            # 조건 데이터 수집
            self.condition_data = self.collect_condition_data()

            if not self.condition_data:
                QMessageBox.warning(self, "데이터 오류", "조건 데이터를 생성할 수 없습니다.")
                return

            # 검증 성공 시 시그널 발생
            if self.edit_mode:
                self.condition_updated.emit(self.condition_data)
                self.logger.info(f"조건 수정 완료: {self.condition_data.get('name', 'Unknown')}")
            else:
                self.condition_created.emit(self.condition_data)
                self.logger.info(f"조건 생성 완료: {self.condition_data.get('name', 'Unknown')}")

            # 다이얼로그 승인
            self.accept()

        except Exception as e:
            self.logger.error(f"조건 승인 처리 실패: {e}")
            QMessageBox.critical(self, "오류", f"조건 처리 중 오류가 발생했습니다: {str(e)}")

    def collect_condition_data(self) -> Dict[str, Any]:
        """현재 UI 상태에서 조건 데이터 수집"""
        try:
            condition_data = {
                'id': self.edit_condition_id or f"condition_{int(self.get_timestamp())}",
                'name': self.condition_name_input.text().strip(),
                'description': self.condition_desc_input.text().strip(),
                'variable': self.variable_combo.currentText(),
                'operator': self.operator_combo.currentText(),
                'comparison_type': self.comparison_type_combo.currentText(),
                'value': self.fixed_value_input.text().strip(),
                'created_at': self.get_timestamp(),
                'edit_mode': self.edit_mode
            }

            self.logger.debug(f"조건 데이터 수집 완료: {condition_data}")
            return condition_data

        except Exception as e:
            self.logger.error(f"조건 데이터 수집 실패: {e}")
            return {}

    def get_timestamp(self) -> float:
        """현재 타임스탬프 반환"""
        from datetime import datetime
        return datetime.now().timestamp()

    def update_variables_by_category(self):
        """카테고리별 변수 목록 업데이트 - DB 기반 동적 로딩"""
        if not self.variable_definitions:
            self.logger.debug("VariableDefinitions가 없어 기본값 사용")
            # 폴백: 기본 변수 목록
            self.variable_combo.clear()
            self.variable_combo.addItems(["현재가", "RSI", "MACD", "거래량"])
            return

        try:
            self.variable_combo.clear()

            category_variables = self.variable_definitions.get_category_variables()
            selected_category = self.category_combo.currentData()

            # currentData()가 None인 경우 currentText() 사용 (아이콘 제거)
            if selected_category is None:
                current_text = self.category_combo.currentText()
                # 아이콘 제거해서 실제 카테고리 이름 추출
                for icon in ["📈 ", "⚡ ", "🔥 ", "📦 ", "💰 ", "� ", "🔹 "]:
                    current_text = current_text.replace(icon, "")
                selected_category = current_text.lower()

            if selected_category in category_variables:
                for var_id, var_name in category_variables[selected_category]:
                    # 아이콘 추가 (카테고리별)
                    icon_map = {
                        "trend": "📈", "momentum": "⚡", "volatility": "🔥",
                        "volume": "📦", "price": "💰", "indicator": "📊"
                    }
                    icon = icon_map.get(selected_category, "🔹")
                    self.variable_combo.addItem(f"{icon} {var_name}", var_id)

                self.logger.info(f"카테고리 '{selected_category}'에서 {self.variable_combo.count()}개 변수 로드됨")

                # 변수 정보 업데이트
                if self.variable_combo.count() > 0:
                    self.update_variable_info()
            else:
                self.logger.warning(f"카테고리 '{selected_category}' 없음. 사용가능 카테고리: {list(category_variables.keys())}")
                self.variable_info_label.setText("선택한 카테고리에 변수가 없습니다.")

        except Exception as e:
            self.logger.error(f"변수 업데이트 실패: {e}")
            # 폴백: 기본 변수 로드
            self.variable_combo.clear()
            self.variable_combo.addItems(["현재가", "RSI", "MACD", "거래량"])
            self.variable_info_label.setText("변수 로드 실패 - 기본값 사용 중")

    def update_variable_info(self):
        """선택된 변수의 정보 표시"""
        if not self.variable_definitions:
            return

        try:
            current_var_id = self.variable_combo.currentData()
            if not current_var_id:
                # currentData()가 None인 경우 첫 번째 변수 가정
                if self.variable_combo.count() > 0:
                    current_var_id = self.variable_combo.itemData(0)

            if current_var_id:
                # 변수 정보 로드
                variables = self.variable_definitions._load_variables_from_db()
                var_info = variables.get(current_var_id, {})

                var_name = var_info.get("name_ko", current_var_id)
                description = var_info.get("description", "설명 없음")
                purpose_category = var_info.get("purpose_category", "알 수 없음")

                info_text = f"📊 {var_name}\n📝 {description}\n🏷️ 카테고리: {purpose_category}"
                self.variable_info_label.setText(info_text)
            else:
                self.variable_info_label.setText("변수를 선택하면 정보가 표시됩니다.")

        except Exception as e:
            self.logger.error(f"변수 정보 업데이트 실패: {e}")
            self.variable_info_label.setText("변수 정보 로드 실패")

    def update_preview(self):
        """조건 미리보기 업데이트"""
        try:
            if not hasattr(self, 'preview_label'):
                return

            # 기본 미리보기 생성
            variable = self.variable_combo.currentText()
            operator = self.operator_combo.currentText()
            value = self.fixed_value_input.text().strip()

            if variable and operator and value:
                preview_text = f"조건: {variable} {operator} {value}"
                self.preview_label.setText(preview_text)
            else:
                self.preview_label.setText("조건을 설정하면 미리보기가 표시됩니다.")

        except Exception as e:
            self.logger.error(f"미리보기 업데이트 실패: {e}")

    # === 공개 API ===

    def get_condition_data(self) -> Dict[str, Any]:
        """생성/수정된 조건 데이터 반환

        Returns:
            조건 데이터 딕셔너리 (다이얼로그가 accept된 경우에만 유효)
        """
        return getattr(self, 'condition_data', {})

    def set_edit_mode(self, condition_data: Dict[str, Any]):
        """편집 모드로 전환 (기존 조건 수정)

        Args:
            condition_data: 편집할 조건 데이터
        """
        try:
            self.edit_mode = True
            self.edit_condition_id = condition_data.get('id')
            self.editing_condition_name = condition_data.get('name')

            # UI에 기존 데이터 로드
            if condition_data.get('name'):
                self.condition_name_input.setText(condition_data['name'])
            if condition_data.get('description'):
                self.condition_desc_input.setText(condition_data['description'])
            if condition_data.get('variable'):
                self.variable_combo.setCurrentText(condition_data['variable'])
            if condition_data.get('operator'):
                self.operator_combo.setCurrentText(condition_data['operator'])
            if condition_data.get('value'):
                self.fixed_value_input.setText(str(condition_data['value']))

            # 창 제목 변경
            self.setWindowTitle(f"🔧 조건 수정: {self.editing_condition_name}")

            self.edit_mode_changed.emit(True)
            self.logger.info(f"편집 모드 활성화: {self.editing_condition_name}")

        except Exception as e:
            self.logger.error(f"편집 모드 설정 실패: {e}")

    def reset_to_create_mode(self):
        """생성 모드로 초기화"""
        self.edit_mode = False
        self.edit_condition_id = None
        self.editing_condition_name = None

        # UI 초기화
        self.condition_name_input.clear()
        self.condition_desc_input.clear()
        self.fixed_value_input.clear()

        # 창 제목 복원
        self.setWindowTitle("🎯 조건 생성기 (독립 다이얼로그)")

        self.edit_mode_changed.emit(False)
        self.logger.info("생성 모드로 초기화")


# === 독립 실행 코드 ===

def main():
    """독립 실행용 메인 함수"""
    print("🚀 ConditionBuilderDialog 독립 실행 시작!")

    app = QApplication(sys.argv)

    # 다이얼로그 생성 및 실행
    dialog = ConditionBuilderDialog()

    # 테스트용 시그널 연결
    def on_condition_created(condition_data):
        print(f"✅ 조건 생성됨: {condition_data}")

    def on_condition_updated(condition_data):
        print(f"🔧 조건 수정됨: {condition_data}")

    dialog.condition_created.connect(on_condition_created)
    dialog.condition_updated.connect(on_condition_updated)

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
