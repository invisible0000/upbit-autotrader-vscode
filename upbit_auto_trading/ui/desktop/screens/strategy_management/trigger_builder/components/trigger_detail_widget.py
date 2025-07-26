"""
트리거 상세정보 위젯 - 기존 기능 정확 복제
integrated_condition_manager.py의 create_trigger_detail_area() 완전 복제
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QGroupBox, QTextEdit, QPushButton, QHBoxLayout, QSizePolicy
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont


class TriggerDetailWidget(QWidget):
    """트리거 상세정보 위젯 - 기존 기능 정확 복제"""
    
    # 시그널 정의
    trigger_copied = pyqtSignal()
    # trigger_tested = pyqtSignal()  # 테스트 버튼 제거로 시그널도 제거
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_trigger = None
        self.setup_ui()
        self.initialize_default_state()
    
    def setup_ui(self):
        """UI 구성 - integrated_condition_manager.py와 정확히 동일"""
        # 메인 그룹박스 (스타일은 애플리케이션 테마를 따름)
        self.group = QGroupBox("📊 트리거 상세정보")
        # 하드코딩된 스타일 제거 - 애플리케이션 테마를 따름
        
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addWidget(self.group)
        
        layout = QVBoxLayout(self.group)
        layout.setContentsMargins(5, 8, 5, 5)
        layout.setSpacing(3)
        
        # 그룹박스 크기 정책도 Expanding으로 설정
        self.group.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        
        # 상세 정보 표시 (원본과 정확히 동일)
        self.detail_text = QTextEdit()
        self.detail_text.setReadOnly(True)
        # setMaximumHeight 제거하여 텍스트 박스가 꽉 차게 함
        # self.detail_text.setMaximumHeight(200)
        
        # 크기 정책을 Expanding으로 설정하여 최대한 확장
        self.detail_text.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        
        # 최소 높이 제한 제거하여 레이아웃 비율이 1:1이 되도록 함
        # self.detail_text.setMinimumHeight(150)
        
        # 폰트 크기를 더 작게 설정 (원본과 동일)
        font = QFont()
        font.setPointSize(9)  # 8 → 9로 살짝 증가
        self.detail_text.setFont(font)
        
        # 문서 여백을 줄여서 줄간격 최소화 (원본과 동일)
        document = self.detail_text.document()
        if document:
            document.setDocumentMargin(3)
        
        # 스타일은 애플리케이션 테마를 따름 (하드코딩 제거)
        layout.addWidget(self.detail_text, 1)  # stretch=1 추가하여 남은 공간을 모두 차지
        
        # 액션 버튼들 (원본에는 없지만 유용한 기능)
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(2)
        
        self.copy_detail_btn = QPushButton("📄 복사")
        self.copy_detail_btn.setMaximumHeight(25)
        self.copy_detail_btn.clicked.connect(self.copy_detail_to_clipboard)
        btn_layout.addWidget(self.copy_detail_btn)
        
        # "🧪 테스트" 버튼 제거 - 용도가 불분명한 버튼
        # self.test_trigger_btn = QPushButton("🧪 테스트")
        # self.test_trigger_btn.setMaximumHeight(25)
        # self.test_trigger_btn.clicked.connect(self.trigger_tested.emit)
        # btn_layout.addWidget(self.test_trigger_btn)
        
        layout.addLayout(btn_layout)
    
    def initialize_default_state(self):
        """기본 상태 초기화 - 원본과 동일"""
        self.detail_text.setPlainText("트리거를 선택하면 상세정보가 표시됩니다.")
    
    def update_trigger_detail(self, trigger_data):
        """트리거 상세정보 업데이트 - 원본 기능 복제"""
        try:
            if not trigger_data:
                self.detail_text.setPlainText("트리거를 선택하면 상세정보가 표시됩니다.")
                self.current_trigger = None
                return
            
            self.current_trigger = trigger_data
            
            # 상세정보 포맷팅 (원본 스타일)
            detail_text = self._format_trigger_detail(trigger_data)
            self.detail_text.setPlainText(detail_text)
            
        except Exception as e:
            print(f"❌ 트리거 상세정보 업데이트 실패: {e}")
            self.detail_text.setPlainText(f"상세정보 로드 중 오류 발생: {e}")
    
    def _format_trigger_detail(self, trigger_data):
        """트리거 상세정보 포맷팅 - 원본 스타일"""
        name = trigger_data.get('name', 'Unknown')
        created_at = trigger_data.get('created_at', 'Unknown')
        active = trigger_data.get('active', False)
        
        # 기본 정보
        detail_text = f"""📋 트리거 상세정보
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🏷️ 이름: {name}
📅 생성일: {created_at}
🔄 상태: {'활성' if active else '비활성'}

"""
        
        # 조건 정보 (있는 경우)
        if 'conditions' in trigger_data:
            conditions = trigger_data['conditions']
            detail_text += "🎯 트리거 조건:\n"
            
            for i, condition in enumerate(conditions, 1):
                variable = condition.get('variable', 'Unknown')
                operator = condition.get('operator', 'Unknown')
                value = condition.get('value', 'Unknown')
                detail_text += f"  {i}. {variable} {operator} {value}\n"
            
            detail_text += "\n"
        
        # 단일 조건 정보 (레거시)
        if 'variable' in trigger_data:
            variable = trigger_data.get('variable', 'Unknown')
            operator = trigger_data.get('operator', 'Unknown')
            value = trigger_data.get('value', 'Unknown')
            
            detail_text += f"""🎯 조건:
  변수: {variable}
  연산자: {operator}
  값: {value}

"""
        
        # 외부 변수 정보 (있는 경우)
        if 'external_variables' in trigger_data:
            external_vars = trigger_data['external_variables']
            if external_vars:
                detail_text += "🔗 외부 변수:\n"
                for var_name, var_info in external_vars.items():
                    var_type = var_info.get('type', 'Unknown')
                    var_value = var_info.get('value', 'Unknown')
                    detail_text += f"  • {var_name}: {var_type} = {var_value}\n"
                detail_text += "\n"
        
        # 메타데이터 (있는 경우)
        if 'metadata' in trigger_data:
            metadata = trigger_data['metadata']
            detail_text += "📊 메타데이터:\n"
            
            for key, value in metadata.items():
                if key not in ['name', 'created_at', 'active', 'conditions', 'variable', 'operator', 'value']:
                    detail_text += f"  • {key}: {value}\n"
        
        return detail_text.strip()
    
    def copy_detail_to_clipboard(self):
        """상세정보를 클립보드에 복사"""
        try:
            from PyQt6.QtWidgets import QApplication
            clipboard = QApplication.clipboard()
            clipboard.setText(self.detail_text.toPlainText())
            print("📄 트리거 상세정보가 클립보드에 복사되었습니다.")
        except Exception as e:
            print(f"❌ 클립보드 복사 실패: {e}")
    
    def clear_detail(self):
        """상세정보 초기화"""
        self.detail_text.setPlainText("트리거를 선택하면 상세정보가 표시됩니다.")
        self.current_trigger = None
    
    def get_current_trigger(self):
        """현재 트리거 반환"""
        return self.current_trigger
    
    def has_trigger_selected(self) -> bool:
        """트리거가 선택되었는지 확인"""
        return self.current_trigger is not None
    
    # 스타일 정의 - integrated_condition_manager.py에서 정확히 복사
    def _get_original_group_style(self):
        """원본 get_groupbox_style("#6f42c1")와 동일"""
        return """
            QGroupBox {
                background-color: white;
                border: 1px solid #6f42c1;
                border-radius: 8px;
                font-weight: bold;
                padding-top: 15px;
                margin: 3px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
                background-color: white;
                color: #6f42c1;
                font-size: 12px;
            }
        """
    
    def _get_original_text_style(self):
        """원본 텍스트 에디터 스타일과 정확히 동일"""
        return """
            QTextEdit {
                border: 2px solid #ddd;
                border-radius: 8px;
                padding: 8px;
                font-size: 8px;
                background-color: white;
                font-family: 'Consolas', 'Monaco', monospace;
            }
        """


if __name__ == "__main__":
    # 테스트용 코드
    from PyQt6.QtWidgets import QApplication
    import sys
    
    app = QApplication(sys.argv)
    
    widget = TriggerDetailWidget()
    widget.show()
    
    # 테스트 트리거 설정
    test_trigger = {
        'name': 'RSI 과매수 테스트',
        'created_at': '2024-01-01 10:30:00',
        'active': True,
        'variable': 'rsi',
        'operator': '>',
        'value': '70',
        'external_variables': {
            'rsi_period': {'type': 'int', 'value': 14},
            'threshold': {'type': 'float', 'value': 70.0}
        },
        'metadata': {
            'description': 'RSI 70 초과 시 매도 신호',
            'category': 'technical_indicator'
        }
    }
    
    widget.update_trigger_detail(test_trigger)
    
    sys.exit(app.exec())
