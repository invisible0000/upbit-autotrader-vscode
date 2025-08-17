"""
백테스팅 화면 - DDD 재개발 중

Legacy 시스템을 제거하고 DDD 아키텍처로 재개발 진행 중입니다.
Modern Infrastructure와 MVP 패턴을 적용한 새로운 백테스팅 시스템을 구현할 예정입니다.
"""

from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont

from upbit_auto_trading.infrastructure.logging import create_component_logger


class BacktestingScreen(QWidget):
    """백테스팅 화면 - DDD 재개발 중"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.logger = create_component_logger("BacktestingScreen")
        self.logger.info("🔧 백테스팅 화면 - DDD 재개발 중 (폴백 화면)")
        self._setup_ui()

    def _setup_ui(self):
        """개발 중 폴백 UI 설정"""
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # 제목
        title = QLabel("📈 백테스팅")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_font = QFont()
        title_font.setPointSize(24)
        title_font.setBold(True)
        title.setFont(title_font)

        # 상태 메시지
        status = QLabel("🔧 DDD 아키텍처로 재개발 진행 중...")
        status.setAlignment(Qt.AlignmentFlag.AlignCenter)
        status_font = QFont()
        status_font.setPointSize(14)
        status.setFont(status_font)

        # 설명
        description = QLabel(
            "Legacy 시스템을 제거하고\n"
            "Modern Infrastructure + Domain Layer로\n"
            "새로운 백테스팅 엔진을 구현 예정입니다."
        )
        description.setAlignment(Qt.AlignmentFlag.AlignCenter)
        desc_font = QFont()
        desc_font.setPointSize(12)
        description.setFont(desc_font)

        layout.addWidget(title)
        layout.addWidget(status)
        layout.addWidget(description)
