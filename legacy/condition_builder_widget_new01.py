"""
컨디션 빌더 위젯 - 4개 전용 위젯의 조합 컨테이너
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGroupBox, QPushButton,
    QLabel, QComboBox, QLineEdit
)
from PyQt6.QtCore import pyqtSignal

from upbit_auto_trading.infrastructure.logging import create_component_logger
from upbit_auto_trading.application.dto.trigger_builder.trading_variable_dto import (
    TradingVariableListDTO,
    TradingVariableDetailDTO
)

# 전용 위젯들 임포트
from .variable_selector_widget import VariableSelectorWidget
from .parameter_input_widget import ParameterInputWidget
from .condition_preview_widget import ConditionPreviewWidget


class ConditionBuilderWidget(QWidget):
    """컨디션 빌더 위젯 - 4개 전용 위젯의 조합 컨테이너

    구성 요소:
    1. VariableSelectorWidget - 변수 선택 (범주/변수/헬프/검색)
    2. ParameterInputWidget - 파라미터 설정
    3. ConditionSetupArea - 조건 설정 (연산자, 비교값) - 내장
    4. ExternalVariableArea - 외부 변수 선택 - 내장
    5. ConditionPreviewWidget - 조건 미리보기
    """

    # 시그널 정의
    variable_selected = pyqtSignal(str)  # 변수 선택
    condition_created = pyqtSignal(dict)  # 조건 생성
    condition_preview_requested = pyqtSignal(dict)  # 미리보기 요청

    def __init__(self, parent=None):
        super().__init__(parent)
        self._logger = create_component_logger("ConditionBuilderWidget")
        self._init_ui()
        self._connect_signals()

    def _init_ui(self):
        """UI 초기화 - 4개 전용 위젯 조합"""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(5, 5, 5, 5)
        main_layout.setSpacing(8)

        # 1. 변수 선택기 (검색 포함)
        self.variable_selector = VariableSelectorWidget()
        main_layout.addWidget(self.variable_selector)

        # 2. 파라미터 입력
        self.parameter_input = ParameterInputWidget()
        main_layout.addWidget(self.parameter_input)

        # 3. 조건 설정 영역 (내장)
        self._create_condition_setup_area(main_layout)

        # 4. 외부 변수 선택 영역 (내장)
        self._create_external_variable_area(main_layout)

        # 5. 조건 미리보기
        self.condition_preview = ConditionPreviewWidget()
        main_layout.addWidget(self.condition_preview)

        self._logger.info("컨디션 빌더 UI 초기화 완료 - 4개 위젯 조합")

    def _create_condition_setup_area(self, parent_layout):
        """조건 설정 영역 - 간단한 내장 구현"""
        group = QGroupBox("⚙️ 조건 설정")
        layout = QVBoxLayout(group)
        layout.setContentsMargins(8, 10, 8, 8)

        # 연산자 선택
        op_layout = QHBoxLayout()
        op_layout.addWidget(QLabel("연산자:"))
        self.operator_combo = QComboBox()
        self.operator_combo.addItems([">", ">=", "<", "<=", "==", "!="])
        op_layout.addWidget(self.operator_combo)
        op_layout.addStretch()
        layout.addLayout(op_layout)

        # 비교값 타입
        value_type_layout = QHBoxLayout()
        value_type_layout.addWidget(QLabel("비교값:"))
        self.value_type_combo = QComboBox()
        self.value_type_combo.addItems(["직접 입력", "외부 변수"])
        value_type_layout.addWidget(self.value_type_combo)
        value_type_layout.addStretch()
        layout.addLayout(value_type_layout)

        # 비교값 입력
        self.value_input = QLineEdit()
        self.value_input.setPlaceholderText("비교값을 입력하세요")
        layout.addWidget(self.value_input)

        parent_layout.addWidget(group)

    def _create_external_variable_area(self, parent_layout):
        """외부 변수 선택 영역 - 간단한 내장 구현"""
        self.external_group = QGroupBox("🔗 외부 변수")
        self.external_group.setEnabled(False)  # 기본적으로 비활성화
        layout = QVBoxLayout(self.external_group)
        layout.setContentsMargins(8, 10, 8, 8)

        # 외부 변수 범주
        ext_cat_layout = QHBoxLayout()
        ext_cat_layout.addWidget(QLabel("범주:"))
        self.external_category_combo = QComboBox()
        self.external_category_combo.addItems(["전체", "추세", "모멘텀", "변동성", "거래량", "가격"])
        ext_cat_layout.addWidget(self.external_category_combo)
        ext_cat_layout.addStretch()
        layout.addLayout(ext_cat_layout)

        # 외부 변수 선택
        ext_var_layout = QHBoxLayout()
        ext_var_layout.addWidget(QLabel("변수:"))
        self.external_variable_combo = QComboBox()
        ext_var_layout.addWidget(self.external_variable_combo)
        ext_var_layout.addStretch()
        layout.addLayout(ext_var_layout)

        parent_layout.addWidget(self.external_group)

    def _connect_signals(self):
        """시그널 연결 - 하위 위젯들의 시그널을 상위로 연결"""
        # 변수 선택기 시그널 연결
        self.variable_selector.variable_selected.connect(self.variable_selected.emit)
        self.variable_selector.search_requested.connect(self._on_search_requested)

        # 파라미터 입력 시그널 연결 (있는 경우)
        if hasattr(self.parameter_input, 'parameters_changed'):
            self.parameter_input.parameters_changed.connect(self._on_parameters_changed)

        # 조건 설정 시그널 연결
        self.value_type_combo.currentTextChanged.connect(self._on_value_type_changed)

        self._logger.info("컨디션 빌더 시그널 연결 완료")

    def _on_search_requested(self, search_term: str):
        """검색 요청 처리"""
        self._logger.info(f"검색 요청: {search_term}")
        # TODO: 검색 로직 구현

    def _on_parameters_changed(self, parameters: dict):
        """파라미터 변경 처리"""
        self._logger.info(f"파라미터 변경: {parameters}")
        # TODO: 파라미터 변경 로직 구현

    def _on_value_type_changed(self, value_type: str):
        """비교값 타입 변경 처리"""
        self._logger.info(f"비교값 타입 변경: {value_type}")
        # 외부 변수 선택 시 외부 변수 영역 활성화
        self.external_group.setEnabled(value_type == "외부 변수")

    # DTO 인터페이스 메서드들
    def load_variables(self, variables_dto: TradingVariableListDTO) -> None:
        """변수 목록 로드"""
        self.variable_selector.load_variables(variables_dto)
        self._logger.info("변수 목록 로드 완료")

    def show_variable_details(self, details_dto: TradingVariableDetailDTO) -> None:
        """변수 상세 정보를 파라미터 영역에 표시"""
        self.parameter_input.show_variable_details(details_dto)
        self._logger.info(f"변수 상세 정보 표시: {details_dto.variable_id or details_dto.display_name_ko}")

    def update_compatibility_status(self, is_compatible: bool, message: str) -> None:
        """호환성 검증 결과 표시"""
        # TODO: 호환성 상태 표시 구현
        self._logger.info(f"호환성 상태 업데이트: {is_compatible} - {message}")

    def get_current_condition(self) -> dict:
        """현재 설정된 조건 반환"""
        return {
            "variable": self.variable_selector.get_selected_variable() if hasattr(self.variable_selector, 'get_selected_variable') else "",
            "operator": self.operator_combo.currentText(),
            "value_type": self.value_type_combo.currentText(),
            "value": self.value_input.text(),
            "external_variable": self.external_variable_combo.currentText() if self.external_group.isEnabled() else None
        }

    def reset_condition(self) -> None:
        """조건 설정 초기화"""
        if hasattr(self.variable_selector, 'reset'):
            self.variable_selector.reset()
        if hasattr(self.parameter_input, 'reset'):
            self.parameter_input.reset()
        self.value_input.clear()
        self.external_group.setEnabled(False)
        self._logger.info("조건 설정 초기화 완료")
