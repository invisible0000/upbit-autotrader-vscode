"""
플레이스홀더 화면 생성 유틸리티
- 개발 중인 화면에 대한 임시 플레이스홀더 제공
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, 
    QLabel, QPushButton, QFrame
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont, QPixmap


def create_placeholder_screen(title: str = "개발 중", description: str = "이 화면은 현재 개발 중입니다."):
    """
    플레이스홀더 화면 생성
    
    Args:
        title: 화면 제목
        description: 화면 설명
        
    Returns:
        QWidget: 플레이스홀더 화면 위젯
    """
    
    # 메인 위젯
    widget = QWidget()
    widget.setObjectName("PlaceholderWidget")
    
    # 메인 레이아웃
    layout = QVBoxLayout(widget)
    layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
    layout.setSpacing(20)
    
    # 아이콘 영역
    icon_frame = QFrame()
    icon_frame.setMaximumSize(100, 100)
    icon_frame.setStyleSheet("""
        QFrame {
            background-color: #f0f0f0;
            border: 2px dashed #cccccc;
            border-radius: 10px;
        }
    """)
    
    icon_layout = QVBoxLayout(icon_frame)
    icon_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
    
    # 아이콘 라벨
    icon_label = QLabel("🚧")
    icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
    icon_label.setStyleSheet("font-size: 48px; border: none;")
    icon_layout.addWidget(icon_label)
    
    # 제목
    title_label = QLabel(title)
    title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
    title_font = QFont()
    title_font.setPointSize(18)
    title_font.setBold(True)
    title_label.setFont(title_font)
    title_label.setStyleSheet("color: #333333; margin: 10px 0;")
    
    # 설명
    desc_label = QLabel(description)
    desc_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
    desc_label.setWordWrap(True)
    desc_label.setStyleSheet("color: #666666; font-size: 14px; margin: 0 20px;")
    
    # 개발 상태 정보
    status_label = QLabel("개발 진행률: 계획 단계")
    status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
    status_label.setStyleSheet("""
        background-color: #fff3cd;
        color: #856404;
        border: 1px solid #ffeaa7;
        border-radius: 5px;
        padding: 8px 16px;
        font-size: 12px;
    """)
    
    # 버튼 영역
    button_layout = QHBoxLayout()
    button_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
    
    # 새로고침 버튼
    refresh_button = QPushButton("새로고침")
    refresh_button.setStyleSheet("""
        QPushButton {
            background-color: #007bff;
            color: white;
            border: none;
            border-radius: 5px;
            padding: 8px 16px;
            font-size: 12px;
        }
        QPushButton:hover {
            background-color: #0056b3;
        }
        QPushButton:pressed {
            background-color: #004085;
        }
    """)
    
    # 돌아가기 버튼
    back_button = QPushButton("대시보드로 돌아가기")
    back_button.setStyleSheet("""
        QPushButton {
            background-color: #6c757d;
            color: white;
            border: none;
            border-radius: 5px;
            padding: 8px 16px;
            font-size: 12px;
        }
        QPushButton:hover {
            background-color: #545b62;
        }
        QPushButton:pressed {
            background-color: #3d4146;
        }
    """)
    
    button_layout.addWidget(refresh_button)
    button_layout.addWidget(back_button)
    
    # 레이아웃에 위젯 추가
    layout.addWidget(icon_frame, alignment=Qt.AlignmentFlag.AlignCenter)
    layout.addWidget(title_label)
    layout.addWidget(desc_label)
    layout.addWidget(status_label)
    layout.addLayout(button_layout)
    
    # 스타일시트 적용
    widget.setStyleSheet("""
        QWidget#PlaceholderWidget {
            background-color: #ffffff;
            border: 1px solid #e0e0e0;
            border-radius: 8px;
        }
    """)
    
    return widget


def create_error_screen(error_message: str = "오류가 발생했습니다.", details: str = ""):
    """
    오류 화면 생성
    
    Args:
        error_message: 오류 메시지
        details: 상세 정보
        
    Returns:
        QWidget: 오류 화면 위젯
    """
    
    widget = QWidget()
    widget.setObjectName("ErrorWidget")
    
    layout = QVBoxLayout(widget)
    layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
    layout.setSpacing(20)
    
    # 오류 아이콘
    icon_label = QLabel("❌")
    icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
    icon_label.setStyleSheet("font-size: 48px;")
    
    # 오류 메시지
    error_label = QLabel(error_message)
    error_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
    error_font = QFont()
    error_font.setPointSize(16)
    error_font.setBold(True)
    error_label.setFont(error_font)
    error_label.setStyleSheet("color: #dc3545; margin: 10px 0;")
    
    # 상세 정보
    if details:
        details_label = QLabel(details)
        details_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        details_label.setWordWrap(True)
        details_label.setStyleSheet("color: #666666; font-size: 12px; margin: 0 20px;")
    
    # 재시도 버튼
    retry_button = QPushButton("다시 시도")
    retry_button.setStyleSheet("""
        QPushButton {
            background-color: #dc3545;
            color: white;
            border: none;
            border-radius: 5px;
            padding: 8px 16px;
        }
        QPushButton:hover {
            background-color: #c82333;
        }
    """)
    
    layout.addWidget(icon_label)
    layout.addWidget(error_label)
    if details:
        layout.addWidget(details_label)
    layout.addWidget(retry_button, alignment=Qt.AlignmentFlag.AlignCenter)
    
    widget.setStyleSheet("""
        QWidget#ErrorWidget {
            background-color: #fff5f5;
            border: 1px solid #fed7d7;
            border-radius: 8px;
        }
    """)
    
    return widget
