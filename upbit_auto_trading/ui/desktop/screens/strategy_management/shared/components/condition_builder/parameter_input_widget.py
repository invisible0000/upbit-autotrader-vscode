"""
파라미터 입력 위젯 - 변수 파라미터 설정 제공
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGroupBox, QLabel, QScrollArea,
    QLineEdit, QSpinBox, QDoubleSpinBox, QComboBox, QCheckBox
)
from PyQt6.QtCore import pyqtSignal
from typing import Dict, Any

from upbit_auto_trading.infrastructure.logging import create_component_logger
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
        self._init_ui()

    def _init_ui(self):
        """UI 초기화"""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)

        # 그룹박스
        group = QGroupBox("⚙️ 파라미터 설정")
        layout = QVBoxLayout(group)
        layout.setContentsMargins(8, 10, 8, 8)

        # 파라미터 정보 라벨
        self.parameter_info_label = QLabel("변수를 선택하면 파라미터 설정이 표시됩니다.")
        self.parameter_info_label.setStyleSheet("color: gray; font-style: italic;")
        layout.addWidget(self.parameter_info_label)

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

    def show_variable_details(self, details_dto: TradingVariableDetailDTO):
        """변수 상세 정보를 파라미터 영역에 표시"""
        try:
            variable_name = details_dto.variable_id or details_dto.display_name_ko or 'Unknown'
            self.parameter_info_label.setText(f"선택된 변수: {variable_name}")

            # 기존 파라미터 위젯들 제거
            self.clear_parameters()

            # 파라미터가 있는 경우 동적으로 생성
            if details_dto.success and details_dto.parameters:
                self._create_parameter_widgets(details_dto.parameters)
                self._logger.info(f"변수 상세 정보 표시: {variable_name}, 파라미터 {len(details_dto.parameters)}개")
            else:
                self.parameter_info_label.setText(f"선택된 변수: {variable_name} (파라미터 없음)")
                self._logger.info(f"변수 선택됨 (파라미터 없음): {variable_name}")

        except Exception as e:
            self._logger.error(f"변수 상세 정보 표시 중 오류: {e}")

    def _create_parameter_widgets(self, parameters: list):
        """파라미터 목록을 기반으로 입력 위젯들을 동적 생성"""
        try:
            for param in parameters:
                param_name = param.get('parameter_name', '')
                param_type = param.get('parameter_type', 'string')
                default_value = param.get('default_value', '')
                description = param.get('description', '')
                min_value = param.get('min_value')
                max_value = param.get('max_value')

                # 파라미터 타입 정규화
                param_type = self._normalize_parameter_type(param_type)

                # 파라미터 행 생성
                param_row = self._create_parameter_row(
                    param_name, param_type, default_value, description, min_value, max_value
                )

                if param_row:
                    self.parameter_layout.addWidget(param_row)

            self._logger.info(f"파라미터 위젯 {len(parameters)}개 생성 완료")

        except Exception as e:
            self._logger.error(f"파라미터 위젯 생성 중 오류: {e}")

    def _normalize_parameter_type(self, param_type: str) -> str:
        """파라미터 타입을 정규화"""
        # 타입 매핑
        type_mapping = {
            'float': 'decimal',
            'double': 'decimal',
            'enum': 'string',
            'text': 'string'
        }
        return type_mapping.get(param_type.lower(), param_type.lower())

    def _create_parameter_row(self, param_name: str, param_type: str, default_value: Any,
                              description: str, min_value: Any = None, max_value: Any = None) -> QWidget:
        """개별 파라미터 입력 행 생성"""
        try:
            row_widget = QWidget()
            row_layout = QHBoxLayout(row_widget)
            row_layout.setContentsMargins(5, 2, 5, 2)

            # 파라미터 이름 라벨
            name_label = QLabel(f"{param_name}:")
            name_label.setMinimumWidth(80)
            name_label.setToolTip(description if description else param_name)
            row_layout.addWidget(name_label)

            # 파라미터 타입별 입력 위젯 생성
            input_widget = self._create_input_widget_by_type(
                param_type, default_value, min_value, max_value
            )

            if input_widget:
                input_widget.setObjectName(f"param_{param_name}")
                row_layout.addWidget(input_widget, 1)  # 확장 가능

                # 입력 변경 시그널 연결
                self._connect_input_signal(input_widget, param_name)

            return row_widget

        except Exception as e:
            self._logger.error(f"파라미터 행 생성 중 오류: {e}")
            return QWidget()  # 빈 위젯 반환

    def _create_input_widget_by_type(self, param_type: str, default_value: Any,
                                     min_value: Any = None, max_value: Any = None) -> QWidget:
        """파라미터 타입에 따른 입력 위젯 생성"""
        try:
            if param_type == 'integer':
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

            else:  # string 및 기타 타입
                widget = QLineEdit()
                widget.setText(str(default_value) if default_value else "")
                widget.setPlaceholderText(f"{param_type} 값을 입력하세요")
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

        self.parameter_info_label.setText("변수를 선택하면 파라미터 설정이 표시됩니다.")
