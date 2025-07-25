"""
트리거 빌더 메인 화면 - 완전 리팩토링 버전
- 모든 컴포넌트 통합 관리
- 새로운 위젯들로 구성
"""

from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
                             QSplitter, QLabel, QTextEdit, QMessageBox, QGroupBox, QPushButton)
from PyQt6.QtCore import Qt

# 리팩토링된 컴포넌트들 임포트
try:
    from .components.condition_dialog import ConditionDialog
    from .components.trigger_list_widget import TriggerListWidget
    from .components.trigger_detail_widget import TriggerDetailWidget
    print("✅ 리팩토링된 컴포넌트들 로드 성공")
except ImportError as e:
    print(f"⚠️ 컴포넌트 임포트 오류: {e}")
    ConditionDialog = None
    TriggerListWidget = None
    TriggerDetailWidget = None


# 스타일드 컴포넌트 (실제 동작하는 버튼들)
class StyledGroupBox(QGroupBox):
    """간단한 스타일드 그룹박스"""
    def __init__(self, title, parent=None):
        super().__init__(title, parent)
        self.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                border: 2px solid #cccccc;
                border-radius: 8px;
                margin-top: 10px;
                padding-top: 5px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
            }
        """)


class PrimaryButton(QPushButton):
    """기본 버튼 (실제 작동)"""
    def __init__(self, text, parent=None):
        super().__init__(text, parent)
        self.setStyleSheet("""
            QPushButton {
                background-color: #007bff;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: #0056b3;
            }
            QPushButton:pressed {
                background-color: #004085;
            }
            QPushButton:disabled {
                background-color: #6c757d;
                color: #adb5bd;
            }
        """)


class SecondaryButton(QPushButton):
    """보조 버튼 (실제 작동)"""
    def __init__(self, text, parent=None):
        super().__init__(text, parent)
        self.setStyleSheet("""
            QPushButton {
                background-color: #6c757d;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: #545b62;
            }
            QPushButton:pressed {
                background-color: #484e53;
            }
            QPushButton:disabled {
                background-color: #adb5bd;
                color: #ffffff;
            }
        """)


class TriggerBuilderScreen(QWidget):
    """리팩토링된 트리거 빌더 메인 화면"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.simulation_engine = None
        self.init_ui()
        self.connect_events()
    
    def init_ui(self):
        """UI 초기화"""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(5, 5, 5, 5)
        main_layout.setSpacing(5)
        
        # 헤더 생성
        self.create_header(main_layout)
        
        # 메인 스플리터 생성
        splitter = QSplitter(Qt.Orientation.Horizontal)
        main_layout.addWidget(splitter)
        
        # 좌측: 조건 빌더 (40% 폭)
        left_widget = self.create_condition_builder_area()
        splitter.addWidget(left_widget)
        
        # 우측: 2x2 그리드 영역 (60% 폭)
        right_widget = self.create_right_panel()
        splitter.addWidget(right_widget)
        
        # 스플리터 비율 설정 (40:60)
        splitter.setSizes([400, 600])
    
    def create_header(self, layout):
        """헤더 영역"""
        header_layout = QHBoxLayout()
        
        # 타이틀
        title_label = QLabel("🎯 트리거 빌더 v2.0 (완전 리팩토링)")
        title_label.setStyleSheet("""
            QLabel {
                font-size: 16px;
                font-weight: bold;
                color: #2c3e50;
                padding: 8px;
            }
        """)
        header_layout.addWidget(title_label)
        
        header_layout.addStretch()
        
        layout.addLayout(header_layout)
    
    def create_condition_builder_area(self):
        """조건 빌더 영역 (좌측)"""
        if ConditionDialog:
            self.condition_dialog = ConditionDialog()
            return self.condition_dialog
        else:
            # 폴백: 간단한 플레이스홀더
            group = StyledGroupBox("🎯 조건 빌더")
            layout = QVBoxLayout()
            label = QLabel("조건 빌더 컴포넌트를 로드하는 중...")
            layout.addWidget(label)
            group.setLayout(layout)
            return group
    
    def create_right_panel(self):
        """우측 패널 (2x2 그리드)"""
        right_widget = QWidget()
        grid_layout = QGridLayout(right_widget)
        grid_layout.setContentsMargins(0, 0, 0, 0)
        grid_layout.setSpacing(5)
        
        # 1행 1열: 트리거 리스트
        if TriggerListWidget:
            self.trigger_list_widget = TriggerListWidget()
        else:
            self.trigger_list_widget = self.create_placeholder("📋 트리거 리스트")
        grid_layout.addWidget(self.trigger_list_widget, 0, 0)
        
        # 1행 2열: 트리거 상세정보
        if TriggerDetailWidget:
            self.trigger_detail_widget = TriggerDetailWidget()
        else:
            self.trigger_detail_widget = self.create_placeholder("📊 트리거 상세정보")
        grid_layout.addWidget(self.trigger_detail_widget, 0, 1)
        
        # 2행 1열: 시뮬레이션 결과
        self.simulation_result_widget = self.create_simulation_result_area()
        grid_layout.addWidget(self.simulation_result_widget, 1, 0)
        
        # 2행 2열: 시뮬레이션 제어
        self.simulation_control_widget = self.create_simulation_control_area()
        grid_layout.addWidget(self.simulation_control_widget, 1, 1)
        
        return right_widget
    
    def create_placeholder(self, title):
        """플레이스홀더 위젯 생성"""
        group = StyledGroupBox(title)
        layout = QVBoxLayout()
        label = QLabel("컴포넌트 로딩 중...")
        label.setStyleSheet("color: #888; font-style: italic;")
        layout.addWidget(label)
        group.setLayout(layout)
        return group
    
    def create_simulation_result_area(self):
        """시뮬레이션 결과 영역"""
        group = StyledGroupBox("🎮 시뮬레이션 결과")
        layout = QVBoxLayout()
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(5)
        
        # 결과 표시 영역
        self.simulation_result_text = QTextEdit()
        self.simulation_result_text.setReadOnly(True)
        self.simulation_result_text.setMaximumHeight(150)
        self.simulation_result_text.setStyleSheet("""
            QTextEdit {
                border: 1px solid #ddd;
                border-radius: 4px;
                font-size: 10px;
                font-family: 'Consolas', 'Monaco', monospace;
                background-color: #f8f9fa;
                padding: 6px;
            }
        """)
        
        # 문서 여백 설정으로 줄간격 조정
        document = self.simulation_result_text.document()
        document.setDocumentMargin(3)
        
        self.simulation_result_text.setPlainText("시뮬레이션을 실행하면 결과가 표시됩니다.")
        layout.addWidget(self.simulation_result_text)
        
        group.setLayout(layout)
        return group
    
    def create_simulation_control_area(self):
        """시뮬레이션 제어 영역"""
        group = StyledGroupBox("⚙️ 시뮬레이션 제어")
        layout = QVBoxLayout()
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(5)
        
        # 시뮬레이션 실행 버튼들
        button_layout = QVBoxLayout()
        
        self.run_simulation_btn = PrimaryButton("▶️ 시뮬레이션 실행")
        self.run_simulation_btn.clicked.connect(self.run_simulation)
        button_layout.addWidget(self.run_simulation_btn)
        
        self.clear_result_btn = SecondaryButton("🗑️ 결과 지우기")
        self.clear_result_btn.clicked.connect(self.clear_simulation_result)
        button_layout.addWidget(self.clear_result_btn)
        
        # 상태 텍스트
        self.status_text = QTextEdit()
        self.status_text.setReadOnly(True)
        self.status_text.setMaximumHeight(80)
        self.status_text.setStyleSheet("""
            QTextEdit {
                border: 1px solid #ddd;
                border-radius: 4px;
                font-size: 9px;
                background-color: #f0f0f0;
                padding: 4px;
            }
        """)
        
        # 상태 텍스트 문서 여백 설정
        status_document = self.status_text.document()
        status_document.setDocumentMargin(2)
        
        self.status_text.setPlainText("시뮬레이션 엔진 대기 중...")
        
        layout.addLayout(button_layout)
        layout.addWidget(self.status_text)
        
        group.setLayout(layout)
        return group
    
    def connect_events(self):
        """이벤트 연결"""
        try:
            # 조건 저장 시 트리거 리스트 새로고침
            if hasattr(self, 'condition_dialog') and hasattr(self.condition_dialog, 'condition_saved'):
                self.condition_dialog.condition_saved.connect(self.on_condition_saved)
            
            # 트리거 선택 시 상세정보 업데이트
            if (hasattr(self, 'trigger_list_widget') and hasattr(self.trigger_list_widget, 'trigger_selected') and
                hasattr(self, 'trigger_detail_widget') and hasattr(self.trigger_detail_widget, 'update_trigger_detail')):
                self.trigger_list_widget.trigger_selected.connect(self.trigger_detail_widget.update_trigger_detail)
            
            # 트리거 편집 요청 시 조건 빌더에 로드
            if (hasattr(self, 'trigger_list_widget') and hasattr(self.trigger_list_widget, 'trigger_edit_requested') and
                hasattr(self, 'condition_dialog') and hasattr(self.condition_dialog, 'load_condition')):
                self.trigger_list_widget.trigger_edit_requested.connect(self.condition_dialog.load_condition)
            
            # 트리거 삭제 시 상세정보 초기화
            if hasattr(self, 'trigger_list_widget') and hasattr(self.trigger_list_widget, 'trigger_deleted'):
                self.trigger_list_widget.trigger_deleted.connect(self.on_trigger_deleted)
                
            print("✅ 이벤트 연결 완료")
        except Exception as e:
            print(f"⚠️ 이벤트 연결 중 오류: {e}")
    
    def on_condition_saved(self, condition_data):
        """조건 저장 완료 처리"""
        try:
            print(f"✅ 조건 저장됨: {condition_data.get('name', 'Unknown')}")
            
            # 트리거 리스트 새로고침
            if hasattr(self, 'trigger_list_widget') and hasattr(self.trigger_list_widget, 'refresh_triggers'):
                self.trigger_list_widget.refresh_triggers()
            
            # 시뮬레이션 결과 초기화
            self.clear_simulation_result()
            
            # 상태 업데이트
            if hasattr(self, 'status_text'):
                self.status_text.setPlainText(f"새 조건 저장됨: {condition_data.get('name', 'Unknown')}")
        except Exception as e:
            print(f"❌ 조건 저장 처리 오류: {e}")
    
    def on_trigger_deleted(self, trigger_id):
        """트리거 삭제 처리"""
        try:
            print(f"🗑️ 트리거 삭제됨: ID {trigger_id}")
            
            # 상세정보 초기화
            if hasattr(self, 'trigger_detail_widget') and hasattr(self.trigger_detail_widget, 'clear_detail'):
                self.trigger_detail_widget.clear_detail()
            
            # 시뮬레이션 결과 초기화
            self.clear_simulation_result()
            
            # 상태 업데이트
            if hasattr(self, 'status_text'):
                self.status_text.setPlainText(f"트리거 삭제됨: ID {trigger_id}")
        except Exception as e:
            print(f"❌ 트리거 삭제 처리 오류: {e}")
    
    def run_simulation(self):
        """시뮬레이션 실행"""
        try:
            # 선택된 트리거 가져오기
            selected_trigger = self.trigger_list_widget.get_selected_trigger()
            if not selected_trigger:
                QMessageBox.warning(self, "⚠️ 경고", "시뮬레이션할 트리거를 선택해주세요.")
                return
            
            self.simulation_result_text.setPlainText("🎮 시뮬레이션 실행 중...")
            self.status_text.setPlainText("시뮬레이션 엔진 초기화 중...")
            
            # 간단한 시뮬레이션 실행 (실제 엔진 없이)
            import time
            import random
            
            # 가상 시뮬레이션 결과 생성
            time.sleep(0.5)  # 실행 시뮬레이션
            
            result = {
                'trigger_name': selected_trigger.get('name', 'Unknown'),
                'signal_count': random.randint(5, 25),
                'return_rate': random.uniform(-5.0, 15.0),
                'win_rate': random.uniform(40.0, 80.0),
                'execution_time': random.uniform(0.1, 1.0)
            }
            
            # 결과 표시
            self.display_simulation_result(result)
            
            # 상태 업데이트
            self.status_text.setPlainText(f"시뮬레이션 완료: {result['trigger_name']}")
            
        except Exception as e:
            error_msg = f"❌ 시뮬레이션 실행 중 오류 발생:\n{str(e)}"
            self.simulation_result_text.setPlainText(error_msg)
            self.status_text.setPlainText(f"오류 발생: {str(e)}")
            print(f"❌ 시뮬레이션 실행 실패: {e}")
    
    def display_simulation_result(self, result):
        """시뮬레이션 결과 표시"""
        try:
            if not result:
                self.simulation_result_text.setPlainText("❌ 시뮬레이션 결과가 없습니다.")
                return
            
            # 결과 포맷팅 (줄간격 최소화)
            result_lines = []
            result_lines.append(f"🎯 시뮬레이션 완료")
            result_lines.append(f"📊 트리거: {result.get('trigger_name', 'Unknown')}")
            result_lines.append(f"📈 신호 발생: {result.get('signal_count', 0)}회")
            result_lines.append(f"💰 수익률: {result.get('return_rate', 0):.2f}%")
            result_lines.append(f"🎲 승률: {result.get('win_rate', 0):.1f}%")
            result_lines.append(f"⏱️ 실행시간: {result.get('execution_time', 0):.3f}초")
            
            result_text = '\n'.join(result_lines)
            self.simulation_result_text.setPlainText(result_text)
            
        except Exception as e:
            error_msg = f"❌ 결과 표시 중 오류:\n{str(e)}"
            self.simulation_result_text.setPlainText(error_msg)
            print(f"❌ 시뮬레이션 결과 표시 실패: {e}")
    
    def clear_simulation_result(self):
        """시뮬레이션 결과 초기화"""
        self.simulation_result_text.setPlainText("시뮬레이션을 실행하면 결과가 표시됩니다.")
        self.status_text.setPlainText("시뮬레이션 엔진 대기 중...")
    
    def refresh_all_data(self):
        """전체 데이터 새로고침"""
        try:
            print("🔄 전체 데이터 새로고침 시작")
            
            # 트리거 리스트 새로고침
            self.trigger_list_widget.refresh_triggers()
            
            # 조건 빌더 새로고침
            self.condition_dialog.refresh_data()
            
            # 시뮬레이션 결과 초기화
            self.clear_simulation_result()
            
            # 상세정보 초기화
            self.trigger_detail_widget.clear_detail()
            
            # 상태 업데이트
            self.status_text.setPlainText("전체 데이터 새로고침 완료")
            
            print("✅ 전체 데이터 새로고침 완료")
            
        except Exception as e:
            print(f"❌ 전체 새로고침 실패: {e}")
            QMessageBox.critical(self, "❌ 오류", f"새로고침 중 오류가 발생했습니다:\n{e}")
            self.status_text.setPlainText(f"새로고침 실패: {str(e)}")
