"""
심플한 조건 빌더 - 단독 실행용
ConditionDialog만 띄워서 확인하는 화면
"""

from PyQt6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QComboBox, QLineEdit, QTextEdit,
    QGroupBox, QFormLayout, QMessageBox, QSpinBox, QDoubleSpinBox
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont

import sys
import os

# 컴포넌트 import
sys.path.append(os.path.dirname(__file__))
from components.condition_dialog import ConditionDialog

class SimpleConditionBuilder(QWidget):
    """심플한 조건 빌더 화면"""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("🎯 심플한 조건 빌더")
        self.setMinimumSize(800, 600)
        
        self.init_ui()
    
    def init_ui(self):
        """UI 초기화"""
        layout = QVBoxLayout(self)
        
        # 제목
        title_label = QLabel("🎯 심플한 조건 빌더")
        title_label.setStyleSheet("""
            font-size: 18px; 
            font-weight: bold; 
            color: #2c3e50;
            padding: 15px;
            background-color: #ecf0f1;
            border-radius: 8px;
            margin-bottom: 10px;
        """)
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title_label)
        
        try:
            # ConditionDialog 임베드
            self.condition_dialog = ConditionDialog()
            self.condition_dialog.setParent(self)
            
            # 다이얼로그를 위젯으로 변환 (창 모드 해제)
            self.condition_dialog.setWindowFlags(Qt.WindowType.Widget)
            
            # 시그널 연결
            self.condition_dialog.condition_saved.connect(self.on_condition_saved)
            
            layout.addWidget(self.condition_dialog)
            
            print("✅ 심플한 조건 빌더 로드 성공")
            
        except Exception as e:
            print(f"❌ 조건 빌더 로딩 실패: {e}")
            
            # 대체 UI
            error_widget = self.create_fallback_ui()
            layout.addWidget(error_widget)
    
    def create_fallback_ui(self):
        """대체 UI - ConditionDialog 로드 실패 시"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # 에러 메시지
        error_label = QLabel("❌ ConditionDialog 로드 실패")
        error_label.setStyleSheet("""
            color: #e74c3c; 
            font-size: 16px; 
            font-weight: bold;
            padding: 20px;
            text-align: center;
        """)
        error_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(error_label)
        
        # 간단한 대체 조건 빌더
        self.create_simple_builder(layout)
        
        return widget
    
    def create_simple_builder(self, layout):
        """간단한 조건 빌더 UI"""
        # 메인 그룹
        main_group = QGroupBox("📊 간단한 조건 설정")
        main_group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                border: 2px solid #3498db;
                border-radius: 8px;
                margin: 10px;
                padding-top: 15px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
                background-color: white;
                color: #3498db;
            }
        """)
        
        form_layout = QFormLayout(main_group)
        
        # 조건명
        self.condition_name = QLineEdit()
        self.condition_name.setPlaceholderText("조건 이름을 입력하세요")
        form_layout.addRow("🎯 조건명:", self.condition_name)
        
        # 변수 선택
        self.variable_combo = QComboBox()
        self.variable_combo.addItems([
            "현재가격", "RSI", "MACD", "볼린저밴드", "이동평균선",
            "거래량", "변동성", "스토캐스틱", "CCI", "Williams %R"
        ])
        form_layout.addRow("📊 변수:", self.variable_combo)
        
        # 연산자
        self.operator_combo = QComboBox()
        self.operator_combo.addItems([">", ">=", "<", "<=", "==", "!="])
        form_layout.addRow("⚖️ 연산자:", self.operator_combo)
        
        # 비교값
        self.target_value = QDoubleSpinBox()
        self.target_value.setRange(-999999, 999999)
        self.target_value.setValue(50.0)
        form_layout.addRow("🎯 비교값:", self.target_value)
        
        # 설명
        self.description = QTextEdit()
        self.description.setPlaceholderText("조건에 대한 설명을 입력하세요")
        self.description.setMaximumHeight(80)
        form_layout.addRow("📝 설명:", self.description)
        
        layout.addWidget(main_group)
        
        # 버튼 영역
        button_layout = QHBoxLayout()
        
        # 저장 버튼
        save_btn = QPushButton("💾 조건 저장")
        save_btn.setStyleSheet("""
            QPushButton {
                background-color: #27ae60;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 10px 20px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #229954;
            }
        """)
        save_btn.clicked.connect(self.save_simple_condition)
        
        # 초기화 버튼
        reset_btn = QPushButton("🔄 초기화")
        reset_btn.setStyleSheet("""
            QPushButton {
                background-color: #95a5a6;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 10px 20px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #7f8c8d;
            }
        """)
        reset_btn.clicked.connect(self.reset_form)
        
        button_layout.addWidget(save_btn)
        button_layout.addWidget(reset_btn)
        button_layout.addStretch()
        
        layout.addLayout(button_layout)
    
    def save_simple_condition(self):
        """간단한 조건 저장"""
        try:
            condition_data = {
                'name': self.condition_name.text() or "새 조건",
                'variable_name': self.variable_combo.currentText(),
                'operator': self.operator_combo.currentText(),
                'target_value': str(self.target_value.value()),
                'description': self.description.toPlainText(),
                'category': 'simple'
            }
            
            print(f"✅ 간단한 조건 생성: {condition_data}")
            
            QMessageBox.information(
                self, 
                "저장 완료", 
                f"조건 '{condition_data['name']}'이 생성되었습니다!\n\n"
                f"변수: {condition_data['variable_name']}\n"
                f"조건: {condition_data['operator']} {condition_data['target_value']}"
            )
            
        except Exception as e:
            QMessageBox.critical(self, "오류", f"조건 저장 중 오류가 발생했습니다:\n{e}")
    
    def reset_form(self):
        """폼 초기화"""
        self.condition_name.clear()
        self.variable_combo.setCurrentIndex(0)
        self.operator_combo.setCurrentIndex(0)
        self.target_value.setValue(50.0)
        self.description.clear()
        
        print("🔄 폼 초기화 완료")
    
    def on_condition_saved(self, condition_data):
        """ConditionDialog에서 조건 저장 완료 시 호출"""
        print(f"✅ 조건 저장 완료: {condition_data.get('name', 'Unknown')}")
        
        QMessageBox.information(
            self, 
            "저장 완료", 
            f"조건 '{condition_data.get('name', 'Unknown')}'이 저장되었습니다!"
        )

if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    window = SimpleConditionBuilder()
    window.show()
    
    sys.exit(app.exec())
