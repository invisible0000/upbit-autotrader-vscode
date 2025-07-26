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
from PyQt6.QtCore import Qt, pyqtSignal, QTimer
from PyQt6.QtGui import QFont, QPixmap, QIcon
import random

# 공통 스타일 시스템 import
try:
    from upbit_auto_trading.ui.desktop.common.styles.style_manager import StyleManager, Theme
    STYLE_MANAGER_AVAILABLE = True
except ImportError:
    STYLE_MANAGER_AVAILABLE = False
    print("⚠️ 공통 스타일 시스템을 로드할 수 없습니다.")

# 공유 컴포넌트들 import
from .trigger_builder.components.shared.chart_visualizer import ChartVisualizer
from .trigger_builder.components.shared.simulation_engines import get_embedded_simulation_engine  
from .trigger_builder.components.shared.trigger_calculator import TriggerCalculator
from .trigger_builder.components.core.simulation_result_widget import SimulationResultWidget

# 새로운 차트 변수 카테고리 시스템 import
try:
    from .trigger_builder.components.shared.chart_variable_service import get_chart_variable_service
    from .trigger_builder.components.shared.variable_display_system import get_variable_registry
    CHART_VARIABLE_SYSTEM_AVAILABLE = True
except ImportError:
    CHART_VARIABLE_SYSTEM_AVAILABLE = False
    print("⚠️ 차트 변수 카테고리 시스템을 로드할 수 없습니다.")

# 차트 라이브러리 import
try:
    import matplotlib.pyplot as plt
    from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
    from matplotlib.figure import Figure
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

from .trigger_builder.components.core.condition_dialog import ConditionDialog
from .components.condition_storage import ConditionStorage
from .components.condition_loader import ConditionLoader
# DataSourceSelectorWidget는 이제 trigger_builder/components에 있음
try:
    from .trigger_builder.components import DataSourceSelectorWidget
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

class IntegratedConditionManager(QWidget):
    """통합 조건 관리 화면 - 3x2 그리드 레이아웃"""
    
    # 시그널 정의
    condition_tested = pyqtSignal(dict, bool)  # 조건, 테스트 결과
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("🎯 통합 조건 관리 시스템")
        # 메인 윈도우에 맞춘 최소 크기 설정 (1280x720)
        self.setMinimumSize(1280, 720)
        self.resize(1600, 1000)  # 초기 크기 설정
        
        # 기존 컴포넌트 초기화
        self.storage = ConditionStorage()
        self.loader = ConditionLoader(self.storage)
        self.selected_condition = None
        
        # 새로운 컴포넌트 초기화
        self.chart_visualizer = ChartVisualizer()  # 기존 호환성 유지
        self.simulation_result_widget = SimulationResultWidget()  # 개선된 차트 시스템
        self.simulation_engine = get_embedded_simulation_engine()
        self.trigger_calculator = TriggerCalculator()
        
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
        
        # 공통 스타일 시스템 적용
        if STYLE_MANAGER_AVAILABLE:
            try:
                self.style_manager = StyleManager()
                self.style_manager.apply_theme()
                print("✅ 공통 스타일 시스템 적용 완료")
            except Exception as e:
                print(f"⚠️ 스타일 적용 실패: {e}")
        else:
            print("⚠️ 공통 스타일 시스템 사용 불가")
    
    def init_ui(self):
        """UI 초기화 - 3x2 그리드 레이아웃"""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(5, 5, 5, 5)  # 원본과 동일한 마진
        main_layout.setSpacing(5)  # 원본과 동일한 간격
        
        # 상단 제목 제거하여 공간 절약
        # self.create_header(main_layout)
        
        # 메인 그리드 레이아웃 (3x2)
        grid_widget = QWidget()
        grid_layout = QGridLayout(grid_widget)
        grid_layout.setContentsMargins(5, 5, 5, 5)  # 원본과 동일한 그리드 마진
        grid_layout.setSpacing(8)  # 원본과 동일한 그리드 간격
        
        # 1+4: 조건 빌더 (좌측, 세로 합쳐짐)
        self.condition_builder_area = self.create_condition_builder_area()
        grid_layout.addWidget(self.condition_builder_area, 0, 0, 2, 1)  # 2행에 걸쳐 배치
        
        # 2: 등록된 트리거 리스트 (중앙 상단)
        self.trigger_list_area = self.create_trigger_list_area()
        grid_layout.addWidget(self.trigger_list_area, 0, 1, 1, 1)
        
        # 3: 케이스 시뮬레이션 버튼들 (우측 상단)
        self.simulation_area = self.create_simulation_area()
        # 고정 너비 제한 제거로 반응형 레이아웃 구현
        grid_layout.addWidget(self.simulation_area, 0, 2, 1, 1)
        
        # 5: 선택한 트리거 상세 정보 (중앙 하단)
        self.trigger_detail_area = self.create_trigger_detail_area()
        grid_layout.addWidget(self.trigger_detail_area, 1, 1, 1, 1)
        
        # 6: 작동 마커 차트 + 작동 기록 (우측 하단)
        self.test_result_area = self.create_test_result_area()
        # 고정 너비 제한 제거로 반응형 레이아웃 구현
        grid_layout.addWidget(self.test_result_area, 1, 2, 1, 1)
        
        # 그리드 비율 설정 - 원본 트리거 빌더와 동일 (17:30:20)
        grid_layout.setColumnStretch(0, 17)  # 조건 빌더
        grid_layout.setColumnStretch(1, 30)  # 트리거 관리 (가장 넓게)
        grid_layout.setColumnStretch(2, 20)  # 시뮬레이션
        
        # 행 비율 설정 - 원본과 동일
        grid_layout.setRowStretch(0, 1)  # 상단
        grid_layout.setRowStretch(1, 1)  # 하단
        
        main_layout.addWidget(grid_widget)
        
        print("✅ 통합 조건 관리 시스템 UI 초기화 완료")
    
    def create_header(self, layout):
        """상단 헤더 생성 - 공통 스타일 시스템 사용"""
        header_widget = QWidget()
        # 하드코딩된 스타일 제거 - 공통 스타일 시스템에 의존
        header_widget.setObjectName("headerWidget")  # CSS 선택자용 이름 설정
        header_layout = QHBoxLayout(header_widget)
        header_layout.setContentsMargins(5, 5, 5, 5)
        
        # 제목
        title_label = QLabel("🎯 통합 조건 관리 시스템")
        title_label.setObjectName("titleLabel")  # CSS 선택자용 이름 설정
        # 하드코딩된 스타일 제거
        header_layout.addWidget(title_label)
        
        header_layout.addStretch()
        
        # 전체 새로고침 버튼 - 공통 컴포넌트 사용
        refresh_btn = PrimaryButton("🔄 전체 새로고침")
        # 하드코딩된 스타일 제거 - 공통 스타일이 적용됨
        refresh_btn.clicked.connect(self.refresh_all)
        header_layout.addWidget(refresh_btn)
        
        layout.addWidget(header_widget)
    
    def create_condition_builder_area(self):
        """영역 1+4: 조건 빌더 (좌측 통합) - 통일된 테두리 스타일"""
        group = QGroupBox("🎯 조건 빌더")
        group.setStyleSheet("""
            QGroupBox {
                background-color: white;
                border: 2px solid #ddd;
                border-radius: 8px;
                font-weight: bold;
                padding-top: 12px;
                margin: 2px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 15px;
                padding: 0 8px 0 8px;
                background-color: white;
                color: #2c3e50;
                font-size: 11px;
                font-weight: bold;
                border-radius: 4px;
                border: 1px solid #2c3e50;
            }
        """)
        layout = QVBoxLayout(group)
        layout.setContentsMargins(8, 8, 8, 8)  # 패딩 줄이기
        
        try:
            # 우리의 조건 다이얼로그를 위젯으로 임베드
            self.condition_dialog = ConditionDialog()
            self.condition_dialog.setParent(group)
            
            # 다이얼로그를 위젯으로 변환 (창 모드 해제)
            self.condition_dialog.setWindowFlags(Qt.WindowType.Widget)
            
            # 시그널 연결
            self.condition_dialog.condition_saved.connect(self.on_condition_saved)
            self.condition_dialog.edit_mode_changed.connect(self.update_edit_button_state)
            
            layout.addWidget(self.condition_dialog)
            
        except Exception as e:
            print(f"❌ 조건 빌더 로딩 실패: {e}")
            
            # 대체 위젯
            error_label = QLabel(f"조건 빌더 로딩 실패: {e}")
            error_label.setObjectName("errorLabel")  # CSS 선택자용 이름 설정
            # 하드코딩된 스타일 제거
            layout.addWidget(error_label)
        
        return group
    
    def create_trigger_list_area(self):
        """영역 2: 등록된 트리거 리스트 (중앙 상단) - 공통 스타일 시스템 사용"""
        group = QGroupBox("📋 등록된 트리거 리스트")
        group.setObjectName("triggerListGroup")  # CSS 선택자용 이름 설정
        # 하드코딩된 스타일 제거 - 공통 스타일 시스템에 의존
        layout = QVBoxLayout(group)
        layout.setContentsMargins(8, 8, 8, 8)
        
        # 트리거 검색
        search_layout = QHBoxLayout()
        search_label = QLabel("🔍")
        search_layout.addWidget(search_label)
        
        self.search_input = StyledLineEdit()
        self.search_input.setPlaceholderText("트리거 검색...")
        search_layout.addWidget(self.search_input)
        layout.addLayout(search_layout)
        
        # 트리거 트리 위젯 - 공통 스타일 시스템 사용
        self.trigger_tree = QTreeWidget()
        self.trigger_tree.setHeaderLabels(["트리거명", "변수", "조건"])
        self.trigger_tree.setObjectName("triggerTree")  # CSS 선택자용 이름 설정
        
        # 트리 구조 제거로 텍스트 간격 문제 해결
        self.trigger_tree.setRootIsDecorated(False)  # 루트 노드 장식 제거
        self.trigger_tree.setIndentation(0)  # 들여쓰기 완전 제거
        
        # 열 폭 설정 (트리거명 폭 10% 줄임)
        self.trigger_tree.setColumnWidth(0, 180)  # 트리거명 폭 (200 → 180)
        self.trigger_tree.setColumnWidth(1, 120)  # 변수 폭
        self.trigger_tree.setColumnWidth(2, 140)  # 조건 폭 (외부변수 정보 포함으로 늘림)
        
        self.trigger_tree.setStyleSheet("""
            QTreeWidget {
                border: 1px solid #cccccc;
                gridline-color: #e0e0e0;
                background-color: white;
                border-radius: 4px;
            }
            QTreeWidget::item {
                padding: 4px 8px;  /* 좌우 패딩 조정으로 텍스트 간격 개선 */
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
        
        # 통일된 버튼 스타일 정의
        button_base_style = """
            QPushButton {
                color: white;
                border: none;
                padding: 8px 12px;
                border-radius: 4px;
                font-size: 11px;
                font-weight: bold;
                min-height: 16px;
                max-height: 32px;
            }
        """
        
        # 트리거 저장 버튼 추가 (클래스 변수로 저장)
        self.save_btn = QPushButton("💾 트리거 저장")
        self.save_btn.setStyleSheet(button_base_style + """
            QPushButton {
                background-color: #28a745;
            }
            QPushButton:hover {
                background-color: #218838;
            }
            QPushButton:pressed {
                background-color: #1e7e34;
            }
            QPushButton:disabled {
                background-color: #6c757d;
                color: #adb5bd;
            }
        """)
        self.save_btn.clicked.connect(self.save_current_condition)
        
        # 편집 버튼 (동적으로 변경됨) - QPushButton으로 통일
        self.edit_btn = QPushButton("✏️ 편집")
        self.edit_btn.setStyleSheet(button_base_style + """
            QPushButton {
                background-color: #007bff;
            }
            QPushButton:hover {
                background-color: #0056b3;
            }
            QPushButton:pressed {
                background-color: #004085;
            }
        """)
        self.edit_btn.clicked.connect(self.edit_selected_trigger)
        
        # 편집 취소 버튼 (항상 표시)
        self.cancel_edit_btn = QPushButton("❌ 편집 취소")
        self.cancel_edit_btn.setStyleSheet(button_base_style + """
            QPushButton {
                background-color: #6c757d;
            }
            QPushButton:hover {
                background-color: #5a6268;
            }
            QPushButton:pressed {
                background-color: #545b62;
            }
        """)
        self.cancel_edit_btn.clicked.connect(self.cancel_edit_trigger)
        
        # 트리거 복사 버튼 추가
        copy_trigger_btn = QPushButton("📋 복사")
        copy_trigger_btn.setStyleSheet(button_base_style + """
            QPushButton {
                background-color: #17a2b8;
            }
            QPushButton:hover {
                background-color: #138496;
            }
            QPushButton:pressed {
                background-color: #117a8b;
            }
        """)
        copy_trigger_btn.clicked.connect(self.copy_trigger_for_edit)
        
        delete_btn = QPushButton("🗑️ 삭제")
        delete_btn.setStyleSheet(button_base_style + """
            QPushButton {
                background-color: #e74c3c;
            }
            QPushButton:hover {
                background-color: #c0392b;
            }
            QPushButton:pressed {
                background-color: #a93226;
            }
        """)
        delete_btn.clicked.connect(self.delete_selected_trigger)
        
        button_layout.addWidget(self.save_btn)
        button_layout.addWidget(self.edit_btn)
        button_layout.addWidget(self.cancel_edit_btn)  # 편집 취소 버튼 추가
        button_layout.addWidget(copy_trigger_btn)      # 복사 버튼 추가
        button_layout.addWidget(delete_btn)
        button_layout.addStretch()
        
        layout.addLayout(button_layout)
        
        return group
    
    def create_simulation_area(self):
        """영역 3: 케이스 시뮬레이션 버튼들 (우측 상단)"""
        group = QGroupBox("케이스 시뮬레이션")
        group.setStyleSheet(self.get_groupbox_style("#6f42c1"))
        layout = QVBoxLayout(group)
        layout.setContentsMargins(8, 8, 8, 8)  # 패딩 줄이기
        layout.setSpacing(3)  # 간격 줄이기
        
        # 고정 높이 제거하여 자동 크기 조정되도록 함 (트리거 리스트와 동일)
        # group.setFixedHeight(280)  # 이 줄 제거
        
        # 크기 정책도 제거 (트리거 리스트와 동일)
        # from PyQt6.QtWidgets import QSizePolicy
        # group.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        
        # 데이터 소스 선택 위젯 추가 (리팩토링된 위치에서 로드)
        if DataSourceSelectorWidget is not None:
            try:
                self.data_source_selector = DataSourceSelectorWidget()
                self.data_source_selector.source_changed.connect(self.on_data_source_changed)
                layout.addWidget(self.data_source_selector)
                print("✅ DataSourceSelectorWidget 생성 성공")
            except Exception as e:
                print(f"⚠️ 데이터 소스 선택기 초기화 실패: {e}")
                # 대체 라벨 - 더 자연스러운 메시지
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
            # 대체 라벨 - 더 자연스러운 메시지
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
        
        # 설명 제거하여 공간 절약
        # desc_label = QLabel("Virtual scenarios for trigger testing")
        # desc_label.setStyleSheet("color: #6c757d; font-size: 11px; margin-bottom: 10px;")
        # layout.addWidget(desc_label)
        
        # 시뮬레이션 버튼들 - 3행 2열 그리드 배치
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
            btn.setFixedHeight(35)  # 버튼 높이 더 줄이기 (40 → 35)
            btn.setMinimumWidth(120)  # 최소 너비 더 줄이기 (150 → 120)
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
            
            # 3행 2열로 배치 (행, 열 계산)
            row = i // 2  # 0, 0, 1, 1, 2, 2
            col = i % 2   # 0, 1, 0, 1, 0, 1
            grid_layout.addWidget(btn, row, col)
        
        # 그리드 레이아웃을 메인 레이아웃에 추가
        layout.addLayout(grid_layout)
        
        layout.addStretch()
        
        # 시뮬레이션 상태
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
        layout.addWidget(self.simulation_status)
        
        return group
    
    def create_trigger_detail_area(self):
        """영역 5: 선택한 트리거 상세 정보 (중앙 하단)"""
        group = QGroupBox("트리거 상세정보")
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
        self.trigger_detail_text.setPlainText("Select a trigger to view details.")
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
        group = QGroupBox("테스트 결과 차트")
        group.setStyleSheet(self.get_groupbox_style("#fd7e14"))
        layout = QVBoxLayout(group)
        
        # 고정 높이 제거하여 자동 크기 조정되도록 함 (트리거 상세 정보와 동일)
        # group.setFixedHeight(380)  # 이 줄 제거
        
        # 크기 정책도 제거 (트리거 상세 정보와 동일)
        # from PyQt6.QtWidgets import QSizePolicy
        # group.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        
        # 미니 차트 영역 - matplotlib 차트 또는 대체 라벨
        if CHART_AVAILABLE:
            try:
                self.mini_chart_widget = self.create_mini_chart_widget()
                layout.addWidget(self.mini_chart_widget)
                print("✅ 미니 차트 위젯 생성 완료")
            except Exception as e:
                print(f"❌ 차트 위젯 생성 실패: {e}")
                chart_label = self.create_fallback_chart_label()
                layout.addWidget(chart_label)
        else:
            chart_label = self.create_fallback_chart_label()
            layout.addWidget(chart_label)
        
        # 작동 기록 리스트
        self.test_history_list = QListWidget()
        self.test_history_list.setStyleSheet("""
            QListWidget {
                border: 2px solid #ddd;
                border-radius: 8px;
                background-color: white;
                max-height: 280px;
                font-size: 11px;
            }
            QListWidget::item {
                padding: 10px;
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
        
        # 기본 항목들 추가
        self.add_test_history_item("시스템 시작", "ready")
        
        layout.addWidget(QLabel("🕐 작동 기록:"))
        layout.addWidget(self.test_history_list)
        
        return group
    
    def create_mini_chart_widget(self):
        """미니 차트 위젯 생성 - 개선된 SimulationResultWidget 사용"""
        # 개선된 차트 시스템 사용
        chart_widget = self.simulation_result_widget
        
        # 기존 호환성을 위해 chart_canvas, chart_figure 참조 유지
        if hasattr(self.simulation_result_widget, 'canvas'):
            self.chart_canvas = self.simulation_result_widget.canvas
            self.chart_figure = self.simulation_result_widget.figure
        
        return chart_widget
    
    def create_fallback_chart_label(self):
        """차트 라이브러리가 없을 때 대체 라벨"""
        chart_label = QLabel("📊 미니 차트 영역")
        chart_label.setStyleSheet("""
            border: 3px dashed #fd7e14;
            border-radius: 12px;
            padding: 40px;
            text-align: center;
            color: #fd7e14;
            font-weight: bold;
            font-size: 14px;
            background-color: #fff8f0;
            min-height: 180px;
        """)
        chart_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        return chart_label
    
    def update_chart_with_sample_data(self):
        """샘플 데이터로 차트 업데이트 - 개선된 SimulationResultWidget 사용"""
        if hasattr(self.simulation_result_widget, 'show_placeholder_chart'):
            self.simulation_result_widget.show_placeholder_chart()
        else:
            # 폴백: 기존 ChartVisualizer 사용
            self.chart_visualizer.update_chart_with_sample_data()
    
    def update_chart_with_simulation_results(self, simulation_data, trigger_results, base_variable_data=None, external_variable_data=None, variable_info=None):
        """시뮬레이션 결과로 차트 업데이트 - 개선된 SimulationResultWidget 사용"""
        try:
            # 개선된 차트 시스템 사용
            scenario = simulation_data.get('scenario', 'Simulation')
            price_data = simulation_data.get('price_data', [])
            
            # 개선된 update_simulation_chart 메서드 호출
            self.simulation_result_widget.update_simulation_chart(
                scenario=scenario,
                price_data=price_data,
                trigger_results=trigger_results,
                base_variable_data=base_variable_data,
                external_variable_data=external_variable_data,
                variable_info=variable_info
            )
            
            print(f"✅ 개선된 차트 시스템으로 업데이트 완료: {scenario}")
            
        except Exception as e:
            print(f"⚠️ 개선된 차트 업데이트 실패, 폴백 사용: {e}")
            # 폴백: 기존 ChartVisualizer 사용
            self.chart_visualizer.update_chart_with_simulation_results(simulation_data, trigger_results)
    
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
        """그룹박스 스타일 생성 - 통일된 테두리 스타일"""
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
        """트리거 리스트 로드 - 3개 열 버전 (외부변수 정보는 조건 텍스트에 포함)"""
        try:
            conditions = self.storage.get_all_conditions()
            self.trigger_tree.clear()
            
            # 조건들을 직접 리스트에 추가 (3개 열 사용: 트리거명, 변수, 조건)
            for condition in conditions:
                name = condition.get('name', 'Unknown')
                variable = condition.get('variable_name', 'Unknown')
                operator = condition.get('operator', '?')
                target = condition.get('target_value', '?')
                category = condition.get('category', 'unknown')
                
                # 외부변수 정보 처리하여 조건 텍스트에 포함
                external_variable = condition.get('external_variable')
                if external_variable and isinstance(external_variable, (dict, str)):
                    if isinstance(external_variable, str):
                        try:
                            import json
                            external_variable = json.loads(external_variable)
                        except:
                            external_variable = None
                    
                    if external_variable:
                        external_var_name = external_variable.get('variable_name', 'N/A')
                        condition_text = f"{operator} {external_var_name} (외부변수)"
                    else:
                        condition_text = f"{operator} {target}"
                else:
                    condition_text = f"{operator} {target}"
                
                # 카테고리 아이콘 추가 (트리거명에 포함)
                category_icons = {
                    "indicator": "📈",
                    "price": "💰", 
                    "capital": "🏦",
                    "state": "📊",
                    "custom": "⚙️",
                    "unknown": "❓"
                }
                icon = category_icons.get(category, "❓")
                
                # 트리거명에 카테고리 아이콘 추가
                display_name = f"{icon} {name}"
                
                # 3개 열 사용: 트리거명, 변수, 조건 (외부변수는 조건 텍스트에 포함)
                item = QTreeWidgetItem([display_name, variable, condition_text])
                item.setData(0, Qt.ItemDataRole.UserRole, condition)  # 조건 데이터 저장
                self.trigger_tree.addTopLevelItem(item)
            
            print(f"✅ {len(conditions)}개 트리거 로드 완료")
            
        except Exception as e:
            print(f"❌ 트리거 리스트 로드 실패: {e}")
    
    def on_condition_saved(self, condition_data):
        """조건 저장 완료 시그널 처리"""
        try:
            print(f"✅ 새 조건 저장: {condition_data.get('name', 'Unknown')}")
            
            # 편집 버튼 상태 복원
            self.update_edit_button_state(False)
            
            # 트리거 리스트 새로고침
            self.load_trigger_list()
            
            # 상태 업데이트
            self.simulation_status.setText(f"✅ '{condition_data.get('name', 'Unknown')}' 저장 완료!")
            
            # 테스트 기록 추가
            self.add_test_history_item(f"조건 저장: {condition_data.get('name', 'Unknown')}", "save")
            
            print("✅ 조건 저장 완료, UI 업데이트됨")
            
        except Exception as e:
            print(f"❌ 조건 저장 완료 처리 실패: {e}")
    
    def on_trigger_selected(self, item, column):
        """트리거 선택 시 호출"""
        condition_data = item.data(0, Qt.ItemDataRole.UserRole)
        if not condition_data:
            return
        
        self.selected_condition = condition_data
        
        # 디버깅: 조건 데이터 전체 출력
        print(f"🔍 조건 데이터 전체: {condition_data}")
        
        # 외부변수 정보 추출 (데이터베이스 구조에 맞게 수정)
        external_variable_info = condition_data.get('external_variable', None)
        variable_params = condition_data.get('variable_params', {})
        comparison_type = condition_data.get('comparison_type', 'Unknown')
        target_value = condition_data.get('target_value', 'Unknown')
        
        # 외부변수 사용 여부 판정
        use_external = comparison_type == 'external' and external_variable_info is not None
        
        print(f"🔍 external_variable_info: {external_variable_info}")
        print(f"🔍 use_external: {use_external}")
        print(f"🔍 comparison_type: {comparison_type}")
        
        # 추세 방향성 정보
        trend_direction = condition_data.get('trend_direction', 'both')  # 기본값 변경
        trend_names = {
            'static': '추세 무관',  # 호환성을 위해 유지
            'rising': '상승 추세',
            'falling': '하락 추세',
            'both': '추세 무관'
        }
        trend_text = trend_names.get(trend_direction, trend_direction)
        
        # 연산자에 추세 방향성 포함 (모든 방향성 표시)
        operator = condition_data.get('operator', 'Unknown')
        operator_with_trend = f"{operator} ({trend_text})"
        
        # 비교 설정 정보 상세화
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
                
                print(f"🔍 외부변수 ID: {ext_var_id}")
                print(f"🔍 외부변수 파라미터: {ext_param_values}")
                
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
        
        # 조건명에 ID 표시 추가
        condition_id = condition_data.get('id', 'Unknown')
        condition_name_with_id = f"{condition_data.get('name', 'Unknown')} [ID:{condition_id}]"
        
        # 상세 정보 표시 (간소화)
        detail_text = f"""
🎯 조건명: {condition_name_with_id}
📝 설명: {condition_data.get('description', 'No description')}

📊 변수 정보:
  • 기본 변수: {condition_data.get('variable_name', 'Unknown')}
  • 기본 변수 파라미터: {variable_params}

⚖️ 비교 설정:
{comparison_info}

🕐 생성일: {condition_data.get('created_at', 'Unknown')}
        """
        
        self.trigger_detail_text.setPlainText(detail_text.strip())
        
        # 시뮬레이션 상태 업데이트
        self.simulation_status.setText(f"'{condition_data.get('name', 'Unknown')}' selected - Click a scenario")
        
        print(f"Trigger selected: {condition_data.get('name', 'Unknown')}")
    
    def on_data_source_changed(self, source_type: str):
        """데이터 소스 변경 시 호출"""
        try:
            print(f"📊 데이터 소스 변경: {source_type}")
            
            # 시뮬레이션 상태 업데이트 (메시지 박스 없이)
            self.simulation_status.setText(
                f"📊 데이터 소스: {source_type}\n"
                "시뮬레이션 준비 완료"
            )
            
            # 메시지 박스 제거 (UI 방해 요소 최소화)
            # QMessageBox.information(...) 제거
            
        except Exception as e:
            print(f"❌ 데이터 소스 변경 중 오류: {e}")
            # 오류 시에도 조용히 처리
            self.simulation_status.setText("📊 데이터 소스: 시뮬레이션 모드\n준비 완료")
    
    def run_simulation(self, scenario):
        """시뮬레이션 실행 - 실제 조건 로직 기반 (상세 로깅 포함)"""
        if not self.selected_condition:
            QMessageBox.warning(self, "Warning", "Please select a trigger first.")
            return
        
        condition_name = self.selected_condition.get('name', 'Unknown')
        variable_name = self.selected_condition.get('variable_name', 'Unknown')
        operator = self.selected_condition.get('operator', '>')
        target_value = self.selected_condition.get('target_value', '0')
        comparison_type = self.selected_condition.get('comparison_type', 'fixed')
        external_variable = self.selected_condition.get('external_variable')
        
        # 상세 트리거 정보 로깅
        print("\n🎯 트리거 계산 시작:")
        print(f"   조건명: {condition_name}")
        print(f"   변수: {variable_name}")
        print(f"   연산자: {operator}")
        print(f"   대상값: {target_value}")
        print(f"   비교 타입: {comparison_type}")
        print(f"   외부변수: {external_variable}")
        print(f"   시나리오: {scenario}")
        
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
        
        print(f"🏁 최종 결과: {result_text}")
        print(f"   상태: {status_text}")
        print(f"   데이터 소스: {simulation_data.get('data_source', 'unknown')}")
        
        # 차트 업데이트 (실제 트리거 포인트 계산)
        trigger_points = []
        if hasattr(self, 'chart_canvas'):
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
            
            # 개선된 차트 시스템에 추가 데이터 전달
            # 기본 변수 데이터 생성
            base_variable_data = None
            if operator in ['>', '>=', '<', '<=', '~=', '!=']:
                # 고정값 비교: 목표값을 수평선으로 표시하기 위한 데이터
                base_variable_data = [target_num] * len(chart_simulation_data['price_data'])
            
            # 변수 정보 구성
            variable_info = {
                'variable_id': variable_name.upper(),
                'variable_name': variable_name,
                'category': self._get_variable_category_for_chart(variable_name),
                'data_type': chart_simulation_data.get('data_type', 'price')
            }
            
            # 개선된 차트 업데이트 호출 (추가 파라미터 포함)
            self.update_chart_with_simulation_results(
                chart_simulation_data, 
                trigger_results,
                base_variable_data=base_variable_data,
                external_variable_data=None,
                variable_info=variable_info
            )
        
        # 상태 업데이트 (신호 개수 포함)
        self.simulation_status.setText(
            f"{result_text}: {scenario}\n"
            f"현재: {current_value:.2f} {operator} {target_num:.2f}\n"
            f"결과: {status_text}\n"
            f"발견된 신호: {len(trigger_points)}개"
        )
        
        # 테스트 기록에 상세 정보 추가 (신호 개수 포함)
        detail_info = f"{result_text} {scenario} - {condition_name} ({status_text}, {len(trigger_points)}신호)"
        self.add_test_history_item(detail_info, "test")
        
        # 시그널 발생
        self.condition_tested.emit(self.selected_condition, result)
        
        print(f"Simulation: {scenario} -> {result} (value: {current_value})")
    
    def calculate_trigger_points(self, price_data, operator, target_value):
        """트리거 포인트 계산 - 새로운 TriggerCalculator 사용"""
        return self.trigger_calculator.calculate_trigger_points(price_data, operator, target_value)
    
    def generate_price_data_for_chart(self, scenario, length=50):
        """차트용 가격 데이터 생성 - 시뮬레이션 엔진 사용"""
        scenario_data = self.simulation_engine.get_scenario_data(scenario, length)
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
    
    def generate_simulation_data(self, scenario, variable_name):
        """시뮬레이션 데이터 생성 - 시뮬레이션 엔진 사용"""
        return self.simulation_engine.get_scenario_data(scenario, 100)
    
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
        """트리거 필터링 구현 - 3개 열 버전 (외부변수는 조건 텍스트에 포함)"""
        if not text.strip():
            # 검색어가 없으면 모든 항목 표시
            for i in range(self.trigger_tree.topLevelItemCount()):
                item = self.trigger_tree.topLevelItem(i)
                item.setHidden(False)
            return
        
        search_text = text.lower()
        hidden_count = 0
        
        # 각 트리거 항목 검색 (3개 열 사용)
        for i in range(self.trigger_tree.topLevelItemCount()):
            item = self.trigger_tree.topLevelItem(i)
            
            # 트리거명, 변수명, 조건에서 검색 (외부변수는 조건에 포함됨)
            trigger_name = item.text(0).lower()
            variable_name = item.text(1).lower()
            condition_text = item.text(2).lower()
            
            # 카테고리는 저장된 조건 데이터에서 확인
            condition_data = item.data(0, Qt.ItemDataRole.UserRole)
            category = condition_data.get('category', 'unknown').lower() if condition_data else ''
            
            is_match = (search_text in trigger_name or 
                       search_text in variable_name or 
                       search_text in condition_text or
                       search_text in category)
            
            item.setHidden(not is_match)
            if not is_match:
                hidden_count += 1
        
        visible_count = self.trigger_tree.topLevelItemCount() - hidden_count
        print(f"🔍 검색 완료: '{text}' - {visible_count}개 표시, {hidden_count}개 숨김")
    
    def edit_selected_trigger(self):
        """선택한 트리거 편집 구현 - 조건 빌더로 로드"""
        if not self.selected_condition:
            QMessageBox.warning(self, "⚠️ 경고", "편집할 트리거를 선택해주세요.")
            return
        
        try:
            # 현재 편집 버튼 텍스트로 모드 확인 (더 안전한 방법)
            is_currently_editing = self.edit_btn.text() == "💾 편집 저장"
            
            if is_currently_editing:
                # 이미 편집 모드인 경우: 편집 저장
                self.condition_dialog.save_condition()
            else:
                # 편집 모드 시작
                if hasattr(self.condition_dialog, 'load_condition'):
                    # 조건 빌더 먼저 초기화
                    if hasattr(self.condition_dialog, 'clear_all_inputs'):
                        self.condition_dialog.clear_all_inputs()
                    
                    # 선택된 조건 로드
                    self.condition_dialog.load_condition(self.selected_condition)
                    
                    # 편집 모드 상태 설정
                    if hasattr(self.condition_dialog, 'edit_mode'):
                        self.condition_dialog.edit_mode = True
                        self.condition_dialog.edit_condition_id = self.selected_condition.get('id')
                        self.condition_dialog.editing_condition_name = self.selected_condition.get('name', '')
                    
                    # 편집 버튼 상태 변경
                    self.update_edit_button_state(True)
                    
                    QMessageBox.information(self, "✅ 편집 모드",
                                        f"'{self.selected_condition.get('name', '')}' 조건이 편집 모드로 로드되었습니다.\n"
                                        "수정 후 '편집 저장' 버튼을 눌러 저장하세요.")
                else:
                    # 기본 방법: 수동 필드 설정 안내
                    condition_name = self.selected_condition.get('name', '')
                    QMessageBox.information(self, "✏️ 편집 모드",
                                        f"'{condition_name}' 조건을 편집하려면:\n"
                                        "1. 조건 빌더에 설정이 Load 되었습니다.\n"
                                        "2. 동일한 이름으로 저장하면 덮어쓰기됩니다")
                
        except Exception as e:
            QMessageBox.critical(self, "❌ 오류", f"편집 중 오류가 발생했습니다:\n{e}")
            print(f"❌ 편집 오류: {e}")
    
    def update_edit_button_state(self, is_edit_mode: bool):
        """편집 버튼 상태 업데이트"""
        # 통일된 버튼 스타일 정의
        button_base_style = """
            QPushButton {
                color: white;
                border: none;
                padding: 8px 12px;
                border-radius: 4px;
                font-size: 11px;
                font-weight: bold;
                min-height: 16px;
                max-height: 32px;
            }
        """
        
        if is_edit_mode:
            # 편집 모드: "편집 저장" 버튼으로 변경
            self.edit_btn.setText("💾 편집 저장")
            self.edit_btn.setStyleSheet(button_base_style + """
                QPushButton {
                    background-color: #fd7e14;
                }
                QPushButton:hover {
                    background-color: #e8681a;
                }
                QPushButton:pressed {
                    background-color: #d9580d;
                }
            """)
            
            # 편집 모드에서는 트리거 저장 버튼 비활성화 (혼동 방지)
            self.save_btn.setEnabled(False)
            self.save_btn.setToolTip("편집 모드에서는 '편집 저장' 버튼을 사용하세요")
            
        else:
            # 일반 모드: "편집" 버튼으로 복원
            self.edit_btn.setText("✏️ 편집")
            self.edit_btn.setStyleSheet(button_base_style + """
                QPushButton {
                    background-color: #007bff;
                }
                QPushButton:hover {
                    background-color: #0056b3;
                }
                QPushButton:pressed {
                    background-color: #004085;
                }
            """)
            
            # 일반 모드에서는 트리거 저장 버튼 활성화
            self.save_btn.setEnabled(True)
            self.save_btn.setToolTip("")
        
        # 편집 취소 버튼은 항상 표시되므로 show/hide 제거
    
    def cancel_edit_trigger(self):
        """트리거 편집 취소"""
        try:
            # 편집 모드 종료
            self.update_edit_button_state(False)
            
            # 조건 빌더의 편집 모드 강제 해제
            if hasattr(self.condition_dialog, 'edit_mode'):
                self.condition_dialog.edit_mode = False
                self.condition_dialog.edit_condition_id = None
                self.condition_dialog.editing_condition_name = None
                print("✅ 조건 빌더 편집 모드 강제 해제")
            
            # 조건 빌더 완전 초기화 (모든 필드를 기본값으로)
            if hasattr(self.condition_dialog, 'clear_all_inputs'):
                self.condition_dialog.clear_all_inputs()
                print("✅ 조건 빌더 완전 초기화 완료")
            elif hasattr(self.condition_dialog, 'reset_form'):
                self.condition_dialog.reset_form()
                print("✅ 조건 빌더 폼 리셋 완료")
            else:
                print("⚠️ 조건 빌더 초기화 메서드를 찾을 수 없음")
            
            # 선택된 조건 해제
            self.selected_condition = None
            
            # 트리거 리스트에서 선택 해제
            if hasattr(self, 'trigger_tree'):
                self.trigger_tree.clearSelection()
                print("✅ 트리거 리스트 선택 해제")
            
            # 트리거 상세 정보 초기화
            self.trigger_detail_text.setPlainText("트리거를 선택하면 상세 정보가 표시됩니다.")
            
            # 상태 업데이트
            self.simulation_status.setText("📝 편집이 취소되었습니다.\n조건 빌더와 선택이 초기화되었습니다.")
            self.add_test_history_item("편집 취소 및 초기화 완료", "ready")
            
            print("✅ 편집 취소 및 전체 초기화 완료")
            
        except Exception as e:
            from PyQt6.QtWidgets import QMessageBox
            QMessageBox.critical(self, "❌ 오류", f"편집 취소 중 오류가 발생했습니다:\n{e}")
            print(f"❌ 편집 취소 오류: {e}")
    
    def copy_trigger_for_edit(self):
        """선택한 트리거를 복사하여 편집 모드로 로드 (이름은 자동으로 변경)"""
        if not self.selected_condition:
            from PyQt6.QtWidgets import QMessageBox
            QMessageBox.warning(self, "⚠️ 경고", "복사할 트리거를 선택해주세요.")
            return
        
        try:
            # 원본 조건 데이터 복사
            original_condition = self.selected_condition.copy()
            
            # 새로운 이름 생성 (원본 이름 + "_copy")
            original_name = original_condition.get('name', 'Unknown')
            new_name = f"{original_name}_copy"
            
            # 이미 같은 이름이 있는지 확인하고 번호 추가
            counter = 1
            while self._check_condition_name_exists(new_name):
                new_name = f"{original_name}_copy_{counter}"
                counter += 1
            
            # 새로운 조건 데이터 생성
            copied_condition = original_condition.copy()
            copied_condition['name'] = new_name
            
            # ID 제거 (새로 생성될 때 새 ID 할당)
            if 'id' in copied_condition:
                del copied_condition['id']
            
            # 생성일 업데이트
            copied_condition['created_at'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            # 조건 빌더에 복사된 데이터 로드
            if hasattr(self.condition_dialog, 'load_condition'):
                self.condition_dialog.load_condition(copied_condition)
                
                # 편집 모드 시작
                self.update_edit_button_state(True)
                
                # 상태 업데이트
                self.simulation_status.setText(f"📋 '{original_name}' 복사 완료!\n새 이름: '{new_name}'")
                self.add_test_history_item(f"트리거 복사: {original_name} → {new_name}", "save")
                
                from PyQt6.QtWidgets import QMessageBox
                QMessageBox.information(self, "📋 복사 완료", 
                                    f"'{original_name}' 트리거가 복사되었습니다.\n\n"
                                    f"새 이름: '{new_name}'\n"
                                    f"필요한 수정을 한 후 '편집 저장'을 눌러 저장하세요.")
                
                print(f"✅ 트리거 복사 완료: {original_name} → {new_name}")
            else:
                from PyQt6.QtWidgets import QMessageBox
                QMessageBox.warning(self, "⚠️ 경고", "조건 빌더에 데이터를 로드할 수 없습니다.")
                
        except Exception as e:
            from PyQt6.QtWidgets import QMessageBox
            QMessageBox.critical(self, "❌ 오류", f"트리거 복사 중 오류가 발생했습니다:\n{e}")
            print(f"❌ 트리거 복사 오류: {e}")
    
    def _check_condition_name_exists(self, name: str) -> bool:
        """조건 이름이 이미 존재하는지 확인"""
        try:
            conditions = self.storage.get_all_conditions()
            return any(condition.get('name') == name for condition in conditions)
        except Exception:
            return False
    
    def delete_selected_trigger(self):
        """선택한 트리거 삭제 구현"""
        if not self.selected_condition:
            QMessageBox.warning(self, "⚠️ 경고", "삭제할 트리거를 선택해주세요.")
            return
        
        condition_name = self.selected_condition.get('name', 'Unknown')
        condition_id = self.selected_condition.get('id', None)
        
        # 삭제 확인
        reply = QMessageBox.question(
            self, "🗑️ 삭제 확인",
            f"정말로 '{condition_name}' 트리거를 삭제하시겠습니까?\n\n이 작업은 되돌릴 수 없습니다.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            try:
                if condition_id:
                    # 데이터베이스에서 삭제
                    success, message = self.storage.delete_condition(condition_id)
                    
                    if success:
                        # UI 업데이트
                        self.load_trigger_list()
                        self.trigger_detail_text.setPlainText("트리거를 선택하면 상세 정보가 표시됩니다.")
                        self.selected_condition = None
                        
                        # 상태 업데이트
                        self.simulation_status.setText(f"🗑️ '{condition_name}' 삭제 완료!")
                        self.add_test_history_item(f"트리거 삭제: {condition_name}", "save")
                        
                        QMessageBox.information(self, "✅ 삭제 완료", f"'{condition_name}' 트리거가 삭제되었습니다.")
                    else:
                        QMessageBox.critical(self, "❌ 삭제 실패", f"삭제 실패: {message}")
                        print(f"❌ 트리거 삭제 실패: {message}")
                    
                else:
                    QMessageBox.warning(self, "⚠️ 경고", "삭제할 수 없는 트리거입니다.")
                    
            except Exception as e:
                QMessageBox.critical(self, "❌ 오류", f"삭제 중 오류가 발생했습니다:\n{e}")
                print(f"❌ 삭제 오류: {e}")
    
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

    def create_chart_variable_selector(self):
        """차트 변수 선택기 생성"""
        if not self.chart_variable_service:
            return None
        
        group = QGroupBox("📊 차트 변수 선택")
        group.setStyleSheet("""
            QGroupBox {
                background-color: #f8f9fa;
                border: 1px solid #ddd;
                border-radius: 6px;
                padding-top: 10px;
                margin: 2px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
                color: #495057;
                font-weight: bold;
            }
        """)
        layout = QVBoxLayout(group)
        layout.setContentsMargins(8, 8, 8, 8)
        
        # 변수 카테고리 선택
        category_layout = QHBoxLayout()
        category_label = QLabel("카테고리:")
        category_combo = QComboBox()
        
        # 카테고리 목록 추가
        categories = [
            ("전체", ""),
            ("가격 오버레이", "price_overlay"),
            ("오실레이터", "oscillator"),
            ("모멘텀", "momentum"),
            ("거래량", "volume")
        ]
        
        for display_name, category_value in categories:
            category_combo.addItem(display_name, category_value)
        
        category_combo.currentTextChanged.connect(self.on_category_changed)
        
        category_layout.addWidget(category_label)
        category_layout.addWidget(category_combo)
        layout.addLayout(category_layout)
        
        # 변수 리스트
        self.variable_list = QListWidget()
        self.variable_list.setStyleSheet("""
            QListWidget {
                border: 1px solid #ddd;
                border-radius: 4px;
                background-color: white;
            }
            QListWidget::item {
                padding: 6px;
                border-bottom: 1px solid #f0f0f0;
            }
            QListWidget::item:selected {
                background-color: #007bff;
                color: white;
            }
        """)
        
        self.variable_list.itemSelectionChanged.connect(self.on_variable_selected)
        layout.addWidget(self.variable_list)
        
        # 호환성 정보 표시
        self.compatibility_info = QLabel()
        self.compatibility_info.setStyleSheet("""
            QLabel {
                background-color: #e9ecef;
                border: 1px solid #ced4da;
                border-radius: 4px;
                padding: 6px;
                font-size: 10px;
            }
        """)
        self.compatibility_info.setWordWrap(True)
        layout.addWidget(self.compatibility_info)
        
        # 차트 프리뷰 버튼
        preview_btn = QPushButton("📈 차트 프리뷰")
        preview_btn.setStyleSheet("""
            QPushButton {
                background-color: #28a745;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 6px 12px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #218838;
            }
        """)
        preview_btn.clicked.connect(self.show_chart_preview)
        layout.addWidget(preview_btn)
        
        # 초기 변수 목록 로드
        self.load_variables_by_category("")
        
        return group
    
    def on_category_changed(self, category_text):
        """카테고리 변경 시 변수 목록 업데이트"""
        category_mapping = {
            "전체": "",
            "가격 오버레이": "price_overlay",
            "오실레이터": "oscillator", 
            "모멘텀": "momentum",
            "거래량": "volume"
        }
        
        category = category_mapping.get(category_text, "")
        self.load_variables_by_category(category)
    
    def load_variables_by_category(self, category):
        """카테고리별 변수 목록 로드"""
        if not self.chart_variable_service:
            return
        
        self.variable_list.clear()
        
        try:
            variables = self.chart_variable_service.get_available_variables_by_category(category)
            
            for var in variables:
                item = QListWidgetItem()
                item.setText(f"{var.variable_name} ({var.unit})")
                item.setData(Qt.ItemDataRole.UserRole, var)
                
                # 카테고리별 아이콘 추가
                if var.category == "price_overlay":
                    item.setText(f"💰 {item.text()}")
                elif var.category == "oscillator":
                    item.setText(f"📊 {item.text()}")
                elif var.category == "momentum":
                    item.setText(f"🚀 {item.text()}")
                elif var.category == "volume":
                    item.setText(f"📈 {item.text()}")
                
                self.variable_list.addItem(item)
                
        except Exception as e:
            print(f"⚠️ 변수 목록 로드 실패: {e}")
    
    def on_variable_selected(self):
        """변수 선택 시 호환성 정보 표시"""
        current_item = self.variable_list.currentItem()
        if not current_item or not self.chart_variable_service:
            self.compatibility_info.clear()
            return
        
        var_config = current_item.data(Qt.ItemDataRole.UserRole)
        if not var_config:
            return
        
        # 호환성 정보 생성
        compatibility_text = f"📋 {var_config.variable_name}\n"
        compatibility_text += f"카테고리: {var_config.category}\n"
        compatibility_text += f"표시 방식: {var_config.display_type}\n"
        
        if var_config.scale_min is not None and var_config.scale_max is not None:
            compatibility_text += f"스케일: {var_config.scale_min} ~ {var_config.scale_max}\n"
        
        compatibility_text += f"단위: {var_config.unit}\n"
        
        if var_config.compatible_categories:
            compatible_names = []
            for cat in var_config.compatible_categories:
                if cat == "price_overlay":
                    compatible_names.append("가격 오버레이")
                elif cat == "oscillator":
                    compatible_names.append("오실레이터")
                elif cat == "momentum":
                    compatible_names.append("모멘텀")
                elif cat == "volume":
                    compatible_names.append("거래량")
                elif cat == "currency":
                    compatible_names.append("통화")
                elif cat == "percentage":
                    compatible_names.append("퍼센트")
                else:
                    compatible_names.append(cat)
            
            compatibility_text += f"호환 카테고리: {', '.join(compatible_names)}"
        
        self.compatibility_info.setText(compatibility_text)
    
    def show_chart_preview(self):
        """차트 프리뷰 표시"""
        current_item = self.variable_list.currentItem()
        if not current_item:
            QMessageBox.information(self, "정보", "먼저 변수를 선택해주세요.")
            return
        
        var_config = current_item.data(Qt.ItemDataRole.UserRole)
        if not var_config:
            return
        
        try:
            # 간단한 정보 다이얼로그로 차트 정보 표시
            info_text = f"차트 변수: {var_config.variable_name}\n"
            info_text += f"카테고리: {var_config.category}\n"
            info_text += f"표시 방식: {var_config.display_type}\n"
            
            if var_config.category == "price_overlay":
                info_text += "\n📊 메인 차트에 표시됩니다:\n"
                if var_config.display_type == "main_line":
                    info_text += "- 선 형태로 시가 차트에 오버레이"
                elif var_config.display_type == "main_band":
                    info_text += "- 밴드 형태로 시가 차트에 오버레이"
                elif var_config.display_type == "main_level":
                    info_text += "- 수평선으로 시가 차트에 표시"
            else:
                info_text += f"\n📈 별도 서브플롯에 표시됩니다:\n"
                info_text += f"- 높이 비율: {var_config.subplot_height_ratio}\n"
                if var_config.scale_min is not None and var_config.scale_max is not None:
                    info_text += f"- 스케일: {var_config.scale_min} ~ {var_config.scale_max}"
            
            QMessageBox.information(self, f"📊 {var_config.variable_name} 차트 정보", info_text)
            
        except Exception as e:
            QMessageBox.warning(self, "⚠️ 경고", f"차트 프리뷰 실패: {e}")
    
    def validate_variable_compatibility(self, base_variable_id, external_variable_id):
        """변수 호환성 검사"""
        if not self.chart_variable_service:
            return True, "차트 변수 서비스를 사용할 수 없습니다."
        
        try:
            return self.chart_variable_service.is_compatible_external_variable(
                base_variable_id, external_variable_id
            )
        except Exception as e:
            return False, f"호환성 검사 오류: {e}"
    
    def _get_variable_category_for_chart(self, variable_name):
        """차트 시스템용 변수 카테고리 매핑"""
        variable_name_lower = variable_name.lower()
        
        # 기본 카테고리 매핑
        if any(keyword in variable_name_lower for keyword in ['rsi', 'stochastic', 'cci']):
            return 'oscillator'
        elif any(keyword in variable_name_lower for keyword in ['macd', 'momentum', 'roc']):
            return 'momentum'
        elif any(keyword in variable_name_lower for keyword in ['sma', 'ema', 'bb', 'bollinger', 'price', 'current']):
            return 'price_overlay'
        elif any(keyword in variable_name_lower for keyword in ['volume', 'vol']):
            return 'volume'
        else:
            return 'price_overlay'  # 기본값


if __name__ == "__main__":
    from PyQt6.QtWidgets import QApplication
    import sys
    
    app = QApplication(sys.argv)
    
    window = IntegratedConditionManager()
    window.show()
    
    sys.exit(app.exec())
