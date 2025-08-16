"""
변수 호환성 상태 표시 위젯 - 변수 조합의 호환성을 표시
"""

from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                            QFrame, QScrollArea, QSizePolicy)
from PyQt6.QtGui import QFont
from PyQt6.QtCore import Qt

from upbit_auto_trading.infrastructure.logging import create_component_logger


class CompatibilityStatusWidget(QWidget):
    """변수 호환성 상태 표시 위젯"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._logger = create_component_logger("CompatibilityStatusWidget")
        self._init_ui()

    def _init_ui(self):
        """UI 초기화"""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(5, 5, 5, 5)
        main_layout.setSpacing(2)

        # 높이를 2줄로 제한 (약 60px)
        self.setFixedHeight(60)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

        # 스크롤 가능한 내용 영역
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.scroll_area.setFrameShape(QFrame.Shape.NoFrame)

        # 내용 위젯
        self.content_widget = QWidget()
        self.content_layout = QVBoxLayout(self.content_widget)
        self.content_layout.setContentsMargins(5, 5, 5, 5)
        self.content_layout.setSpacing(3)

        # 상태 표시 영역 생성
        self._create_status_lines(self.content_layout)

        self.scroll_area.setWidget(self.content_widget)
        main_layout.addWidget(self.scroll_area)

    def _create_status_lines(self, parent_layout):
        """상태 표시 라인들 생성"""
        # 첫 번째 줄: 호환성 상태
        self.status_line1 = QHBoxLayout()
        self.status_line1.setContentsMargins(0, 0, 0, 0)

        self.status_icon = QLabel("⚪")
        self.status_icon.setFixedWidth(20)
        self.status_line1.addWidget(self.status_icon)

        self.status_text = QLabel("변수를 선택하면 호환성을 검토합니다")
        self.status_text.setWordWrap(True)
        self.status_text.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        font = QFont()
        font.setPointSize(9)
        self.status_text.setFont(font)
        self.status_line1.addWidget(self.status_text, 1)  # stretch factor 1

        parent_layout.addLayout(self.status_line1)

        # 두 번째 줄: 상세 정보
        self.detail_line = QHBoxLayout()
        self.detail_line.setContentsMargins(20, 0, 0, 0)

        self.detail_text = QLabel("")
        self.detail_text.setWordWrap(True)
        self.detail_text.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        self.detail_text.setStyleSheet("color: #666666;")
        detail_font = QFont()
        detail_font.setPointSize(8)
        self.detail_text.setFont(detail_font)
        self.detail_line.addWidget(self.detail_text, 1)  # stretch factor 1

        parent_layout.addLayout(self.detail_line)

        # 레이아웃에 stretch 추가
        parent_layout.addStretch()

    def update_compatibility_status(self, is_compatible: bool, message: str, detail: str = ""):
        """호환성 상태 업데이트"""
        try:
            # 아이콘 및 색상 설정
            if is_compatible:
                self.status_icon.setText("✅")
                self.status_text.setStyleSheet("color: #2E7D32;")  # 녹색
            else:
                self.status_icon.setText("❌")
                self.status_text.setStyleSheet("color: #C62828;")  # 빨간색

            # 메시지 설정
            self.status_text.setText(message)

            # 상세 정보 설정
            if detail:
                self.detail_text.setText(detail)
                self.detail_text.setVisible(True)
            else:
                self.detail_text.setVisible(False)

            self._logger.info(f"호환성 상태 업데이트: {is_compatible} - {message}")

        except Exception as e:
            self._logger.error(f"호환성 상태 업데이트 중 오류: {e}")

    def update_checking_status(self):
        """검토 중 상태로 업데이트"""
        self.status_icon.setText("🔄")
        self.status_text.setText("호환성을 검토하고 있습니다...")
        self.status_text.setStyleSheet("color: #1976D2;")  # 파란색
        self.detail_text.setVisible(False)

    def clear_status(self):
        """상태 초기화"""
        self.status_icon.setText("⚪")
        self.status_text.setText("변수를 선택하면 호환성을 검토합니다")
        self.status_text.setStyleSheet("color: #666666;")  # 기본 색상
        self.detail_text.setVisible(False)

    def update_warning_status(self, message: str, detail: str = ""):
        """경고 상태 업데이트"""
        self.status_icon.setText("⚠️")
        self.status_text.setText(message)
        self.status_text.setStyleSheet("color: #F57C00;")  # 주황색

        if detail:
            self.detail_text.setText(detail)
            self.detail_text.setVisible(True)
        else:
            self.detail_text.setVisible(False)
