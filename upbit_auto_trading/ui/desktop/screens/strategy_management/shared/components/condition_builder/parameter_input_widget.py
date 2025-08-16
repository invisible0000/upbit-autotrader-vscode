"""
파라미터 입력 위젯 - 변수 파라미터 설정 제공
"""

from pathlib import Path
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGroupBox, QLabel, QScrollArea,
    QLineEdit, QSpinBox, QDoubleSpinBox, QComboBox, QCheckBox
)
from PyQt6.QtCore import pyqtSignal
from typing import Dict, Any, Optional

from upbit_auto_trading.infrastructure.logging import create_component_logger
from upbit_auto_trading.infrastructure.repositories.variable_help_repository import VariableHelpRepository
from upbit_auto_trading.application.dto.trigger_builder.trading_variable_dto import (
    TradingVariableDetailDTO
)


class ParameterInputWidget(QWidget):
    """파라미터 입력 위젯 - 변수 파라미터 설정 담당"""

    # 시그널 정의
    parameters_changed = pyqtSignal(dict)  # 파라미터 변경

    def __init__(self, parent=None):
        super().__init__(parent)
        self._logger = create_component_logger("ParameterInputWidget")
        self._help_repository = VariableHelpRepository()  # Repository 의존성 주입
        self._current_base_variable = "현재가"  # 현재 기본 변수 저장
        self._meta_target_label = None  # 메타 변수 대상 라벨 참조
        self._current_variable_id = ""  # 현재 선택된 변수 ID
        self._current_variable_name = ""  # 현재 선택된 변수 이름
        self._init_ui()

    def set_base_variable(self, variable_name: str):
        """기본 변수명 설정 (외부에서 호출)"""
        self._current_base_variable = variable_name
        if self._meta_target_label and hasattr(self._meta_target_label, 'setText'):
            try:
                self._meta_target_label.setText(variable_name)
            except RuntimeError:
                # QLabel이 이미 삭제된 경우 무시
                self._meta_target_label = None

    def _init_ui(self):
        """UI 초기화"""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)

        # 그룹박스
        group = QGroupBox("⚙️ 파라미터 설정")
        layout = QVBoxLayout(group)
        layout.setContentsMargins(8, 10, 8, 8)

        # 스크롤 가능한 파라미터 영역
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setMaximumHeight(150)

        self.parameter_container = QWidget()
        self.parameter_layout = QVBoxLayout(self.parameter_container)
        self.parameter_layout.setContentsMargins(5, 5, 5, 5)
        self.parameter_layout.setSpacing(3)

        scroll_area.setWidget(self.parameter_container)
        layout.addWidget(scroll_area)

        main_layout.addWidget(group)

    def _get_help_text(self, variable_id: str, parameter_name: str) -> tuple[str, str]:
        """DB에서 도움말 텍스트 조회 - Repository 사용"""
        return self._help_repository.get_help_text(variable_id, parameter_name)

    def _get_placeholder_text(self, variable_id: str, parameter_name: str) -> str:
        """DB에서 플레이스홀더 텍스트 조회 - Repository 사용"""
        return self._help_repository.get_placeholder_text(variable_id, parameter_name)

    def _parse_enum_values(self, enum_string: str) -> Dict[str, str]:
        """enum 문자열을 파싱하여 값:표시명 딕셔너리 반환"""
        try:
            if not enum_string:
                return {}

            # JSON 배열 형태의 문자열 처리
            import json
            if enum_string.startswith('[') and enum_string.endswith(']'):
                enum_list = json.loads(enum_string)
                result = {}

                for item in enum_list:
                    if ':' in item:
                        value, display = item.split(':', 1)
                        result[value] = display
                    else:
                        result[item] = item

                return result

            return {}

        except Exception as e:
            self._logger.warning(f"enum 값 파싱 실패: {e}")
            return {}

    def show_variable_details(self, details_dto: TradingVariableDetailDTO):
        """변수 상세 정보를 파라미터 영역에 표시"""
        """변수 상세 정보를 파라미터 영역에 표시"""
        try:
            variable_name = details_dto.variable_id or details_dto.display_name_ko or 'Unknown'

            # 현재 변수 정보 저장
            self._current_variable_id = details_dto.variable_id or ""
            self._current_variable_name = details_dto.display_name_ko or variable_name

            # 기존 파라미터 위젯들 제거
            self.clear_parameters()

            # 파라미터가 있는 경우 동적으로 생성
            if details_dto.success and details_dto.parameters:
                # 메타 변수인지 확인 (META_로 시작하는 것들)
                is_meta_variable = details_dto.variable_id and details_dto.variable_id.startswith('META_')

                if is_meta_variable:
                    self._create_meta_variable_widgets(details_dto)
                else:
                    self._create_parameter_widgets(details_dto.parameters, details_dto.variable_id or "")

                self._logger.info(f"변수 상세 정보 표시: {variable_name}, 파라미터 {len(details_dto.parameters)}개")
            else:
                self._logger.info(f"변수 선택됨 (파라미터 없음): {variable_name}")

        except Exception as e:
            self._logger.error(f"변수 상세 정보 표시 중 오류: {e}")

    def _create_parameter_widgets(self, parameters: list, variable_id: str = ""):
        """파라미터 목록을 기반으로 입력 위젯들을 동적 생성 (DB 정보 활용)"""
        try:
            for param in parameters:
                param_name = param.get('parameter_name', '')
                param_type = param.get('parameter_type', 'string')
                default_value = param.get('default_value', '')
                description = param.get('description', '')
                min_value = param.get('min_value')
                max_value = param.get('max_value')
                enum_values = param.get('enum_values', '')
                display_name_ko = param.get('display_name_ko', param_name)

                # DB에서 추가 정보 조회
                help_text, tooltip = self._get_help_text(variable_id, param_name)
                placeholder_text = self._get_placeholder_text(variable_id, param_name)

                # 파라미터 타입 정규화
                param_type = self._normalize_parameter_type(param_type)

                # 파라미터 행 생성 (DB 정보 포함)
                param_row = self._create_parameter_row(
                    param_name=param_name,
                    param_type=param_type,
                    default_value=default_value,
                    description=description or help_text,
                    min_value=min_value,
                    max_value=max_value,
                    enum_values=enum_values,
                    display_name_ko=display_name_ko,
                    tooltip=tooltip,
                    placeholder_text=placeholder_text
                )

                if param_row:
                    self.parameter_layout.addWidget(param_row)

            self._logger.info(f"파라미터 위젯 {len(parameters)}개 생성 완료")

        except Exception as e:
            self._logger.error(f"파라미터 위젯 생성 중 오류: {e}")

    def _create_meta_variable_widgets(self, details_dto):
        """메타 변수 전용 위젯 생성 - 기본 변수 정보 표시"""
        try:
            variable_id = details_dto.variable_id

            # 메타 변수 대상 표시 (실제 기본 변수와 연동)
            target_info_row = QWidget()
            target_layout = QHBoxLayout(target_info_row)
            target_layout.setContentsMargins(5, 2, 5, 2)

            target_label = QLabel("메타 변수 대상:")
            target_label.setMinimumWidth(80)
            target_layout.addWidget(target_label)

            # 실제 기본 변수명 가져오기
            target_variable = self._current_base_variable
            self._meta_target_label = QLabel(target_variable)
            self._meta_target_label.setStyleSheet("font-weight: bold; color: #0066cc;")
            target_layout.addWidget(self._meta_target_label)
            target_layout.addStretch()

            self.parameter_layout.addWidget(target_info_row)

            # 기존 파라미터들도 표시 (tracking_variable 제외하고 한국어 표시명 적용)
            filtered_params = []
            for param in details_dto.parameters:
                param_name = param.get('parameter_name', '')
                # tracking_variable은 제외 (메타 변수는 기본 변수를 자동 추적)
                if param_name != 'tracking_variable' and param_name != 'source_variable':
                    filtered_params.append(param)

            if filtered_params:
                self._create_parameter_widgets(filtered_params, variable_id)

            self._logger.info(f"메타 변수 위젯 생성 완료: {variable_id}")

        except Exception as e:
            self._logger.error(f"메타 변수 위젯 생성 중 오류: {e}")

    def _get_selected_base_variable(self) -> str:
        """현재 선택된 기본 변수명 가져오기"""
        return self._current_base_variable

    def _normalize_parameter_type(self, param_type: str) -> str:
        """파라미터 타입을 정규화"""
        # 타입 매핑
        type_mapping = {
            'float': 'decimal',
            'double': 'decimal',
            'enum': 'string',
            'text': 'string',
            'external_variable': 'external_variable'  # 외부 변수 타입 추가
        }
        return type_mapping.get(param_type.lower(), param_type.lower())

    def _create_parameter_row(self, param_name: str, param_type: str, default_value: Any,
                              description: str, min_value: Any = None, max_value: Any = None,
                              enum_values: str = "", display_name_ko: str = "",
                              tooltip: str = "", placeholder_text: str = "") -> QWidget:
        """개별 파라미터 입력 행 생성 (DB 정보 활용)"""
        try:
            row_widget = QWidget()
            row_layout = QHBoxLayout(row_widget)
            row_layout.setContentsMargins(5, 2, 5, 2)

            # 파라미터 이름 라벨 (한국어 표시명 우선 사용)
            label_text = display_name_ko if display_name_ko else param_name
            name_label = QLabel(f"{label_text}:")
            name_label.setMinimumWidth(80)

            # 툴팁 설정 (우선순위: tooltip > description > param_name)
            tooltip_text = tooltip or description or param_name
            if tooltip_text:
                name_label.setToolTip(tooltip_text)

            row_layout.addWidget(name_label)

            # 파라미터 타입별 입력 위젯 생성 (enum 처리 포함)
            input_widget = self._create_input_widget_by_type(
                param_type, default_value, min_value, max_value, enum_values, placeholder_text
            )

            if input_widget:
                input_widget.setObjectName(f"param_{param_name}")

                # 입력 위젯 크기 최적화 (타입별 적절한 크기 설정)
                self._set_optimal_widget_size(input_widget, param_type)

                # 입력 위젯에도 툴팁 설정
                if tooltip_text:
                    input_widget.setToolTip(tooltip_text)

                row_layout.addWidget(input_widget, 0)  # 고정 크기로 변경

                # 입력 변경 시그널 연결
                self._connect_input_signal(input_widget, param_name)

            # 우측 공간 활용을 위한 stretch 추가
            row_layout.addStretch(1)

            return row_widget

        except Exception as e:
            self._logger.error(f"파라미터 행 생성 중 오류: {e}")
            return QWidget()  # 빈 위젯 반환

    def _set_optimal_widget_size(self, widget: QWidget, param_type: str):
        """파라미터 타입에 따른 위젯 최적 크기 설정"""
        try:
            if param_type == 'integer':
                widget.setFixedWidth(80)  # 정수용 짧은 입력
            elif param_type == 'decimal':
                widget.setFixedWidth(100)  # 소수용 중간 입력
            elif param_type == 'boolean':
                widget.setFixedWidth(60)  # 체크박스용 짧은 폭
            elif param_type == 'enum':
                widget.setMinimumWidth(120)
                widget.setMaximumWidth(200)  # enum용 적절한 콤보박스
            elif param_type == 'external_variable':
                widget.setMinimumWidth(150)
                widget.setMaximumWidth(250)  # 외부 변수용 긴 콤보박스
            else:
                # 기본 문자열 입력
                widget.setMinimumWidth(100)
                widget.setMaximumWidth(180)
        except Exception as e:
            self._logger.warning(f"위젯 크기 설정 실패: {e}")

    def _create_input_widget_by_type(self, param_type: str, default_value: Any,
                                     min_value: Any = None, max_value: Any = None,
                                     enum_values: str = "", placeholder_text: str = "") -> QWidget:
        """파라미터 타입에 따른 입력 위젯 생성 (enum 및 placeholder 지원)"""
        try:
            # enum 타입 처리
            if param_type == 'enum' or enum_values:
                widget = QComboBox()

                # enum 값들 파싱
                enum_dict = self._parse_enum_values(enum_values)

                if enum_dict:
                    # 한국어 표시명과 함께 콤보박스 구성
                    for value, display_name in enum_dict.items():
                        widget.addItem(display_name, value)  # 표시명, 실제값

                    # 기본값 설정
                    if default_value:
                        index = widget.findData(default_value)
                        if index >= 0:
                            widget.setCurrentIndex(index)
                        else:
                            # 데이터에 없으면 텍스트로 찾아보기
                            index = widget.findText(default_value)
                            if index >= 0:
                                widget.setCurrentIndex(index)
                else:
                    # enum_values가 없는 경우 에디터블 콤보박스
                    widget.setEditable(True)
                    if placeholder_text:
                        line_edit = widget.lineEdit()
                        if line_edit:
                            line_edit.setPlaceholderText(placeholder_text)
                    if default_value:
                        widget.setCurrentText(str(default_value))

                return widget

            elif param_type == 'integer':
                widget = QSpinBox()
                widget.setRange(int(min_value) if min_value else -999999,
                                int(max_value) if max_value else 999999)
                widget.setValue(int(default_value) if str(default_value).isdigit() else 0)
                return widget

            elif param_type == 'decimal':
                widget = QDoubleSpinBox()
                widget.setRange(float(min_value) if min_value else -999999.0,
                                float(max_value) if max_value else 999999.0)
                widget.setDecimals(4)
                try:
                    widget.setValue(float(default_value))
                except (ValueError, TypeError):
                    widget.setValue(0.0)
                return widget

            elif param_type == 'boolean':
                widget = QCheckBox()
                if isinstance(default_value, bool):
                    widget.setChecked(default_value)
                elif isinstance(default_value, str):
                    widget.setChecked(default_value.lower() in ['true', '1', 'yes'])
                return widget

            elif param_type == 'external_variable':
                # 외부 변수 참조 타입 - 콤보박스로 변수 선택
                widget = QComboBox()
                widget.setEditable(True)  # 직접 입력도 가능하도록

                # 플레이스홀더 설정
                placeholder = placeholder_text or "외부 변수를 선택하거나 직접 입력"
                line_edit = widget.lineEdit()
                if line_edit:
                    line_edit.setPlaceholderText(placeholder)

                # 기본값이 있으면 설정
                if default_value:
                    widget.setCurrentText(str(default_value))

                # 자주 사용되는 변수들을 기본 목록으로 제공
                common_variables = [
                    "현재가", "고가", "저가", "시가", "종가",
                    "RSI", "MACD", "SMA", "EMA",
                    "거래량", "볼린저밴드", "ATR"
                ]
                widget.addItems(common_variables)
                return widget

            else:  # string 및 기타 타입
                widget = QLineEdit()
                widget.setText(str(default_value) if default_value else "")

                # 플레이스홀더 설정 (우선순위: placeholder_text > 기본 메시지)
                placeholder = placeholder_text or f"{param_type} 값을 입력하세요"
                widget.setPlaceholderText(placeholder)
                return widget

        except Exception as e:
            self._logger.error(f"입력 위젯 생성 중 오류: {e}")
            # 폴백: 기본 텍스트 입력
            widget = QLineEdit()
            widget.setText(str(default_value) if default_value else "")
            return widget

    def _connect_input_signal(self, widget: QWidget, param_name: str):
        """입력 위젯의 변경 시그널 연결"""
        try:
            if isinstance(widget, QSpinBox):
                widget.valueChanged.connect(lambda: self._emit_parameters_changed())
            elif isinstance(widget, QDoubleSpinBox):
                widget.valueChanged.connect(lambda: self._emit_parameters_changed())
            elif isinstance(widget, QLineEdit):
                widget.textChanged.connect(lambda: self._emit_parameters_changed())
            elif isinstance(widget, QCheckBox):
                widget.toggled.connect(lambda: self._emit_parameters_changed())
            elif isinstance(widget, QComboBox):
                widget.currentTextChanged.connect(lambda: self._emit_parameters_changed())

        except Exception as e:
            self._logger.error(f"시그널 연결 중 오류: {e}")

    def _emit_parameters_changed(self):
        """파라미터 변경 시그널 발생"""
        try:
            parameters = self.get_current_parameters()
            self.parameters_changed.emit(parameters)
            self._logger.debug(f"파라미터 변경됨: {parameters}")
        except Exception as e:
            self._logger.error(f"파라미터 변경 시그널 발생 중 오류: {e}")

    def get_current_parameters(self) -> Dict[str, Any]:
        """현재 설정된 파라미터 값들 반환"""
        parameters = {}

        try:
            for i in range(self.parameter_layout.count()):
                item = self.parameter_layout.itemAt(i)
                if not item:
                    continue
                row_widget = item.widget()
                if not row_widget:
                    continue

                # 행에서 입력 위젯 찾기
                for child in row_widget.findChildren(QWidget):
                    obj_name = child.objectName()
                    if obj_name.startswith("param_"):
                        param_name = obj_name.replace("param_", "")

                        # 위젯 타입별 값 추출
                        if isinstance(child, QSpinBox):
                            parameters[param_name] = child.value()
                        elif isinstance(child, QDoubleSpinBox):
                            parameters[param_name] = child.value()
                        elif isinstance(child, QLineEdit):
                            parameters[param_name] = child.text()
                        elif isinstance(child, QCheckBox):
                            parameters[param_name] = child.isChecked()
                        elif isinstance(child, QComboBox):
                            parameters[param_name] = child.currentText()

            return parameters

        except Exception as e:
            self._logger.error(f"파라미터 값 수집 중 오류: {e}")
            return {}

    def clear_parameters(self):
        """파라미터 영역 초기화"""
        # 기존 파라미터 위젯들 제거
        for i in reversed(range(self.parameter_layout.count())):
            item = self.parameter_layout.takeAt(i)
            if item and item.widget():
                widget = item.widget()
                if widget:
                    widget.deleteLater()
