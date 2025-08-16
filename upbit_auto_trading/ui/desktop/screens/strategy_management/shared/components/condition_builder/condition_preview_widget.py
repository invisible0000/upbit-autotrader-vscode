"""
조건 미리보기 위젯 - 설정된 조건의 미리보기 표시
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QGroupBox, QLabel
)
from PyQt6.QtCore import pyqtSignal, Qt

from upbit_auto_trading.infrastructure.logging import create_component_logger


class ConditionPreviewWidget(QWidget):
    """조건 미리보기 위젯 - 조건 미리보기 표시 담당"""

    # 시그널 정의
    preview_updated = pyqtSignal(str)  # 미리보기 업데이트

    def __init__(self, parent=None):
        super().__init__(parent)
        self._logger = create_component_logger("ConditionPreviewWidget")
        self._init_ui()

    def _init_ui(self):
        """UI 초기화"""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)

        # 그룹박스
        group = QGroupBox("👁️ 조건 미리보기")
        layout = QVBoxLayout(group)
        layout.setContentsMargins(8, 10, 8, 8)

        self.preview_label = QLabel("조건을 설정하면 미리보기가 표시됩니다.")
        self.preview_label.setWordWrap(True)
        self.preview_label.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)
        layout.addWidget(self.preview_label)

        main_layout.addWidget(group)

    def update_preview(self, preview_text: str):
        """미리보기 텍스트 업데이트"""
        self.preview_label.setText(preview_text)
        self.preview_updated.emit(preview_text)
        self._logger.info(f"조건 미리보기 업데이트: {preview_text[:50]}...")

    def clear_preview(self):
        """미리보기 초기화"""
        self.preview_label.setText("조건을 설정하면 미리보기가 표시됩니다.")
