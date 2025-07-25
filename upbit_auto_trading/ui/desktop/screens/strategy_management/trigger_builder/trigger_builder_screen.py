"""
트리거 빌더 메인 화면 - 기존 기능 완전 복원
IntegratedConditionManager에서 검증된 모든 기능을 그대로 이관
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QGroupBox,
    QPushButton, QLabel, QMessageBox, QTreeWidget, QTreeWidgetItem,
    QTextEdit, QSplitter, QFrame, QListWidget, QListWidgetItem,
    QProgressBar, QLineEdit, QComboBox, QStyle
)
from PyQt6.QtCore import Qt, pyqtSignal, QTimer
from PyQt6.QtGui import QFont, QPixmap, QIcon
import random
from datetime import datetime, timedelta

# 새로운 컴포넌트들 import - 기존 기능 정확 복제
try:
    from .components.condition_dialog import ConditionDialog
    from .components.trigger_list_widget import TriggerListWidget
    from .components.trigger_detail_widget import TriggerDetailWidget
    from .components.simulation_control_widget import SimulationControlWidget
    from .components.simulation_result_widget import SimulationResultWidget
    REFACTORED_COMPONENTS_AVAILABLE = True
    print("✅ 리팩토링된 컴포넌트들 로드 성공")
except ImportError as e:
    REFACTORED_COMPONENTS_AVAILABLE = False
    print(f"⚠️ 리팩토링된 컴포넌트를 찾을 수 없습니다: {e}")

# 기존 컴포넌트들 (폴백용)
from .components.chart_visualizer import ChartVisualizer
from .components.trigger_calculator import TriggerCalculator

# 새로운 차트 변수 카테고리 시스템 import
try:
    from .components.chart_variable_service import get_chart_variable_service
    from .components.variable_display_system import get_variable_registry
    CHART_VARIABLE_SYSTEM_AVAILABLE = True
except ImportError:
    CHART_VARIABLE_SYSTEM_AVAILABLE = False
    print("⚠️ 차트 변수 카테고리 시스템을 로드할 수 없습니다.")

# 차트 라이브러리 import
try:
    import matplotlib.pyplot as plt
    from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
    from matplotlib.figure import Figure
    from matplotlib.ticker import FuncFormatter
    import numpy as np
    import pandas as pd
    from datetime import datetime, timedelta
    
    # 한글 폰트 설정
    import matplotlib.font_manager as fm
    
    # 시스템에서 사용 가능한 한글 폰트 찾기
    font_list = fm.findSystemFonts(fontpaths=None, fontext='ttf')
    korean_fonts = []
    
    for font_path in font_list:
        try:
            font_prop = fm.FontProperties(fname=font_path)
            font_name = font_prop.get_name()
            if any(keyword in font_name.lower() for keyword in ['malgun', 'gulim', 'dotum', 'batang', 'nanum', '맑은 고딕', '굴림']):
                korean_fonts.append(font_name)
        except:
            continue
    
    # 우선순위에 따라 폰트 설정
    preferred_fonts = ['Malgun Gothic', 'NanumGothic', 'Gulim', 'Dotum']
    selected_font = None
    
    for pref_font in preferred_fonts:
        if pref_font in korean_fonts:
            selected_font = pref_font
            break
    
    if not selected_font and korean_fonts:
        selected_font = korean_fonts[0]
    
    if selected_font:
        plt.rcParams['font.family'] = selected_font
        plt.rcParams['axes.unicode_minus'] = False
        print(f"✅ 차트 한글 폰트 설정: {selected_font}")
    else:
        plt.rcParams['axes.unicode_minus'] = False
        print("⚠️ 한글 폰트를 찾을 수 없어 기본 폰트 사용")
    
    print("✅ 차트 라이브러리 로드 성공")
    CHART_AVAILABLE = True
except ImportError as e:
    print(f"⚠️ 차트 라이브러리를 찾을 수 없습니다: {e}")
    CHART_AVAILABLE = False

# 우리의 컴포넌트 시스템 import
import sys
import os
import importlib
sys.path.append(os.path.dirname(__file__))

# 강제 모듈 리로드
def reload_condition_dialog():
    """조건 다이얼로그 모듈 강제 리로드"""
    module_names = [
        'components.condition_dialog',
        'components.condition_storage', 
        'components.condition_loader',
        'components.variable_definitions',
        'components.parameter_widgets',
        'components.condition_validator',
        'components.condition_builder',
        'components.preview_components'
    ]
    
    for module_name in module_names:
        if module_name in sys.modules:
            print(f"🔄 리로드: {module_name}")
            importlib.reload(sys.modules[module_name])

# 리로드 실행
reload_condition_dialog()

from .components.condition_dialog import ConditionDialog

# ConditionStorage와 ConditionLoader는 현재 프로젝트에서 찾기
try:
    from upbit_auto_trading.ui.desktop.screens.strategy_management.components.condition_storage import ConditionStorage
    from upbit_auto_trading.ui.desktop.screens.strategy_management.components.condition_loader import ConditionLoader
    print("✅ ConditionStorage, ConditionLoader 로드 성공")
except ImportError as e:
    print(f"❌ ConditionStorage, ConditionLoader 로드 실패: {e}")
    # 간단한 폴백 클래스 생성
    class ConditionStorage:
        def get_all_conditions(self):
            return []
        def delete_condition(self, condition_id):
            pass
    
    class ConditionLoader:
        def __init__(self, storage):
            self.storage = storage

# DataSourceSelectorWidget는 이제 trigger_builder/components에 있음
try:
    from .components import DataSourceSelectorWidget
    print("✅ DataSourceSelectorWidget 로드 성공")
except ImportError as e:
    print(f"❌ DataSourceSelectorWidget 로드 실패: {e}")
    DataSourceSelectorWidget = None

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

class TriggerBuilderScreen(QWidget):
    """트리거 빌더 메인 화면 - 기존 기능 완전 복원"""
    
    # 시그널 정의
    condition_tested = pyqtSignal(dict, bool)  # 조건, 테스트 결과
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("🎯 트리거 빌더 v2.0 (완전 리팩토링)")
        # 크기를 1600x1000 화면에 최적화 - 더 넓게 설정
        self.setMinimumSize(1400, 900)
        self.resize(1600, 1000)  # 초기 크기 설정
        
        # 기존 컴포넌트 초기화
        self.storage = ConditionStorage()
        self.loader = ConditionLoader(self.storage)
        self.selected_condition = None
        
        # 새로운 컴포넌트 초기화
        self.chart_visualizer = ChartVisualizer()
        self.trigger_calculator = TriggerCalculator()
        
        # 시뮬레이션 엔진 초기화
        from .components.simulation_engines import get_embedded_simulation_engine
        self.simulation_engine = get_embedded_simulation_engine()
        
        # 차트 변수 카테고리 시스템 초기화
        if CHART_VARIABLE_SYSTEM_AVAILABLE:
            try:
                self.chart_variable_service = get_chart_variable_service()
                self.variable_registry = get_variable_registry()
                print("✅ 차트 변수 카테고리 시스템 로드 완료")
            except Exception as e:
                print(f"⚠️ 차트 변수 카테고리 시스템 초기화 실패: {e}")
                self.chart_variable_service = None
                self.variable_registry = None
        else:
            self.chart_variable_service = None
            self.variable_registry = None
        
        self.init_ui()
        self.load_trigger_list()
    
    def init_ui(self):
        """UI 초기화 - 3x2 그리드 레이아웃"""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(5, 5, 5, 5)  # 마진 늘리기
        main_layout.setSpacing(5)  # 간격 늘리기
        
        # 상단 제목 추가
        self.create_header(main_layout)
        
        # 메인 그리드 레이아웃 (3x2)
        grid_widget = QWidget()
        grid_layout = QGridLayout(grid_widget)
        grid_layout.setContentsMargins(5, 5, 5, 5)  # 그리드 마진 늘리기
        grid_layout.setSpacing(8)  # 그리드 간격 늘리기
        
        # 1+4: 조건 빌더 (좌측, 세로 합쳐짐)
        self.condition_builder_area = self.create_condition_builder_area()
        grid_layout.addWidget(self.condition_builder_area, 0, 0, 2, 1)  # 2행에 걸쳐 배치
        
        # 2: 등록된 트리거 리스트 (중앙 상단)
        self.trigger_list_area = self.create_trigger_list_area()
        grid_layout.addWidget(self.trigger_list_area, 0, 1, 1, 1)
        
        # 3: 케이스 시뮬레이션 버튼들 (우측 상단)
        self.simulation_area = self.create_simulation_area()
        self.simulation_area.setMinimumWidth(400)  # 최소 너비 증가
        self.simulation_area.setMaximumWidth(500)  # 최대 너비 증가
        grid_layout.addWidget(self.simulation_area, 0, 2, 1, 1)
        
        # 5: 선택한 트리거 상세 정보 (중앙 하단)
        self.trigger_detail_area = self.create_trigger_detail_area()
        grid_layout.addWidget(self.trigger_detail_area, 1, 1, 1, 1)
        
        # 6: 작동 마커 차트 + 작동 기록 (우측 하단)
        self.test_result_area = self.create_test_result_area()
        self.test_result_area.setMinimumWidth(400)  # 최소 너비 증가
        self.test_result_area.setMaximumWidth(500)  # 최대 너비 증가
        grid_layout.addWidget(self.test_result_area, 1, 2, 1, 1)
        
        # 그리드 비율 설정 - 조건 빌더 폭을 15% 축소 (2:3:2 → 17:30:20)
        grid_layout.setColumnStretch(0, 17)  # 조건 빌더 (15% 축소)
        grid_layout.setColumnStretch(1, 30)  # 트리거 관리 (가장 넓게)
        grid_layout.setColumnStretch(2, 20)  # 시뮬레이션 (넓게)
        
        # 행 비율 설정
        grid_layout.setRowStretch(0, 1)  # 상단
        grid_layout.setRowStretch(1, 1)  # 하단
        
        main_layout.addWidget(grid_widget)
        
        print("✅ 트리거 빌더 UI 초기화 완료")
    
    def create_header(self, layout):
        """헤더 영역 생성"""
        header_layout = QHBoxLayout()
        
        # 타이틀
        title_label = QLabel("🎯 트리거 빌더 v2.0 (완전 리팩토링)")
        title_label.setStyleSheet("""
            QLabel {
                font-size: 18px;
                font-weight: bold;
                color: #2c3e50;
                padding: 10px;
                background-color: #ecf0f1;
                border-radius: 8px;
                margin: 5px;
            }
        """)
        header_layout.addWidget(title_label)
        
        # 상태 표시
        status_label = QLabel("✅ 시스템 준비됨")
        status_label.setStyleSheet("""
            QLabel {
                font-size: 12px;
                color: #27ae60;
                padding: 5px 10px;
                background-color: #d5f4e6;
                border-radius: 6px;
                margin: 5px;
            }
        """)
        header_layout.addWidget(status_label)
        
        layout.addLayout(header_layout)
    
    def create_condition_builder_area(self):
        """1+4: 조건 빌더 영역"""
        group = QGroupBox("🎯 조건 빌더")
        layout = QVBoxLayout()
        layout.setContentsMargins(5, 8, 5, 5)
        layout.setSpacing(3)
        
        # 조건 빌더 다이얼로그를 임베디드 형태로 포함
        try:
            # embedded 파라미터 없이 생성 시도
            self.condition_dialog = ConditionDialog()
            # 임베디드 모드에서는 최대한 공간 절약
            self.condition_dialog.setMaximumHeight(800)
            layout.addWidget(self.condition_dialog)
            print("✅ 조건 빌더 다이얼로그 생성 성공")
        except Exception as e:
            print(f"⚠️ 조건 빌더 다이얼로그 생성 실패: {e}")
            # 폴백: 간단한 인터페이스
            fallback_widget = self.create_condition_builder_fallback()
            layout.addWidget(fallback_widget)
        
        group.setLayout(layout)
        return group
    
    def create_condition_builder_fallback(self):
        """조건 빌더 폴백 위젯"""
        fallback_widget = QWidget()
        fallback_layout = QVBoxLayout(fallback_widget)
        
        # 상태 표시
        status_label = QLabel("🔧 조건 빌더 로딩 중...")
        status_label.setStyleSheet("""
            QLabel {
                color: #666;
                font-style: italic;
                padding: 20px;
                text-align: center;
                border: 2px dashed #ccc;
                border-radius: 8px;
                background-color: #f9f9f9;
            }
        """)
        fallback_layout.addWidget(status_label)
        
        # 새 조건 생성 버튼
        new_condition_btn = QPushButton("➕ 새 조건 생성")
        new_condition_btn.clicked.connect(self.open_condition_dialog)
        fallback_layout.addWidget(new_condition_btn)
        
        return fallback_widget
    
    def open_condition_dialog(self):
        """조건 다이얼로그를 별도 창으로 열기"""
        try:
            dialog = ConditionDialog()
            dialog.setWindowTitle("조건 생성/편집")
            dialog.setModal(True)
            dialog.exec()
        except Exception as e:
            QMessageBox.warning(self, "⚠️ 경고", f"조건 다이얼로그를 열 수 없습니다: {e}")
    
    def create_trigger_list_area(self):
        """2: 등록된 트리거 리스트 영역"""
        if REFACTORED_COMPONENTS_AVAILABLE:
            # 새로운 컴포넌트 사용
            trigger_list_widget = TriggerListWidget(self)
            # 기존 시그널 연결 유지
            trigger_list_widget.trigger_selected.connect(self.on_trigger_selected)
            trigger_list_widget.trigger_edited.connect(self.edit_trigger)
            trigger_list_widget.trigger_deleted.connect(self.delete_trigger)
            trigger_list_widget.trigger_copied.connect(self.copy_trigger)
            trigger_list_widget.trigger_save_requested.connect(self.save_current_condition)  # 새로운 시그널 연결
            trigger_list_widget.edit_mode_changed.connect(self.on_edit_mode_changed)  # 편집 모드 변경 시그널 연결
            
            # 기존 위젯 참조 유지 (호환성) - new_trigger_btn은 제거 (원본에 없음)
            self.trigger_tree = trigger_list_widget.trigger_tree
            # self.new_trigger_btn = trigger_list_widget.new_trigger_btn  # 원본에 없는 기능
            self.save_btn = trigger_list_widget.save_btn
            self.edit_btn = trigger_list_widget.edit_btn
            self.cancel_edit_btn = trigger_list_widget.cancel_edit_btn
            
            return trigger_list_widget
        else:
            # 기존 구현 유지 (원본에 맞게 수정 - new_trigger_btn 제거)
            group = QGroupBox("📋 등록된 트리거 리스트")
            layout = QVBoxLayout()
            layout.setContentsMargins(5, 8, 5, 5)
            layout.setSpacing(3)
            
            # 검색 입력 (원본 순서)
            search_layout = QHBoxLayout()
            search_layout.addWidget(QLabel("🔍"))
            self.search_input = QLineEdit()
            self.search_input.setPlaceholderText("트리거 검색...")
            search_layout.addWidget(self.search_input)
            layout.addLayout(search_layout)
            
            # 트리거 목록 (원본 구조)
            self.trigger_tree = QTreeWidget()
            self.trigger_tree.setHeaderLabels(["트리거명", "변수", "조건"])  # 원본과 동일
            self.trigger_tree.itemClicked.connect(self.on_trigger_selected)
            layout.addWidget(self.trigger_tree)
            
            # 하단 버튼들 (원본 구조)
            btn_layout = QHBoxLayout()
            
            self.save_btn = QPushButton("� 트리거 저장")
            self.save_btn.clicked.connect(self.save_current_condition)
            btn_layout.addWidget(self.save_btn)
            
            self.edit_btn = QPushButton("✏️ 편집")
            self.edit_btn.clicked.connect(self.edit_trigger)
            btn_layout.addWidget(self.edit_btn)
            
            self.cancel_edit_btn = QPushButton("❌ 편집 취소")
            self.cancel_edit_btn.clicked.connect(self.cancel_edit_trigger)
            btn_layout.addWidget(self.cancel_edit_btn)
            
            copy_trigger_btn = QPushButton("📋 복사")
            copy_trigger_btn.clicked.connect(self.copy_trigger)
            btn_layout.addWidget(copy_trigger_btn)
            
            delete_btn = QPushButton("🗑️ 삭제")
            delete_btn.clicked.connect(self.delete_trigger)
            btn_layout.addWidget(delete_btn)
            
            btn_layout.addStretch()
            layout.addLayout(btn_layout)
            
            group.setLayout(layout)
            return group
    
    def create_simulation_area(self):
        """3: 케이스 시뮬레이션 버튼들 영역"""
        if REFACTORED_COMPONENTS_AVAILABLE:
            # 새로운 컴포넌트 사용
            simulation_control_widget = SimulationControlWidget(self)
            
            # 시그널 연결 (기존과 동일)
            simulation_control_widget.simulation_requested.connect(self.run_simulation)
            simulation_control_widget.data_source_changed.connect(self.on_data_source_changed)
            
            # 기존 위젯 참조 유지 (호환성) - 존재하는 것만
            self.simulation_status = simulation_control_widget.simulation_status
            
            return simulation_control_widget
        else:
            # 원본 integrated_condition_manager.py와 동일한 구현
            group = QGroupBox("🎮 케이스 시뮬레이션")
            layout = QVBoxLayout()
            layout.setContentsMargins(5, 8, 5, 5)
            layout.setSpacing(3)
            
            # 데이터 소스 선택 위젯 추가 (원본과 동일)
            if DataSourceSelectorWidget is not None:
                try:
                    self.data_source_selector = DataSourceSelectorWidget()
                    self.data_source_selector.source_changed.connect(self.on_data_source_changed)
                    layout.addWidget(self.data_source_selector)
                    print("✅ DataSourceSelectorWidget 생성 성공")
                except Exception as e:
                    print(f"⚠️ 데이터 소스 선택기 초기화 실패: {e}")
                    # 대체 라벨
                    fallback_label = QLabel("📊 가상 데이터로 시뮬레이션")
                    fallback_label.setStyleSheet("""
                        background-color: #e7f3ff;
                        border: 1px solid #007bff;
                        border-radius: 4px;
                        padding: 8px;
                        font-size: 11px;
                        color: #007bff;
                        text-align: center;
                        font-weight: bold;
                    """)
                    fallback_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
                    layout.addWidget(fallback_label)
            else:
                print("⚠️ DataSourceSelectorWidget 클래스를 로드할 수 없음")
                # 대체 라벨
                fallback_label = QLabel("📊 가상 데이터로 시뮬레이션")
                fallback_label.setStyleSheet("""
                    background-color: #e7f3ff;
                    border: 1px solid #007bff;
                    border-radius: 4px;
                    padding: 8px;
                    font-size: 11px;
                    color: #007bff;
                    text-align: center;
                    font-weight: bold;
                """)
                fallback_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
                layout.addWidget(fallback_label)
            
            # 구분선
            separator = QFrame()
            separator.setFrameShape(QFrame.Shape.HLine)
            separator.setFrameShadow(QFrame.Shadow.Sunken)
            separator.setStyleSheet("color: #dee2e6; margin: 5px 0;")
            layout.addWidget(separator)
            
            # 시뮬레이션 버튼들 - 원본과 동일
            simulation_buttons = [
                ("상승 추세", "상승 추세 시나리오", "#28a745"),
                ("하락 추세", "하락 추세 시나리오", "#dc3545"),
                ("급등", "급등 시나리오", "#007bff"),
                ("급락", "급락 시나리오", "#fd7e14"),
                ("횡보", "횡보 시나리오", "#6c757d"),
                ("이동평균 교차", "이동평균 교차", "#17a2b8")
            ]
            
            # 그리드 레이아웃 생성 (3행 2열)
            grid_layout = QGridLayout()
            grid_layout.setSpacing(3)  # 버튼 간격
            
            for i, (icon_text, tooltip, color) in enumerate(simulation_buttons):
                btn = QPushButton(icon_text)
                btn.setToolTip(tooltip)
                btn.setFixedHeight(35)  # 버튼 높이
                btn.setMinimumWidth(120)  # 최소 너비
                btn.setStyleSheet(f"""
                    QPushButton {{
                        background-color: {color};
                        color: white;
                        border: none;
                        border-radius: 6px;
                        padding: 6px 8px;
                        font-size: 11px;
                        font-weight: bold;
                        margin: 1px;
                        text-align: center;
                    }}
                    QPushButton:hover {{
                        background-color: {color}dd;
                    }}
                    QPushButton:pressed {{
                        background-color: {color}aa;
                    }}
                """)
                btn.clicked.connect(lambda checked, scenario=icon_text: self.run_simulation(scenario))
                
                # 3행 2열로 배치
                row = i // 2  # 0, 0, 1, 1, 2, 2
                col = i % 2   # 0, 1, 0, 1, 0, 1
                grid_layout.addWidget(btn, row, col)
            
            # 그리드 레이아웃을 메인 레이아웃에 추가
            layout.addLayout(grid_layout)
            
            layout.addStretch()
            
            # 시뮬레이션 상태 (원본과 동일)
            self.simulation_status = QLabel("Select a trigger and click a scenario")
            self.simulation_status.setStyleSheet("""
                background-color: #f8f9fa;
                border: 2px solid #dee2e6;
                border-radius: 8px;
                padding: 8px;
                font-size: 10px;
                color: #495057;
                font-weight: bold;
                text-align: center;
            """)
            self.simulation_status.setAlignment(Qt.AlignmentFlag.AlignCenter)
            layout.addWidget(self.simulation_status)
            
            group.setLayout(layout)
            return group
    
    def create_trigger_detail_area(self):
        """5: 선택한 트리거 상세 정보 영역"""
        if REFACTORED_COMPONENTS_AVAILABLE:
            # 새로운 컴포넌트 사용
            trigger_detail_widget = TriggerDetailWidget(self)
            
            # 기존 위젯 참조 유지 (호환성)
            self.detail_text = trigger_detail_widget.detail_text
            
            return trigger_detail_widget
        else:
            # 기존 구현 유지
            group = QGroupBox("📊 트리거 상세정보")
            layout = QVBoxLayout()
            layout.setContentsMargins(5, 8, 5, 5)
            layout.setSpacing(3)
            
            # 상세 정보 표시
            self.detail_text = QTextEdit()
            self.detail_text.setReadOnly(True)
            self.detail_text.setMaximumHeight(200)
            
            # 폰트 크기를 적절하게 설정 (원본과 동일)
            font = QFont()
            font.setPointSize(24)  # 8 → 11로 변경
            self.detail_text.setFont(font)
            
            # 문서 여백을 줄여서 줄간격 최소화
            document = self.detail_text.document()
            document.setDocumentMargin(3)
            
            self.detail_text.setPlainText("트리거를 선택하면 상세정보가 표시됩니다.")
            layout.addWidget(self.detail_text)
            
            group.setLayout(layout)
            return group
    
    def create_test_result_area(self):
        """6: 작동 마커 차트 + 작동 기록 영역"""
        if REFACTORED_COMPONENTS_AVAILABLE:
            # 새로운 컴포넌트 사용
            simulation_result_widget = SimulationResultWidget(self)
            
            # 기존 위젯 참조 유지 (호환성) - 원본에 있는 것만
            self.test_history_list = simulation_result_widget.test_history_list
            
            # 차트 참조 연결 (SimulationResultWidget의 figure를 메인에서 사용할 수 있도록)
            if hasattr(simulation_result_widget, 'figure'):
                self.figure = simulation_result_widget.figure
                self.canvas = simulation_result_widget.canvas
                print("✅ SimulationResultWidget의 차트를 메인 클래스에 연결")
            else:
                print("⚠️ SimulationResultWidget에 figure 속성이 없습니다.")
            
            return simulation_result_widget
        else:
            # 기존 구현 유지
            group = QGroupBox("📈 작동 마커 차트 & 기록")
            layout = QVBoxLayout()
            layout.setContentsMargins(5, 8, 5, 5)
            layout.setSpacing(3)
            
            # 탭 버튼들
            tab_layout = QHBoxLayout()
            tab_layout.setSpacing(2)
            
            self.chart_tab_btn = QPushButton("📈 차트")
            self.chart_tab_btn.setMaximumHeight(25)
            self.chart_tab_btn.setCheckable(True)
            self.chart_tab_btn.setChecked(True)
            self.chart_tab_btn.clicked.connect(lambda: self.switch_test_tab("chart"))
            tab_layout.addWidget(self.chart_tab_btn)
            
            self.log_tab_btn = QPushButton("📋 기록")
            self.log_tab_btn.setMaximumHeight(25)
            self.log_tab_btn.setCheckable(True)
            self.log_tab_btn.clicked.connect(lambda: self.switch_test_tab("log"))
            tab_layout.addWidget(self.log_tab_btn)
            
            layout.addLayout(tab_layout)
            
            # 차트 영역
            self.chart_widget = self.create_chart_widget()
            layout.addWidget(self.chart_widget)
            
            # 기록 영역 (초기에는 숨김)
            self.log_widget = QTextEdit()
            self.log_widget.setReadOnly(True)
            self.log_widget.setVisible(False)
            self.log_widget.setMaximumHeight(200)
            
            # 기록 위젯도 폰트 크기 조정
            log_font = QFont()
            log_font.setPointSize(7)
            log_font.setFamily("Consolas")
            self.log_widget.setFont(log_font)
            
            # 기록 위젯 문서 여백 설정
            log_document = self.log_widget.document()
            log_document.setDocumentMargin(2)
            
            self.log_widget.setPlainText("시뮬레이션 실행 기록이 여기에 표시됩니다.")
            layout.addWidget(self.log_widget)
            
            group.setLayout(layout)
            return group
    
    def create_chart_widget(self):
        """차트 위젯 생성"""
        print(f"🔍 차트 위젯 생성 시도: CHART_AVAILABLE={CHART_AVAILABLE}")
        
        if CHART_AVAILABLE:
            try:
                print("📊 matplotlib 차트 생성 중...")
                # matplotlib 차트 생성
                self.figure = Figure(figsize=(6, 3), dpi=80)
                self.canvas = FigureCanvas(self.figure)
                self.canvas.setMaximumHeight(200)
                
                print("✅ 차트 위젯 생성 성공")
                
                # 초기 차트 그리기
                self.update_chart_display()
                
                return self.canvas
            except Exception as e:
                print(f"⚠️ 차트 위젯 생성 실패: {e}")
                import traceback
                traceback.print_exc()
        else:
            print("⚠️ CHART_AVAILABLE이 False이므로 폴백 위젯 생성")
        
        # 폴백: 텍스트 위젯
        chart_text = QTextEdit()
        chart_text.setReadOnly(True)
        chart_text.setMaximumHeight(200)
        chart_text.setPlainText("📈 차트 라이브러리를 로드할 수 없습니다.\n시뮬레이션 결과가 텍스트로 표시됩니다.")
        return chart_text
    
    def update_chart_display(self):
        """차트 업데이트"""
        if not CHART_AVAILABLE or not hasattr(self, 'figure'):
            return
        
        try:
            self.figure.clear()
            ax = self.figure.add_subplot(111)
            
            # 임시 데이터 생성
            dates = pd.date_range(start='2024-01-01', periods=30, freq='D')
            prices = np.random.randn(30).cumsum() + 100
            
            ax.plot(dates, prices, 'b-', linewidth=1, label='가격')
            ax.set_title('트리거 작동 마커', fontsize=10)
            ax.set_ylabel('가격', fontsize=8)
            ax.tick_params(axis='both', which='major', labelsize=7)
            ax.grid(True, alpha=0.3)
            
            # 레이아웃 조정
            self.figure.tight_layout(pad=1.0)
            self.canvas.draw()
            
        except Exception as e:
            print(f"⚠️ 차트 업데이트 실패: {e}")
    
    def switch_test_tab(self, tab_name):
        """테스트 결과 탭 전환"""
        if tab_name == "chart":
            self.chart_tab_btn.setChecked(True)
            self.log_tab_btn.setChecked(False)
            self.chart_widget.setVisible(True)
            self.log_widget.setVisible(False)
        elif tab_name == "log":
            self.chart_tab_btn.setChecked(False)
            self.log_tab_btn.setChecked(True)
            self.chart_widget.setVisible(False)
            self.log_widget.setVisible(True)
    
    def load_trigger_list(self):
        """트리거 목록 로드"""
        try:
            self.trigger_tree.clear()
            
            # 저장된 조건들을 트리거로 표시
            conditions = self.storage.get_all_conditions()
            
            for condition in conditions:
                item = QTreeWidgetItem([
                    condition.get('name', 'Unknown'),
                    condition.get('created_at', 'Unknown'),
                    "활성" if condition.get('active', True) else "비활성"
                ])
                item.setData(0, Qt.ItemDataRole.UserRole, condition)
                self.trigger_tree.addTopLevelItem(item)
            
            # 컬럼 너비 조정
            self.trigger_tree.resizeColumnToContents(0)
            self.trigger_tree.resizeColumnToContents(1)
            self.trigger_tree.resizeColumnToContents(2)
            
            print(f"✅ 트리거 목록 로드 완료: {len(conditions)}개")
            
        except Exception as e:
            print(f"❌ 트리거 목록 로드 실패: {e}")
    
    def on_trigger_selected(self, item, column):
        """트리거 선택 처리"""
        try:
            condition = item.data(0, Qt.ItemDataRole.UserRole)
            if condition:
                self.selected_condition = condition
                self.update_trigger_detail(condition)
                print(f"✅ 트리거 선택: {condition.get('name', 'Unknown')}")
        except Exception as e:
            print(f"❌ 트리거 선택 처리 실패: {e}")
    
    def update_trigger_detail(self, condition):
        """트리거 상세정보 업데이트 - 원본 형식 정확 복제"""
        try:
            if not condition:
                self.detail_text.setPlainText("Select a trigger to view details.")
                return
            
            # 조건명에 ID 표시 추가 (원본과 동일)
            condition_id = condition.get('id', 'Unknown')
            condition_name_with_id = f"{condition.get('name', 'Unknown')} [ID:{condition_id}]"
            
            # 외부변수 정보 추출 (원본과 동일한 방식)
            external_variable_info = condition.get('external_variable', None)
            variable_params = condition.get('variable_params', {})
            comparison_type = condition.get('comparison_type', 'Unknown')
            target_value = condition.get('target_value', 'Unknown')
            
            # 외부변수 사용 여부 판정
            use_external = comparison_type == 'external' and external_variable_info is not None
            
            # 추세 방향성 정보
            trend_direction = condition.get('trend_direction', 'both')  # 기본값 변경
            trend_names = {
                'static': '추세 무관',  # 호환성을 위해 유지
                'rising': '상승 추세',
                'falling': '하락 추세',
                'both': '추세 무관'
            }
            trend_text = trend_names.get(trend_direction, trend_direction)
            
            # 연산자에 추세 방향성 포함 (모든 방향성 표시)
            operator = condition.get('operator', 'Unknown')
            operator_with_trend = f"{operator} ({trend_text})"
            
            # 비교 설정 정보 상세화 (원본과 동일)
            if comparison_type == 'external' and use_external:
                if external_variable_info and isinstance(external_variable_info, dict):
                    ext_var_name = external_variable_info.get('variable_name', '알 수 없음')
                    ext_var_id = external_variable_info.get('variable_id', '알 수 없음')
                    
                    # 외부변수 파라미터는 condition_dialog에서 다시 로드할 때만 확인 가능
                    # 데이터베이스에서는 external_variable 객체에 parameters가 있을 수 있음
                    ext_param_values = {}
                    if 'parameters' in external_variable_info:
                        ext_param_values = external_variable_info.get('parameters', {})
                    elif 'variable_params' in external_variable_info:
                        ext_param_values = external_variable_info.get('variable_params', {})
                    
                    if ext_param_values:
                        comparison_info = (f"  • 연산자: {operator_with_trend}\n"
                                          f"  • 비교 타입: 외부변수 비교\n"
                                          f"  • 외부변수: {ext_var_name}\n"
                                          f"  • 외부변수 파라미터: {ext_param_values}")
                    else:
                        comparison_info = (f"  • 연산자: {operator_with_trend}\n"
                                          f"  • 비교 타입: 외부변수 비교\n"
                                          f"  • 외부변수: {ext_var_name}\n"
                                          f"  • 외부변수 파라미터: 저장되지 않음")
                else:
                    comparison_info = (f"  • 연산자: {operator_with_trend}\n"
                                      f"  • 비교 타입: 외부변수 비교 (설정 오류)\n"
                                      f"  • 대상값: {target_value}")
            else:
                comparison_info = (f"  • 연산자: {operator_with_trend}\n"
                                  f"  • 비교 타입: 고정값 비교\n"
                                  f"  • 대상값: {target_value}")
            
            # 상세 정보 표시 (원본과 동일한 형식)
            detail_text = f"""🎯 조건명: {condition_name_with_id}
📝 설명: {condition.get('description', 'No description')}

📊 변수 정보:
  • 기본 변수: {condition.get('variable_name', 'Unknown')}
  • 기본 변수 파라미터: {variable_params}

⚖️ 비교 설정:
{comparison_info}

� 생성일: {condition.get('created_at', 'Unknown')}"""
            
            self.detail_text.setPlainText(detail_text)
            
        except Exception as e:
            print(f"❌ 트리거 상세정보 업데이트 실패: {e}")
            self.detail_text.setPlainText(f"❌ 상세정보 로드 실패: {str(e)}")
    
    def load_condition_for_edit(self, condition_data):
        """편집을 위한 조건 로드 - 원본 기능 복제"""
        try:
            if hasattr(self, 'condition_dialog') and hasattr(self.condition_dialog, 'load_condition'):
                self.condition_dialog.load_condition(condition_data)
                print(f"✅ 편집용 조건 로드 완료: {condition_data.get('name', 'Unknown')}")
            else:
                QMessageBox.warning(self, "⚠️ 경고", "조건 빌더를 찾을 수 없습니다.")
        except Exception as e:
            print(f"❌ 편집용 조건 로드 실패: {e}")
            QMessageBox.critical(self, "❌ 오류", f"조건 로드 중 오류가 발생했습니다:\n{e}")
    
    def cancel_edit_mode(self):
        """편집 모드 취소 - 원본 기능 복제"""
        try:
            # 조건 빌더 편집 모드 해제
            if hasattr(self, 'condition_dialog'):
                if hasattr(self.condition_dialog, 'exit_edit_mode'):
                    self.condition_dialog.exit_edit_mode()
                
                # 조건 빌더 완전 초기화
                if hasattr(self.condition_dialog, 'clear_all_inputs'):
                    self.condition_dialog.clear_all_inputs()
                    print("✅ 조건 빌더 초기화 완료")
            
            print("✅ 편집 모드 취소 완료")
            
        except Exception as e:
            print(f"❌ 편집 모드 취소 실패: {e}")
            QMessageBox.critical(self, "❌ 오류", f"편집 모드 취소 중 오류가 발생했습니다:\n{e}")
    
    def on_edit_mode_changed(self, is_edit_mode: bool):
        """편집 모드 변경 핸들러 - 트리거 리스트에서 받은 시그널 처리"""
        try:
            # 조건 빌더의 편집 모드도 동기화
            if hasattr(self, 'condition_dialog'):
                if hasattr(self.condition_dialog, 'edit_mode'):
                    self.condition_dialog.edit_mode = is_edit_mode
                    
                # 편집 모드 변경 시그널 발송
                if hasattr(self.condition_dialog, 'edit_mode_changed'):
                    self.condition_dialog.edit_mode_changed.emit(is_edit_mode)
            
            print(f"✅ 편집 모드 변경: {'편집 모드' if is_edit_mode else '일반 모드'}")
            
        except Exception as e:
            print(f"❌ 편집 모드 변경 처리 실패: {e}")
    
    # 트리거 관리 메서드들
    # def new_trigger(self):
    #     """새 트리거 생성 - 원본에는 없는 기능 (조건 빌더에서 직접 저장)"""
    #     try:
    #         if hasattr(self, 'condition_dialog'):
    #             if hasattr(self.condition_dialog, 'clear_all_inputs'):
    #                 self.condition_dialog.clear_all_inputs()
    #             print("✅ 새 트리거 생성 모드")
    #         else:
    #             QMessageBox.information(self, "ℹ️ 알림", "조건 빌더를 사용하여 새 트리거를 생성하세요.")
    #     except Exception as e:
    #         print(f"❌ 새 트리거 생성 실패: {e}")
    
    def save_current_condition(self):
        """트리거 저장 - 원본 기능 (조건 빌더에서 처리)"""
        try:
            if hasattr(self, 'condition_dialog'):
                if hasattr(self.condition_dialog, 'save_condition'):
                    self.condition_dialog.save_condition()
                    self.load_trigger_list()  # 저장 후 리스트 새로고침
                    print("✅ 트리거 저장 완료")
                else:
                    QMessageBox.information(self, "💾 저장", "조건 빌더에서 트리거를 저장해주세요.")
            else:
                QMessageBox.information(self, "💾 저장", "조건 빌더를 먼저 설정해주세요.")
        except Exception as e:
            print(f"❌ 트리거 저장 실패: {e}")
            QMessageBox.critical(self, "❌ 오류", f"트리거 저장 중 오류가 발생했습니다:\n{e}")
    
    def cancel_edit_trigger(self):
        """편집 취소 - 원본 기능"""
        try:
            if hasattr(self, 'condition_dialog'):
                if hasattr(self.condition_dialog, 'clear_all_inputs'):
                    self.condition_dialog.clear_all_inputs()
                print("✅ 편집 취소")
            QMessageBox.information(self, "❌ 취소", "편집이 취소되었습니다.")
        except Exception as e:
            print(f"❌ 편집 취소 실패: {e}")
    
    def edit_trigger(self):
        """트리거 편집"""
        try:
            if not self.selected_condition:
                QMessageBox.warning(self, "⚠️ 경고", "편집할 트리거를 선택하세요.")
                return
            
            if hasattr(self, 'condition_dialog'):
                self.condition_dialog.load_condition(self.selected_condition)
                print(f"✅ 트리거 편집 모드: {self.selected_condition.get('name', 'Unknown')}")
            else:
                QMessageBox.information(self, "ℹ️ 알림", "조건 빌더를 사용하여 트리거를 편집하세요.")
        except Exception as e:
            print(f"❌ 트리거 편집 실패: {e}")
    
    def delete_trigger(self):
        """트리거 삭제"""
        try:
            if not self.selected_condition:
                QMessageBox.warning(self, "⚠️ 경고", "삭제할 트리거를 선택하세요.")
                return
            
            reply = QMessageBox.question(
                self, "🗑️ 삭제 확인",
                f"'{self.selected_condition.get('name', 'Unknown')}' 트리거를 삭제하시겠습니까?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No
            )
            
            if reply == QMessageBox.StandardButton.Yes:
                condition_id = self.selected_condition.get('id')
                if condition_id:
                    self.storage.delete_condition(condition_id)
                    self.load_trigger_list()
                    self.detail_text.setPlainText("트리거를 선택하면 상세정보가 표시됩니다.")
                    self.selected_condition = None
                    print(f"✅ 트리거 삭제 완료: {condition_id}")
        except Exception as e:
            print(f"❌ 트리거 삭제 실패: {e}")
            QMessageBox.critical(self, "❌ 오류", f"삭제 중 오류가 발생했습니다:\n{e}")
    
    def copy_trigger(self):
        """트리거 복사"""
        try:
            if not self.selected_condition:
                QMessageBox.warning(self, "⚠️ 경고", "복사할 트리거를 선택하세요.")
                return
            
            # 조건 복사
            copied_condition = self.selected_condition.copy()
            copied_condition['name'] = f"{copied_condition['name']} (복사본)"
            copied_condition.pop('id', None)  # ID 제거
            
            if hasattr(self, 'condition_dialog'):
                self.condition_dialog.load_condition(copied_condition)
                print(f"✅ 트리거 복사 완료: {copied_condition.get('name', 'Unknown')}")
            else:
                QMessageBox.information(self, "ℹ️ 알림", "조건 빌더를 사용하여 복사된 트리거를 편집하세요.")
        except Exception as e:
            print(f"❌ 트리거 복사 실패: {e}")
    
    def run_simulation(self, scenario):
        """시뮬레이션 실행 - 실제 시장 데이터 사용, 원래처럼 차트와 로그에 바로 출력"""
        if not self.selected_condition:
            print("⚠️ 트리거를 선택하세요.")
            return
        
        condition_name = self.selected_condition.get('name', 'Unknown')
        variable_name = self.selected_condition.get('variable_name', 'Unknown')
        operator = self.selected_condition.get('operator', '>')
        target_value = self.selected_condition.get('target_value', '0')
        comparison_type = self.selected_condition.get('comparison_type', 'fixed')
        external_variable = self.selected_condition.get('external_variable')
        
        # 상세 트리거 정보 로깅
        print(f"\n🎯 실제 데이터 시뮬레이션 시작: {scenario}")
        print(f"   조건명: {condition_name}")
        print(f"   변수: {variable_name} {operator} {target_value}")
        
        # target_value 검증 및 기본값 설정
        if target_value is None or target_value == '':
            target_value = '0'
        
        # 시뮬레이션 상태 업데이트
        self.simulation_status.setText(f"🧮 계산 중: {scenario} 시나리오...")
        
        # 시나리오별 가상 데이터 생성
        simulation_data = self.generate_simulation_data(scenario, variable_name)
        
        print(f"📊 시뮬레이션 데이터: {simulation_data}")
        
        # 조건 평가
        try:
            current_value = simulation_data['current_value']
            
            # 외부변수 사용 여부에 따른 계산
            if comparison_type == 'external' and external_variable:
                # 외부변수와 비교하는 경우
                print("🔗 외부변수 비교 모드")
                # 외부변수도 같은 시나리오로 시뮬레이션
                ext_var_name = external_variable.get('variable_name', 'unknown')
                external_simulation = self.generate_simulation_data(scenario, ext_var_name)
                target_num = external_simulation['current_value']
                print(f"   외부변수 값: {target_num}")
            else:
                # 고정값과 비교하는 경우
                print("📌 고정값 비교 모드")
                target_num = float(str(target_value))
            
            print(f"⚖️ 비교: {current_value:.4f} {operator} {target_num:.4f}")
            
            # 연산자에 따른 결과 계산
            if operator == '>':
                result = current_value > target_num
            elif operator == '>=':
                result = current_value >= target_num
            elif operator == '<':
                result = current_value < target_num
            elif operator == '<=':
                result = current_value <= target_num
            elif operator == '~=':  # 근사값 (±1%)
                if target_num != 0:
                    diff_percent = abs(current_value - target_num) / abs(target_num) * 100
                    result = diff_percent <= 1.0
                    print(f"   근사값 차이: {diff_percent:.2f}%")
                else:
                    result = abs(current_value) <= 0.01
            elif operator == '!=':
                result = current_value != target_num
            else:
                result = False
                print(f"❓ 알 수 없는 연산자: {operator}")
                
        except (ValueError, ZeroDivisionError) as e:
            result = False
            current_value = 0
            target_num = 0
            print(f"❌ 계산 오류: {e}")
        
        # 결과 로깅
        result_text = "✅ PASS" if result else "❌ FAIL"
        status_text = "조건 충족" if result else "조건 불충족"
        
        print(f"� 최종 결과: {result_text}")
        print(f"   상태: {status_text}")
        print(f"   데이터 소스: {simulation_data.get('data_source', 'unknown')}")
        
        # 차트 업데이트 (실제 트리거 포인트 계산) - 원본과 동일한 로직
        trigger_points = []
        if hasattr(self, 'simulation_result_widget'):
            # 차트용 목표값 설정 (외부변수 고려)
            chart_target_value = target_num  # 계산된 실제 목표값 사용
            
            # 변수 타입에 따른 적절한 데이터 생성
            if 'rsi' in variable_name.lower():
                # RSI용 데이터 (0-100 범위)
                data_for_chart = self.generate_rsi_data_for_chart(scenario, 50)
                trigger_points = self.calculate_trigger_points(data_for_chart, operator, target_num)
                
                chart_simulation_data = {
                    'scenario': scenario,
                    'price_data': data_for_chart,  # RSI 값들
                    'current_value': current_value,
                    'target_value': chart_target_value,  # 수정된 목표값
                    'data_type': 'rsi'
                }
            elif 'macd' in variable_name.lower():
                # MACD용 데이터 (-2 ~ 2 범위)
                data_for_chart = self.generate_macd_data_for_chart(scenario, 50)
                trigger_points = self.calculate_trigger_points(data_for_chart, operator, target_num)
                
                chart_simulation_data = {
                    'scenario': scenario,
                    'price_data': data_for_chart,  # MACD 값들
                    'current_value': current_value,
                    'target_value': chart_target_value,  # 수정된 목표값
                    'data_type': 'macd'
                }
            else:
                # 가격용 데이터 (기존 로직)
                price_data = self.generate_price_data_for_chart(scenario, 50)
                trigger_points = self.calculate_trigger_points(price_data, operator, target_num)
                
                chart_simulation_data = {
                    'scenario': scenario,
                    'price_data': price_data,
                    'current_value': current_value,
                    'target_value': chart_target_value,  # 수정된 목표값
                    'data_type': 'price'
                }
            
            trigger_results = {
                'trigger_points': trigger_points,
                'trigger_activated': result,
                'total_signals': len(trigger_points)
            }
            
            print(f"📊 트리거 포인트 계산 완료: {len(trigger_points)}개 신호 발견")
            # 차트 위젯에 시뮬레이션 결과 업데이트
            self.simulation_result_widget.update_chart_with_simulation_results(chart_simulation_data, trigger_results)
        
        # 상태 업데이트 (신호 개수 포함) - 원본과 동일
        self.simulation_status.setText(
            f"{result_text}: {scenario}\n"
            f"현재: {current_value:.2f} {operator} {target_num:.2f}\n"
            f"결과: {status_text}\n"
            f"발견된 신호: {len(trigger_points)}개"
        )
        
        # 테스트 기록에 상세 정보 추가 (신호 개수 포함) - 원본과 동일
        detail_info = f"{result_text} {scenario} - {condition_name} ({status_text}, {len(trigger_points)}신호)"
        self.add_test_history_item(detail_info, "test")
        
        # 시그널 발생
        self.condition_tested.emit(self.selected_condition, result)
        
        # 차트 업데이트 - 실제 시뮬레이션 데이터 사용
        if CHART_AVAILABLE:
            price_data = simulation_data.get('price_data', [])
            # 트리거 포인트 계산
            trigger_points = self.calculate_trigger_points(price_data, operator, target_num)
            
            self.update_chart_with_scenario(scenario, {
                'result': result_text,
                'target_value': target_num,
                'current_value': current_value,
                'price_data': price_data,
                'trigger_points': trigger_points
            })
        
        print(f"Simulation: {scenario} -> {result} (value: {current_value})")
    
    def generate_simulation_data(self, scenario, variable_name):
        """시뮬레이션 데이터 생성 - 시뮬레이션 엔진 사용"""
        # 한국어 시나리오를 영어로 매핑
        scenario_mapping = {
            '상승 추세': 'bull_market',
            '하락 추세': 'bear_market',
            '횡보': 'sideways',
            '급등': 'surge',
            '급락': 'crash'
        }
        
        mapped_scenario = scenario_mapping.get(scenario, scenario)
        return self.simulation_engine.get_scenario_data(mapped_scenario, 100)
    
    def generate_price_data_for_chart(self, scenario, length=50):
        """차트용 가격 데이터 생성 - 시뮬레이션 엔진 사용"""
        # 한국어 시나리오를 영어로 매핑
        scenario_mapping = {
            '상승 추세': 'bull_market',
            '하락 추세': 'bear_market',
            '횡보': 'sideways',
            '급등': 'surge',
            '급락': 'crash'
        }
        
        mapped_scenario = scenario_mapping.get(scenario, scenario)
        scenario_data = self.simulation_engine.get_scenario_data(mapped_scenario, length)
        return scenario_data.get('price_data', [])
    
    def generate_rsi_data_for_chart(self, scenario, length=50):
        """RSI 데이터 생성 - 시뮬레이션 엔진 사용"""
        market_data = self.simulation_engine.load_market_data(length)
        if market_data is not None and 'rsi' in market_data.columns:
            return market_data['rsi'].tolist()
        return [50] * length  # 기본값
    
    def generate_macd_data_for_chart(self, scenario, length=50):
        """MACD 데이터 생성 - 시뮬레이션 엔진 사용"""
        market_data = self.simulation_engine.load_market_data(length)
        if market_data is not None and 'macd' in market_data.columns:
            return market_data['macd'].tolist()
        return [0] * length  # 기본값
    
    def calculate_trigger_points(self, data, operator, target_value):
        """트리거 포인트 계산"""
        trigger_points = []
        for i, value in enumerate(data):
            triggered = False
            if operator == '>':
                triggered = value > target_value
            elif operator == '>=':
                triggered = value >= target_value
            elif operator == '<':
                triggered = value < target_value
            elif operator == '<=':
                triggered = value <= target_value
            elif operator == '~=':
                if target_value != 0:
                    triggered = abs(value - target_value) / abs(target_value) <= 0.01
                else:
                    triggered = abs(value) <= 0.01
            elif operator == '!=':
                triggered = value != target_value
            
            if triggered:
                trigger_points.append(i)
        
        return trigger_points
    
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
    
    def update_simulation_result(self, result):
        """시뮬레이션 결과 업데이트"""
        try:
            current_time = datetime.now().strftime("%H:%M:%S")
            
            # 상태 업데이트
            if hasattr(self, 'simulation_status') and self.simulation_status is not None:
                self.simulation_status.setText(
                    f"✅ {result['scenario']} 완료\n"
                    f"신호: {result['trigger_count']}회, "
                    f"성공률: {result['success_rate']:.1f}%"
                )
            
            # 로그에 추가 (있는 경우)
            if hasattr(self, 'log_widget'):
                log_entry = (
                    f"[{current_time}] {result['scenario']} "
                    f"| 신호: {result['trigger_count']}회 "
                    f"| 성공률: {result['success_rate']:.1f}% "
                    f"| 수익률: {result['profit_loss']:+.2f}%"
                )
                
                current_log = self.log_widget.toPlainText()
                if current_log.strip() == "시뮬레이션 실행 기록이 여기에 표시됩니다.":
                    self.log_widget.setPlainText(log_entry)
                else:
                    self.log_widget.setPlainText(f"{current_log}\n{log_entry}")
        
        except Exception as e:
            print(f"❌ 시뮬레이션 결과 업데이트 실패: {e}")
    
    def on_data_source_changed(self, source):
        """데이터 소스 변경 처리"""
        try:
            if source == "real":
                print("📊 실시간 데이터 소스로 변경")
            else:
                print("📊 시뮬레이션 데이터 소스로 변경")
        except Exception as e:
            print(f"❌ 데이터 소스 변경 처리 실패: {e}")
    
    def run_simulation_scenario(self, scenario):
        """시뮬레이션 시나리오 실행"""
        try:
            if not self.selected_condition:
                QMessageBox.warning(self, "⚠️ 경고", "시뮬레이션할 트리거를 선택하세요.")
                return
            
            print(f"🎮 {scenario} 시뮬레이션 시작")
            
            # 임시 시뮬레이션 결과 생성
            import random
            result = {
                'scenario': scenario,
                'trigger_count': random.randint(3, 15),
                'success_rate': random.uniform(60.0, 90.0),
                'profit_loss': random.uniform(-5.0, 12.0),
                'execution_time': random.uniform(0.1, 0.8)
            }
            
            # 결과 로그에 추가
            self.add_simulation_log(result)
            
            # 차트 업데이트
            if CHART_AVAILABLE:
                self.update_chart_with_scenario(scenario)
            
            print(f"✅ {scenario} 시뮬레이션 완료")
            
        except Exception as e:
            print(f"❌ {scenario} 시뮬레이션 실패: {e}")
    
    def add_simulation_log(self, result):
        """시뮬레이션 결과를 로그에 추가"""
        try:
            from datetime import datetime
            current_time = datetime.now().strftime("%H:%M:%S")
            
            # 결과 포맷팅
            scenario = result.get('scenario', 'Unknown')
            condition_name = result.get('condition_name', 'Unknown')
            test_value = result.get('test_value', 0)
            target_value = result.get('target_value', 0)
            operator = result.get('operator', '>')
            result_text = result.get('result', '❌ FAIL')
            success_rate = result.get('success_rate', 0)
            
            log_entry = (
                f"[{current_time}] {scenario} | {condition_name} | "
                f"{test_value:.0f} {operator} {target_value:.0f} = {result_text} | "
                f"성공률: {success_rate:.0f}%"
            )
            
            # 테스트 히스토리 리스트에 추가
            if hasattr(self, 'test_history_list'):
                item = QListWidgetItem(log_entry)
                # 성공/실패에 따른 색상 설정
                if success_rate > 50:
                    item.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_DialogApplyButton))
                else:
                    item.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_DialogCancelButton))
                
                self.test_history_list.addItem(item)
                self.test_history_list.scrollToBottom()
                
                print(f"✅ 로그 추가됨: {log_entry}")
            
            # 시뮬레이션 상태 업데이트
            if hasattr(self, 'simulation_status'):
                self.simulation_status.setText(f"✅ {scenario} 완료 | {result_text}")
                
        except Exception as e:
            print(f"❌ 시뮬레이션 로그 추가 실패: {e}")
            # 폴백: 콘솔에만 출력
            print(f"시뮬레이션 결과: {result}")
    
    def update_chart_with_scenario(self, scenario_name, simulation_result=None):
        """시나리오에 따른 차트 업데이트 - 실제 시뮬레이션 데이터 사용"""
        print(f"🔍 차트 업데이트 디버깅: CHART_AVAILABLE={CHART_AVAILABLE}, hasattr(self, 'figure')={hasattr(self, 'figure')}")
        
        if not CHART_AVAILABLE:
            print("⚠️ CHART_AVAILABLE이 False입니다.")
            return
            
        if not hasattr(self, 'figure'):
            print("⚠️ self.figure 속성이 없습니다. 차트 위젯이 초기화되지 않았습니다.")
            return
        
        try:
            print(f"📈 차트 업데이트 시작: {scenario_name}")
            self.figure.clear()
            ax = self.figure.add_subplot(111)
            
            # 시뮬레이션 결과가 있으면 실제 시뮬레이션 데이터 사용
            if simulation_result and 'price_data' in simulation_result:
                price_data = simulation_result['price_data']
                trigger_points = simulation_result.get('trigger_points', [])
                current_value = simulation_result.get('current_value', 0)
                target_value = simulation_result.get('target_value', 0)
                
                if price_data and len(price_data) > 0:
                    # X축 (시간/인덱스)
                    x_values = range(len(price_data))
                    
                    # 가격 라인 플롯
                    ax.plot(x_values, price_data, 'b-', linewidth=2, 
                           label=f'{scenario_name} 가격 추세', alpha=0.8)
                    
                    # 목표 가격 라인 표시
                    if target_value > 0:
                        ax.axhline(y=target_value, color='orange', linestyle='--', 
                                  linewidth=1, label=f'목표가: {target_value:,.0f}원', alpha=0.7)
                    
                    # 트리거 포인트 표시
                    if trigger_points and len(trigger_points) > 0:
                        for i, point_idx in enumerate(trigger_points):
                            if 0 <= point_idx < len(price_data):
                                ax.scatter(point_idx, price_data[point_idx], 
                                         c='red', s=50, marker='^', 
                                         label='트리거 발동' if i == 0 else "",
                                         zorder=5, alpha=0.8)
                    
                    # 현재 가격 표시
                    if len(price_data) > 0:
                        last_idx = len(price_data) - 1
                        ax.scatter(last_idx, current_value, 
                                 c='green', s=80, marker='o', 
                                 label=f'현재가: {current_value:,.0f}원',
                                 zorder=6, alpha=0.9)
                    
                    # 차트 스타일링
                    ax.set_title(f'🎯 {scenario_name} 시뮬레이션 결과', 
                               fontsize=12, fontweight='bold', pad=20)
                    ax.set_xlabel('시간 (일)', fontsize=10)
                    ax.set_ylabel('가격 (원)', fontsize=10)
                    ax.grid(True, alpha=0.3)
                    ax.legend(loc='upper left', fontsize=8)
                    
                    # Y축 포맷팅 (원 단위) - 간단한 방식 사용
                    def format_currency(x, pos):
                        return f'{x:,.0f}'
                    
                    from matplotlib.ticker import FuncFormatter
                    ax.yaxis.set_major_formatter(FuncFormatter(format_currency))
                    
                    print(f"📈 차트 업데이트 완료: {scenario_name}, {len(price_data)}개 데이터포인트, {len(trigger_points) if trigger_points else 0}개 트리거")
                    
                else:
                    # 데이터가 없을 때 플레이스홀더
                    ax.text(0.5, 0.5, '시뮬레이션 데이터 없음', 
                           transform=ax.transAxes, ha='center', va='center',
                           fontsize=12, alpha=0.5)
                    ax.set_title('시뮬레이션 결과', fontsize=12)
            
            else:
                # 기본 플레이스홀더 차트
                ax.text(0.5, 0.5, f'{scenario_name} 시나리오\n차트 준비 중...', 
                       transform=ax.transAxes, ha='center', va='center',
                       fontsize=12, alpha=0.6)
                ax.set_title(f'{scenario_name} 차트', fontsize=12)
            
            # 차트 여백 조정 및 다시 그리기
            self.figure.tight_layout(pad=1.0)
            self.canvas.draw()
                
        except Exception as e:
            print(f"❌ 차트 업데이트 중 오류 발생: {e}")
            import traceback
            traceback.print_exc()
            
            # 에러 시 플레이스홀더 표시
            try:
                self.figure.clear()
                ax = self.figure.add_subplot(111)
                ax.text(0.5, 0.5, f'차트 오류\n{str(e)}', 
                       transform=ax.transAxes, ha='center', va='center',
                       fontsize=10, alpha=0.5)
                self.figure.tight_layout(pad=1.0)
                self.canvas.draw()
            except:
                pass
    
    def _create_fallback_chart(self, ax, scenario_name):
        """폴백 차트 생성"""
        import random
        
        # 기본 가격 패턴 생성
        x_values = list(range(30))
        base_price = 50000000  # 5천만원 기준
        
        if "상승" in scenario_name:
            prices = [base_price + i * 1000000 + random.uniform(-500000, 500000) for i in x_values]
        elif "하락" in scenario_name:
            prices = [base_price - i * 800000 + random.uniform(-500000, 500000) for i in x_values]
        else:  # 횡보 등
            prices = [base_price + random.uniform(-2000000, 2000000) for _ in x_values]
        
        ax.plot(x_values, prices, 'b-', linewidth=1.5, label='가격 패턴')
        
        # 랜덤 트리거 포인트
        trigger_points = random.sample(range(5, 25), random.randint(2, 4))
        for point in trigger_points:
            ax.scatter(point, prices[point], c='red', s=30, marker='^', zorder=5)
            
        ax.set_title(f'{scenario_name} (시뮬레이션)', fontsize=10)
    
    # 기존 integrated_condition_manager.py에서 이관된 메서드들
    def filter_triggers(self, text):
        """트리거 필터링"""
        try:
            for i in range(self.trigger_tree.topLevelItemCount()):
                item = self.trigger_tree.topLevelItem(i)
                if item is not None:
                    visible = text.lower() in item.text(0).lower() if text else True
                    item.setHidden(not visible)
        except Exception as e:
            print(f"❌ 트리거 필터링 실패: {e}")
    
    def quick_test_trigger(self):
        """빠른 트리거 테스트"""
        try:
            if not self.selected_condition:
                QMessageBox.warning(self, "⚠️ 경고", "테스트할 트리거를 선택하세요.")
                return
            
            print(f"🧪 빠른 테스트: {self.selected_condition.get('name', 'Unknown')}")
            
            # 간단한 테스트 실행
            self.run_simulation("빠른테스트")
            
        except Exception as e:
            print(f"❌ 빠른 테스트 실패: {e}")
    
    def copy_trigger_info(self):
        """트리거 정보 복사"""
        try:
            if not self.selected_condition:
                QMessageBox.warning(self, "⚠️ 경고", "복사할 트리거를 선택하세요.")
                return
            
            from PyQt6.QtWidgets import QApplication
            clipboard = QApplication.clipboard()
            if hasattr(self, 'detail_text') and self.detail_text is not None:
                clipboard.setText(self.detail_text.toPlainText())
                QMessageBox.information(self, "📋 복사 완료", "트리거 정보가 클립보드에 복사되었습니다.")
            else:
                print("⚠️ 상세 텍스트를 찾을 수 없습니다.")
            
        except Exception as e:
            print(f"❌ 트리거 정보 복사 실패: {e}")
    
    def refresh_all_components(self):
        """모든 컴포넌트 새로고침"""
        try:
            print("🔄 전체 컴포넌트 새로고침")
            
            # 트리거 목록 새로고침
            self.load_trigger_list()
            
            # 조건 다이얼로그 새로고침 (메서드가 있는 경우에만)
            if hasattr(self, 'condition_dialog') and hasattr(self.condition_dialog, 'refresh_all_data'):
                self.condition_dialog.refresh_all_data()
            
            # 차트 초기화
            if CHART_AVAILABLE:
                self.update_chart_display()
            
            # 상세정보 초기화
            if hasattr(self, 'detail_text') and self.detail_text is not None:
                self.detail_text.setPlainText("트리거를 선택하면 상세정보가 표시됩니다.")
            
            # 로그 초기화
            if hasattr(self, 'log_widget') and self.log_widget is not None:
                self.log_widget.setPlainText("시뮬레이션 실행 기록이 여기에 표시됩니다.")
            
            print("✅ 전체 컴포넌트 새로고침 완료")
            
        except Exception as e:
            print(f"❌ 컴포넌트 새로고침 실패: {e}")
    
    def get_selected_trigger(self):
        """선택된 트리거 반환"""
        return self.selected_condition
    
    def clear_all_results(self):
        """모든 결과 초기화"""
        try:
            self.detail_text.setPlainText("트리거를 선택하면 상세정보가 표시됩니다.")
            self.log_widget.setPlainText("시뮬레이션 실행 기록이 여기에 표시됩니다.")
            
            if CHART_AVAILABLE:
                self.update_chart_display()
            
            print("✅ 모든 결과 초기화 완료")
            
        except Exception as e:
            print(f"❌ 결과 초기화 실패: {e}")


# 차트 관련 클래스 추가
class MiniChartWidget(QWidget):
    """미니 차트 위젯"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()
    
    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(2, 2, 2, 2)
        
        if CHART_AVAILABLE:
            try:
                self.figure = Figure(figsize=(4, 2), dpi=80)
                self.canvas = FigureCanvas(self.figure)
                self.canvas.setMaximumHeight(120)
                layout.addWidget(self.canvas)
                
                # 초기 차트 표시
                self.show_placeholder_chart()
                
            except Exception as e:
                print(f"⚠️ 미니 차트 생성 실패: {e}")
                self.add_text_placeholder(layout)
        else:
            self.add_text_placeholder(layout)
    
    def add_text_placeholder(self, layout):
        """텍스트 플레이스홀더 추가"""
        text_widget = QTextEdit()
        text_widget.setReadOnly(True)
        text_widget.setMaximumHeight(120)
        text_widget.setPlainText("📈 차트 영역\n시뮬레이션 결과가 표시됩니다.")
        layout.addWidget(text_widget)
    
    def show_placeholder_chart(self):
        """플레이스홀더 차트 표시"""
        if not CHART_AVAILABLE or not hasattr(self, 'figure'):
            return
        
        try:
            self.figure.clear()
            ax = self.figure.add_subplot(111)
            
            # 플레이스홀더 데이터
            x = range(10)
            y = [0] * 10
            
            ax.plot(x, y, 'b-', linewidth=1)
            ax.set_title('차트 대기 중', fontsize=8)
            ax.set_ylabel('가격', fontsize=7)
            ax.tick_params(axis='both', which='major', labelsize=6)
            ax.grid(True, alpha=0.3)
            
            self.figure.tight_layout(pad=0.5)
            self.canvas.draw()
            
        except Exception as e:
            print(f"⚠️ 플레이스홀더 차트 표시 실패: {e}")
    
    def update_simulation_chart(self, scenario, price_data, trigger_results):
        """시뮬레이션 결과로 차트 업데이트"""
        if not CHART_AVAILABLE or not hasattr(self, 'figure'):
            return
        
        try:
            self.figure.clear()
            ax = self.figure.add_subplot(111)
            
            if price_data:
                # 가격 데이터 플롯
                x = range(len(price_data))
                ax.plot(x, price_data, 'b-', linewidth=1, label='가격')
                
                # 트리거 포인트 표시
                if trigger_results:
                    for i, (triggered, _) in enumerate(trigger_results):
                        if triggered and i < len(price_data):
                            ax.scatter(i, price_data[i], c='red', s=20, marker='^', zorder=5)
            
            ax.set_title(f'{scenario} 결과', fontsize=8)
            ax.set_ylabel('가격', fontsize=7)
            ax.tick_params(axis='both', which='major', labelsize=6)
            ax.grid(True, alpha=0.3)
            
            self.figure.tight_layout(pad=0.5)
            self.canvas.draw()
            
        except Exception as e:
            print(f"⚠️ 시뮬레이션 차트 업데이트 실패: {e}")
    
    def update_chart_with_simulation_data(self, scenario, price_data, trigger_points, current_value, target_value):
        """실제 시뮬레이션 데이터로 차트 업데이트"""
        if not CHART_AVAILABLE or not hasattr(self, 'figure'):
            print("⚠️ 차트 기능을 사용할 수 없습니다.")
            return
        
        try:
            # 차트 클리어
            self.figure.clear()
            ax = self.figure.add_subplot(111)
            
            if price_data and len(price_data) > 0:
                # X축 (시간/인덱스)
                x_values = range(len(price_data))
                
                # 가격 라인 플롯
                ax.plot(x_values, price_data, 'b-', linewidth=2, label=f'{scenario} 가격 추세', alpha=0.8)
                
                # 목표 가격 라인 표시
                if target_value > 0:
                    ax.axhline(y=target_value, color='orange', linestyle='--', linewidth=1, 
                              label=f'목표가: {target_value:,.0f}원', alpha=0.7)
                
                # 트리거 포인트 표시
                if trigger_points and len(trigger_points) > 0:
                    for point_idx in trigger_points:
                        if 0 <= point_idx < len(price_data):
                            ax.scatter(point_idx, price_data[point_idx], 
                                     c='red', s=50, marker='^', 
                                     label='트리거 발동' if point_idx == trigger_points[0] else "",
                                     zorder=5, alpha=0.8)
                
                # 현재 가격 표시
                if len(price_data) > 0:
                    last_idx = len(price_data) - 1
                    ax.scatter(last_idx, current_value, 
                             c='green', s=80, marker='o', 
                             label=f'현재가: {current_value:,.0f}원',
                             zorder=6, alpha=0.9)
                
                # 차트 스타일링
                ax.set_title(f'🎯 {scenario} 시뮬레이션 결과', fontsize=12, fontweight='bold', pad=20)
                ax.set_xlabel('시간 (일)', fontsize=10)
                ax.set_ylabel('가격 (원)', fontsize=10)
                ax.grid(True, alpha=0.3)
                ax.legend(loc='upper left', fontsize=8)
                
                # Y축 포맷팅 (원 단위)
                from matplotlib.ticker import FuncFormatter
                ax.yaxis.set_major_formatter(FuncFormatter(lambda x, p: f'{x:,.0f}'))
                
                # 차트 여백 조정
                self.figure.tight_layout(pad=1.0)
                
                # 차트 다시 그리기
                self.canvas.draw()
                
                print(f"📈 차트 업데이트 완료: {scenario}, {len(price_data)}개 데이터포인트, {len(trigger_points) if trigger_points else 0}개 트리거")
                
            else:
                # 데이터가 없을 때 플레이스홀더
                ax.text(0.5, 0.5, '시뮬레이션 데이터 없음', 
                       transform=ax.transAxes, ha='center', va='center',
                       fontsize=12, alpha=0.5)
                ax.set_title('시뮬레이션 결과', fontsize=12)
                self.figure.tight_layout(pad=1.0)
                self.canvas.draw()
                
        except Exception as e:
            print(f"❌ 차트 업데이트 중 오류 발생: {e}")
            import traceback
            traceback.print_exc()


if __name__ == "__main__":
    from PyQt6.QtWidgets import QApplication
    import sys
    
    app = QApplication(sys.argv)
    
    window = TriggerBuilderScreen()
    window.show()
    
    sys.exit(app.exec())
