"""
Trigger Builder Screen
트리거 생성 및 관리를 위한 메인 UI 화면
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QGroupBox,
    QPushButton, QLabel, QMessageBox, QTreeWidget, QTreeWidgetItem,
    QTextEdit, QSplitter, QFrame, QListWidget, QListWidgetItem,
    QProgressBar, QLineEdit, QComboBox
)
from PyQt6.QtCore import Qt, pyqtSignal, QTimer
from PyQt6.QtGui import QFont, QIcon

# 컴포넌트 import
from .components.chart_visualizer import ChartVisualizer
from .components.data_generators import DataGenerators
from .components.trigger_calculator import TriggerCalculator

# 조건 다이얼로그 import
try:
    from ..components.condition_dialog import ConditionDialog
except ImportError:
    print("⚠️ ConditionDialog import 실패, 폴백 사용")
    ConditionDialog = None


class TriggerBuilderScreen(QWidget):
    """트리거 빌더 메인 화면"""
    
    # 시그널 정의
    condition_tested = pyqtSignal(dict, bool)
    trigger_selected = pyqtSignal(dict)
    
    def __init__(self, parent=None):
        """초기화"""
        super().__init__(parent)
        
        # 컴포넌트 초기화
        self.chart_visualizer = ChartVisualizer()
        self.data_generators = DataGenerators()
        self.trigger_calculator = TriggerCalculator()
        
        # 상태 변수
        self.selected_condition = None
        self.current_simulation_data = None
        self.current_trigger_results = None
        
        self.init_ui()
    
    def init_ui(self):
        """UI 초기화"""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(5, 5, 5, 5)
        main_layout.setSpacing(5)
        
        # 헤더 생성
        self.create_header(main_layout)
        
        # 메인 3x2 그리드 생성
        splitter = QSplitter(Qt.Orientation.Horizontal)
        main_layout.addWidget(splitter)
        
        # 좌측: 조건 빌더 (세로로 길게)
        left_widget = self.create_condition_builder_area()
        splitter.addWidget(left_widget)
        
        # 우측: 2x2 그리드 영역
        right_widget = QWidget()
        right_layout = QGridLayout(right_widget)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(5)
        
        # 우측 상단: 트리거 리스트
        right_layout.addWidget(self.create_trigger_list_area(), 0, 0)
        
        # 우측 중간: 시뮬레이션 영역
        right_layout.addWidget(self.create_simulation_area(), 0, 1)
        
        # 우측 하단 왼쪽: 트리거 상세
        right_layout.addWidget(self.create_trigger_detail_area(), 1, 0)
        
        # 우측 하단 오른쪽: 테스트 결과
        right_layout.addWidget(self.create_test_result_area(), 1, 1)
        
        splitter.addWidget(right_widget)
        
        # 분할 비율 설정 (1:2)
        splitter.setSizes([400, 800])
        
        # 초기 데이터 로드
        self.load_trigger_list()
        
        print("✅ 트리거 빌더 화면 초기화 완료")
    
    def create_header(self, layout):
        """헤더 생성"""
        header_widget = QFrame()
        header_widget.setFixedHeight(60)
        header_widget.setStyleSheet("""
            QFrame {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #667eea, stop:1 #764ba2);
                border-radius: 8px;
                margin: 2px;
            }
        """)
        
        header_layout = QHBoxLayout(header_widget)
        header_layout.setContentsMargins(15, 10, 15, 10)
        
        # 제목
        title_label = QLabel("🎯 트리거 빌더")
        title_label.setFont(QFont("Arial", 16, QFont.Weight.Bold))
        title_label.setStyleSheet("color: white;")
        header_layout.addWidget(title_label)
        
        # 부제목
        subtitle_label = QLabel("조건 생성 • 시뮬레이션 • 트리거 관리")
        subtitle_label.setFont(QFont("Arial", 10))
        subtitle_label.setStyleSheet("color: #f0f0f0; margin-left: 10px;")
        header_layout.addWidget(subtitle_label)
        
        header_layout.addStretch()
        
        # 새로고침 버튼
        refresh_btn = QPushButton("🔄 새로고침")
        refresh_btn.setStyleSheet(self.get_white_button_style())
        refresh_btn.clicked.connect(self.refresh_all)
        header_layout.addWidget(refresh_btn)
        
        layout.addWidget(header_widget)
    
    def create_condition_builder_area(self):
        """조건 빌더 영역"""
        group = QGroupBox("🎯 조건 빌더")
        group.setStyleSheet(self.get_groupbox_style("#2c3e50"))
        layout = QVBoxLayout(group)
        layout.setContentsMargins(8, 8, 8, 8)
        
        try:
            if ConditionDialog:
                # 조건 다이얼로그를 위젯으로 임베드
                self.condition_dialog = ConditionDialog()
                self.condition_dialog.setParent(group)
                
                # 다이얼로그를 위젯으로 변환
                self.condition_dialog.setWindowFlags(Qt.WindowType.Widget)
                
                # 시그널 연결
                self.condition_dialog.condition_saved.connect(self.on_condition_saved)
                
                layout.addWidget(self.condition_dialog)
            else:
                # 폴백 UI
                error_label = QLabel("조건 빌더를 사용할 수 없습니다")
                error_label.setStyleSheet("color: #e74c3c; padding: 20px; font-size: 12px;")
                layout.addWidget(error_label)
            
        except Exception as e:
            print(f"❌ 조건 빌더 로딩 실패: {e}")
            error_label = QLabel(f"조건 빌더 로딩 실패: {e}")
            error_label.setStyleSheet("color: #e74c3c; padding: 20px; font-size: 12px;")
            layout.addWidget(error_label)
        
        return group
    
    def create_trigger_list_area(self):
        """트리거 리스트 영역"""
        group = QGroupBox("📋 등록된 트리거 리스트")
        group.setStyleSheet(self.get_groupbox_style("#27ae60"))
        layout = QVBoxLayout(group)
        layout.setContentsMargins(8, 8, 8, 8)
        
        # 검색 입력
        self.search_input = self.create_search_input()
        layout.addWidget(self.search_input)
        
        # 트리거 트리
        self.trigger_tree = QTreeWidget()
        self.trigger_tree.setHeaderLabels(["트리거", "조건", "상태"])
        self.trigger_tree.setStyleSheet("""
            QTreeWidget {
                border: 1px solid #ddd;
                border-radius: 4px;
                font-size: 11px;
            }
            QTreeWidget::item {
                padding: 4px;
                border-bottom: 1px solid #f0f0f0;
            }
            QTreeWidget::item:selected {
                background-color: #e3f2fd;
                color: #1976d2;
            }
        """)
        self.trigger_tree.itemClicked.connect(self.on_trigger_selected)
        layout.addWidget(self.trigger_tree)
        
        # 버튼 영역
        button_layout = QHBoxLayout()
        
        edit_btn = QPushButton("✏️ 편집")
        edit_btn.setStyleSheet(self.get_small_button_style("#f39c12"))
        edit_btn.clicked.connect(self.edit_selected_trigger)
        button_layout.addWidget(edit_btn)
        
        delete_btn = QPushButton("🗑️ 삭제")
        delete_btn.setStyleSheet(self.get_small_button_style("#e74c3c"))
        delete_btn.clicked.connect(self.delete_selected_trigger)
        button_layout.addWidget(delete_btn)
        
        test_btn = QPushButton("⚡ 테스트")
        test_btn.setStyleSheet(self.get_small_button_style("#3498db"))
        test_btn.clicked.connect(self.quick_test_trigger)
        button_layout.addWidget(test_btn)
        
        layout.addLayout(button_layout)
        
        return group
    
    def create_simulation_area(self):
        """시뮬레이션 영역"""
        group = QGroupBox("🧪 미니 시뮬레이션")
        group.setStyleSheet(self.get_groupbox_style("#8e44ad"))
        layout = QVBoxLayout(group)
        layout.setContentsMargins(8, 8, 8, 8)
        
        # 시나리오 선택
        scenario_layout = QHBoxLayout()
        scenario_layout.addWidget(QLabel("시나리오:"))
        
        self.scenario_combo = QComboBox()
        self.scenario_combo.addItems([
            "상승 추세", "하락 추세", "급등", "급락", 
            "횡보", "이동평균 교차"
        ])
        self.scenario_combo.currentTextChanged.connect(self.on_scenario_changed)
        scenario_layout.addWidget(self.scenario_combo)
        
        layout.addLayout(scenario_layout)
        
        # 차트 영역
        chart_widget = self.chart_visualizer.create_chart_widget()
        layout.addWidget(chart_widget)
        
        # 실행 버튼
        run_btn = QPushButton("🚀 시뮬레이션 실행")
        run_btn.setStyleSheet(self.get_white_button_style())
        run_btn.clicked.connect(self.run_simulation)
        layout.addWidget(run_btn)
        
        return group
    
    def create_trigger_detail_area(self):
        """트리거 상세 영역"""
        group = QGroupBox("📊 트리거 상세정보")
        group.setStyleSheet(self.get_groupbox_style("#34495e"))
        layout = QVBoxLayout(group)
        layout.setContentsMargins(8, 8, 8, 8)
        
        self.detail_text = QTextEdit()
        self.detail_text.setStyleSheet("""
            QTextEdit {
                border: 1px solid #ddd;
                border-radius: 4px;
                font-size: 11px;
                font-family: 'Consolas', 'Monaco', monospace;
                background-color: #f8f9fa;
            }
        """)
        self.detail_text.setMaximumHeight(120)
        self.detail_text.setPlainText("트리거를 선택하면 상세정보가 표시됩니다.")
        layout.addWidget(self.detail_text)
        
        return group
    
    def create_test_result_area(self):
        """테스트 결과 영역"""
        group = QGroupBox("📈 테스트 결과")
        group.setStyleSheet(self.get_groupbox_style("#16a085"))
        layout = QVBoxLayout(group)
        layout.setContentsMargins(8, 8, 8, 8)
        
        # 결과 히스토리
        self.result_list = QListWidget()
        self.result_list.setStyleSheet("""
            QListWidget {
                border: 1px solid #ddd;
                border-radius: 4px;
                font-size: 10px;
                background-color: #f8f9fa;
            }
        """)
        self.result_list.setMaximumHeight(80)
        layout.addWidget(self.result_list)
        
        # 통계 정보
        self.stats_label = QLabel("통계: 대기 중...")
        self.stats_label.setStyleSheet("font-size: 10px; color: #666; padding: 4px;")
        layout.addWidget(self.stats_label)
        
        return group
    
    def create_search_input(self):
        """검색 입력 생성"""
        search_input = QLineEdit()
        search_input.setPlaceholderText("🔍 트리거 검색...")
        search_input.setStyleSheet("""
            QLineEdit {
                border: 2px solid #ddd;
                border-radius: 6px;
                padding: 8px 12px;
                font-size: 12px;
                background-color: white;
            }
            QLineEdit:focus {
                border-color: #007bff;
                background-color: #f8f9fa;
            }
            QLineEdit:hover {
                border-color: #adb5bd;
            }
        """)
        search_input.textChanged.connect(self.filter_triggers)
        return search_input
    
    def get_groupbox_style(self, color):
        """그룹박스 스타일 생성"""
        return f"""
            QGroupBox {{
                font-weight: bold;
                border: 2px solid #ddd;
                border-radius: 8px;
                margin: 2px;
                padding-top: 12px;
                background-color: white;
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                left: 15px;
                padding: 0 8px 0 8px;
                background-color: white;
                color: {color};
                font-size: 11px;
                font-weight: bold;
                border-radius: 4px;
                border: 1px solid {color};
            }}
        """
    
    def get_white_button_style(self):
        """흰색 버튼 스타일"""
        return """
            QPushButton {
                background-color: white;
                border: 2px solid #007bff;
                border-radius: 6px;
                color: #007bff;
                font-weight: bold;
                padding: 8px 16px;
                font-size: 11px;
            }
            QPushButton:hover {
                background-color: #007bff;
                color: white;
            }
            QPushButton:pressed {
                background-color: #0056b3;
            }
        """
    
    def get_small_button_style(self, color):
        """작은 버튼 스타일"""
        return f"""
            QPushButton {{
                background-color: {color};
                border: none;
                border-radius: 4px;
                color: white;
                font-weight: bold;
                padding: 6px 12px;
                font-size: 10px;
            }}
            QPushButton:hover {{
                background-color: {color}dd;
            }}
            QPushButton:pressed {{
                background-color: {color}aa;
            }}
        """
    
    def load_trigger_list(self):
        """트리거 리스트 로드"""
        # TODO: 실제 데이터베이스에서 로드
        print("📋 트리거 리스트 로드 중...")
        pass
    
    def on_condition_saved(self, condition_data):
        """조건 저장 이벤트 처리"""
        print(f"✅ 조건 저장됨: {condition_data}")
        self.load_trigger_list()
    
    def on_trigger_selected(self, item, column):
        """트리거 선택 이벤트 처리"""
        if item:
            print(f"🎯 트리거 선택됨: {item.text(0)}")
            # TODO: 트리거 상세정보 표시
    
    def on_scenario_changed(self, scenario):
        """시나리오 변경 이벤트 처리"""
        print(f"📊 시나리오 변경: {scenario}")
    
    def filter_triggers(self, text):
        """트리거 필터링"""
        # TODO: 실제 필터링 로직
        print(f"🔍 트리거 검색: {text}")
    
    def edit_selected_trigger(self):
        """선택된 트리거 편집"""
        print("✏️ 트리거 편집")
    
    def delete_selected_trigger(self):
        """선택된 트리거 삭제"""
        print("🗑️ 트리거 삭제")
    
    def quick_test_trigger(self):
        """빠른 트리거 테스트"""
        print("⚡ 트리거 테스트")
    
    def run_simulation(self):
        """시뮬레이션 실행"""
        scenario = self.scenario_combo.currentText()
        print(f"🚀 시뮬레이션 실행: {scenario}")
        
        # TODO: 실제 시뮬레이션 로직
        # 현재는 샘플 데이터로 차트 업데이트
        self.chart_visualizer.update_chart_with_sample_data()
    
    def refresh_all(self):
        """전체 새로고침"""
        print("🔄 전체 새로고침")
        self.load_trigger_list()
        self.chart_visualizer.update_chart_with_sample_data()
