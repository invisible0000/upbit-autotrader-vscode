"""
트리거 빌더 메인 화면
- 완전 리팩토링된 트리거 빌더
- 모든 컴포넌트 통합 관리
"""

from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
                            QSplitter, QLabel, QTextEdit, QMessageBox)
from PyQt6.QtCore import Qt, pyqtSignal
from upbit_auto_trading.ui.desktop.components.styled_components import (
    StyledGroupBox, PrimaryButton, SecondaryButton
)

# 리팩토링된 컴포넌트들 임포트
from .components.condition_dialog import ConditionDialog
from .components.trigger_list_widget import TriggerListWidget
from .components.trigger_detail_widget import TriggerDetailWidget
from .components.data_source_selector import DataSourceSelectorWidget
from .components.chart_visualizer import ChartVisualizerWidget

# 시뮬레이션 엔진들
from .components.simulation_engines.real_data_simulation import RealDataSimulationEngine
from .components.simulation_engines.embedded_simulation_engine import EmbeddedSimulationEngine


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
        
        # 우측: 3x2 그리드 영역 (60% 폭)
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
        
        # 전체 새로고침 버튼
        refresh_all_btn = PrimaryButton("🔄 전체 새로고침")
        refresh_all_btn.clicked.connect(self.refresh_all_data)
        header_layout.addWidget(refresh_all_btn)
        
        layout.addLayout(header_layout)
    
    def create_condition_builder_area(self):
        """조건 빌더 영역 (좌측)"""
        self.condition_dialog = ConditionDialog()
        return self.condition_dialog
    
    def create_right_panel(self):
        """우측 패널 (3x2 그리드)"""
        right_widget = QWidget()
        grid_layout = QGridLayout(right_widget)
        grid_layout.setContentsMargins(0, 0, 0, 0)
        grid_layout.setSpacing(5)
        
        # 1행 1열: 트리거 리스트
        self.trigger_list_widget = TriggerListWidget()
        grid_layout.addWidget(self.trigger_list_widget, 0, 0)
        
        # 1행 2열: 데이터 소스 선택
        self.data_source_widget = DataSourceSelectorWidget()
        grid_layout.addWidget(self.data_source_widget, 0, 1)
        
        # 2행 1열: 트리거 상세정보
        self.trigger_detail_widget = TriggerDetailWidget()
        grid_layout.addWidget(self.trigger_detail_widget, 1, 0)
        
        # 2행 2열: 시뮬레이션 결과
        self.simulation_result_widget = self.create_simulation_result_area()
        grid_layout.addWidget(self.simulation_result_widget, 1, 1)
        
        # 3행 전체: 차트 시각화 (2열 병합)
        self.chart_widget = ChartVisualizerWidget()
        grid_layout.addWidget(self.chart_widget, 2, 0, 1, 2)  # 2열 병합
        
        # 행 높이 설정 (1:1:2 비율)
        grid_layout.setRowStretch(0, 1)  # 트리거 리스트 & 데이터 소스
        grid_layout.setRowStretch(1, 1)  # 상세정보 & 시뮬레이션
        grid_layout.setRowStretch(2, 2)  # 차트 (더 높게)
        
        return right_widget
    
    def create_simulation_result_area(self):
        """시뮬레이션 결과 영역"""
        group = StyledGroupBox("🎮 시뮬레이션 결과")
        layout = QVBoxLayout()
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(5)
        
        # 시뮬레이션 실행 버튼들
        button_layout = QHBoxLayout()
        
        self.run_simulation_btn = PrimaryButton("▶️ 시뮬레이션 실행")
        self.run_simulation_btn.clicked.connect(self.run_simulation)
        button_layout.addWidget(self.run_simulation_btn)
        
        self.clear_result_btn = SecondaryButton("🗑️ 결과 지우기")
        self.clear_result_btn.clicked.connect(self.clear_simulation_result)
        button_layout.addWidget(self.clear_result_btn)
        
        layout.addLayout(button_layout)
        
        # 결과 표시 영역
        self.simulation_result_text = QTextEdit()
        self.simulation_result_text.setReadOnly(True)
        self.simulation_result_text.setMaximumHeight(120)
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
    
    def connect_events(self):
        """이벤트 연결"""
        # 조건 저장 시 트리거 리스트 새로고침
        self.condition_dialog.condition_saved.connect(self.on_condition_saved)
        
        # 트리거 선택 시 상세정보 업데이트
        self.trigger_list_widget.trigger_selected.connect(self.trigger_detail_widget.update_trigger_detail)
        
        # 트리거 편집 요청 시 조건 빌더에 로드
        self.trigger_list_widget.trigger_edit_requested.connect(self.condition_dialog.load_condition)
        
        # 트리거 삭제 시 상세정보 초기화
        self.trigger_list_widget.trigger_deleted.connect(self.on_trigger_deleted)
        
        # 데이터 소스 변경 시 차트 업데이트
        self.data_source_widget.data_source_changed.connect(self.on_data_source_changed)
    
    def on_condition_saved(self, condition_data):
        """조건 저장 완료 처리"""
        print(f"✅ 조건 저장됨: {condition_data.get('name', 'Unknown')}")
        
        # 트리거 리스트 새로고침
        self.trigger_list_widget.refresh_triggers()
        
        # 시뮬레이션 결과 초기화
        self.clear_simulation_result()
    
    def on_trigger_deleted(self, trigger_id):
        """트리거 삭제 처리"""
        print(f"🗑️ 트리거 삭제됨: ID {trigger_id}")
        
        # 상세정보 초기화
        self.trigger_detail_widget.clear_detail()
        
        # 시뮬레이션 결과 초기화
        self.clear_simulation_result()
    
    def on_data_source_changed(self, data_source_info):
        """데이터 소스 변경 처리"""
        print(f"📊 데이터 소스 변경: {data_source_info}")
        
        # 차트 업데이트
        self.chart_widget.update_data_source(data_source_info)
        
        # 시뮬레이션 결과 초기화
        self.clear_simulation_result()
    
    def run_simulation(self):
        """시뮬레이션 실행"""
        try:
            # 선택된 트리거 가져오기
            selected_trigger = self.trigger_list_widget.get_selected_trigger()
            if not selected_trigger:
                QMessageBox.warning(self, "⚠️ 경고", "시뮬레이션할 트리거를 선택해주세요.")
                return
            
            # 데이터 소스 정보 가져오기
            data_source_info = self.data_source_widget.get_current_data_source()
            
            self.simulation_result_text.setPlainText("🎮 시뮬레이션 실행 중...")
            
            # 시뮬레이션 엔진 초기화
            if not self.simulation_engine:
                try:
                    self.simulation_engine = RealDataSimulationEngine()
                    print("✅ 실제 데이터 시뮬레이션 엔진 로드")
                except Exception as e:
                    print(f"⚠️ 실제 데이터 엔진 로드 실패: {e}")
                    self.simulation_engine = EmbeddedSimulationEngine()
                    print("✅ 임베디드 시뮬레이션 엔진 로드")
            
            # 시뮬레이션 실행
            result = self.simulation_engine.run_simulation(selected_trigger, data_source_info)
            
            # 결과 표시
            self.display_simulation_result(result)
            
            # 차트 업데이트
            self.chart_widget.update_simulation_result(result)
            
        except Exception as e:
            error_msg = f"❌ 시뮬레이션 실행 중 오류 발생:\n{str(e)}"
            self.simulation_result_text.setPlainText(error_msg)
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
            
            # 추가 정보
            if result.get('details'):
                result_lines.append("")
                result_lines.append("📋 상세정보:")
                for detail in result.get('details', []):
                    result_lines.append(f"  • {detail}")
            
            result_text = '\n'.join(result_lines)
            self.simulation_result_text.setPlainText(result_text)
            
        except Exception as e:
            error_msg = f"❌ 결과 표시 중 오류:\n{str(e)}"
            self.simulation_result_text.setPlainText(error_msg)
            print(f"❌ 시뮬레이션 결과 표시 실패: {e}")
    
    def clear_simulation_result(self):
        """시뮬레이션 결과 초기화"""
        self.simulation_result_text.setPlainText("시뮬레이션을 실행하면 결과가 표시됩니다.")
    
    def refresh_all_data(self):
        """전체 데이터 새로고침"""
        try:
            print("🔄 전체 데이터 새로고침 시작")
            
            # 트리거 리스트 새로고침
            self.trigger_list_widget.refresh_triggers()
            
            # 조건 빌더 새로고침
            self.condition_dialog.refresh_data()
            
            # 데이터 소스 새로고침
            self.data_source_widget.refresh_data()
            
            # 차트 초기화
            self.chart_widget.clear_chart()
            
            # 시뮬레이션 결과 초기화
            self.clear_simulation_result()
            
            # 상세정보 초기화
            self.trigger_detail_widget.clear_detail()
            
            print("✅ 전체 데이터 새로고침 완료")
            
        except Exception as e:
            print(f"❌ 전체 새로고침 실패: {e}")
            QMessageBox.critical(self, "❌ 오류", f"새로고침 중 오류가 발생했습니다:\n{e}")
    
    def get_style_definitions(self):
        """스타일 정의"""
        return {
            'primary_color': '#3498db',
            'secondary_color': '#95a5a6',
            'success_color': '#27ae60',
            'warning_color': '#f39c12',
            'danger_color': '#e74c3c'
        }
