#!/usr/bin/env python3
"""
변수 선택 위젯 - 파라미터 동적 생성 포함

변수 선택 시 해당 변수의 파라미터를 동적으로 생성하는 기능이 추가된 위젯입니다.
첨부 이미지의 1단계: 변수 선택 구조를 정확히 구현합니다.
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QComboBox, QSizePolicy, QGroupBox
)
from PyQt6.QtCore import pyqtSignal
from typing import Optional, Dict, Any, TYPE_CHECKING

from upbit_auto_trading.infrastructure.logging import create_component_logger

# 공통 컴포넌트 import
try:
    from upbit_auto_trading.ui.desktop.common.components import (
        StyledComboBox, StyledGroupBox
    )
    STYLED_COMPONENTS_AVAILABLE = True
except ImportError:
    StyledComboBox = QComboBox
    StyledGroupBox = QGroupBox
    STYLED_COMPONENTS_AVAILABLE = False

# TYPE_CHECKING for lint safety
if TYPE_CHECKING:
    from ...trigger_builder.components.core.variable_definitions import VariableDefinitions
    from ...trigger_builder.components.core.parameter_widgets import ParameterWidgetFactory

# 런타임 import 처리
VARIABLE_DEFINITIONS_AVAILABLE = False
PARAMETER_FACTORY_AVAILABLE = False

try:
    from ...trigger_builder.components.core.variable_definitions import VariableDefinitions as VarDef
    VARIABLE_DEFINITIONS_AVAILABLE = True
except ImportError:
    VarDef = None

try:
    from ...trigger_builder.components.core.parameter_widgets import ParameterWidgetFactory as ParamFactory
    PARAMETER_FACTORY_AVAILABLE = True
except ImportError:
    ParamFactory = None


class VariableSelectionWidget(QWidget):
    """변수 선택 위젯

    변수 선택 시 해당 변수의 파라미터를 동적으로 생성합니다.
    첨부 이미지의 1단계: 변수 선택 구조를 정확히 구현합니다.

    Features:
        - 카테고리별 변수 선택
        - 변수 정보 표시
        - 파라미터 동적 생성 (핵심 기능)
        - 재사용 가능 (내부변수/외부변수 모두 사용)

    Signals:
        variable_selected: 변수가 선택되었을 때 발생 (var_id, var_info)
        category_changed: 카테고리가 변경되었을 때 발생 (category)
        parameters_changed: 파라미터가 변경되었을 때 발생 (parameters)
    """

    # 시그널 정의
    variable_selected = pyqtSignal(str, dict)     # var_id, var_info
    category_changed = pyqtSignal(str)            # category
    parameters_changed = pyqtSignal(dict)         # parameters

    def __init__(self, title: str = "📊 1단계: 변수 선택", parent=None):
        """위젯 초기화

        Args:
            title: 위젯 타이틀 (내부변수/외부변수별로 구분)
            parent: 부모 위젯
        """
        super().__init__(parent)
        self.logger = create_component_logger("EnhancedVariableSelectionWidget")

        self.title = title
        self.current_variable_id = None
        self.current_parameters = {}

        # 변수 정의 시스템 초기화
        self.variable_definitions = None
        if VARIABLE_DEFINITIONS_AVAILABLE and VarDef:
            try:
                self.variable_definitions = VarDef()
                self.logger.info("VariableDefinitions 초기화 완료")
            except Exception as e:
                self.logger.error(f"VariableDefinitions 초기화 실패: {e}")

        # 파라미터 위젯 팩토리 초기화
        self.parameter_factory = None
        if PARAMETER_FACTORY_AVAILABLE and ParamFactory:
            try:
                self.parameter_factory = ParamFactory(
                    update_callback=self._on_parameter_changed
                )
                self.logger.info("ParameterWidgetFactory 초기화 완료")
            except Exception as e:
                self.logger.error(f"ParameterWidgetFactory 초기화 실패: {e}")

        # UI 초기화
        self.init_ui()
        self.load_initial_data()

    def init_ui(self):
        """UI 초기화"""
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        # 메인 그룹박스
        self.main_group = QGroupBox(self.title)
        self.main_group.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)

        self.main_layout = QVBoxLayout()
        self.main_layout.setContentsMargins(8, 8, 8, 8)
        self.main_layout.setSpacing(6)

        # 1. 카테고리 + 변수 선택 (한 줄)
        self._create_selection_row()

        # 2. 변수 정보 표시
        self._create_info_section()

        # 3. 파라미터 섹션 (동적 생성)
        self.parameter_container = QWidget()
        self.parameter_layout = QVBoxLayout()
        self.parameter_layout.setContentsMargins(0, 0, 0, 0)
        self.parameter_container.setLayout(self.parameter_layout)
        self.main_layout.addWidget(self.parameter_container)

        self.main_group.setLayout(self.main_layout)
        layout.addWidget(self.main_group)
        self.setLayout(layout)

    def _create_selection_row(self):
        """카테고리 + 변수 선택 행 생성"""
        selection_layout = QHBoxLayout()

        # 범주 선택
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

        self.main_layout.addLayout(selection_layout)

        # 시그널 연결
        self.category_combo.currentTextChanged.connect(self._on_category_changed)
        self.variable_combo.currentTextChanged.connect(self._on_variable_changed)

    def _create_info_section(self):
        """변수 정보 표시 섹션"""
        self.variable_info_label = QLabel("변수를 선택하면 정보가 표시됩니다.")
        self.variable_info_label.setWordWrap(True)
        self.variable_info_label.setStyleSheet("color: #666; font-size: 11px; margin: 5px 0;")
        self.main_layout.addWidget(self.variable_info_label)

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
        self._create_parameter_widgets()

        current_var_id = self.variable_combo.currentData()
        if current_var_id and self.variable_definitions:
            try:
                variables = self.variable_definitions._load_variables_from_db()
                var_info = variables.get(current_var_id, {})
                self.current_variable_id = current_var_id
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
                    self._create_parameter_widgets()
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

    def _create_parameter_widgets(self):
        """선택된 변수의 파라미터 위젯 동적 생성"""
        if not self.parameter_factory or not self.variable_definitions:
            return

        try:
            # 기존 파라미터 위젯 제거
            self._clear_parameter_widgets()

            current_var_id = self.variable_combo.currentData()
            if not current_var_id:
                return

            # 변수의 파라미터 정보 로드
            parameters = self.variable_definitions.get_variable_parameters(current_var_id)

            if parameters:
                # 파라미터 위젯 생성
                param_widgets = self.parameter_factory.create_parameter_widgets(
                    current_var_id, parameters, self.parameter_layout
                )

                # 파라미터 값 추출
                self.current_parameters = self._extract_parameter_values(param_widgets)

                self.logger.info(f"변수 '{current_var_id}'의 {len(parameters)}개 파라미터 위젯 생성됨")
            else:
                self.logger.debug(f"변수 '{current_var_id}'에 파라미터 없음")

        except Exception as e:
            self.logger.error(f"파라미터 위젯 생성 실패: {e}")

    def _clear_parameter_widgets(self):
        """기존 파라미터 위젯들 제거"""
        while self.parameter_layout.count():
            child = self.parameter_layout.takeAt(0)
            if child and hasattr(child, 'widget') and child.widget():
                child.widget().deleteLater()

    def _extract_parameter_values(self, param_widgets: Dict) -> Dict[str, Any]:
        """파라미터 위젯에서 값 추출"""
        values = {}
        for param_name, widget in param_widgets.items():
            try:
                if hasattr(widget, 'value'):
                    values[param_name] = widget.value()
                elif hasattr(widget, 'text'):
                    values[param_name] = widget.text()
                elif hasattr(widget, 'currentText'):
                    values[param_name] = widget.currentText()
            except Exception as e:
                self.logger.error(f"파라미터 '{param_name}' 값 추출 실패: {e}")
        return values

    def _on_parameter_changed(self):
        """파라미터 변경 콜백"""
        # 현재 파라미터 값 업데이트
        if self.parameter_factory and self.current_variable_id:
            param_widgets = self.parameter_factory.widgets.get(self.current_variable_id, {})
            self.current_parameters = self._extract_parameter_values(param_widgets)
            self.parameters_changed.emit(self.current_parameters)

    # === 공개 API ===

    def get_selected_variable(self) -> Optional[str]:
        """현재 선택된 변수 ID 반환"""
        return self.variable_combo.currentData()

    def get_selected_category(self) -> Optional[str]:
        """현재 선택된 카테고리 반환"""
        return self.category_combo.currentData()

    def get_variable_display_text(self) -> str:
        """현재 선택된 변수의 표시 텍스트 반환"""
        return self.variable_combo.currentText()

    def get_current_parameters(self) -> Dict[str, Any]:
        """현재 파라미터 값들 반환"""
        return self.current_parameters.copy()

    def set_selected_variable(self, var_id: str):
        """특정 변수 선택 (편집 모드용)"""
        for i in range(self.variable_combo.count()):
            if self.variable_combo.itemData(i) == var_id:
                self.variable_combo.setCurrentIndex(i)
                break

    def set_title(self, title: str):
        """위젯 타이틀 변경 (재사용시 구분용)"""
        self.title = title
        self.main_group.setTitle(title)

    def is_external_variable_mode(self) -> bool:
        """외부 변수 모드 여부 확인"""
        return "외부" in self.title or "3단계" in self.title
