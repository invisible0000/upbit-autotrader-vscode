#!/usr/bin/env python3
"""
비교 설정 위젯 - 2단계: 비교 설정

첨부 이미지의 2단계 구현: 비교값 + 연산자 + 추세방향을 하나의 박스에서 처리합니다.
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QComboBox,
    QLineEdit, QGroupBox, QSizePolicy, QButtonGroup, QRadioButton
)
from PyQt6.QtCore import pyqtSignal
from typing import Dict, Any
from decimal import Decimal

from upbit_auto_trading.infrastructure.logging import create_component_logger

# 공통 컴포넌트 import
try:
    from upbit_auto_trading.ui.desktop.common.components import (
        StyledComboBox, StyledGroupBox, StyledLineEdit
    )
    STYLED_COMPONENTS_AVAILABLE = True
except ImportError:
    StyledComboBox = QComboBox
    StyledGroupBox = QGroupBox
    StyledLineEdit = QLineEdit
    STYLED_COMPONENTS_AVAILABLE = False


class ComparisonSettingsWidget(QWidget):
    """비교 설정 위젯

    첨부 이미지의 2단계 구현:
    - 첫 번째 줄: 비교값 + 연산자 + 방식(고정값/다른변수)
    - 두 번째 줄: 추세 방향 (상승중/하락중/양방향)

    Features:
        - 비교값 입력 (숫자/소수점)
        - 연산자 선택 (>, <, >=, <=, ==, !=)
        - 비교 방식 (고정값/다른변수)
        - 추세 방향 선택 (상승중/하락중/양방향)
        - 실시간 검증

    Signals:
        comparison_value_changed: 비교값 변경 (value)
        operator_changed: 연산자 변경 (operator)
        comparison_type_changed: 비교 방식 변경 (type)
        trend_direction_changed: 추세 방향 변경 (direction)
        settings_changed: 전체 설정 변경 (settings_dict)
    """

    # 시그널 정의
    comparison_value_changed = pyqtSignal(str)    # value
    operator_changed = pyqtSignal(str)            # operator
    comparison_type_changed = pyqtSignal(str)     # type: fixed_value or other_variable
    trend_direction_changed = pyqtSignal(str)     # direction: rising, falling, both
    settings_changed = pyqtSignal(dict)           # all settings

    def __init__(self, parent=None):
        """위젯 초기화"""
        super().__init__(parent)
        self.logger = create_component_logger("ComparisonSettingsWidget")

        # 현재 설정 상태
        self.current_settings = {
            'comparison_value': '',
            'operator': '>',
            'comparison_type': 'fixed_value',
            'trend_direction': 'both'
        }

        # UI 초기화
        self.init_ui()
        self.connect_signals()

    def init_ui(self):
        """UI 초기화"""
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        # 메인 그룹박스
        self.main_group = QGroupBox("🔍 2단계: 비교 설정")
        self.main_group.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)

        self.main_layout = QVBoxLayout()
        self.main_layout.setContentsMargins(8, 8, 8, 8)
        self.main_layout.setSpacing(6)

        # 1. 비교값 + 연산자 + 방식 (첫 번째 줄)
        self._create_comparison_row()

        # 2. 추세 방향 선택 (두 번째 줄)
        self._create_trend_direction_row()

        self.main_group.setLayout(self.main_layout)
        layout.addWidget(self.main_group)
        self.setLayout(layout)

    def _create_comparison_row(self):
        """비교값 + 연산자 + 방식 행 생성"""
        comparison_layout = QHBoxLayout()

        # 비교값 입력
        comparison_layout.addWidget(QLabel("비교값:"))

        self.comparison_value_input = StyledLineEdit()
        self.comparison_value_input.setPlaceholderText("예: 30, 70, 0.5")
        self.comparison_value_input.setFixedHeight(28)
        self.comparison_value_input.setFixedWidth(120)
        comparison_layout.addWidget(self.comparison_value_input)

        # 연산자 선택
        comparison_layout.addWidget(QLabel("연산자:"))

        self.operator_combo = StyledComboBox()
        self.operator_combo.addItems([
            "> (보다 크다)",
            "< (보다 작다)",
            ">= (크거나 같다)",
            "<= (작거나 같다)",
            "== (같다)",
            "!= (같지 않다)"
        ])
        self.operator_combo.setFixedHeight(28)
        self.operator_combo.setFixedWidth(130)
        comparison_layout.addWidget(self.operator_combo)

        # 비교 방식 선택
        comparison_layout.addWidget(QLabel("방식:"))

        self.comparison_type_combo = StyledComboBox()
        self.comparison_type_combo.addItems([
            "🔢 고정값",
            "📊 다른변수"
        ])
        self.comparison_type_combo.setFixedHeight(28)
        self.comparison_type_combo.setFixedWidth(100)
        comparison_layout.addWidget(self.comparison_type_combo)

        # 여백 추가
        comparison_layout.addStretch()

        self.main_layout.addLayout(comparison_layout)

    def _create_trend_direction_row(self):
        """추세 방향 선택 행 생성"""
        trend_layout = QHBoxLayout()

        # 라벨
        trend_layout.addWidget(QLabel("추세방향:"))

        # 라디오 버튼 그룹
        self.trend_button_group = QButtonGroup()

        # 상승중
        self.rising_radio = QRadioButton("📈 상승중")
        self.rising_radio.setProperty("trend_direction", "rising")
        self.trend_button_group.addButton(self.rising_radio, 0)
        trend_layout.addWidget(self.rising_radio)

        # 하락중
        self.falling_radio = QRadioButton("📉 하락중")
        self.falling_radio.setProperty("trend_direction", "falling")
        self.trend_button_group.addButton(self.falling_radio, 1)
        trend_layout.addWidget(self.falling_radio)

        # 양방향 (기본값)
        self.both_radio = QRadioButton("↕️ 양방향")
        self.both_radio.setProperty("trend_direction", "both")
        self.both_radio.setChecked(True)  # 기본값
        self.trend_button_group.addButton(self.both_radio, 2)
        trend_layout.addWidget(self.both_radio)

        # 여백 추가
        trend_layout.addStretch()

        self.main_layout.addLayout(trend_layout)

    def connect_signals(self):
        """시그널 연결"""
        # 비교값 변경
        self.comparison_value_input.textChanged.connect(self._on_comparison_value_changed)

        # 연산자 변경
        self.operator_combo.currentTextChanged.connect(self._on_operator_changed)

        # 비교 방식 변경
        self.comparison_type_combo.currentTextChanged.connect(self._on_comparison_type_changed)

        # 추세 방향 변경
        self.trend_button_group.buttonClicked.connect(self._on_trend_direction_changed)

    def _on_comparison_value_changed(self):
        """비교값 변경 이벤트 핸들러"""
        value = self.comparison_value_input.text().strip()

        # 기본 숫자 검증
        if value and not self._is_valid_number(value):
            self.comparison_value_input.setStyleSheet("border: 2px solid red;")
            self.logger.warning(f"잘못된 비교값 형식: {value}")
        else:
            self.comparison_value_input.setStyleSheet("")

        self.current_settings['comparison_value'] = value
        self.comparison_value_changed.emit(value)
        self._emit_settings_changed()

    def _on_operator_changed(self):
        """연산자 변경 이벤트 핸들러"""
        operator_text = self.operator_combo.currentText()
        # 연산자 추출 (예: "> (보다 크다)" → ">")
        operator = operator_text.split()[0]

        self.current_settings['operator'] = operator
        self.operator_changed.emit(operator)
        self._emit_settings_changed()

    def _on_comparison_type_changed(self):
        """비교 방식 변경 이벤트 핸들러"""
        type_text = self.comparison_type_combo.currentText()

        # 타입 매핑
        if "고정값" in type_text:
            comparison_type = "fixed_value"
            self.comparison_value_input.setPlaceholderText("예: 30, 70, 0.5")
        else:  # 다른변수
            comparison_type = "other_variable"
            self.comparison_value_input.setPlaceholderText("외부 변수 선택됨")
            # 다른변수 선택시 입력 비활성화 (외부변수 위젯에서 처리)
            self.comparison_value_input.setEnabled(False)

        self.current_settings['comparison_type'] = comparison_type
        self.comparison_type_changed.emit(comparison_type)
        self._emit_settings_changed()

    def _on_trend_direction_changed(self, button):
        """추세 방향 변경 이벤트 핸들러"""
        direction = button.property("trend_direction")

        self.current_settings['trend_direction'] = direction
        self.trend_direction_changed.emit(direction)
        self._emit_settings_changed()

    def _emit_settings_changed(self):
        """전체 설정 변경 시그널 발생"""
        self.settings_changed.emit(self.current_settings.copy())

    def _is_valid_number(self, value: str) -> bool:
        """숫자 형식 검증"""
        try:
            # 정수 또는 소수점 검증
            float(value)
            return True
        except ValueError:
            try:
                # Decimal로도 검증
                Decimal(value)
                return True
            except Exception:
                return False

    # === 공개 API ===

    def get_comparison_value(self) -> str:
        """현재 비교값 반환"""
        return self.comparison_value_input.text().strip()

    def get_operator(self) -> str:
        """현재 연산자 반환"""
        operator_text = self.operator_combo.currentText()
        return operator_text.split()[0]

    def get_comparison_type(self) -> str:
        """현재 비교 방식 반환"""
        return self.current_settings['comparison_type']

    def get_trend_direction(self) -> str:
        """현재 추세 방향 반환"""
        return self.current_settings['trend_direction']

    def get_all_settings(self) -> Dict[str, Any]:
        """모든 설정 반환"""
        return self.current_settings.copy()

    def set_comparison_value(self, value: str):
        """비교값 설정 (편집 모드용)"""
        self.comparison_value_input.setText(value)

    def set_operator(self, operator: str):
        """연산자 설정 (편집 모드용)"""
        operator_map = {
            ">": "> (보다 크다)",
            "<": "< (보다 작다)",
            ">=": ">= (크거나 같다)",
            "<=": "<= (작거나 같다)",
            "==": "== (같다)",
            "!=": "!= (같지 않다)"
        }
        operator_text = operator_map.get(operator, "> (보다 크다)")
        index = self.operator_combo.findText(operator_text)
        if index >= 0:
            self.operator_combo.setCurrentIndex(index)

    def set_comparison_type(self, comparison_type: str):
        """비교 방식 설정 (편집 모드용)"""
        if comparison_type == "fixed_value":
            self.comparison_type_combo.setCurrentIndex(0)
            self.comparison_value_input.setEnabled(True)
        else:  # other_variable
            self.comparison_type_combo.setCurrentIndex(1)
            self.comparison_value_input.setEnabled(False)

    def set_trend_direction(self, direction: str):
        """추세 방향 설정 (편집 모드용)"""
        direction_map = {
            "rising": self.rising_radio,
            "falling": self.falling_radio,
            "both": self.both_radio
        }
        radio_button = direction_map.get(direction, self.both_radio)
        radio_button.setChecked(True)

    def enable_other_variable_mode(self):
        """다른변수 모드 활성화 (외부에서 호출)"""
        self.comparison_type_combo.setCurrentIndex(1)
        self.comparison_value_input.setEnabled(False)
        self.comparison_value_input.setText("")
        self.comparison_value_input.setPlaceholderText("외부 변수가 선택됨")

    def disable_other_variable_mode(self):
        """다른변수 모드 비활성화 (외부에서 호출)"""
        self.comparison_type_combo.setCurrentIndex(0)
        self.comparison_value_input.setEnabled(True)
        self.comparison_value_input.setPlaceholderText("예: 30, 70, 0.5")

    def is_other_variable_mode(self) -> bool:
        """다른변수 모드 여부 확인"""
        return self.current_settings['comparison_type'] == 'other_variable'

    def validate_settings(self) -> tuple[bool, str]:
        """설정 검증"""
        # 고정값 모드에서 값 검증
        if self.current_settings['comparison_type'] == 'fixed_value':
            value = self.get_comparison_value()
            if not value:
                return False, "비교값을 입력해주세요"
            if not self._is_valid_number(value):
                return False, "올바른 숫자를 입력해주세요"

        # 다른변수 모드에서는 외부 검증 필요
        return True, "설정이 유효합니다"
