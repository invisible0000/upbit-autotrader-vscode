"""
컨디션 빌더 위젯 - IConditionBuilderView 구현체 (MVP View)
실제 DB와 연동되는 정상적인 컨디션 빌더
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGroupBox, QPushButton,
    QLabel, QComboBox, QLineEdit, QProgressBar, QMessageBox
)
from PyQt6.QtCore import pyqtSignal
from typing import Optional

from upbit_auto_trading.infrastructure.logging import create_component_logger
from upbit_auto_trading.infrastructure.repositories.variable_help_repository import VariableHelpRepository
from upbit_auto_trading.application.dto.trigger_builder.trading_variable_dto import (
    TradingVariableListDTO,
    TradingVariableDetailDTO
)

# 하위 위젯들 임포트
from .parameter_input_widget import ParameterInputWidget
from .condition_preview_widget import ConditionPreviewWidget
from .compatibility_status_widget import CompatibilityStatusWidget


class ConditionBuilderWidget(QWidget):
    """컨디션 빌더 위젯 - DB 연동 가능한 MVP View 구현체

    IConditionBuilderView 인터페이스를 컴포지션으로 구현하여 메타클래스 충돌 방지
    """

    # 시그널 정의
    variable_selected = pyqtSignal(str)  # 변수 선택
    external_variable_selected = pyqtSignal(str)  # 외부 변수 선택 (파라미터 표시용)
    category_changed = pyqtSignal(str)   # 카테고리 변경
    condition_created = pyqtSignal(dict)  # 조건 생성
    condition_preview_requested = pyqtSignal(dict)  # 미리보기 요청
    compatibility_check_requested = pyqtSignal(str, str)  # 호환성 검토 요청 (main_var_id, external_var_id)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._logger = create_component_logger("ConditionBuilderWidget")
        self._help_repository = VariableHelpRepository()  # Repository 의존성 주입
        self._current_variables_dto: Optional[TradingVariableListDTO] = None
        self._init_ui()
        self._connect_signals()

    def _init_ui(self):
        """UI 초기화 - 상하단 구조로 변경"""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(5, 5, 5, 5)
        main_layout.setSpacing(6)

        # 조건 빌더 레이아웃 비율 조절은 이곳에서
        # 1. 변수 선택 영역 (작은 비율)
        self._create_variable_selection_area(main_layout)

        # 2. 조건 설정 영역 (작은 비율)
        self._create_condition_setup_area(main_layout)

        # 3. 호환성 검토 결과 영역 (작은 비율)
        self._create_compatibility_status_area(main_layout)

        # 4. 외부 변수 영역 (작은 비율)
        self._create_external_variable_area(main_layout)

        # 5. 조건 미리보기 영역 (큰 비율)
        self._create_condition_preview_area(main_layout)

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
        # 기본 변수 선택에서는 메타변수 카테고리 제외
        self.category_combo.addItems(["전체", "추세", "모멘텀", "변동성", "거래량", "가격"])
        self.category_combo.setMinimumWidth(80)
        main_row.addWidget(self.category_combo)

        main_row.addSpacing(15)  # 간격

        # 변수
        main_row.addWidget(QLabel("변수:"))
        self.variable_combo = QComboBox()
        self.variable_combo.setMinimumWidth(200)
        main_row.addWidget(self.variable_combo)

        # 헬프 버튼 - 기본 QSS 스타일 사용
        self.help_button = QPushButton("📖")
        self.help_button.setFixedSize(50, 28)
        self.help_button.setToolTip("변수 상세 도움말 보기")
        main_row.addWidget(self.help_button)

        main_row.addStretch()  # 나머지 공간
        var_layout.addLayout(main_row)

        layout.addLayout(var_layout)

        # 파라미터 입력 임베딩
        self.parameter_input = ParameterInputWidget()
        layout.addWidget(self.parameter_input)

        parent_layout.addWidget(group)

    def _create_condition_setup_area(self, parent_layout):
        """조건 설정 영역 - 1줄 배치"""
        group = QGroupBox("⚙️ 조건 설정")
        layout = QVBoxLayout(group)
        layout.setContentsMargins(8, 10, 8, 8)

        # 모든 조건 요소를 한 줄에 배치
        condition_layout = QHBoxLayout()

        # 연산자 선택
        condition_layout.addWidget(QLabel("연산자:"))
        self.operator_combo = QComboBox()
        self.operator_combo.addItems([">", ">=", "<", "<=", "==", "!=", "상향 돌파", "하향 돌파"])
        self.operator_combo.setMinimumWidth(100)
        condition_layout.addWidget(self.operator_combo)

        condition_layout.addWidget(QLabel("비교값:"))
        self.value_type_combo = QComboBox()
        self.value_type_combo.addItems(["직접 입력", "외부 변수"])
        self.value_type_combo.setMinimumWidth(100)
        condition_layout.addWidget(self.value_type_combo)

        condition_layout.addWidget(QLabel("값:"))
        self.value_input = QLineEdit()
        self.value_input.setPlaceholderText("비교할 값을 입력하세요")
        self.value_input.setMinimumWidth(120)
        condition_layout.addWidget(self.value_input)

        condition_layout.addStretch()
        layout.addLayout(condition_layout)

        parent_layout.addWidget(group)

    def _create_compatibility_status_area(self, parent_layout):
        """호환성 검토 결과 영역"""
        # 호환성 검증 그룹박스 생성
        self.compatibility_group = QGroupBox("🔍 호환성 검증")
        compatibility_layout = QVBoxLayout()
        compatibility_layout.setContentsMargins(8, 8, 8, 8)
        compatibility_layout.setSpacing(5)

        # 호환성 상태 위젯 생성
        self.compatibility_status = CompatibilityStatusWidget()
        compatibility_layout.addWidget(self.compatibility_status)

        self.compatibility_group.setLayout(compatibility_layout)
        # 초기에는 숨김 처리
        self.compatibility_group.setVisible(False)
        parent_layout.addWidget(self.compatibility_group)

    def _create_external_variable_area(self, parent_layout):
        """외부 변수 선택 + 파라미터 설정 영역"""
        self.external_group = QGroupBox("🔗 외부 변수")
        self.external_group.setEnabled(False)  # 기본적으로 비활성화
        layout = QVBoxLayout(self.external_group)
        layout.setContentsMargins(8, 10, 8, 8)

        # 외부 변수 범주, 변수, 헬프 버튼을 한 줄에 배치
        ext_main_row = QHBoxLayout()

        # 범주
        ext_main_row.addWidget(QLabel("범주:"))
        self.external_category_combo = QComboBox()
        self.external_category_combo.addItems(["전체", "추세", "모멘텀", "변동성", "거래량", "가격", "메타변수"])
        self.external_category_combo.setMinimumWidth(80)
        ext_main_row.addWidget(self.external_category_combo)

        ext_main_row.addSpacing(15)  # 간격

        # 변수
        ext_main_row.addWidget(QLabel("변수:"))
        self.external_variable_combo = QComboBox()
        self.external_variable_combo.setMinimumWidth(200)
        ext_main_row.addWidget(self.external_variable_combo)

        # 외부 변수 헬프 버튼 - 기본 QSS 스타일 사용
        self.external_help_button = QPushButton("📖")
        self.external_help_button.setFixedSize(50, 28)
        self.external_help_button.setToolTip("외부 변수 상세 도움말 보기")
        ext_main_row.addWidget(self.external_help_button)

        ext_main_row.addStretch()
        layout.addLayout(ext_main_row)

        # 외부 변수용 파라미터 설정
        self.external_parameter_input = ParameterInputWidget()
        layout.addWidget(self.external_parameter_input)

        parent_layout.addWidget(self.external_group)

    def _create_condition_preview_area(self, parent_layout):
        """조건 미리보기 영역 - 동적 크기 조정"""
        from PyQt6.QtWidgets import QSizePolicy

        self.condition_preview = ConditionPreviewWidget()

        # 미리보기 위젯이 남은 공간을 모두 차지하도록 설정
        self.condition_preview.setSizePolicy(
            QSizePolicy.Policy.Expanding,  # 가로 확장
            QSizePolicy.Policy.Expanding   # 세로 확장
        )

        # 최소 높이 설정으로 너무 작아지는 것 방지
        self.condition_preview.setMinimumHeight(150)

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
        self.value_type_combo.currentTextChanged.connect(self._on_value_type_changed)

        # 조건 설정 관련 시그널들
        self.operator_combo.currentTextChanged.connect(self._on_condition_changed)
        self.value_input.textChanged.connect(self._on_condition_changed)
        self.value_type_combo.currentTextChanged.connect(self._on_value_type_changed)
        self.external_variable_combo.currentTextChanged.connect(self._on_condition_changed)

        # 외부 변수 범주 변경 시그널 추가
        self.external_category_combo.currentTextChanged.connect(self._on_external_category_changed)

        # 외부 변수 선택 시그널 추가 (파라미터 표시용)
        self.external_variable_combo.currentTextChanged.connect(self._on_external_variable_changed)

        # 외부 변수 헬프 버튼 시그널 추가
        self.external_help_button.clicked.connect(self._on_external_help_clicked)

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
                # 기본 변수는 메타변수 제외하고 추가
                for category, variables in variables_dto.grouped_variables.items():
                    for var in variables:
                        display_name = var.get('display_name_ko', var.get('variable_id', ''))
                        variable_id = var.get('variable_id', '')

                        # 기본 변수 선택에는 메타변수(dynamic_management) 제외
                        if category != "dynamic_management":
                            self.variable_combo.addItem(display_name, variable_id)

                        # 외부 변수에는 모든 변수 포함 (메타변수 포함)
                        self.external_variable_combo.addItem(display_name, variable_id)

                # 현재 선택된 카테고리에 따라 필터링 적용
                current_category = self.category_combo.currentText()
                if current_category != "전체":
                    self._filter_variables_by_category(current_category)

                # 외부 변수도 현재 선택된 범주에 따라 필터링
                current_external_category = self.external_category_combo.currentText()
                if current_external_category != "전체":
                    self._filter_external_variables_by_category(current_external_category)

            self._logger.info(f"변수 목록 표시 완료: {variables_dto.total_count}개 (기본 변수에서 메타변수 제외)")

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

    def show_external_variable_details(self, details_dto: TradingVariableDetailDTO) -> None:
        """선택된 외부 변수의 상세 정보 표시"""
        try:
            if details_dto.success:
                # 외부 파라미터 입력 위젯에 상세 정보 전달
                self.external_parameter_input.show_variable_details(details_dto)
                self._logger.info(f"외부 변수 상세 정보 표시: {details_dto.variable_id}")
            else:
                self._logger.error(f"외부 변수 상세 정보 오류: {details_dto.error_message}")

        except Exception as e:
            self._logger.error(f"외부 변수 상세 정보 표시 중 오류: {e}")

    def update_compatibility_status(self, result_dto) -> None:
        """변수 호환성 검증 결과 표시"""
        try:
            # DTO에서 정보 추출
            is_compatible = result_dto.is_compatible
            message = result_dto.message
            detail = result_dto.detail or ""

            # 호환성 검증 영역 표시
            self.compatibility_group.setVisible(True)

            # 호환성 상태 위젯 업데이트
            self.compatibility_status.update_compatibility_status(is_compatible, message, detail)
            self._logger.info(f"호환성 상태: {is_compatible} - {message}")

        except Exception as e:
            self._logger.error(f"호환성 상태 업데이트 중 오류: {e}")
            # 오류 시에도 영역은 표시
            self.compatibility_group.setVisible(True)

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
        """카테고리별 변수 필터링 - 기본 변수 선택에서는 메타변수 제외"""
        if not hasattr(self, '_current_variables_dto') or not self._current_variables_dto:
            return

        # 카테고리 한글->영문 매핑
        category_mapping = {
            "전체": None,
            "추세": "trend",
            "모멘텀": "momentum",
            "변동성": "volatility",
            "거래량": "volume",
            "가격": "price",
            "메타변수": "dynamic_management"
        }

        selected_category = category_mapping.get(category)

        # 변수 콤보박스 클리어
        self.variable_combo.clear()

        # 변수 필터링 및 추가
        if self._current_variables_dto.success and self._current_variables_dto.grouped_variables:
            for cat, variables in self._current_variables_dto.grouped_variables.items():
                # 기본 변수 선택에서는 메타변수(dynamic_management) 절대 제외
                if cat == "dynamic_management":
                    continue

                # 전체 선택이거나 선택된 카테고리와 일치하는 경우
                if selected_category is None or cat == selected_category:
                    for var in variables:
                        display_name = var.get('display_name_ko', var.get('variable_id', ''))
                        variable_id = var.get('variable_id', '')
                        self.variable_combo.addItem(display_name, variable_id)

        self._logger.info(f"카테고리 '{category}'로 필터링 완료: {self.variable_combo.count()}개 변수 (메타변수 제외)")

    def _on_external_category_changed(self, category: str):
        """외부 변수 범주 변경 처리"""
        self._logger.info(f"외부 변수 범주 변경: {category}")
        self._filter_external_variables_by_category(category)

    def _filter_external_variables_by_category(self, category: str) -> None:
        """외부 변수 범주별 필터링"""
        if not hasattr(self, '_current_variables_dto') or not self._current_variables_dto:
            return

        # 카테고리 한글->영문 매핑 (동일한 매핑 사용)
        category_mapping = {
            "전체": None,
            "추세": "trend",
            "모멘텀": "momentum",
            "변동성": "volatility",
            "거래량": "volume",
            "가격": "price",
            "메타변수": "dynamic_management"
        }

        selected_category = category_mapping.get(category)

        # 외부 변수 콤보박스 클리어
        self.external_variable_combo.clear()

        # 변수 필터링 및 추가
        if self._current_variables_dto.success and self._current_variables_dto.grouped_variables:
            for cat, variables in self._current_variables_dto.grouped_variables.items():
                # 전체 선택이거나 선택된 카테고리와 일치하는 경우
                if selected_category is None or cat == selected_category:
                    for var in variables:
                        display_name = var.get('display_name_ko', var.get('variable_id', ''))
                        variable_id = var.get('variable_id', '')
                        self.external_variable_combo.addItem(display_name, variable_id)

        self._logger.info(f"외부 변수 범주 '{category}'로 필터링 완료: {self.external_variable_combo.count()}개 변수")

    def _on_external_variable_changed(self, variable_name: str):
        """외부 변수 선택 시 파라미터 표시"""
        variable_id = self.external_variable_combo.currentData()
        if variable_id:
            self._logger.info(f"외부 변수 선택: {variable_name} (ID: {variable_id})")
            # DDD 준수: 시그널을 통해 Presenter에게 위임
            self.external_variable_selected.emit(variable_id)

            # 호환성 검토 요청
            self._request_compatibility_check()

    def _on_variable_changed(self, variable_name: str):
        """변수 변경 처리"""
        variable_id = self.variable_combo.currentData()
        if variable_id:
            self._logger.info(f"변수 변경: {variable_name} (ID: {variable_id})")
            self.variable_selected.emit(variable_id)

            # 메타 변수 대상 업데이트 (외부 변수 메타 변수용)
            if hasattr(self, 'external_parameter_input'):
                self.external_parameter_input.set_base_variable(variable_name)

            # 호환성 검토 요청
            self._request_compatibility_check()

    def _request_compatibility_check(self):
        """호환성 검토 요청"""
        try:
            main_var_id = self.variable_combo.currentData()
            external_var_id = self.external_variable_combo.currentData() if self.external_group.isEnabled() else ""

            # 기본값 확인
            main_var_text = self.variable_combo.currentText()
            external_var_text = self.external_variable_combo.currentText() if self.external_group.isEnabled() else ""
            value_type = self.value_type_combo.currentText()

            # 기본 변수가 선택되지 않은 경우 - 박스 숨김
            if not main_var_id or main_var_text == "선택하세요":
                self.compatibility_group.setVisible(False)
                self.compatibility_status.clear_status()
                return

            # 기본 변수는 선택되었지만 비교값이 '직접 입력'인 경우 - 박스는 보이되 메시지 없음
            if value_type == "직접 입력":
                self.compatibility_group.setVisible(True)
                self.compatibility_status.clear_status()
                return

            # 외부 변수 선택 상태이지만 외부 변수가 미선택인 경우 - 박스 숨김
            if (value_type == "외부 변수"
                    and (not external_var_id or external_var_text == "선택하세요")):
                self.compatibility_group.setVisible(False)
                self.compatibility_status.clear_status()
                return

            # 유효한 변수가 모두 선택된 경우만 호환성 검증 진행
            if main_var_id and value_type == "외부 변수" and external_var_id:
                # 호환성 검증 영역 표시
                self.compatibility_group.setVisible(True)

                # 호환성 검토 중 상태 표시
                self.compatibility_status.update_checking_status()

                # 시그널을 통해 Presenter에게 호환성 검토 요청
                self.compatibility_check_requested.emit(main_var_id, external_var_id or "")

                self._logger.info(f"호환성 검토 요청: main={main_var_id}, external={external_var_id}")
            else:
                # 조건이 충족되지 않은 경우 영역 숨김
                self.compatibility_group.setVisible(False)
                self.compatibility_status.clear_status()

        except Exception as e:
            self._logger.error(f"호환성 검토 요청 중 오류: {e}")
            self.compatibility_group.setVisible(True)
            self.compatibility_status.update_warning_status("호환성 검토 중 오류가 발생했습니다.")

    def _get_variable_help_info(self, variable_id: str) -> str:
        """변수 ID로 도움말 정보 제공 - Repository 패턴 사용"""
        variable_name = ""

        # 현재 선택된 변수 이름 찾기
        if hasattr(self, 'variable_combo') and self.variable_combo.currentData() == variable_id:
            variable_name = self.variable_combo.currentText()
        elif hasattr(self, 'external_variable_combo') and self.external_variable_combo.currentData() == variable_id:
            variable_name = self.external_variable_combo.currentText()

        # DB에서 도움말 조회 시도
        help_text_ko, tooltip_ko = self._help_repository.get_help_text(variable_id, None)

        if help_text_ko:
            # DB에서 조회 성공
            help_text = f"변수 ID: {variable_id}\n"
            help_text += f"이름: {variable_name}\n\n"
            help_text += help_text_ko
            if tooltip_ko:
                help_text += f"\n\n💡 팁: {tooltip_ko}"
            return help_text
        else:
            # DB 조회 실패 시 기본 도움말 사용
            return self._help_repository.generate_basic_help_info(variable_id, variable_name)

    def _on_help_clicked(self):
        """헬프 버튼 클릭 처리 - 새로운 헬프 다이얼로그 표시"""
        variable_id = self.variable_combo.currentData()
        variable_name = self.variable_combo.currentText()

        if variable_id:
            try:
                # 새로운 헬프 다이얼로그 import (지연 로드)
                from upbit_auto_trading.ui.desktop.screens.strategy_management.shared.dialogs.variable_help_dialog import (
                    VariableHelpDialog
                )

                dialog = VariableHelpDialog(
                    variable_id=variable_id,
                    variable_name=variable_name,
                    parent=self
                )
                dialog.exec()

                self._logger.info(f"헬프 다이얼로그 표시: {variable_id}")

            except Exception as e:
                self._logger.error(f"헬프 다이얼로그 표시 중 오류: {e}")
                # 폴백: 기본 메시지박스
                help_info = self._get_variable_help_info(variable_id)
                QMessageBox.information(
                    self,
                    f"변수 도움말 - {variable_name}",
                    help_info
                )
        else:
            QMessageBox.warning(self, "알림", "먼저 변수를 선택해주세요.")

    def _on_external_help_clicked(self):
        """외부 변수 헬프 버튼 클릭 처리 - 새로운 헬프 다이얼로그 표시"""
        variable_id = self.external_variable_combo.currentData()
        variable_name = self.external_variable_combo.currentText()

        if variable_id:
            try:
                # 새로운 헬프 다이얼로그 import (지연 로드)
                from upbit_auto_trading.ui.desktop.screens.strategy_management.shared.dialogs.variable_help_dialog import (
                    VariableHelpDialog
                )

                dialog = VariableHelpDialog(
                    variable_id=variable_id,
                    variable_name=variable_name,
                    parent=self
                )
                dialog.exec()

                self._logger.info(f"외부 변수 헬프 다이얼로그 표시: {variable_id}")

            except Exception as e:
                self._logger.error(f"외부 변수 헬프 다이얼로그 표시 중 오류: {e}")
                # 폴백: 기본 메시지박스
                help_info = self._get_variable_help_info(variable_id)
                QMessageBox.information(
                    self,
                    f"외부 변수 도움말 - {variable_name}",
                    help_info
                )
        else:
            QMessageBox.warning(self, "알림", "먼저 외부 변수를 선택해주세요.")

    def _on_value_type_changed(self, value_type: str):
        """비교값 타입 변경 처리"""
        self._logger.info(f"비교값 타입 변경: {value_type}")

        # 외부 변수 선택 시 외부 변수 영역 활성화, 입력값 비활성화
        is_external = (value_type == "외부 변수")
        self.external_group.setEnabled(is_external)
        self.value_input.setEnabled(not is_external)

        if is_external:
            self.value_input.clear()
            self.value_input.setPlaceholderText("외부 변수 선택 시 입력 불가")
            # 외부 변수 모드로 변경 시 호환성 검토
            self._request_compatibility_check()
        else:
            self.value_input.setPlaceholderText("비교할 값을 입력하세요")
            # 직접 입력 모드로 변경 시 호환성 상태 초기화
            self.compatibility_status.clear_status()

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
