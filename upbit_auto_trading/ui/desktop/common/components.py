"""
공통 컴포넌트 라이브러리

이 모듈은 모든 화면에서 재사용할 수 있는 UI 컴포넌트를 제공합니다.
"""

from PyQt6.QtWidgets import (
    QWidget, QLabel, QPushButton, QLineEdit, QComboBox, 
    QCheckBox, QRadioButton, QSlider, QProgressBar,
    QVBoxLayout, QHBoxLayout, QFormLayout, QGridLayout,
    QGroupBox, QTabWidget, QTableWidget, QTableWidgetItem,
    QHeaderView, QScrollArea, QSizePolicy
)
from PyQt6.QtCore import Qt, pyqtSignal, QSize
from PyQt6.QtGui import QIcon, QFont, QColor

class StyledButton(QPushButton):
    """스타일이 적용된 버튼 컴포넌트"""
    
    def __init__(self, text="", icon_path=None, parent=None):
        """
        초기화
        
        Args:
            text (str): 버튼 텍스트
            icon_path (str, optional): 아이콘 경로
            parent (QWidget, optional): 부모 위젯
        """
        super().__init__(text, parent)
        
        if icon_path:
            self.setIcon(QIcon(icon_path))
        
        self.setMinimumHeight(30)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

class PrimaryButton(StyledButton):
    """주요 액션을 위한 버튼 컴포넌트"""
    
    def __init__(self, text="", icon_path=None, parent=None):
        """
        초기화
        
        Args:
            text (str): 버튼 텍스트
            icon_path (str, optional): 아이콘 경로
            parent (QWidget, optional): 부모 위젯
        """
        super().__init__(text, icon_path, parent)
        
        self.setObjectName("primary-button")
        self.setStyleSheet("""
            #primary-button {
                background-color: #3498db;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
            }
            
            #primary-button:hover {
                background-color: #2980b9;
            }
            
            #primary-button:pressed {
                background-color: #1a5276;
            }
            
            #primary-button:disabled {
                background-color: #cccccc;
                color: #999999;
            }
        """)

class SecondaryButton(StyledButton):
    """보조 액션을 위한 버튼 컴포넌트"""
    
    def __init__(self, text="", icon_path=None, parent=None):
        """
        초기화
        
        Args:
            text (str): 버튼 텍스트
            icon_path (str, optional): 아이콘 경로
            parent (QWidget, optional): 부모 위젯
        """
        super().__init__(text, icon_path, parent)
        
        self.setObjectName("secondary-button")
        self.setStyleSheet("""
            #secondary-button {
                background-color: #e0e0e0;
                color: #333333;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
            }
            
            #secondary-button:hover {
                background-color: #d0d0d0;
            }
            
            #secondary-button:pressed {
                background-color: #c0c0c0;
            }
            
            #secondary-button:disabled {
                background-color: #f0f0f0;
                color: #999999;
            }
        """)

class DangerButton(StyledButton):
    """위험한 액션을 위한 버튼 컴포넌트"""
    
    def __init__(self, text="", icon_path=None, parent=None):
        """
        초기화
        
        Args:
            text (str): 버튼 텍스트
            icon_path (str, optional): 아이콘 경로
            parent (QWidget, optional): 부모 위젯
        """
        super().__init__(text, icon_path, parent)
        
        self.setObjectName("danger-button")
        self.setStyleSheet("""
            #danger-button {
                background-color: #e74c3c;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
            }
            
            #danger-button:hover {
                background-color: #c0392b;
            }
            
            #danger-button:pressed {
                background-color: #922b21;
            }
            
            #danger-button:disabled {
                background-color: #cccccc;
                color: #999999;
            }
        """)

class StyledLineEdit(QLineEdit):
    """스타일이 적용된 라인 에디트 컴포넌트"""
    
    def __init__(self, placeholder="", parent=None):
        """
        초기화
        
        Args:
            placeholder (str): 플레이스홀더 텍스트
            parent (QWidget, optional): 부모 위젯
        """
        super().__init__(parent)
        
        self.setPlaceholderText(placeholder)
        self.setMinimumHeight(30)
        # 하드코딩된 스타일 제거 - QSS 테마를 따름

class StyledComboBox(QComboBox):
    """스타일이 적용된 콤보 박스 컴포넌트"""
    
    def __init__(self, items=None, parent=None):
        """
        초기화
        
        Args:
            items (list, optional): 콤보 박스 아이템 목록
            parent (QWidget, optional): 부모 위젯
        """
        super().__init__(parent)
        
        if items:
            self.addItems(items)
        
        self.setMinimumHeight(30)
        # 하드코딩된 스타일 제거 - QSS 테마를 따름

class StyledCheckBox(QCheckBox):
    """스타일이 적용된 체크 박스 컴포넌트"""
    
    def __init__(self, text="", parent=None):
        """
        초기화
        
        Args:
            text (str): 체크 박스 텍스트
            parent (QWidget, optional): 부모 위젯
        """
        super().__init__(text, parent)
        # 하드코딩된 스타일 제거 - QSS 테마를 따름

class StyledGroupBox(QGroupBox):
    """스타일이 적용된 그룹 박스 컴포넌트"""
    
    def __init__(self, title="", parent=None):
        """
        초기화
        
        Args:
            title (str): 그룹 박스 제목
            parent (QWidget, optional): 부모 위젯
        """
        super().__init__(title, parent)
        # 하드코딩된 스타일 제거 - QSS 테마를 따름

class StyledTableWidget(QTableWidget):
    """스타일이 적용된 테이블 위젯 컴포넌트"""
    
    def __init__(self, rows=0, columns=0, parent=None):
        """
        초기화
        
        Args:
            rows (int): 행 수
            columns (int): 열 수
            parent (QWidget, optional): 부모 위젯
        """
        super().__init__(rows, columns, parent)
        
        self.setAlternatingRowColors(True)
        self.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.horizontalHeader().setStretchLastSection(True)
        self.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        self.verticalHeader().setVisible(False)
        
        self.setStyleSheet("""
            QTableWidget {
                border: 1px solid #cccccc;
                gridline-color: #e0e0e0;
            }
            
            QTableWidget::item {
                padding: 6px;
            }
            
            QTableWidget::item:selected {
                background-color: #3498db;
                color: white;
            }
            
            QHeaderView::section {
                background-color: #f0f0f0;
                padding: 6px;
                border: 1px solid #cccccc;
                font-weight: bold;
            }
        """)

class FormRow(QWidget):
    """폼 행 컴포넌트"""
    
    def __init__(self, label_text, widget, parent=None):
        """
        초기화
        
        Args:
            label_text (str): 레이블 텍스트
            widget (QWidget): 입력 위젯
            parent (QWidget, optional): 부모 위젯
        """
        super().__init__(parent)
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        label = QLabel(label_text)
        label.setMinimumWidth(120)
        label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        
        layout.addWidget(label)
        layout.addWidget(widget)

class CardWidget(QWidget):
    """카드 위젯 컴포넌트"""
    
    def __init__(self, title="", parent=None):
        """
        초기화
        
        Args:
            title (str): 카드 제목
            parent (QWidget, optional): 부모 위젯
        """
        super().__init__(parent)
        
        self.setObjectName("card-widget")
        self.setStyleSheet("""
            #card-widget {
                background-color: white;
                border: 1px solid #e0e0e0;
                border-radius: 6px;
            }
        """)
        
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(15, 15, 15, 15)
        
        if title:
            title_label = QLabel(title)
            title_label.setObjectName("card-title")
            font = title_label.font()
            font.setPointSize(12)
            font.setBold(True)
            title_label.setFont(font)
            title_label.setStyleSheet("color: #333333; margin-bottom: 10px;")
            
            self.layout.addWidget(title_label)
    
    def add_widget(self, widget):
        """
        위젯 추가
        
        Args:
            widget (QWidget): 추가할 위젯
        """
        self.layout.addWidget(widget)
    
    def add_layout(self, layout):
        """
        레이아웃 추가
        
        Args:
            layout (QLayout): 추가할 레이아웃
        """
        self.layout.addLayout(layout)