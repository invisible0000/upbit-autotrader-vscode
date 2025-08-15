"""
컨디션 빌더 위젯 - IConditionBuilderView 구현체 (MVP View)
실제 DB와 연동되는 정상적인 컨디션 빌더
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGroupBox, QPushButton,
    QLabel, QComboBox, QLineEdit, QProgressBar
)
from PyQt6.QtCore import pyqtSignal
from PyQt6.QtWidgets import QMessageBox
from typing import Optional

from upbit_auto_trading.infrastructure.logging import create_component_logger
from upbit_auto_trading.application.dto.trigger_builder.trading_variable_dto import (
    TradingVariableListDTO,
    TradingVariableDetailDTO
)

# 하위 위젯들 임포트
from .parameter_input_widget import ParameterInputWidget
from .condition_preview_widget import ConditionPreviewWidget


class ConditionBuilderWidget(QWidget):
    """컨디션 빌더 위젯 - DB 연동 가능한 MVP View 구현체

    IConditionBuilderView 인터페이스를 컴포지션으로 구현하여 메타클래스 충돌 방지
    """

    # 시그널 정의
    variable_selected = pyqtSignal(str)  # 변수 선택
    search_requested = pyqtSignal(str)   # 검색 요청
    category_changed = pyqtSignal(str)   # 카테고리 변경
    condition_created = pyqtSignal(dict)  # 조건 생성
    condition_preview_requested = pyqtSignal(dict)  # 미리보기 요청

    def __init__(self, parent=None):
        super().__init__(parent)
        self._logger = create_component_logger("ConditionBuilderWidget")
        self._current_variables_dto: Optional[TradingVariableListDTO] = None
        self._init_ui()
        self._connect_signals()

    def _init_ui(self):
        """UI 초기화 - 4개 영역 구성"""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(5, 5, 5, 5)
        main_layout.setSpacing(8)

        # 1. 변수 선택 + 파라미터 설정 통합 영역
        self._create_variable_selection_area(main_layout)

        # 2. 조건 설정 영역
        self._create_condition_setup_area(main_layout)

        # 3. 외부 변수 선택 + 파라미터 설정 영역
        self._create_external_variable_area(main_layout)

        # 4. 조건 미리보기 영역
        self._create_condition_preview_area(main_layout)

        # 5. 로딩 상태 표시
        self._create_loading_indicator(main_layout)

        self._logger.info("컨디션 빌더 UI 초기화 완료")

    def _create_variable_selection_area(self, parent_layout):
        """변수 선택 + 파라미터 설정 통합 영역"""
        group = QGroupBox("📊 변수 선택")
        layout = QVBoxLayout(group)
        layout.setContentsMargins(8, 10, 8, 8)

        # 변수 선택 영역
        var_layout = QVBoxLayout()

        # 범주, 변수, 헬프 버튼을 한 줄에 배치
        main_row = QHBoxLayout()

        # 범주
        main_row.addWidget(QLabel("범주:"))
        self.category_combo = QComboBox()
        self.category_combo.addItems(["전체", "추세", "모멘텀", "변동성", "거래량", "가격"])
        self.category_combo.setMinimumWidth(80)
        main_row.addWidget(self.category_combo)

        main_row.addSpacing(15)  # 간격

        # 변수
        main_row.addWidget(QLabel("변수:"))
        self.variable_combo = QComboBox()
        self.variable_combo.setMinimumWidth(200)
        main_row.addWidget(self.variable_combo)

        # 헬프 버튼
        self.help_button = QPushButton("?")
        self.help_button.setFixedSize(24, 24)
        main_row.addWidget(self.help_button)

        main_row.addStretch()  # 나머지 공간
        var_layout.addLayout(main_row)

        # 검색 영역
        search_layout = QHBoxLayout()
        search_layout.addWidget(QLabel("검색:"))
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("변수 이름으로 검색...")
        self.search_input.setMinimumWidth(200)
        search_layout.addWidget(self.search_input)

        self.search_button = QPushButton("🔍 검색")
        self.search_button.setFixedHeight(self.search_input.sizeHint().height())
        search_layout.addWidget(self.search_button)
        search_layout.addStretch()
        var_layout.addLayout(search_layout)

        layout.addLayout(var_layout)

        # 파라미터 입력 임베딩
        self.parameter_input = ParameterInputWidget()
        layout.addWidget(self.parameter_input)

        parent_layout.addWidget(group)

    def _create_condition_setup_area(self, parent_layout):
        """조건 설정 영역 - 1열 배치"""
        group = QGroupBox("⚙️ 조건 설정")
        layout = QVBoxLayout(group)
        layout.setContentsMargins(8, 10, 8, 8)

        # 연산자 선택
        op_layout = QHBoxLayout()
        op_layout.addWidget(QLabel("연산자:"))
        self.operator_combo = QComboBox()
        self.operator_combo.addItems([">", ">=", "<", "<=", "==", "!=", "상향 돌파", "하향 돌파"])
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
        value_input_layout = QHBoxLayout()
        value_input_layout.addWidget(QLabel("입력값:"))
        self.value_input = QLineEdit()
        self.value_input.setPlaceholderText("비교값을 입력하세요")
        value_input_layout.addWidget(self.value_input)
        layout.addLayout(value_input_layout)

        parent_layout.addWidget(group)

    def _create_external_variable_area(self, parent_layout):
        """외부 변수 선택 + 파라미터 설정 영역"""
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

        # 외부 변수용 파라미터 설정
        self.external_parameter_input = ParameterInputWidget()
        layout.addWidget(self.external_parameter_input)

        parent_layout.addWidget(self.external_group)

    def _create_condition_preview_area(self, parent_layout):
        """조건 미리보기 영역"""
        self.condition_preview = ConditionPreviewWidget()
        parent_layout.addWidget(self.condition_preview)

    def _create_loading_indicator(self, parent_layout):
        """로딩 상태 표시"""
        self.loading_bar = QProgressBar()
        self.loading_bar.setVisible(False)
        self.loading_bar.setRange(0, 0)  # 무한 로딩
        parent_layout.addWidget(self.loading_bar)

    def _connect_signals(self):
        """시그널 연결"""
        # 기본 UI 시그널들
        self.category_combo.currentTextChanged.connect(self._on_category_changed)
        self.variable_combo.currentTextChanged.connect(self._on_variable_changed)
        self.help_button.clicked.connect(self._on_help_clicked)
        self.search_button.clicked.connect(self._on_search_clicked)
        self.search_input.returnPressed.connect(self._on_search_clicked)
        self.value_type_combo.currentTextChanged.connect(self._on_value_type_changed)

        # 조건 설정 관련 시그널들
        self.operator_combo.currentTextChanged.connect(self._on_condition_changed)
        self.value_input.textChanged.connect(self._on_condition_changed)
        self.external_variable_combo.currentTextChanged.connect(self._on_condition_changed)

        # 파라미터 입력 위젯 시그널들
        self.parameter_input.parameters_changed.connect(self._on_condition_changed)
        self.external_parameter_input.parameters_changed.connect(self._on_condition_changed)

        self._logger.info("컨디션 빌더 시그널 연결 완료")

    # =============================================================================
    # IConditionBuilderView 인터페이스 구현
    # =============================================================================

    def display_variables(self, variables_dto: TradingVariableListDTO) -> None:
        """변수 목록을 UI에 표시"""
        try:
            self._current_variables_dto = variables_dto

            # 변수 콤보박스 업데이트
            self.variable_combo.clear()
            self.external_variable_combo.clear()

            if variables_dto.success and variables_dto.grouped_variables:
                # 모든 변수를 우선 추가 (전체 카테고리 선택 상태)
                for category, variables in variables_dto.grouped_variables.items():
                    for var in variables:
                        display_name = var.get('display_name_ko', var.get('variable_id', ''))
                        variable_id = var.get('variable_id', '')

                        self.variable_combo.addItem(display_name, variable_id)
                        self.external_variable_combo.addItem(display_name, variable_id)

                # 현재 선택된 카테고리에 따라 필터링 적용
                current_category = self.category_combo.currentText()
                if current_category != "전체":
                    self._filter_variables_by_category(current_category)

            self._logger.info(f"변수 목록 표시 완료: {variables_dto.total_count}개")

        except Exception as e:
            self._logger.error(f"변수 목록 표시 중 오류: {e}")

    def show_variable_details(self, details_dto: TradingVariableDetailDTO) -> None:
        """선택된 변수의 상세 정보 표시"""
        try:
            if details_dto.success:
                # 파라미터 입력 위젯에 상세 정보 전달
                self.parameter_input.show_variable_details(details_dto)
                self._logger.info(f"변수 상세 정보 표시: {details_dto.variable_id}")
            else:
                self._logger.error(f"변수 상세 정보 오류: {details_dto.error_message}")

        except Exception as e:
            self._logger.error(f"변수 상세 정보 표시 중 오류: {e}")

    def update_compatibility_status(self, is_compatible: bool, message: str) -> None:
        """변수 호환성 검증 결과 표시"""
        try:
            # TODO: 호환성 상태 UI 업데이트 구현
            self._logger.info(f"호환성 상태: {is_compatible} - {message}")

        except Exception as e:
            self._logger.error(f"호환성 상태 업데이트 중 오류: {e}")

    def get_current_condition(self) -> dict:
        """현재 설정된 조건 반환"""
        try:
            current_var_text = self.variable_combo.currentText()
            current_var_id = self.variable_combo.currentData()

            return {
                "variable_id": current_var_id,
                "variable_name": current_var_text,
                "operator": self.operator_combo.currentText(),
                "value_type": self.value_type_combo.currentText(),
                "value": self.value_input.text(),
                "external_variable_id": (
                    self.external_variable_combo.currentData()
                    if self.external_group.isEnabled() else None
                ),
                "external_variable_name": (
                    self.external_variable_combo.currentText()
                    if self.external_group.isEnabled() else None
                )
            }

        except Exception as e:
            self._logger.error(f"조건 정보 수집 중 오류: {e}")
            return {}

    def reset_condition(self) -> None:
        """조건 설정 초기화"""
        try:
            self.variable_combo.setCurrentIndex(0)
            self.operator_combo.setCurrentIndex(0)
            self.value_type_combo.setCurrentIndex(0)
            self.value_input.clear()
            self.external_group.setEnabled(False)
            self.search_input.clear()

            # 하위 위젯들 초기화
            if hasattr(self.parameter_input, 'clear_parameters'):
                self.parameter_input.clear_parameters()
            if hasattr(self.external_parameter_input, 'clear_parameters'):
                self.external_parameter_input.clear_parameters()

            self._logger.info("조건 설정 초기화 완료")

        except Exception as e:
            self._logger.error(f"조건 초기화 중 오류: {e}")

    def set_loading_state(self, is_loading: bool) -> None:
        """로딩 상태 표시/숨김"""
        self.loading_bar.setVisible(is_loading)
        self.setEnabled(not is_loading)

    # =============================================================================
    # 내부 이벤트 핸들러들
    # =============================================================================

    def _on_category_changed(self, category: str):
        """카테고리 변경 처리"""
        self._logger.info(f"카테고리 변경: {category}")
        self._filter_variables_by_category(category)
        self.category_changed.emit(category)

    def _filter_variables_by_category(self, category: str) -> None:
        """카테고리별 변수 필터링"""
        if not hasattr(self, '_current_variables_dto') or not self._current_variables_dto:
            return

        # 카테고리 한글->영문 매핑
        category_mapping = {
            "전체": None,
            "추세": "trend",
            "모멘텀": "momentum",
            "변동성": "volatility",
            "거래량": "volume",
            "가격": "price"
        }

        selected_category = category_mapping.get(category)

        # 변수 콤보박스 클리어
        self.variable_combo.clear()

        # 변수 필터링 및 추가
        if self._current_variables_dto.success and self._current_variables_dto.grouped_variables:
            for cat, variables in self._current_variables_dto.grouped_variables.items():
                # 전체 선택이거나 선택된 카테고리와 일치하는 경우
                if selected_category is None or cat == selected_category:
                    for var in variables:
                        display_name = var.get('display_name_ko', var.get('variable_id', ''))
                        variable_id = var.get('variable_id', '')
                        self.variable_combo.addItem(display_name, variable_id)

        self._logger.info(f"카테고리 '{category}'로 필터링 완료: {self.variable_combo.count()}개 변수")

    def _on_variable_changed(self, variable_name: str):
        """변수 변경 처리"""
        variable_id = self.variable_combo.currentData()
        if variable_id:
            self._logger.info(f"변수 변경: {variable_name} (ID: {variable_id})")
            self.variable_selected.emit(variable_id)

    def _on_help_clicked(self):
        """헬프 버튼 클릭 처리"""
        current_variable = self.variable_combo.currentText()
        if current_variable:
            QMessageBox.information(
                self,
                "변수 도움말",
                f"선택된 변수: {current_variable}\n\n"
                "이 변수에 대한 상세 도움말이 표시됩니다.\n"
                "(실제 도움말 시스템은 구현 예정)"
            )
        else:
            QMessageBox.warning(self, "알림", "먼저 변수를 선택해주세요.")

    def _on_search_clicked(self):
        """검색 버튼 클릭 처리"""
        search_term = self.search_input.text().strip()
        self._logger.info(f"검색 요청: {search_term}")
        self.search_requested.emit(search_term)

    def _on_value_type_changed(self, value_type: str):
        """비교값 타입 변경 처리"""
        self._logger.info(f"비교값 타입 변경: {value_type}")
        # 외부 변수 선택 시 외부 변수 영역 활성화
        self.external_group.setEnabled(value_type == "외부 변수")
        # 조건 미리보기 업데이트
        self._update_condition_preview()

    def _on_condition_changed(self):
        """조건 설정 변경 시 미리보기 업데이트"""
        self._update_condition_preview()

    def _update_condition_preview(self):
        """조건 미리보기 업데이트"""
        try:
            condition_data = self.get_current_condition()

            # 기본 정보 확인
            if not condition_data.get("variable_name") or not condition_data.get("operator"):
                self.condition_preview.update_preview("조건을 완성해주세요.")
                return

            # 미리보기 텍스트 생성
            preview_text = self._generate_preview_text(condition_data)
            self.condition_preview.update_preview(preview_text)

        except Exception as e:
            self._logger.error(f"조건 미리보기 업데이트 중 오류: {e}")
            self.condition_preview.update_preview("미리보기 생성 중 오류가 발생했습니다.")

    def _generate_preview_text(self, condition_data: dict) -> str:
        """조건 데이터로부터 미리보기 텍스트 생성"""
        try:
            variable_name = condition_data.get("variable_name", "")
            operator = condition_data.get("operator", "")
            value_type = condition_data.get("value_type", "직접 입력")
            value = condition_data.get("value", "")
            external_variable_name = condition_data.get("external_variable_name", "")

            # 파라미터 정보 추가
            main_params = self.parameter_input.get_current_parameters()
            external_params = self.external_parameter_input.get_current_parameters()

            # 기본 조건 텍스트
            if value_type == "외부 변수" and external_variable_name:
                preview = f"{variable_name} {operator} {external_variable_name}"
            else:
                preview = f"{variable_name} {operator} {value if value else '(값 없음)'}"

            # 파라미터 정보 추가
            param_parts = []
            if main_params:
                param_str = ", ".join([f"{k}={v}" for k, v in main_params.items()])
                param_parts.append(f"주변수({param_str})")

            if external_params and value_type == "외부 변수":
                param_str = ", ".join([f"{k}={v}" for k, v in external_params.items()])
                param_parts.append(f"비교변수({param_str})")

            if param_parts:
                preview += f" | {' / '.join(param_parts)}"

            return preview

        except Exception as e:
            self._logger.error(f"미리보기 텍스트 생성 중 오류: {e}")
            return "미리보기 생성 중 오류가 발생했습니다."
