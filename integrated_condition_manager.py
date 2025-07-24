"""
통합 조건 관리 화면 - 3x2 그리드 레이아웃
조건 빌더 + 트리거 관리 + 미니 테스트 통합 시스템
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QGroupBox,
    QPushButton, QLabel, QMessageBox, QTreeWidget, QTreeWidgetItem,
    QTextEdit, QSplitter, QFrame, QListWidget, QListWidgetItem,
    QProgressBar, QLineEdit, QComboBox
)
from PyQt6.QtCore import Qt, pyqtSignal, QTimer, QThread, pyqtSlot
from PyQt6.QtGui import QFont, QPixmap, QIcon

# 우리의 컴포넌트 시스템 import
import sys
import os
sys.path.append(os.path.dirname(__file__))
from components.condition_dialog import ConditionDialog
from components.condition_storage import ConditionStorage
from components.condition_loader import ConditionLoader

# 시뮬레이션 시스템 import
try:
    from enhanced_real_data_simulation_engine import EnhancedRealDataSimulationEngine as RealDataSimulationEngine
    from extended_data_scenario_mapper import ExtendedDataScenarioMapper
    print("✅ 시뮬레이션 엔진 로드 성공")
except ImportError as e:
    print(f"⚠️ 시뮬레이션 엔진을 찾을 수 없습니다: {e}")
    RealDataSimulationEngine = None
    ExtendedDataScenarioMapper = None

# 차트 라이브러리 import
try:
    import matplotlib.pyplot as plt
    from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
    from matplotlib.figure import Figure
    import numpy as np
    import pandas as pd
    from datetime import datetime, timedelta
    print("✅ 차트 라이브러리 로드 성공")
    CHART_AVAILABLE = True
except ImportError as e:
    print(f"⚠️ 차트 라이브러리를 찾을 수 없습니다: {e}")
    CHART_AVAILABLE = False

# 기존 UI 컴포넌트 임포트 (스타일 통일을 위해)
try:
    from upbit_auto_trading.ui.desktop.common.components import (
        CardWidget, StyledTableWidget, PrimaryButton, SecondaryButton, 
        StyledLineEdit, StyledComboBox
    )
except ImportError:
    # 컴포넌트가 없을 경우 기본 위젯 사용
    CardWidget = QGroupBox
    StyledTableWidget = QTreeWidget
    PrimaryButton = QPushButton
    SecondaryButton = QPushButton
    StyledLineEdit = QLineEdit
    StyledComboBox = QComboBox

class MiniChartWidget(QWidget):
    """미니 차트 위젯 - 시뮬레이션 결과 시각화"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumSize(300, 200)
        self.init_ui()
        
        # 차트 데이터
        self.price_data = []
        self.trigger_points = []
        self.current_scenario = ""
        
    def init_ui(self):
        """UI 초기화"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        
        if CHART_AVAILABLE:
            # matplotlib 차트 생성
            self.figure = Figure(figsize=(4, 2.5), dpi=80)
            self.canvas = FigureCanvas(self.figure)
            self.canvas.setParent(self)
            
            # 축 설정
            self.ax = self.figure.add_subplot(111)
            self.ax.set_title("시뮬레이션 결과", fontsize=10, pad=5)
            self.ax.tick_params(axis='both', which='major', labelsize=8)
            
            # 여백 조정
            self.figure.tight_layout(pad=1.0)
            
            layout.addWidget(self.canvas)
            
            # 초기 차트 표시
            self.show_placeholder_chart()
        else:
            # matplotlib이 없을 경우 플레이스홀더
            placeholder = QLabel("📊 차트 로딩 실패\n(matplotlib 필요)")
            placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)
            placeholder.setStyleSheet("""
                border: 2px dashed #ccc;
                border-radius: 8px;
                padding: 20px;
                color: #666;
            """)
            layout.addWidget(placeholder)
    
    def show_placeholder_chart(self):
        """플레이스홀더 차트 표시"""
        if not CHART_AVAILABLE:
            return
            
        self.ax.clear()
        self.ax.text(0.5, 0.5, '📈 시뮬레이션을 실행하세요', 
                    ha='center', va='center', transform=self.ax.transAxes,
                    fontsize=10, color='gray')
        self.ax.set_xlim(0, 1)
        self.ax.set_ylim(0, 1)
        self.ax.set_xticks([])
        self.ax.set_yticks([])
        self.canvas.draw()
    
    def update_simulation_chart(self, scenario: str, price_data: list, trigger_results: list = None):
        """시뮬레이션 결과를 차트에 표시"""
        if not CHART_AVAILABLE or not price_data:
            return
            
        try:
            self.ax.clear()
            
            # 가격 데이터 플롯
            x_data = list(range(len(price_data)))
            self.ax.plot(x_data, price_data, 'b-', linewidth=1.5, alpha=0.8, label='가격')
            
            # 트리거 포인트 표시
            if trigger_results:
                trigger_x = []
                trigger_y = []
                trigger_colors = []
                
                for i, (triggered, value) in enumerate(trigger_results):
                    if triggered and i < len(price_data):
                        trigger_x.append(i)
                        trigger_y.append(price_data[i])
                        trigger_colors.append('red' if 'sell' in scenario.lower() or '매도' in scenario else 'green')
                
                if trigger_x:
                    self.ax.scatter(trigger_x, trigger_y, c=trigger_colors, 
                                  s=50, alpha=0.8, zorder=5, 
                                  label=f'트리거 발동 ({len(trigger_x)}회)')
            
            # 차트 스타일링
            self.ax.set_title(f"📊 {scenario} 시뮬레이션", fontsize=10, pad=5)
            self.ax.set_xlabel("시간", fontsize=8)
            self.ax.set_ylabel("가격", fontsize=8)
            self.ax.tick_params(axis='both', which='major', labelsize=7)
            self.ax.grid(True, alpha=0.3)
            
            # 범례 추가 (작게)
            if trigger_results and any(t[0] for t in trigger_results):
                self.ax.legend(fontsize=7, loc='upper right')
            
            # 여백 조정
            self.figure.tight_layout(pad=1.0)
            
            # 차트 업데이트
            self.canvas.draw()
            
            print(f"✅ 미니 차트 업데이트 완료: {scenario}")
            
        except Exception as e:
            print(f"❌ 차트 업데이트 실패: {e}")
            self.show_error_chart(str(e))
    
    def show_error_chart(self, error_msg: str):
        """에러 차트 표시"""
        if not CHART_AVAILABLE:
            return
            
        self.ax.clear()
        self.ax.text(0.5, 0.5, f'❌ 차트 오류\n{error_msg}', 
                    ha='center', va='center', transform=self.ax.transAxes,
                    fontsize=9, color='red')
        self.ax.set_xlim(0, 1)
        self.ax.set_ylim(0, 1)
        self.ax.set_xticks([])
        self.ax.set_yticks([])
        self.canvas.draw()

class SimulationWorker(QThread):
    """시뮬레이션 실행을 위한 워커 스레드"""
    
    # 시그널 정의
    progress_updated = pyqtSignal(str)  # 진행 상황 메시지
    simulation_completed = pyqtSignal(dict)  # 시뮬레이션 결과
    simulation_error = pyqtSignal(str)  # 에러 메시지
    
    def __init__(self, scenario: str, trigger_data = None):
        super().__init__()
        self.scenario = scenario
        self.trigger_data = trigger_data
        
    def run(self):
        """시뮬레이션 실행"""
        try:
            self.progress_updated.emit(f"🚀 {self.scenario} 시뮬레이션 시작...")
            
            # 시뮬레이션 엔진 체크
            if RealDataSimulationEngine is None:
                self.simulation_error.emit("❌ 시뮬레이션 엔진을 찾을 수 없습니다.")
                return
            
            # 시뮬레이션 엔진 생성
            engine = RealDataSimulationEngine()
            
            # 시나리오 매핑
            self.progress_updated.emit(f"📊 {self.scenario} 데이터 준비 중...")
            
            # 시뮬레이션 데이터 준비
            session_id = engine.prepare_enhanced_simulation_data(self.scenario, 0)
            if not session_id:
                self.simulation_error.emit(f"❌ {self.scenario} 시나리오 데이터를 찾을 수 없습니다.")
                return
            
            self.progress_updated.emit(f"⚡ {self.scenario} 시뮬레이션 실행 중...")
            
            # 시뮬레이션 실행 - 올바른 메서드 사용
            result = engine.run_enhanced_simulation(session_id)
            
            if result and 'error' not in result:
                self.progress_updated.emit(f"✅ {self.scenario} 시뮬레이션 완료!")
                # 시나리오 정보를 결과에 추가
                result['scenario'] = self.scenario
                result['session_id'] = session_id
                self.simulation_completed.emit(result)
            else:
                error_msg = result.get('error', '알 수 없는 오류') if result else '시뮬레이션 실패'
                self.simulation_error.emit(f"❌ {self.scenario} 시뮬레이션 실패: {error_msg}")
                
        except Exception as e:
            self.simulation_error.emit(f"❌ 시뮬레이션 오류: {str(e)}")
            print(f"시뮬레이션 디버그 오류: {e}")  # 디버깅용

class IntegratedConditionManager(QWidget):
    """통합 조건 관리 화면 - 3x2 그리드 레이아웃"""
    
    # 시그널 정의
    condition_tested = pyqtSignal(dict, bool)  # 조건, 테스트 결과
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("🎯 통합 조건 관리 시스템")
        # 크기를 대폭 줄여서 1600x1000 화면에 맞춤
        self.setMinimumSize(800, 500)
        
        # 컴포넌트 초기화
        self.storage = ConditionStorage()
        self.loader = ConditionLoader(self.storage)
        self.selected_condition = None
        
        # 시뮬레이션 관련 초기화
        self.simulation_worker = None
        self.simulation_results = {}
        
        self.init_ui()
        self.load_trigger_list()
    
    def init_ui(self):
        """UI 초기화 - 3x2 그리드 레이아웃"""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(5, 5, 5, 5)  # 마진 줄이기
        main_layout.setSpacing(5)  # 간격 줄이기
        
        # 상단 제목 제거하여 공간 절약
        # self.create_header(main_layout)
        
        # 메인 그리드 레이아웃 (3x2)
        grid_widget = QWidget()
        grid_layout = QGridLayout(grid_widget)
        grid_layout.setContentsMargins(2, 2, 2, 2)  # 그리드 마진 줄이기
        grid_layout.setSpacing(5)  # 그리드 간격 줄이기
        
        # 1+4: 조건 빌더 (좌측, 세로 합쳐짐)
        self.condition_builder_area = self.create_condition_builder_area()
        grid_layout.addWidget(self.condition_builder_area, 0, 0, 2, 1)  # 2행에 걸쳐 배치
        
        # 2: 등록된 트리거 리스트 (중앙 상단)
        self.trigger_list_area = self.create_trigger_list_area()
        grid_layout.addWidget(self.trigger_list_area, 0, 1, 1, 1)
        
        # 3: 케이스 시뮬레이션 버튼들 (우측 상단)
        self.simulation_area = self.create_simulation_area()
        grid_layout.addWidget(self.simulation_area, 0, 2, 1, 1)
        
        # 5: 선택한 트리거 상세 정보 (중앙 하단)
        self.trigger_detail_area = self.create_trigger_detail_area()
        grid_layout.addWidget(self.trigger_detail_area, 1, 1, 1, 1)
        
        # 6: 작동 마커 차트 + 작동 기록 (우측 하단)
        self.test_result_area = self.create_test_result_area()
        grid_layout.addWidget(self.test_result_area, 1, 2, 1, 1)
        
        # 그리드 비율 설정 - 두 번째 첨부 이미지와 유사하게 (1:2:1)
        grid_layout.setColumnStretch(0, 1)  # 조건 빌더 (좁게)
        grid_layout.setColumnStretch(1, 2)  # 트리거 관리 (넓게)
        grid_layout.setColumnStretch(2, 1)  # 시뮬레이션 (좁게)
        
        # 행 비율 설정 (상단 좀 더 크게)
        grid_layout.setRowStretch(0, 3)  # 상단
        grid_layout.setRowStretch(1, 2)  # 하단
        
        main_layout.addWidget(grid_widget)
        
        print("✅ 통합 조건 관리 시스템 UI 초기화 완료")
    
    def create_header(self, layout):
        """상단 헤더 생성 - 기존 대시보드 스타일"""
        header_widget = QWidget()
        header_widget.setStyleSheet("""
            QWidget {
                background-color: #3498db;
                border-radius: 6px;
                padding: 8px;  /* 패딩 줄이기 */
                margin: 2px;   /* 마진 줄이기 */
            }
        """)
        header_layout = QHBoxLayout(header_widget)
        header_layout.setContentsMargins(5, 5, 5, 5)  # 헤더 마진 줄이기
        
        # 제목
        title_label = QLabel("🎯 통합 조건 관리 시스템")
        title_label.setStyleSheet("""
            font-size: 14px;  /* 폰트 크기 줄이기 */
            font-weight: bold; 
            color: white;
            background: transparent;
        """)
        header_layout.addWidget(title_label)
        
        # 부제목 - 공간 절약을 위해 제거하거나 축소
        # subtitle_label = QLabel("조건 생성 → 트리거 관리 → 미니 테스트 통합 워크플로우")
        # subtitle_label.setStyleSheet("""
        #     font-size: 11px; 
        #     color: #ecf0f1;
        #     background: transparent;
        #     margin-left: 20px;
        # """)
        # header_layout.addWidget(subtitle_label)
        
        header_layout.addStretch()
        
        # 전체 새로고침 버튼 - 기존 스타일 적용
        refresh_btn = PrimaryButton("🔄 전체 새로고침")
        refresh_btn.setStyleSheet("""
            QPushButton {
                background-color: white;
                color: #3498db;
                border: 1px solid white;
                border-radius: 4px;
                padding: 6px 12px;
                font-weight: bold;
                font-size: 11px;
            }
            QPushButton:hover {
                background-color: #ecf0f1;
            }
            QPushButton:pressed {
                background-color: #d5dbdb;
            }
        """)
        refresh_btn.clicked.connect(self.refresh_all)
        header_layout.addWidget(refresh_btn)
        
        layout.addWidget(header_widget)
    
    def create_condition_builder_area(self):
        """영역 1+4: 조건 빌더 (좌측 통합) - CardWidget 스타일"""
        group = QGroupBox("🎯 조건 빌더")
        group.setStyleSheet("""
            QGroupBox {
                background-color: white;
                border: 1px solid #e0e0e0;
                border-radius: 6px;
                font-weight: bold;
                padding-top: 15px;
                margin: 3px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
                background-color: white;
                color: #333333;
                font-size: 12px;
            }
        """)
        layout = QVBoxLayout(group)
        layout.setContentsMargins(15, 15, 15, 15)
        
        try:
            # 우리의 조건 다이얼로그를 위젯으로 임베드
            self.condition_dialog = ConditionDialog()
            self.condition_dialog.setParent(group)
            
            # 다이얼로그를 위젯으로 변환 (창 모드 해제)
            self.condition_dialog.setWindowFlags(Qt.WindowType.Widget)
            
            # 시그널 연결
            self.condition_dialog.condition_saved.connect(self.on_condition_saved)
            
            layout.addWidget(self.condition_dialog)
            
        except Exception as e:
            print(f"❌ 조건 빌더 로딩 실패: {e}")
            
            # 대체 위젯
            error_label = QLabel(f"조건 빌더 로딩 실패: {e}")
            error_label.setStyleSheet("color: #e74c3c; padding: 20px; font-size: 12px;")
            layout.addWidget(error_label)
        
        return group
    
    def create_trigger_list_area(self):
        """영역 2: 등록된 트리거 리스트 (중앙 상단) - 대시보드 스타일"""
        group = QGroupBox("📋 등록된 트리거 리스트")
        group.setStyleSheet("""
            QGroupBox {
                background-color: white;
                border: 1px solid #e0e0e0;
                border-radius: 6px;
                font-weight: bold;
                padding-top: 15px;
                margin: 3px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
                background-color: white;
                color: #333333;
                font-size: 12px;
            }
        """)
        layout = QVBoxLayout(group)
        layout.setContentsMargins(15, 15, 15, 15)
        
        # 트리거 검색
        search_layout = QHBoxLayout()
        search_label = QLabel("🔍")
        search_layout.addWidget(search_label)
        
        self.search_input = StyledLineEdit()
        self.search_input.setPlaceholderText("트리거 검색...")
        search_layout.addWidget(self.search_input)
        layout.addLayout(search_layout)
        
        # 트리거 트리 위젯 - 대시보드 테이블 스타일
        self.trigger_tree = QTreeWidget()
        self.trigger_tree.setHeaderLabels(["트리거명", "변수", "조건", "카테고리"])
        self.trigger_tree.setStyleSheet("""
            QTreeWidget {
                border: 1px solid #cccccc;
                gridline-color: #e0e0e0;
                background-color: white;
                border-radius: 4px;
            }
            QTreeWidget::item {
                padding: 6px;
                border-bottom: 1px solid #f0f0f0;
            }
            QTreeWidget::item:selected {
                background-color: #3498db;
                color: white;
            }
            QHeaderView::section {
                background-color: #f0f0f0;
                padding: 6px;
                border: 1px solid #cccccc;
                font-weight: bold;
                font-size: 11px;
            }
        """)
        
        # 트리거 선택 시그널 연결
        self.trigger_tree.itemClicked.connect(self.on_trigger_selected)
        self.search_input.textChanged.connect(self.filter_triggers)
        
        layout.addWidget(self.trigger_tree)
        
        # 하단 버튼들 - 대시보드 버튼 스타일
        button_layout = QHBoxLayout()
        
        # 저장 버튼 추가 (조건 빌더에서 이동)
        save_btn = QPushButton("💾 저장")
        save_btn.setStyleSheet("""
            QPushButton {
                background-color: #28a745;
                color: white;
                border: none;
                padding: 6px 12px;
                border-radius: 4px;
                font-size: 11px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #218838;
            }
        """)
        save_btn.clicked.connect(self.save_current_condition)
        
        edit_btn = SecondaryButton("✏️ 편집")
        edit_btn.clicked.connect(self.edit_selected_trigger)
        
        delete_btn = QPushButton("🗑️ 삭제")
        delete_btn.setStyleSheet("""
            QPushButton {
                background-color: #e74c3c;
                color: white;
                border: none;
                padding: 6px 12px;
                border-radius: 4px;
                font-size: 11px;
            }
            QPushButton:hover {
                background-color: #c0392b;
            }
        """)
        delete_btn.clicked.connect(self.delete_selected_trigger)
        
        button_layout.addWidget(save_btn)
        button_layout.addWidget(edit_btn)
        button_layout.addWidget(delete_btn)
        button_layout.addStretch()
        
        layout.addLayout(button_layout)
        
        return group
    
    def create_simulation_area(self):
        """영역 3: 케이스 시뮬레이션 버튼들 (우측 상단)"""
        group = QGroupBox("🎮 케이스 시뮬레이션")
        group.setStyleSheet(self.get_groupbox_style("#6f42c1"))
        layout = QVBoxLayout(group)
        
        # 설명
        desc_label = QLabel("📈 가상 시나리오로 트리거 테스트")
        desc_label.setStyleSheet("color: #6c757d; font-size: 11px; margin-bottom: 10px;")
        layout.addWidget(desc_label)
        
        # 시뮬레이션 버튼들
        simulation_buttons = [
            ("📈 상승", "상승 추세 시나리오", "#28a745"),
            ("📉 하락", "하락 추세 시나리오", "#dc3545"),
            ("🚀 급등", "급등 시나리오", "#007bff"),
            ("💥 급락", "급락 시나리오", "#fd7e14"),
            ("➡️ 횡보", "횡보 시나리오", "#6c757d"),
            ("🔄 지수크로스", "이동평균 교차", "#17a2b8")
        ]
        
        for i, (icon_text, tooltip, color) in enumerate(simulation_buttons):
            btn = QPushButton(icon_text)
            btn.setToolTip(tooltip)
            btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: {color};
                    color: white;
                    border: none;
                    border-radius: 8px;
                    padding: 12px;
                    font-size: 14px;
                    font-weight: bold;
                    margin: 2px;
                }}
                QPushButton:hover {{
                    background-color: {color}dd;
                }}
                QPushButton:pressed {{
                    background-color: {color}aa;
                }}
            """)
            btn.clicked.connect(lambda checked, scenario=icon_text: self.run_simulation(scenario))
            layout.addWidget(btn)
        
        layout.addStretch()
        
        # 시뮬레이션 상태
        self.simulation_status = QLabel("💡 트리거를 선택하고 시나리오를 클릭하세요")
        self.simulation_status.setStyleSheet("""
            background-color: #f8f9fa;
            border: 2px solid #dee2e6;
            border-radius: 8px;
            padding: 12px;
            font-size: 11px;
            color: #495057;
            font-weight: bold;
            text-align: center;
        """)
        layout.addWidget(self.simulation_status)
        
        return group
    
    def create_trigger_detail_area(self):
        """영역 5: 선택한 트리거 상세 정보 (중앙 하단)"""
        group = QGroupBox("📊 트리거 상세 정보")
        group.setStyleSheet(self.get_groupbox_style("#17a2b8"))
        layout = QVBoxLayout(group)
        
        # 상세 정보 텍스트
        self.trigger_detail_text = QTextEdit()
        self.trigger_detail_text.setStyleSheet("""
            QTextEdit {
                border: 2px solid #ddd;
                border-radius: 8px;
                background-color: #f8f9fa;
                font-family: 'Consolas', 'Monaco', monospace;
                font-size: 12px;
                padding: 12px;
                line-height: 1.4;
            }
            QTextEdit:focus {
                border-color: #007bff;
                background-color: white;
            }
        """)
        self.trigger_detail_text.setReadOnly(True)
        self.trigger_detail_text.setPlainText("트리거를 선택하면 상세 정보가 표시됩니다.")
        layout.addWidget(self.trigger_detail_text)
        
        # 빠른 액션 버튼들
        action_layout = QHBoxLayout()
        
        test_btn = QPushButton("🧪 빠른 테스트")
        test_btn.setStyleSheet(self.get_small_button_style("#007bff"))
        test_btn.clicked.connect(self.quick_test_trigger)
        
        copy_btn = QPushButton("📋 복사")
        copy_btn.setStyleSheet(self.get_small_button_style("#6c757d"))
        copy_btn.clicked.connect(self.copy_trigger_info)
        
        action_layout.addWidget(test_btn)
        action_layout.addWidget(copy_btn)
        action_layout.addStretch()
        
        layout.addLayout(action_layout)
        
        return group
    
    def create_test_result_area(self):
        """영역 6: 작동 마커 차트 + 작동 기록 (우측 하단)"""
        group = QGroupBox("📈 테스트 결과 & 작동 기록")
        group.setStyleSheet(self.get_groupbox_style("#fd7e14"))
        layout = QVBoxLayout(group)
        
        # 미니 차트 위젯
        self.mini_chart = MiniChartWidget()
        layout.addWidget(self.mini_chart)
        
        # 작동 기록 리스트
        self.test_history_list = QListWidget()
        self.test_history_list.setStyleSheet("""
            QListWidget {
                border: 2px solid #ddd;
                border-radius: 8px;
                background-color: white;
                max-height: 120px;
                font-size: 11px;
            }
            QListWidget::item {
                padding: 8px;
                border-bottom: 1px solid #f0f0f0;
                margin: 2px;
                border-radius: 4px;
            }
            QListWidget::item:selected {
                background-color: #fff3cd;
                color: #856404;
                border: 1px solid #ffeaa7;
            }
            QListWidget::item:hover {
                background-color: #f8f9fa;
            }
        """)
        
        # 테스트 결과 텍스트 영역 추가
        self.test_result_text = QTextEdit()
        self.test_result_text.setStyleSheet("""
            QTextEdit {
                border: 2px solid #ddd;
                border-radius: 8px;
                padding: 8px;
                font-size: 10px;
                background-color: white;
                max-height: 120px;
            }
        """)
        self.test_result_text.setReadOnly(True)
        self.test_result_text.setText("💡 시뮬레이션 결과가 여기에 표시됩니다.")
        
        # 기본 항목들 추가
        self.add_test_history_item("시스템 시작", "ready")
        
        layout.addWidget(QLabel("🕐 작동 기록:"))
        layout.addWidget(self.test_history_list)
        layout.addWidget(QLabel("📋 상세 결과:"))
        layout.addWidget(self.test_result_text)
        
        return group
    
    def create_search_input(self):
        """검색 입력 생성 - 기존 시스템 스타일 적용"""
        from PyQt6.QtWidgets import QLineEdit
        
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
        """그룹박스 스타일 생성 - 기존 시스템과 통일"""
        return f"""
            QGroupBox {{
                font-weight: bold;
                border: 2px solid {color};
                border-radius: 8px;
                margin: 8px;
                padding-top: 20px;
                background-color: #fafafa;
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                left: 15px;
                padding: 0 8px 0 8px;
                background-color: white;
                color: {color};
                font-size: 13px;
                font-weight: bold;
                border-radius: 4px;
            }}
        """
    
    def get_white_button_style(self):
        """흰색 버튼 스타일 - 기존 시스템과 통일"""
        return """
            QPushButton {
                background-color: white;
                color: #333;
                border: 2px solid #ddd;
                border-radius: 6px;
                padding: 8px 16px;
                font-weight: bold;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: #f8f9fa;
                border-color: #007bff;
                color: #007bff;
            }
            QPushButton:pressed {
                background-color: #e9ecef;
            }
        """
    
    def get_small_button_style(self, color):
        """작은 버튼 스타일 - 기존 시스템과 통일"""
        return f"""
            QPushButton {{
                background-color: {color};
                color: white;
                border: none;
                border-radius: 6px;
                padding: 8px 12px;
                font-size: 11px;
                font-weight: bold;
                min-width: 60px;
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
        try:
            conditions = self.storage.get_all_conditions()
            self.trigger_tree.clear()
            
            # 카테고리별 그룹화
            category_groups = {}
            
            for condition in conditions:
                category = condition.get('category', 'unknown')
                if category not in category_groups:
                    category_groups[category] = []
                category_groups[category].append(condition)
            
            # 트리에 추가
            for category, items in category_groups.items():
                category_item = QTreeWidgetItem([f"📁 {category.upper()}", "", "", ""])
                category_item.setExpanded(True)
                
                for condition in items:
                    name = condition.get('name', 'Unknown')
                    variable = condition.get('variable_name', 'Unknown')
                    operator = condition.get('operator', '?')
                    target = condition.get('target_value', '?')
                    
                    condition_text = f"{operator} {target}"
                    
                    item = QTreeWidgetItem([name, variable, condition_text, category])
                    item.setData(0, Qt.ItemDataRole.UserRole, condition)  # 조건 데이터 저장
                    category_item.addChild(item)
                
                self.trigger_tree.addTopLevelItem(category_item)
            
            print(f"✅ {len(conditions)}개 트리거 로드 완료")
            
        except Exception as e:
            print(f"❌ 트리거 리스트 로드 실패: {e}")
    
    def on_condition_saved(self, condition_data):
        """조건 저장 완료 시 호출"""
        print(f"✅ 새 조건 저장: {condition_data.get('name', 'Unknown')}")
        
        # 트리거 리스트 새로고침
        self.load_trigger_list()
        
        # 상태 업데이트
        self.simulation_status.setText(f"✅ '{condition_data.get('name', 'Unknown')}' 저장 완료!")
        
        # 테스트 기록 추가
        self.add_test_history_item(f"조건 저장: {condition_data.get('name', 'Unknown')}", "save")
    
    def on_trigger_selected(self, item, column):
        """트리거 선택 시 호출"""
        condition_data = item.data(0, Qt.ItemDataRole.UserRole)
        if not condition_data:
            return
        
        self.selected_condition = condition_data
        
        # 외부변수 정보 처리
        external_variable_info = condition_data.get('external_variable')
        if external_variable_info:
            # JSON 문자열인 경우 파싱
            if isinstance(external_variable_info, str):
                try:
                    import json
                    external_variable_info = json.loads(external_variable_info)
                except json.JSONDecodeError:
                    external_variable_info = None
        
        # 비교 설정 섹션 구성
        comparison_type = condition_data.get('comparison_type', 'fixed')
        if comparison_type == 'external' and external_variable_info:
            # 외부 변수 사용
            ext_var_name = external_variable_info.get('variable_name', 'Unknown')
            ext_var_category = external_variable_info.get('category', 'Unknown')
            ext_var_params = external_variable_info.get('variable_params', {})
            
            # 외부변수 파라미터 텍스트 생성
            if ext_var_params:
                params_text = ""
                for key, value in ext_var_params.items():
                    params_text += f"\n    - {key}: {value}"
            else:
                params_text = "\n    - 파라미터 없음"
            
            comparison_info = f"""외부 변수 '{ext_var_name}' (카테고리: {ext_var_category})
  • 파라미터:{params_text}"""
        else:
            # 고정값 사용
            target_value = condition_data.get('target_value', 'Unknown')
            comparison_info = f"고정값: {target_value}"
        
        # 상세 정보 표시
        detail_text = f"""🎯 조건명: {condition_data.get('name', 'Unknown')}
📝 설명: {condition_data.get('description', 'No description')}

📊 변수 정보:
  • 변수: {condition_data.get('variable_name', 'Unknown')}
  • 파라미터: {condition_data.get('variable_params', {})}

⚖️ 비교 설정:
  • 연산자: {condition_data.get('operator', 'Unknown')}
  • {comparison_info}

🏷️ 카테고리: {condition_data.get('category', 'Unknown')}
🕐 생성일: {condition_data.get('created_at', 'Unknown')}"""
        
        self.trigger_detail_text.setPlainText(detail_text.strip())
        
        # 시뮬레이션 상태 업데이트
        self.simulation_status.setText(f"🎯 '{condition_data.get('name', 'Unknown')}' 선택됨 - 시나리오를 클릭하세요")
        
        print(f"📊 트리거 선택: {condition_data.get('name', 'Unknown')}")
    
    def generate_simulation_data(self, scenario, variable_name):
        """시나리오별 가상 데이터 생성"""
        import random
        
        # 기본값 설정
        base_value = 50.0  # 기본 중간값
        
        # 변수 타입에 따른 기본값 조정
        if 'rsi' in variable_name.lower():
            base_value = random.uniform(30, 70)
        elif 'price' in variable_name.lower() or '가격' in variable_name.lower():
            base_value = random.uniform(1000, 100000)
        elif 'volume' in variable_name.lower() or '거래량' in variable_name.lower():
            base_value = random.uniform(1000000, 10000000)
        elif 'macd' in variable_name.lower():
            base_value = random.uniform(-0.5, 0.5)
        
        # 시나리오별 변화 적용
        if scenario == "📈 상승":
            multiplier = random.uniform(1.1, 1.3)  # 10-30% 상승
        elif scenario == "📉 하락":
            multiplier = random.uniform(0.7, 0.9)  # 10-30% 하락
        elif scenario == "🚀 급등":
            multiplier = random.uniform(1.5, 2.0)  # 50-100% 급등
        elif scenario == "💥 급락":
            multiplier = random.uniform(0.3, 0.6)  # 40-70% 급락
        elif scenario == "➡️ 횡보":
            multiplier = random.uniform(0.98, 1.02)  # ±2% 범위
        elif scenario == "🔄 지수크로스":
            multiplier = random.uniform(0.95, 1.05)  # ±5% 범위
        else:
            multiplier = random.uniform(0.9, 1.1)  # 기본 ±10%
        
        current_value = base_value * multiplier
        
        return {
            'current_value': current_value,
            'base_value': base_value,
            'change_percent': (multiplier - 1) * 100,
            'scenario': scenario
        }
    
    def add_test_history_item(self, text, item_type):
        """테스트 기록 항목 추가"""
        from datetime import datetime
        
        timestamp = datetime.now().strftime("%H:%M:%S")
        
        type_icons = {
            "ready": "🟢",
            "save": "💾",
            "test": "🧪",
            "error": "❌"
        }
        
        icon = type_icons.get(item_type, "ℹ️")
        full_text = f"{timestamp} {icon} {text}"
        
        item = QListWidgetItem(full_text)
        self.test_history_list.addItem(item)
        
        # 자동 스크롤
        self.test_history_list.scrollToBottom()
        
        # 최대 100개 항목만 유지
        if self.test_history_list.count() > 100:
            self.test_history_list.takeItem(0)
    
    def filter_triggers(self, text):
        """트리거 필터링 구현"""
        if not text.strip():
            # 검색어가 없으면 모든 항목 표시
            for i in range(self.trigger_tree.topLevelItemCount()):
                category_item = self.trigger_tree.topLevelItem(i)
                category_item.setHidden(False)
                for j in range(category_item.childCount()):
                    category_item.child(j).setHidden(False)
            return
        
        search_text = text.lower()
        hidden_categories = 0
        
        # 각 카테고리와 항목들을 검색
        for i in range(self.trigger_tree.topLevelItemCount()):
            category_item = self.trigger_tree.topLevelItem(i)
            visible_children = 0
            
            for j in range(category_item.childCount()):
                child_item = category_item.child(j)
                
                # 트리거명, 변수명, 조건에서 검색
                trigger_name = child_item.text(0).lower()
                variable_name = child_item.text(1).lower()
                condition_text = child_item.text(2).lower()
                
                is_match = (search_text in trigger_name or 
                           search_text in variable_name or 
                           search_text in condition_text)
                
                child_item.setHidden(not is_match)
                if is_match:
                    visible_children += 1
            
            # 카테고리에 보이는 항목이 없으면 카테고리도 숨김
            if visible_children == 0:
                category_item.setHidden(True)
                hidden_categories += 1
            else:
                category_item.setHidden(False)
        
        print(f"🔍 검색 완료: '{text}' - {hidden_categories}개 카테고리 필터링됨")
    
    def edit_selected_trigger(self):
        """선택한 트리거 편집 구현"""
        if not self.selected_condition:
            QMessageBox.warning(self, "⚠️ 경고", "편집할 트리거를 선택해주세요.")
            return
        
        try:
            # 조건 다이얼로그에 현재 조건 로드
            if hasattr(self.condition_dialog, 'load_condition'):
                self.condition_dialog.load_condition(self.selected_condition)
                QMessageBox.information(self, "✅ 편집", "조건이 편집기에 로드되었습니다.\n좌측 편집기에서 수정 후 저장하세요.")
            else:
                # 수동으로 필드 설정
                condition_name = self.selected_condition.get('name', '')
                QMessageBox.information(self, "� 편집 모드", 
                                      f"'{condition_name}' 조건을 편집하려면:\n"
                                      "1. 좌측 조건 빌더에서 동일한 설정을 다시 구성\n"
                                      "2. 새 이름으로 저장하거나 기존 조건 덮어쓰기")
                
        except Exception as e:
            QMessageBox.critical(self, "❌ 오류", f"편집 중 오류가 발생했습니다:\n{e}")
            print(f"❌ 편집 오류: {e}")
    
    def delete_selected_trigger(self):
        """선택한 트리거 삭제 구현 (강화된 확인)"""
        if not self.selected_condition:
            QMessageBox.warning(self, "⚠️ 경고", "삭제할 트리거를 선택해주세요.")
            return
        
        condition_name = self.selected_condition.get('name', 'Unknown')
        condition_id = self.selected_condition.get('id', None)
        
        # 1차 삭제 확인
        reply1 = QMessageBox.question(
            self, "🗑️ 삭제 확인", 
            f"'{condition_name}' 트리거를 삭제하시겠습니까?\n\n"
            f"⚠️ 주의사항:\n"
            f"• 이 작업은 완전히 되돌릴 수 없습니다\n"
            f"• 이 트리거를 사용하는 전략이 있다면 영향을 받습니다\n"
            f"• 삭제된 데이터는 복구할 수 없습니다",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply1 == QMessageBox.StandardButton.Yes:
            # 2차 최종 확인 (트리거 이름 입력)
            from PyQt6.QtWidgets import QInputDialog
            
            text, ok = QInputDialog.getText(
                self, "🔒 최종 확인", 
                f"정말로 삭제하시려면 트리거 이름을 정확히 입력하세요:\n\n'{condition_name}'"
            )
            
            if ok and text.strip() == condition_name:
                try:
                    if condition_id:
                        # 하드 삭제로 완전 제거
                        success, message = self.storage.delete_condition(condition_id, hard_delete=True)
                        
                        if success:
                            QMessageBox.information(self, "✅ 삭제 완료", f"'{condition_name}' 트리거가 완전히 삭제되었습니다.")
                            self.load_trigger_list()  # 목록 새로고침
                            self.selected_condition = None
                        else:
                            QMessageBox.critical(self, "❌ 삭제 실패", f"삭제 중 오류가 발생했습니다:\n{message}")
                    else:
                        QMessageBox.warning(self, "⚠️ 오류", "트리거 ID를 찾을 수 없습니다.")
                        
                except Exception as e:
                    QMessageBox.critical(self, "❌ 오류", f"삭제 중 예외가 발생했습니다:\n{str(e)}")
            elif ok:
                QMessageBox.warning(self, "❌ 이름 불일치", 
                                  f"입력한 이름이 일치하지 않습니다.\n"
                                  f"입력: '{text.strip()}'\n"
                                  f"정확한 이름: '{condition_name}'")
            # else: 사용자가 취소함
    
    def quick_test_trigger(self):
        """선택한 트리거 빠른 테스트"""
        if not self.selected_condition:
            QMessageBox.warning(self, "⚠️ 경고", "테스트할 트리거를 선택해주세요.")
            return
        
        # 기본 시나리오로 빠른 테스트
        self.run_simulation("빠른 테스트")
    
    def copy_trigger_info(self):
        """트리거 정보 클립보드 복사 구현"""
        if not self.selected_condition:
            QMessageBox.warning(self, "⚠️ 경고", "복사할 트리거를 선택해주세요.")
            return
        
        try:
            from PyQt6.QtWidgets import QApplication
            
            # 현재 상세 정보 텍스트를 클립보드에 복사
            detail_text = self.trigger_detail_text.toPlainText()
            
            clipboard = QApplication.clipboard()
            clipboard.setText(detail_text)
            
            # 상태 업데이트
            condition_name = self.selected_condition.get('name', 'Unknown')
            self.add_test_history_item(f"정보 복사: {condition_name}", "save")
            
            QMessageBox.information(self, "📋 복사 완료", "트리거 정보가 클립보드에 복사되었습니다.")
            
        except Exception as e:
            QMessageBox.critical(self, "❌ 오류", f"복사 중 오류가 발생했습니다:\n{e}")
            print(f"❌ 복사 오류: {e}")
    
    def refresh_all(self):
        """전체 새로고침"""
        try:
            # 트리거 리스트 새로고침
            self.load_trigger_list()
            
            # 조건 빌더 새로고침
            if hasattr(self.condition_dialog, 'refresh_data'):
                self.condition_dialog.refresh_data()
            
            # 상태 초기화
            self.simulation_status.setText("🔄 전체 새로고침 완료!")
            self.add_test_history_item("전체 새로고침 완료", "ready")
            
            print("✅ 전체 새로고침 완료")
            
        except Exception as e:
            print(f"❌ 새로고침 실패: {e}")
            QMessageBox.warning(self, "오류", f"새로고침 중 오류가 발생했습니다:\n{e}")
    
    def save_current_condition(self):
        """현재 조건 빌더의 조건을 저장"""
        try:
            if hasattr(self.condition_dialog, 'save_condition'):
                self.condition_dialog.save_condition()
            else:
                QMessageBox.warning(self, "⚠️ 경고", "조건 저장 기능을 사용할 수 없습니다.")
        except Exception as e:
            print(f"❌ 조건 저장 실패: {e}")
            QMessageBox.critical(self, "❌ 오류", f"조건 저장 중 오류가 발생했습니다:\n{e}")
    
    # ===== 시뮬레이션 관련 메서드들 =====
    
    def run_simulation(self, scenario: str):
        """시나리오별 시뮬레이션 실행"""
        try:
            # 시뮬레이션 엔진 가용성 체크
            if RealDataSimulationEngine is None:
                QMessageBox.warning(
                    self, 
                    "⚠️ 시뮬레이션 불가", 
                    "시뮬레이션 엔진을 찾을 수 없습니다.\n"
                    "enhanced_real_data_simulation_engine.py 파일이 필요합니다."
                )
                return
            
            # 이미 실행 중인 시뮬레이션이 있으면 중단
            if self.simulation_worker and self.simulation_worker.isRunning():
                self.simulation_worker.terminate()
                self.simulation_worker.wait()
            
            # 선택된 트리거 정보 가져오기 (추후 확장용)
            selected_trigger = None
            if hasattr(self, 'trigger_tree') and self.trigger_tree.currentItem():
                # 현재 선택된 트리거가 있다면 해당 정보 사용
                item = self.trigger_tree.currentItem()
                if item and item.parent():  # 카테고리가 아닌 실제 트리거인 경우
                    selected_trigger = {
                        'name': item.text(0),
                        'variable': item.text(1),
                        'condition': item.text(2)
                    }
            
            # 시뮬레이션 워커 생성 및 시작
            self.simulation_worker = SimulationWorker(scenario, selected_trigger)
            
            # 시그널 연결
            self.simulation_worker.progress_updated.connect(self.on_simulation_progress)
            self.simulation_worker.simulation_completed.connect(self.on_simulation_completed)
            self.simulation_worker.simulation_error.connect(self.on_simulation_error)
            
            # 상태 업데이트
            self.simulation_status.setText(f"🚀 {scenario} 시뮬레이션 시작...")
            self.simulation_status.setStyleSheet("""
                background-color: #e3f2fd;
                border: 2px solid #2196f3;
                border-radius: 8px;
                padding: 12px;
                font-size: 11px;
                color: #1565c0;
                font-weight: bold;
                text-align: center;
            """)
            
            # 시뮬레이션 시작
            self.simulation_worker.start()
            
        except Exception as e:
            QMessageBox.critical(
                self, 
                "❌ 시뮬레이션 오류", 
                f"시뮬레이션 실행 중 오류가 발생했습니다:\n{str(e)}"
            )
    
    @pyqtSlot(str)
    def on_simulation_progress(self, message: str):
        """시뮬레이션 진행 상황 업데이트"""
        self.simulation_status.setText(message)
        
        # 메시지에 따라 색상 변경
        if "시작" in message:
            bg_color = "#e3f2fd"
            border_color = "#2196f3"
            text_color = "#1565c0"
        elif "준비" in message:
            bg_color = "#fff3e0"
            border_color = "#ff9800"
            text_color = "#e65100"
        elif "실행" in message:
            bg_color = "#f3e5f5"
            border_color = "#9c27b0"
            text_color = "#6a1b9a"
        else:
            bg_color = "#f8f9fa"
            border_color = "#dee2e6"
            text_color = "#495057"
        
        self.simulation_status.setStyleSheet(f"""
            background-color: {bg_color};
            border: 2px solid {border_color};
            border-radius: 8px;
            padding: 12px;
            font-size: 11px;
            color: {text_color};
            font-weight: bold;
            text-align: center;
        """)
    
    @pyqtSlot(dict)
    def on_simulation_completed(self, result: dict):
        """시뮬레이션 완료 처리"""
        try:
            scenario = result.get('scenario', '알 수 없음')
            session_id = result.get('session_id', 'unknown')
            
            # 결과 저장
            self.simulation_results[scenario] = result
            
            # 차트 데이터 추출 및 업데이트
            price_data = result.get('price_data', [])
            trigger_results = result.get('trigger_results', [])
            
            # 미니 차트 업데이트
            if hasattr(self, 'mini_chart') and price_data:
                self.mini_chart.update_simulation_chart(scenario, price_data, trigger_results)
                
            # 결과 표시
            total_return = result.get('total_return_percent', 0)
            max_drawdown = result.get('max_drawdown_percent', 0)
            total_trades = result.get('total_trades', 0)
            triggered_conditions = result.get('triggered_conditions', 0)
            
            # 성공 메시지
            success_msg = f"""✅ {scenario} 시뮬레이션 완료!
            
📊 결과 요약:
💰 총 수익률: {total_return:.2f}%
📉 최대 손실률: {max_drawdown:.2f}%
🔄 총 거래 수: {total_trades}개
⚡ 트리거 발동: {triggered_conditions}회
🆔 세션 ID: {session_id}"""
            
            # 상태 업데이트
            self.simulation_status.setText(success_msg)
            self.simulation_status.setStyleSheet("""
                background-color: #e8f5e8;
                border: 2px solid #4caf50;
                border-radius: 8px;
                padding: 12px;
                font-size: 10px;
                color: #2e7d32;
                font-weight: bold;
                text-align: left;
            """)
            
            # 작동 기록에 차트 업데이트 기록 추가
            trigger_count = len([t for t in trigger_results if t[0]]) if trigger_results else 0
            self.add_test_history_item(f"{scenario} 시뮬레이션: {trigger_count}회 트리거 발동", "test")
            
            # 결과 상세 정보를 테스트 결과 영역에 표시
            if hasattr(self, 'test_result_text'):
                detailed_result = f"""🎯 {scenario} 시뮬레이션 결과

📈 성과 지표:
• 총 수익률: {total_return:.2f}%
• 최대 손실률: {max_drawdown:.2f}%
• 샤프 비율: {result.get('sharpe_ratio', 'N/A')}

📊 거래 분석:
• 총 거래 수: {total_trades}개
• 트리거 발동: {triggered_conditions}회
• 평균 거래당 수익: {(total_return / max(total_trades, 1)):.2f}%

🔍 포트폴리오:
• 초기 자본: {result.get('initial_capital', 0):,.0f}원
• 최종 자본: {result.get('final_capital', 0):,.0f}원
• 최고 자산 가치: {result.get('portfolio', {}).get('max_value', 0):,.0f}원

⏰ 시뮬레이션 정보:
• 세션 ID: {session_id}
• 시나리오: {scenario}
• 상태: {result.get('status', 'completed')}

📋 최근 거래 내역:
"""
                # 최근 거래 내역 추가
                trades = result.get('trades', [])
                if trades:
                    for i, trade in enumerate(trades[-3:], 1):  # 최근 3개 거래만
                        action = trade.get('action', 'N/A')
                        amount = trade.get('amount', 0)
                        trigger = trade.get('trigger_name', 'N/A')
                        detailed_result += f"{i}. {action} - {amount:,.0f}원 ({trigger})\n"
                else:
                    detailed_result += "거래 내역이 없습니다.\n"
                
                # 차트 데이터 정보 추가
                if price_data:
                    detailed_result += f"\n📊 차트 데이터: {len(price_data)}개 포인트\n"
                    if trigger_results:
                        trigger_count = len([t for t in trigger_results if t[0]])
                        detailed_result += f"🎯 트리거 발동 포인트: {trigger_count}개\n"
                
                self.test_result_text.setText(detailed_result)
            
        except Exception as e:
            print(f"❌ 시뮬레이션 결과 처리 오류: {e}")
            QMessageBox.warning(self, "⚠️ 경고", f"결과 처리 중 오류가 발생했습니다: {str(e)}")
    
    @pyqtSlot(str)
    def on_simulation_error(self, error_message: str):
        """시뮬레이션 오류 처리"""
        self.simulation_status.setText(error_message)
        self.simulation_status.setStyleSheet("""
            background-color: #ffebee;
            border: 2px solid #f44336;
            border-radius: 8px;
            padding: 12px;
            font-size: 11px;
            color: #c62828;
            font-weight: bold;
            text-align: center;
        """)
        
        # 에러 상세 정보를 테스트 결과 영역에 표시
        if hasattr(self, 'test_result_text'):
            self.test_result_text.setText(f"""❌ 시뮬레이션 오류

{error_message}

🔧 해결 방법:
1. enhanced_real_data_simulation_engine.py 파일이 있는지 확인
2. data/upbit_auto_trading.sqlite3 파일에 데이터가 있는지 확인
3. 네트워크 연결 상태 확인
4. 프로그램 재시작 후 다시 시도

💡 도움말:
시뮬레이션 기능을 사용하려면 실제 KRW-BTC 시장 데이터가 필요합니다.
데이터 수집 기능을 먼저 실행해주세요.""")

if __name__ == "__main__":
    from PyQt6.QtWidgets import QApplication
    import sys
    
    app = QApplication(sys.argv)
    
    window = IntegratedConditionManager()
    window.show()
    
    sys.exit(app.exec())
