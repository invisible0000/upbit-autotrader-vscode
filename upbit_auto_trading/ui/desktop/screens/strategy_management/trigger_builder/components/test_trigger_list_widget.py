#!/usr/bin/env python3
"""
TriggerListWidget 기능 점검 테스트
- 저장, 편집, 복사, 삭제 기능 테스트
- 단순화된 저장 로직 검증
"""

import sys
import os

# 패키지 경로 설정 - 더 정확한 경로
current_dir = os.path.dirname(os.path.abspath(__file__))
components_dir = current_dir
trigger_builder_dir = os.path.dirname(current_dir)
screens_dir = os.path.dirname(trigger_builder_dir)
upbit_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(screens_dir))))

sys.path.insert(0, upbit_dir)
sys.path.insert(0, components_dir)

from PyQt6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QHBoxLayout, QWidget, QPushButton, QTextEdit, QLabel, QLineEdit, QComboBox
from PyQt6.QtCore import pyqtSlot

# 절대 import로 변경
try:
    from trigger_list_widget import TriggerListWidget
    print("✅ TriggerListWidget 가져오기 성공")
except ImportError as e:
    print(f"❌ TriggerListWidget 가져오기 실패: {e}")
    sys.exit(1)

class MockConditionDialog:
    """테스트용 조건 다이얼로그 모크"""
    
    def __init__(self):
        self.current_condition = {
            "name": "테스트 트리거",
            "variable_name": "RSI",
            "operator": "<",
            "target_value": "30",
            "category": "indicator",
            "comparison_type": "fixed",
            "description": "RSI 과매도 테스트"
        }
    
    def get_current_condition(self):
        return self.current_condition.copy()
    
    def collect_condition_data(self):
        return self.current_condition.copy()
    
    def save_condition(self):
        print("✅ MockConditionDialog: save_condition 호출됨")
        return True

class TriggerListTestWindow(QMainWindow):
    """TriggerListWidget 테스트 윈도우"""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("🧪 TriggerListWidget 기능 테스트")
        self.setGeometry(100, 100, 1200, 800)
        
        # 중앙 위젯 설정
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # 레이아웃 설정
        main_layout = QHBoxLayout(central_widget)
        
        # 왼쪽: TriggerListWidget
        left_layout = QVBoxLayout()
        left_layout.addWidget(QLabel("📋 TriggerListWidget"))
        
        self.trigger_list = TriggerListWidget(self)
        left_layout.addWidget(self.trigger_list)
        
        # 시그널 연결
        self.trigger_list.trigger_selected.connect(self.on_trigger_selected)
        self.trigger_list.trigger_save_requested.connect(self.on_save_requested)
        self.trigger_list.trigger_edited.connect(self.on_trigger_edited)
        self.trigger_list.trigger_deleted.connect(self.on_trigger_deleted)
        self.trigger_list.trigger_copied.connect(self.on_trigger_copied)
        
        # 오른쪽: 테스트 패널
        right_layout = QVBoxLayout()
        right_layout.addWidget(QLabel("🧪 테스트 패널"))
        
        # 조건 입력 폼
        form_layout = QVBoxLayout()
        
        # 트리거 이름
        form_layout.addWidget(QLabel("트리거 이름:"))
        self.name_input = QLineEdit("새로운 테스트 트리거")
        form_layout.addWidget(self.name_input)
        
        # 변수 선택
        form_layout.addWidget(QLabel("변수:"))
        self.variable_combo = QComboBox()
        self.variable_combo.addItems(["RSI", "MACD", "볼린저밴드", "이평선", "거래량"])
        form_layout.addWidget(self.variable_combo)
        
        # 연산자
        form_layout.addWidget(QLabel("연산자:"))
        self.operator_combo = QComboBox()
        self.operator_combo.addItems([">", "<", ">=", "<=", "=="])
        form_layout.addWidget(self.operator_combo)
        
        # 값
        form_layout.addWidget(QLabel("값:"))
        self.value_input = QLineEdit("30")
        form_layout.addWidget(self.value_input)
        
        right_layout.addLayout(form_layout)
        
        # 테스트 버튼들
        test_buttons_layout = QVBoxLayout()
        
        # 조건 업데이트 버튼
        update_btn = QPushButton("🔄 조건 업데이트")
        update_btn.clicked.connect(self.update_mock_condition)
        test_buttons_layout.addWidget(update_btn)
        
        # 직접 저장 테스트
        direct_save_btn = QPushButton("💾 직접 저장 테스트")
        direct_save_btn.clicked.connect(self.test_direct_save)
        test_buttons_layout.addWidget(direct_save_btn)
        
        # 목록 새로고침
        refresh_btn = QPushButton("🔄 목록 새로고침")
        refresh_btn.clicked.connect(self.trigger_list.refresh_list)
        test_buttons_layout.addWidget(refresh_btn)
        
        right_layout.addLayout(test_buttons_layout)
        
        # 로그 출력
        right_layout.addWidget(QLabel("📝 이벤트 로그:"))
        self.log_text = QTextEdit()
        self.log_text.setMaximumHeight(200)
        right_layout.addWidget(self.log_text)
        
        # 레이아웃 조합
        main_layout.addLayout(left_layout, 7)  # 70%
        main_layout.addLayout(right_layout, 3)  # 30%
        
        # Mock 조건 다이얼로그 설정
        self.condition_dialog = MockConditionDialog()
        
        self.log("🚀 TriggerListWidget 테스트 시작")
    
    def get_current_condition_data(self):
        """현재 폼에서 조건 데이터 생성"""
        return {
            "name": self.name_input.text(),
            "variable_name": self.variable_combo.currentText(),
            "operator": self.operator_combo.currentText(),
            "target_value": self.value_input.text(),
            "category": "indicator",
            "comparison_type": "fixed",
            "description": f"{self.variable_combo.currentText()} {self.operator_combo.currentText()} {self.value_input.text()}"
        }
    
    def update_mock_condition(self):
        """Mock 조건 업데이트"""
        new_condition = self.get_current_condition_data()
        self.condition_dialog.current_condition = new_condition
        self.log(f"🔄 조건 업데이트: {new_condition['name']}")
    
    def test_direct_save(self):
        """직접 저장 테스트"""
        self.log("💾 직접 저장 테스트 시작")
        self.update_mock_condition()
        self.trigger_list.save_current_condition()
    
    def log(self, message):
        """로그 출력"""
        self.log_text.append(f"[{len(self.log_text.toPlainText().split())}] {message}")
        print(message)
    
    # 시그널 핸들러들
    @pyqtSlot(object, int)
    def on_trigger_selected(self, item, column):
        if item:
            trigger_name = item.text(0)
            self.log(f"🎯 트리거 선택: {trigger_name}")
    
    @pyqtSlot()
    def on_save_requested(self):
        self.log("💾 저장 요청 시그널 수신 (폴백)")
    
    @pyqtSlot()
    def on_trigger_edited(self):
        self.log("✏️ 편집 시그널 수신")
    
    @pyqtSlot()
    def on_trigger_deleted(self):
        self.log("🗑️ 삭제 시그널 수신")
    
    @pyqtSlot()
    def on_trigger_copied(self):
        self.log("📋 복사 시그널 수신")

def main():
    """메인 함수"""
    app = QApplication(sys.argv)
    
    # 테스트 윈도우 실행
    window = TriggerListTestWindow()
    window.show()
    
    print("="*60)
    print("🧪 TriggerListWidget 기능 테스트")
    print("="*60)
    print("📋 테스트 항목:")
    print("1. 💾 트리거 저장 (직접 저장 vs 시그널 폴백)")
    print("2. ✏️ 트리거 편집")
    print("3. 📋 트리거 복사")
    print("4. 🗑️ 트리거 삭제")
    print("5. 🔍 트리거 검색")
    print("6. 🎯 트리거 선택")
    print("-"*60)
    print("👆 오른쪽 패널에서 조건을 설정하고 테스트하세요!")
    print("="*60)
    
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
