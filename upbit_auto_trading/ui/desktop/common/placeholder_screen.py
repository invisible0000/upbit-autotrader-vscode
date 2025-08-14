"""
Placeholder 화면 생성 유틸리티
"""
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel
from PyQt6.QtCore import Qt


def create_placeholder_screen(title: str) -> QWidget:
    """플레이스홀더 화면 생성"""
    widget = QWidget()
    layout = QVBoxLayout(widget)

    label = QLabel(f"{title}\n\n구현 예정입니다.")
    label.setAlignment(Qt.AlignmentFlag.AlignCenter)
    label.setStyleSheet("""
        QLabel {
            font-size: 16px;
            color: #666;
            padding: 40px;
        }
    """)

    layout.addWidget(label)

    return widget
