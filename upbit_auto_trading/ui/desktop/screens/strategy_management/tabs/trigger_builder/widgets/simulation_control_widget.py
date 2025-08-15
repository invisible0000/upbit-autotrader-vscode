"""
시뮬레이션 컨트롤 위젯 - Legacy UI 기반 MVP 구현
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QPushButton, QLabel, QGridLayout, QFrame
)
from PyQt6.QtCore import pyqtSignal

from upbit_auto_trading.infrastructure.logging import create_component_logger

logger = create_component_logger("SimulationControlWidget")


class SimulationControlWidget(QWidget):
    """시뮬레이션 컨트롤 위젯 - MVP 패턴"""

    # 시그널 정의
    simulation_requested = pyqtSignal(str)  # 시나리오 타입
    data_source_changed = pyqtSignal(str)  # 데이터 소스 변경

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()

    def setup_ui(self):
        """UI 구성"""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)

        # 데이터 소스 영역 (간소화 버전)
        self.create_data_source_area(main_layout)

        # 구분선
        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.HLine)
        separator.setFrameShadow(QFrame.Shadow.Sunken)
        main_layout.addWidget(separator)

        # 시뮬레이션 버튼 영역
        self.create_simulation_buttons(main_layout)

    def create_data_source_area(self, parent_layout):
        """데이터 소스 선택 영역"""
        # 간소화된 데이터 소스 정보
        info_label = QLabel("📊 데이터 소스: 업비트 1분봉")
        info_label.setStyleSheet("font-size: 11px; color: #666; margin: 5px;")
        parent_layout.addWidget(info_label)

    def create_simulation_buttons(self, parent_layout):
        """시뮬레이션 버튼들 생성"""
        # 3행 2열 그리드 배치
        grid_layout = QGridLayout()
        grid_layout.setSpacing(5)

        # 시뮬레이션 시나리오 버튼들
        scenarios = [
            ("📈 상승 추세", "uptrend", "#28a745"),
            ("📉 하락 추세", "downtrend", "#dc3545"),
            ("🚀 급등", "surge", "#007bff"),
            ("💥 급락", "crash", "#fd7e14"),
            ("➡️ 횡보", "sideways", "#6c757d"),
            ("🔄 MA 교차", "ma_cross", "#17a2b8")
        ]

        for i, (text, scenario_type, color) in enumerate(scenarios):
            row = i // 2
            col = i % 2

            btn = QPushButton(text)
            btn.setMinimumHeight(35)
            btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: {color};
                    color: white;
                    border: none;
                    border-radius: 4px;
                    padding: 5px;
                    font-size: 10px;
                    font-weight: bold;
                }}
                QPushButton:hover {{
                    opacity: 0.8;
                }}
                QPushButton:pressed {{
                    background-color: {self._darken_color(color)};
                }}
            """)

            # 시그널 연결
            btn.clicked.connect(lambda checked, st=scenario_type: self.request_simulation(st))

            grid_layout.addWidget(btn, row, col)

        parent_layout.addLayout(grid_layout)

        # 전체 시뮬레이션 버튼
        full_test_btn = QPushButton("🎯 전체 시뮬레이션")
        full_test_btn.setMinimumHeight(40)
        full_test_btn.setStyleSheet("""
            QPushButton {
                background-color: #6f42c1;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 8px;
                font-size: 11px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #563d7c;
            }
            QPushButton:pressed {
                background-color: #4e3677;
            }
        """)
        full_test_btn.clicked.connect(lambda: self.request_simulation("full_test"))
        parent_layout.addWidget(full_test_btn)

    def request_simulation(self, scenario_type):
        """시뮬레이션 요청"""
        self.simulation_requested.emit(scenario_type)
        logger.info(f"시뮬레이션 요청: {scenario_type}")

    def _darken_color(self, color):
        """색상을 약간 어둡게 만들기"""
        # 간단한 색상 어둡게 처리
        color_map = {
            "#28a745": "#218838",
            "#dc3545": "#c82333",
            "#007bff": "#0069d9",
            "#fd7e14": "#e06700",
            "#6c757d": "#5a6268",
            "#17a2b8": "#148892"
        }
        return color_map.get(color, color)

    def update_status(self, message):
        """상태 메시지 업데이트"""
        logger.debug(f"시뮬레이션 상태: {message}")
