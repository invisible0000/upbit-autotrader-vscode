#!/usr/bin/env python3
"""
조건 입력 위젯 - 조건 빌더 컴포넌트

비교 연산자, 값 입력을 담당하는 독립적인 위젯입니다.
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QComboBox, QLineEdit, QGroupBox
)
from PyQt6.QtCore import pyqtSignal

from upbit_auto_trading.infrastructure.logging import create_component_logger

# 공통 컴포넌트 import
try:
    from upbit_auto_trading.ui.desktop.common.components import (
        StyledComboBox, StyledLineEdit
    )
    STYLED_COMPONENTS_AVAILABLE = True
except ImportError:
    StyledComboBox = QComboBox
    StyledLineEdit = QLineEdit
    STYLED_COMPONENTS_AVAILABLE = False


class ConditionInputWidget(QWidget):
    """조건 입력 위젯

    비교 연산자와 값 입력을 담당합니다.
    단일 책임 원칙을 따라 입력 기능만 처리합니다.

    Signals:
        operator_changed: 연산자가 변경되었을 때 발생 (operator)
        value_changed: 값이 변경되었을 때 발생 (value)
        comparison_type_changed: 비교 방식이 변경되었을 때 발생 (type)
    """

    # 시그널 정의
    operator_changed = pyqtSignal(str)      # operator
    value_changed = pyqtSignal(str)         # value
    comparison_type_changed = pyqtSignal(str)  # type

    def __init__(self, parent=None):
        """조건 입력 위젯 초기화"""
        super().__init__(parent)
        self.logger = create_component_logger("ConditionInputWidget")

        # UI 초기화
        self.init_ui()

    def init_ui(self):
        """UI 초기화"""
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        # 비교 설정 그룹
        comparison_group = QGroupBox("⚖️ 비교 설정")
        comparison_layout = QVBoxLayout()
        comparison_layout.setContentsMargins(8, 8, 8, 8)
        comparison_layout.setSpacing(6)

        # 비교 연산자 선택
        operator_layout = QHBoxLayout()
        operator_layout.addWidget(QLabel("연산자:"))

        self.operator_combo = StyledComboBox()
        self.operator_combo.addItems([">", ">=", "<", "<=", "==", "!="])
        self.operator_combo.setFixedHeight(28)
        operator_layout.addWidget(self.operator_combo)
        operator_layout.addStretch()

        comparison_layout.addLayout(operator_layout)
        comparison_group.setLayout(comparison_layout)
        layout.addWidget(comparison_group)

        # 비교 대상 그룹
        target_group = QGroupBox("🔗 비교 대상")
        target_layout = QVBoxLayout()
        target_layout.setContentsMargins(8, 8, 8, 8)
        target_layout.setSpacing(6)

        # 비교 방식 선택
        type_layout = QHBoxLayout()
        type_layout.addWidget(QLabel("방식:"))

        self.comparison_type_combo = StyledComboBox()
        self.comparison_type_combo.addItems(["고정값", "다른 변수"])
        self.comparison_type_combo.setFixedHeight(28)
        type_layout.addWidget(self.comparison_type_combo)
        type_layout.addStretch()

        target_layout.addLayout(type_layout)

        # 값 입력
        value_layout = QHBoxLayout()
        value_layout.addWidget(QLabel("값:"))

        self.value_input = StyledLineEdit()
        self.value_input.setPlaceholderText("비교할 값을 입력하세요 (예: 30, 1.5)")
        value_layout.addWidget(self.value_input)

        target_layout.addLayout(value_layout)

        target_group.setLayout(target_layout)
        layout.addWidget(target_group)

        self.setLayout(layout)

        # 시그널 연결
        self.operator_combo.currentTextChanged.connect(self.operator_changed.emit)
        self.comparison_type_combo.currentTextChanged.connect(self.comparison_type_changed.emit)
        self.value_input.textChanged.connect(self.value_changed.emit)

    # === 공개 API ===

    def get_operator(self) -> str:
        """현재 선택된 연산자 반환"""
        return self.operator_combo.currentText()

    def get_comparison_type(self) -> str:
        """현재 선택된 비교 방식 반환"""
        return self.comparison_type_combo.currentText()

    def get_value(self) -> str:
        """현재 입력된 값 반환"""
        return self.value_input.text().strip()

    def set_operator(self, operator: str):
        """연산자 설정 (편집 모드용)"""
        index = self.operator_combo.findText(operator)
        if index >= 0:
            self.operator_combo.setCurrentIndex(index)

    def set_comparison_type(self, comp_type: str):
        """비교 방식 설정 (편집 모드용)"""
        index = self.comparison_type_combo.findText(comp_type)
        if index >= 0:
            self.comparison_type_combo.setCurrentIndex(index)

    def set_value(self, value: str):
        """값 설정 (편집 모드용)"""
        self.value_input.setText(value)

    def clear_value(self):
        """값 입력 필드 클리어"""
        self.value_input.clear()

    def is_valid(self) -> bool:
        """입력값 유효성 검사"""
        return bool(self.get_value())
