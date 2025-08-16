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
    3. ConditionSetupWidget - 조건 설정 (연산자, 비교값)
    4. ExternalVariableWidget - 외부 변수 선택
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

        # 3. 조건 설정 (기존 로직 유지)
        self._create_condition_setup_area(main_layout)

        # 4. 외부 변수 선택 (기존 로직 유지)
        self._create_external_variable_area(main_layout)

        # 5. 조건 미리보기
        self.condition_preview = ConditionPreviewWidget()
        main_layout.addWidget(self.condition_preview)

        self._logger.info("컨디션 빌더 UI 초기화 완료 - 4개 위젯 조합")

    def _create_base_variable_area(self, parent_layout):
        """1. 기본 변수 선택 영역 - 범주/변수/헬프 한 줄 배치"""
        group = QGroupBox("📊 변수 선택")
        layout = QVBoxLayout(group)
        layout.setContentsMargins(8, 10, 8, 8)

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
        layout.addLayout(main_row)

        # 검색 기능 추가
        search_layout = QHBoxLayout()
        search_layout.addWidget(QLabel("검색:"))
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("변수명 또는 설명 검색...")
        search_layout.addWidget(self.search_input)

        # 검색 버튼
        self.search_button = QPushButton("🔍 검색")
        self.search_button.setMaximumHeight(self.search_input.sizeHint().height())
        search_layout.addWidget(self.search_button)
        layout.addLayout(search_layout)

        # 파라미터 설정 영역 추가
        param_label = QLabel("⚙️ 파라미터 설정")
        layout.addWidget(param_label)

        # 스크롤 가능한 파라미터 영역
        self.parameter_scroll = QScrollArea()
        self.parameter_scroll.setWidgetResizable(True)
        self.parameter_scroll.setMaximumHeight(150)

        self.parameter_container = QWidget()
        self.parameter_layout = QVBoxLayout(self.parameter_container)
        self.parameter_layout.addWidget(QLabel("변수를 선택하면 파라미터 설정이 표시됩니다."))

        self.parameter_scroll.setWidget(self.parameter_container)
        layout.addWidget(self.parameter_scroll)

        parent_layout.addWidget(group)

    def _create_condition_setup_area(self, parent_layout):
        """2. 조건 설정 영역"""
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
        """3. 외부 변수 선택 영역 - 조건 설정에서 '외부 변수' 선택 시 활성화"""
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

    def _create_condition_preview_area(self, parent_layout):
        """4. 조건 미리보기 영역 - 순수 미리보기만"""
        group = QGroupBox("👁️ 조건 미리보기")
        layout = QVBoxLayout(group)
        layout.setContentsMargins(8, 10, 8, 8)

        self.preview_label = QLabel("조건을 설정하면 미리보기가 표시됩니다.")
        self.preview_label.setWordWrap(True)
        layout.addWidget(self.preview_label)

        parent_layout.addWidget(group)
        self.parameter_layout.addWidget(self.parameter_info_label)

        self.parameter_scroll.setWidget(self.parameter_container)
        layout.addWidget(self.parameter_scroll)

        parent_layout.addWidget(group)

    def _create_condition_setup_area(self, parent_layout):
        """조건 설정 영역 생성"""
        group = QGroupBox("🎯 조건 설정")
        layout = QVBoxLayout(group)
        layout.setContentsMargins(5, 8, 5, 5)
        layout.setSpacing(3)

        # 연산자 선택
        operator_layout = QHBoxLayout()
        operator_layout.addWidget(QLabel("연산자:"))

        self.operator_combo = QComboBox()
        self.operator_combo.addItems([
            "> (크다)", "< (작다)", ">= (크거나 같다)",
            "<= (작거나 같다)", "== (같다)",
            "crossover (상향 돌파)", "crossunder (하향 돌파)"
        ])
        operator_layout.addWidget(self.operator_combo)
        layout.addLayout(operator_layout)

        # 비교값 설정
        value_layout = QHBoxLayout()
        value_layout.addWidget(QLabel("비교값:"))

        # 비교값 타입 선택
        self.value_type_combo = QComboBox()
        self.value_type_combo.addItems(["상수값", "다른 변수"])
        value_layout.addWidget(self.value_type_combo)

        # 값 입력
        self.value_input = QLineEdit()
        self.value_input.setPlaceholderText("비교할 값을 입력하세요...")
        value_layout.addWidget(self.value_input)
        layout.addLayout(value_layout)

        parent_layout.addWidget(group)

    def _create_preview_area(self, parent_layout):
        """미리보기 영역 생성"""
        group = QGroupBox("👁️ 조건 미리보기")
        layout = QVBoxLayout(group)
        layout.setContentsMargins(5, 8, 5, 5)
        layout.setSpacing(3)

        # 조건식 표시
        self.condition_preview = QLabel("조건을 설정하면 미리보기가 표시됩니다.")
        self.condition_preview.setStyleSheet("""
            background-color: #f5f5f5;
            border: 1px solid #ddd;
            padding: 10px;
            border-radius: 5px;
            font-family: monospace;
        """)
        self.condition_preview.setWordWrap(True)
        layout.addWidget(self.condition_preview)

        # 호환성 검증 결과
        self.compatibility_result = QLabel("호환성 검증 결과가 표시됩니다.")
        self.compatibility_result.setStyleSheet("""
            background-color: #e3f2fd;
            border: 1px solid #2196f3;
            padding: 5px;
            border-radius: 3px;
            font-size: 11px;
        """)
        layout.addWidget(self.compatibility_result)

        parent_layout.addWidget(group)

    def _create_button_area(self, parent_layout):
        """버튼 영역 생성"""
        button_layout = QHBoxLayout()
        button_layout.addStretch()

        # 미리보기 버튼
        self.preview_button = QPushButton("👁️ 미리보기")
        self.preview_button.setStyleSheet("""
            QPushButton {
                background-color: #2196f3;
                color: white;
                font-weight: bold;
                padding: 8px 16px;
                border: none;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #1976d2;
            }
        """)
        button_layout.addWidget(self.preview_button)

        # 조건 생성 버튼
        self.create_button = QPushButton("✅ 조건 생성")
        self.create_button.setStyleSheet("""
            QPushButton {
                background-color: #4caf50;
                color: white;
                font-weight: bold;
                padding: 8px 16px;
                border: none;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
        """)
        button_layout.addWidget(self.create_button)

        # 초기화 버튼
        self.reset_button = QPushButton("🔄 초기화")
        self.reset_button.setStyleSheet("""
            QPushButton {
                background-color: #ff9800;
                color: white;
                font-weight: bold;
                padding: 8px 16px;
                border: none;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #f57c00;
            }
        """)
        button_layout.addWidget(self.reset_button)

        parent_layout.addLayout(button_layout)

    def _connect_signals(self):
        """시그널 연결"""
        self.category_combo.currentTextChanged.connect(self._on_category_changed)
        self.variable_combo.currentTextChanged.connect(self._on_variable_changed)
        self.help_button.clicked.connect(self._on_help_clicked)
        self.search_button.clicked.connect(self._on_search_clicked)
        self.value_type_combo.currentTextChanged.connect(self._on_value_type_changed)

        self.preview_button.clicked.connect(self._on_preview_clicked)
        self.create_button.clicked.connect(self._on_create_clicked)
        self.reset_button.clicked.connect(self._on_reset_clicked)

        self._logger.info("컨디션 빌더 시그널 연결 완료")

    def _on_category_changed(self, category: str):
        """카테고리 변경 처리"""
        self._logger.info(f"카테고리 변경: {category}")
        # TODO: 카테고리별 변수 필터링

    def _on_variable_changed(self, variable: str):
        """변수 변경 처리"""
        self._logger.info(f"변수 변경: {variable}")
        self.variable_selected.emit(variable)
        # TODO: 파라미터 UI 동적 생성

    def _on_help_clicked(self):
        """헬프 버튼 클릭 처리 - 선택된 변수의 도움말 표시"""
        from PyQt6.QtWidgets import QMessageBox

        current_variable = self.variable_combo.currentText()
        if current_variable and current_variable != "":
            self._logger.info(f"변수 도움말 요청: {current_variable}")
            # TODO: 변수 도움말 다이얼로그 표시
            QMessageBox.information(
                self,
                "변수 도움말",
                f"선택된 변수: {current_variable}\n\n"
                "설명: 이 변수에 대한 상세 설명\n"
                "사용법: 파라미터 설정 방법\n"
                "추천 범위: 일반적인 사용 범위\n\n"
                "※ 실제 변수 정보는 구현 예정"
            )
        else:
            QMessageBox.warning(self, "알림", "먼저 변수를 선택해주세요.")

    def _on_search_clicked(self):
        """검색 버튼 클릭 처리"""
        search_term = self.search_input.text().strip()
        if search_term:
            self._logger.info(f"변수 검색: {search_term}")
            # TODO: 검색 로직

    def _on_value_type_changed(self, value_type: str):
        """비교값 타입 변경 처리"""
        self._logger.info(f"비교값 타입 변경: {value_type}")
        # TODO: 비교값 입력 UI 동적 변경

    def _on_preview_clicked(self):
        """미리보기 버튼 클릭 처리"""
        condition_data = self._get_current_condition()
        self.condition_preview_requested.emit(condition_data)
        self._logger.info("조건 미리보기 요청")

    def _on_create_clicked(self):
        """조건 생성 버튼 클릭 처리"""
        condition_data = self._get_current_condition()
        self.condition_created.emit(condition_data)
        self._logger.info("조건 생성 요청")

    def _on_reset_clicked(self):
        """초기화 버튼 클릭 처리"""
        self._reset_all_inputs()
        self._logger.info("조건 빌더 초기화")

    def _get_current_condition(self) -> dict:
        """현재 설정된 조건 데이터 반환"""
        return {
            'category': self.category_combo.currentText(),
            'variable': self.variable_combo.currentText(),
            'operator': self.operator_combo.currentText(),
            'value_type': self.value_type_combo.currentText(),
            'value': self.value_input.text()
        }

    def _reset_all_inputs(self):
        """모든 입력 필드 초기화"""
        self.category_combo.setCurrentIndex(0)
        self.variable_combo.setCurrentIndex(0)
        self.search_input.clear()
        self.operator_combo.setCurrentIndex(0)
        self.value_type_combo.setCurrentIndex(0)
        self.value_input.clear()
        self.condition_preview.setText("조건을 설정하면 미리보기가 표시됩니다.")
        self.compatibility_result.setText("호환성 검증 결과가 표시됩니다.")

    # ITriggerBuilderView 인터페이스 구현 메서드들 (부분적)
    def display_variables(self, variables_dto: TradingVariableListDTO) -> None:
        """변수 목록을 콤보박스에 표시"""
        self.variable_combo.clear()
        if variables_dto.success and variables_dto.grouped_variables:
            for category, variables in variables_dto.grouped_variables.items():
                for var in variables:
                    self.variable_combo.addItem(f"{var['display_name_ko']} ({var['variable_id']})")
        self._logger.info(f"변수 목록 표시 완료: {variables_dto.total_count}개")

    def show_variable_details(self, details_dto: TradingVariableDetailDTO) -> None:
        """변수 상세 정보를 파라미터 영역에 표시"""
        # TODO: 파라미터 UI 동적 생성
        self.parameter_info_label.setText(f"선택된 변수: {details_dto.variable_id or details_dto.display_name_ko or 'Unknown'}")
        self._logger.info(f"변수 상세 정보 표시: {details_dto.variable_id or details_dto.display_name_ko}")

    def update_compatibility_status(self, is_compatible: bool, message: str) -> None:
        """호환성 검증 결과 표시"""
        if is_compatible:
            self.compatibility_result.setStyleSheet("""
                background-color: #e8f5e8;
                border: 1px solid #4caf50;
                padding: 5px;
                border-radius: 3px;
                font-size: 11px;
            """)
            self.compatibility_result.setText(f"✅ {message}")
        else:
            self.compatibility_result.setStyleSheet("""
                background-color: #fff3e0;
                border: 1px solid #ff9800;
                padding: 5px;
                border-radius: 3px;
                font-size: 11px;
            """)
            self.compatibility_result.setText(f"⚠️ {message}")

        self._logger.info(f"호환성 검증 결과: {is_compatible}, {message}")
