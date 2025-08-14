#!/usr/bin/env python3
"""
변수 선택 위젯 - 조건 빌더 컴포넌트

카테고리별 변수 선택 및 변수 정보 표시를 담당하는 독립적인 위젯입니다.
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QComboBox, QSizePolicy
)
from PyQt6.QtCore import pyqtSignal
from typing import Optional

from upbit_auto_trading.infrastructure.logging import create_component_logger

# 공통 컴포넌트 import
try:
    from upbit_auto_trading.ui.desktop.common.components import (
        StyledComboBox, StyledGroupBox
    )
    STYLED_COMPONENTS_AVAILABLE = True
except ImportError:
    StyledComboBox = QComboBox
    StyledGroupBox = QWidget
    STYLED_COMPONENTS_AVAILABLE = False

# 변수 정의 시스템 import
try:
    from ...trigger_builder.components.core.variable_definitions import VariableDefinitions
    VARIABLE_DEFINITIONS_AVAILABLE = True
except ImportError:
    VARIABLE_DEFINITIONS_AVAILABLE = False


class VariableSelectionWidget(QWidget):
    """변수 선택 위젯

    카테고리별 변수 선택 및 변수 정보 표시를 담당합니다.
    단일 책임 원칙을 따라 변수 선택 기능만 처리합니다.

    Signals:
        variable_selected: 변수가 선택되었을 때 발생 (var_id, var_info)
        category_changed: 카테고리가 변경되었을 때 발생 (category)
    """

    # 시그널 정의
    variable_selected = pyqtSignal(str, dict)  # var_id, var_info
    category_changed = pyqtSignal(str)         # category

    def __init__(self, parent=None):
        """변수 선택 위젯 초기화"""
        super().__init__(parent)
        self.logger = create_component_logger("VariableSelectionWidget")

        # 변수 정의 시스템 초기화
        self.variable_definitions = None
        if VARIABLE_DEFINITIONS_AVAILABLE:
            try:
                self.variable_definitions = VariableDefinitions()
                self.logger.info("VariableDefinitions 초기화 완료")
            except Exception as e:
                self.logger.error(f"VariableDefinitions 초기화 실패: {e}")

        # UI 초기화
        self.init_ui()
        self.load_initial_data()

    def init_ui(self):
        """UI 초기화"""
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        # 그룹박스로 감싸기
        group = StyledGroupBox("📊 변수 선택")
        group_layout = QVBoxLayout()
        group_layout.setContentsMargins(8, 8, 8, 8)
        group_layout.setSpacing(6)

        # 카테고리 + 변수 선택 한 줄
        selection_layout = QHBoxLayout()

        # 카테고리 선택
        selection_layout.addWidget(QLabel("범주:"))

        self.category_combo = StyledComboBox()
        self.category_combo.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        self.category_combo.setFixedHeight(28)
        selection_layout.addWidget(self.category_combo)

        # 변수 선택
        selection_layout.addWidget(QLabel("변수:"))

        self.variable_combo = StyledComboBox()
        self.variable_combo.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        self.variable_combo.setFixedHeight(28)
        selection_layout.addWidget(self.variable_combo)

        group_layout.addLayout(selection_layout)

        # 변수 정보 표시 라벨
        self.variable_info_label = QLabel("변수를 선택하면 정보가 표시됩니다.")
        self.variable_info_label.setWordWrap(True)
        self.variable_info_label.setStyleSheet("color: #666; font-size: 11px; margin: 5px 0;")
        group_layout.addWidget(self.variable_info_label)

        group.setLayout(group_layout)
        layout.addWidget(group)
        self.setLayout(layout)

        # 시그널 연결
        self.category_combo.currentTextChanged.connect(self._on_category_changed)
        self.variable_combo.currentTextChanged.connect(self._on_variable_changed)

    def load_initial_data(self):
        """초기 데이터 로드"""
        if not self.variable_definitions:
            self.logger.warning("VariableDefinitions를 사용할 수 없어 기본 카테고리 사용")
            self._load_fallback_categories()
            return

        try:
            # DB에서 카테고리 로드
            category_variables = self.variable_definitions.get_category_variables()

            self.category_combo.clear()
            for category in category_variables.keys():
                icon_map = {
                    "trend": "📈", "momentum": "⚡", "volatility": "🔥",
                    "volume": "📦", "price": "💰", "indicator": "📊"
                }
                icon = icon_map.get(category, "🔹")
                self.category_combo.addItem(f"{icon} {category.title()}", category)

            self.logger.info(f"DB에서 {len(category_variables)}개 카테고리 로드 완료")

            # 첫 번째 카테고리의 변수들 로드
            if self.category_combo.count() > 0:
                self._update_variables_for_category()

        except Exception as e:
            self.logger.error(f"초기 데이터 로드 실패: {e}")
            self._load_fallback_categories()

    def _load_fallback_categories(self):
        """폴백: 기본 카테고리 로드"""
        self.category_combo.clear()
        default_categories = ["trend", "momentum", "volatility", "volume", "price"]
        for category in default_categories:
            self.category_combo.addItem(category.title(), category)

        # 기본 변수들 로드
        self.variable_combo.clear()
        self.variable_combo.addItems(["현재가", "RSI", "MACD", "거래량"])

    def _on_category_changed(self):
        """카테고리 변경 이벤트 핸들러"""
        self._update_variables_for_category()
        current_category = self.category_combo.currentData()
        if current_category:
            self.category_changed.emit(current_category)

    def _on_variable_changed(self):
        """변수 변경 이벤트 핸들러"""
        self._update_variable_info()

        current_var_id = self.variable_combo.currentData()
        if current_var_id and self.variable_definitions:
            try:
                variables = self.variable_definitions._load_variables_from_db()
                var_info = variables.get(current_var_id, {})
                self.variable_selected.emit(current_var_id, var_info)
            except Exception as e:
                self.logger.error(f"변수 정보 로드 실패: {e}")

    def _update_variables_for_category(self):
        """선택된 카테고리의 변수들 업데이트"""
        if not self.variable_definitions:
            return

        try:
            self.variable_combo.clear()

            category_variables = self.variable_definitions.get_category_variables()
            selected_category = self.category_combo.currentData()

            if not selected_category:
                # currentData()가 None인 경우 currentText()에서 추출
                current_text = self.category_combo.currentText()
                for icon in ["📈 ", "⚡ ", "🔥 ", "📦 ", "💰 ", "📊 ", "🔹 "]:
                    current_text = current_text.replace(icon, "")
                selected_category = current_text.lower()

            if selected_category in category_variables:
                for var_id, var_name in category_variables[selected_category]:
                    icon_map = {
                        "trend": "📈", "momentum": "⚡", "volatility": "🔥",
                        "volume": "📦", "price": "💰", "indicator": "📊"
                    }
                    icon = icon_map.get(selected_category, "🔹")
                    self.variable_combo.addItem(f"{icon} {var_name}", var_id)

                self.logger.debug(f"카테고리 '{selected_category}'에서 {self.variable_combo.count()}개 변수 로드됨")

                # 첫 번째 변수 자동 선택
                if self.variable_combo.count() > 0:
                    self._update_variable_info()
            else:
                self.logger.warning(f"카테고리 '{selected_category}' 없음")
                self.variable_info_label.setText("선택한 카테고리에 변수가 없습니다.")

        except Exception as e:
            self.logger.error(f"변수 업데이트 실패: {e}")
            self.variable_combo.clear()
            self.variable_combo.addItems(["현재가", "RSI", "MACD", "거래량"])

    def _update_variable_info(self):
        """선택된 변수의 정보 표시"""
        if not self.variable_definitions:
            return

        try:
            current_var_id = self.variable_combo.currentData()
            if not current_var_id and self.variable_combo.count() > 0:
                current_var_id = self.variable_combo.itemData(0)

            if current_var_id:
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

    # === 공개 API ===

    def get_selected_variable(self) -> Optional[str]:
        """현재 선택된 변수 ID 반환"""
        return self.variable_combo.currentData()

    def get_selected_category(self) -> Optional[str]:
        """현재 선택된 카테고리 반환"""
        return self.category_combo.currentData()

    def set_selected_variable(self, var_id: str):
        """특정 변수 선택 (편집 모드용)"""
        for i in range(self.variable_combo.count()):
            if self.variable_combo.itemData(i) == var_id:
                self.variable_combo.setCurrentIndex(i)
                break

    def get_variable_display_text(self) -> str:
        """현재 선택된 변수의 표시 텍스트 반환"""
        return self.variable_combo.currentText()
