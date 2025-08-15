"""
파라미터 입력 위젯 - 변수 파라미터 설정 제공
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGroupBox, QLabel, QScrollArea
)
from PyQt6.QtCore import pyqtSignal

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
        variable_name = details_dto.variable_id or details_dto.display_name_ko or 'Unknown'
        self.parameter_info_label.setText(f"선택된 변수: {variable_name}")
        self._logger.info(f"변수 상세 정보 표시: {variable_name}")
        # TODO: 파라미터 UI 동적 생성

    def clear_parameters(self):
        """파라미터 영역 초기화"""
        # 기존 파라미터 위젯들 제거
        for i in reversed(range(self.parameter_layout.count())):
            widget = self.parameter_layout.takeAt(i).widget()
            if widget:
                widget.deleteLater()

        self.parameter_info_label.setText("변수를 선택하면 파라미터 설정이 표시됩니다.")
