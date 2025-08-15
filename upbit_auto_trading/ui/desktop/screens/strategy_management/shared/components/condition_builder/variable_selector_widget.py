"""
변수 선택기 위젯 - 기본 변수 선택과 검색 기능 제공
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


class VariableSelectorWidget(QWidget):
    """변수 선택기 위젯 - 기본 변수 선택 담당"""

    # 시그널 정의
    variable_selected = pyqtSignal(str)  # 변수 선택
    search_requested = pyqtSignal(str)   # 검색 요청

    def __init__(self, parent=None):
        super().__init__(parent)
        self._logger = create_component_logger("VariableSelectorWidget")
        self._init_ui()
        self._connect_signals()

    def _init_ui(self):
        """UI 초기화"""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)

        # 그룹박스
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

        # 검색 영역
        search_layout = QHBoxLayout()
        search_layout.addWidget(QLabel("검색:"))
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("변수 명 또는 설명 검색")
        search_layout.addWidget(self.search_input)

        self.search_button = QPushButton("검색")
        self.search_button.setFixedHeight(self.search_input.sizeHint().height())
        search_layout.addWidget(self.search_button)

        layout.addLayout(search_layout)

        main_layout.addWidget(group)

    def _connect_signals(self):
        """시그널 연결"""
        self.variable_combo.currentTextChanged.connect(self._on_variable_changed)
        self.search_button.clicked.connect(self._on_search_clicked)
        self.help_button.clicked.connect(self._on_help_clicked)

    def _on_variable_changed(self, variable: str):
        """변수 변경 처리"""
        self._logger.info(f"변수 변경: {variable}")
        self.variable_selected.emit(variable)

    def _on_search_clicked(self):
        """검색 버튼 클릭 처리"""
        search_term = self.search_input.text().strip()
        self._logger.info(f"검색 요청: {search_term}")
        self.search_requested.emit(search_term)

    def _on_help_clicked(self):
        """헬프 버튼 클릭 처리"""
        from PyQt6.QtWidgets import QMessageBox

        current_variable = self.variable_combo.currentText()
        if current_variable and current_variable != "":
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

    def update_variables(self, variables_dto: TradingVariableListDTO):
        """변수 목록 업데이트"""
        # TODO: DTO에서 변수 목록 추출하여 콤보박스 업데이트
        self._logger.info("변수 목록 업데이트")

    def update_categories(self, categories: list):
        """카테고리 목록 업데이트"""
        self.category_combo.clear()
        self.category_combo.addItems(categories)
