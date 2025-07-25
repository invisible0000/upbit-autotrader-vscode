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

from .components.condition_dialog import ConditionDialog
from .components.condition_storage import ConditionStorage
from .components.condition_loader import ConditionLoader
from .components.data_source_selector import DataSourceSelectorWidget

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
        # 크기를 더욱 압축하여 1600x1000 화면에 최적화
        self.setMinimumSize(600, 400)
        
        # 컴포넌트 초기화
        self.storage = ConditionStorage()
        self.loader = ConditionLoader(self.storage)
        self.selected_condition = None
        
        self.init_ui()
        self.load_trigger_list()
    
    def init_ui(self):
        """UI 초기화 - 3x2 그리드 레이아웃"""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(2, 2, 2, 2)  # 마진 더욱 줄이기
        main_layout.setSpacing(2)  # 간격 더욱 줄이기
        
        # 상단 제목 제거하여 공간 절약
        # self.create_header(main_layout)
        
        # 메인 그리드 레이아웃 (3x2)
        grid_widget = QWidget()
        grid_layout = QGridLayout(grid_widget)
        grid_layout.setContentsMargins(1, 1, 1, 1)  # 그리드 마진 더욱 줄이기
        grid_layout.setSpacing(2)  # 그리드 간격 더욱 줄이기
        
        # 1+4: 조건 빌더 (좌측, 세로 합쳐짐)
        self.condition_builder_area = self.create_condition_builder_area()
        grid_layout.addWidget(self.condition_builder_area, 0, 0, 2, 1)  # 2행에 걸쳐 배치
        
        # 2: 등록된 트리거 리스트 (중앙 상단)
        self.trigger_list_area = self.create_trigger_list_area()
        grid_layout.addWidget(self.trigger_list_area, 0, 1, 1, 1)
        
        # 3: 케이스 시뮬레이션 버튼들 (우측 상단)
        self.simulation_area = self.create_simulation_area()
        self.simulation_area.setMinimumWidth(360)  # 최소 너비 증가 (250 → 360)
        self.simulation_area.setMaximumWidth(400)  # 최대 너비 증가 (280 → 400)
        grid_layout.addWidget(self.simulation_area, 0, 2, 1, 1)
        
        # 5: 선택한 트리거 상세 정보 (중앙 하단)
        self.trigger_detail_area = self.create_trigger_detail_area()
        grid_layout.addWidget(self.trigger_detail_area, 1, 1, 1, 1)
        
        # 6: 작동 마커 차트 + 작동 기록 (우측 하단)
        self.test_result_area = self.create_test_result_area()
        self.test_result_area.setMinimumWidth(360)  # 최소 너비 증가 (250 → 360)
        self.test_result_area.setMaximumWidth(400)  # 최대 너비 증가 (280 → 400)
        grid_layout.addWidget(self.test_result_area, 1, 2, 1, 1)
        
        # 그리드 비율 설정 - 두 번째 첨부 이미지와 유사하게 (1:2:1)
        grid_layout.setColumnStretch(0, 1)  # 조건 빌더 (좁게)
        grid_layout.setColumnStretch(1, 2)  # 트리거 관리 (넓게)
        grid_layout.setColumnStretch(2, 1)  # 시뮬레이션 (좁게)
        
        # 행 비율 설정 (상단 영역도 증가: 3 → 5, 하단 영역: 4 → 6)
        grid_layout.setRowStretch(0, 5)  # 상단 (케이스 시뮬레이션 포함)
        grid_layout.setRowStretch(1, 6)  # 하단 (트리거 디테일 & 테스트 결과)
        
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
            error_label.setStyleSheet("color: #e74c3c; padding: 20px; font-size: 12px;")
            layout.addWidget(error_label)
        
        return group
    
    def create_trigger_list_area(self):
        """영역 2: 등록된 트리거 리스트 (중앙 상단) - 통일된 테두리 스타일"""
        group = QGroupBox("📋 등록된 트리거 리스트")
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
                color: #27ae60;
                font-size: 11px;
                font-weight: bold;
                border-radius: 4px;
                border: 1px solid #27ae60;
            }
        """)
        layout = QVBoxLayout(group)
        layout.setContentsMargins(8, 8, 8, 8)  # 패딩 줄이기
        
        # 트리거 검색
        search_layout = QHBoxLayout()
        search_label = QLabel("🔍")
        search_layout.addWidget(search_label)
        
        self.search_input = StyledLineEdit()
        self.search_input.setPlaceholderText("트리거 검색...")
        search_layout.addWidget(self.search_input)
        layout.addLayout(search_layout)
        
        # 트리거 트리 위젯 - 대시보드 테이블 스타일 (외부변수 열 제거)
        self.trigger_tree = QTreeWidget()
        self.trigger_tree.setHeaderLabels(["트리거명", "변수", "조건"])  # 외부변수 열 제거
        
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
        
        # 트리거 저장 버튼 추가
        save_btn = QPushButton("💾 트리거 저장")
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
            QPushButton:pressed {
                background-color: #1e7e34;
            }
        """)
        save_btn.clicked.connect(self.save_current_condition)
        
        # 편집 버튼 (동적으로 변경됨)
        self.edit_btn = SecondaryButton("✏️ 편집")
        self.edit_btn.clicked.connect(self.edit_selected_trigger)
        
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
        button_layout.addWidget(self.edit_btn)
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
        
        # 데이터 소스 선택 위젯 추가
        self.data_source_selector = DataSourceSelectorWidget()
        self.data_source_selector.source_changed.connect(self.on_data_source_changed)
        layout.addWidget(self.data_source_selector)
        
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
        """미니 차트 위젯 생성 - matplotlib 기반"""
        if not CHART_AVAILABLE:
            return self.create_fallback_chart_label()
        
        try:
            # matplotlib Figure와 Canvas 생성
            self.chart_figure = Figure(figsize=(5, 3), dpi=80)  # 차트 높이 증가 (2 → 3)
            self.chart_canvas = FigureCanvas(self.chart_figure)
            self.chart_canvas.setMinimumHeight(150)  # 최소 높이 증가 (100 → 150)
            self.chart_canvas.setMaximumHeight(250)  # 최대 높이 증가 (150 → 250)
            
            # 차트 영역 스타일링
            self.chart_figure.patch.set_facecolor('#fff8f0')
            
            # 기본 차트 그리기
            self.update_chart_with_sample_data()
            
            return self.chart_canvas
            
        except Exception as e:
            print(f"❌ 차트 위젯 생성 실패: {e}")
            return self.create_fallback_chart_label()
    
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
        """샘플 데이터로 차트 업데이트"""
        if not CHART_AVAILABLE or not hasattr(self, 'chart_figure'):
            return
        
        try:
            # 기존 차트 지우기
            self.chart_figure.clear()
            
            # 서브플롯 생성
            ax = self.chart_figure.add_subplot(111)
            
            # 샘플 가격 데이터 생성
            x = np.arange(50)
            base_price = 50000
            price_data = base_price + np.cumsum(np.random.randn(50) * 100)
            
            # 가격 선 그리기
            ax.plot(x, price_data, color='#3498db', linewidth=2, label='Price')
            
            # 트리거 포인트 예시 (랜덤하게 몇 개)
            trigger_points = np.random.choice(x, size=3, replace=False)
            trigger_prices = price_data[trigger_points]
            ax.scatter(trigger_points, trigger_prices, color='#e74c3c', s=50, 
                      zorder=5, label='Trigger', marker='o')
            
            # 차트 스타일링 - 심플하게
            ax.set_title('Simulation Result', fontsize=10, fontweight='bold')
            ax.legend(fontsize=8, loc='upper left')
            ax.grid(True, alpha=0.2)
            
            # X/Y축 틱 및 라벨 제거
            ax.set_xticks([])
            ax.set_yticks([])
            ax.set_xlabel('')
            ax.set_ylabel('')
            
            # 차트 여백 조정 - 더 타이트하게
            self.chart_figure.tight_layout(pad=0.5)
            self.chart_figure.subplots_adjust(left=0.05, right=0.95, top=0.85, bottom=0.1)
            
            # 차트 업데이트
            if hasattr(self, 'chart_canvas'):
                self.chart_canvas.draw()
            
            print("✅ 차트 업데이트 완료")
            
        except Exception as e:
            print(f"❌ 차트 업데이트 실패: {e}")
    
    def update_chart_with_simulation_results(self, simulation_data, trigger_results):
        """시뮬레이션 결과로 차트 업데이트 - 데이터 타입별 대응"""
        if not CHART_AVAILABLE or not hasattr(self, 'chart_figure'):
            return
        
        try:
            # 기존 차트 지우기
            self.chart_figure.clear()
            ax = self.chart_figure.add_subplot(111)
            
            # 시뮬레이션 데이터 시각화
            if 'price_data' in simulation_data:
                data = simulation_data['price_data']
                data_type = simulation_data.get('data_type', 'price')
                x = np.arange(len(data))
                
                # 데이터 타입별 라벨 및 색상 설정
                if data_type == 'rsi':
                    label = 'RSI'
                    color = '#9b59b6'  # 보라색
                    # RSI 기준선 추가
                    ax.axhline(y=70, color='red', linestyle='--', alpha=0.5, label='과매수(70)')
                    ax.axhline(y=30, color='blue', linestyle='--', alpha=0.5, label='과매도(30)')
                elif data_type == 'macd':
                    label = 'MACD'
                    color = '#e67e22'  # 주황색
                    # MACD 기준선 추가
                    ax.axhline(y=0, color='gray', linestyle='-', alpha=0.5, label='기준선(0)')
                else:
                    label = 'Price'
                    color = '#3498db'  # 파란색
                    # 목표값 기준선 추가 (가격인 경우)
                    if 'target_value' in simulation_data:
                        target = simulation_data['target_value']
                        ax.axhline(y=target, color='green', linestyle='--', alpha=0.7, 
                                  label=f'목표값({target:,.0f})')
                
                ax.plot(x, data, color=color, linewidth=2, label=label)
                
                # 트리거 발생 지점 표시
                if trigger_results and 'trigger_points' in trigger_results:
                    trigger_x = trigger_results['trigger_points']
                    if trigger_x:  # 트리거 포인트가 있는 경우에만
                        trigger_y = [data[i] for i in trigger_x if i < len(data)]
                        trigger_x_filtered = [i for i in trigger_x if i < len(data)]
                        
                        if trigger_x_filtered:
                            ax.scatter(trigger_x_filtered, trigger_y, color='#e74c3c', s=60, 
                                      zorder=5, label=f'신호({len(trigger_x_filtered)}개)', marker='o')
                
                # 차트 제목에 신호 개수 포함
                total_signals = len(trigger_results.get('trigger_points', []))
                scenario = simulation_data.get("scenario", "Simulation")
                ax.set_title(f'{scenario} - {total_signals}개 신호', 
                            fontsize=10, fontweight='bold')
                
                ax.legend(fontsize=8, loc='upper left')
                ax.grid(True, alpha=0.2)
                
                # Y축만 표시 (데이터 범위 확인용)
                ax.set_xticks([])
                if data_type == 'rsi':
                    ax.set_ylim(0, 100)
                    ax.set_yticks([0, 30, 50, 70, 100])
                elif data_type == 'macd':
                    ax.set_ylim(-2, 2)
                    ax.set_yticks([-2, -1, 0, 1, 2])
                else:
                    # 가격 데이터는 자동 스케일링
                    pass
                
                ax.set_xlabel('')
                ax.set_ylabel('')
            
            # 차트 여백 조정
            self.chart_figure.tight_layout(pad=0.5)
            self.chart_figure.subplots_adjust(left=0.1, right=0.95, top=0.85, bottom=0.1)
            
            # 차트 업데이트
            if hasattr(self, 'chart_canvas'):
                self.chart_canvas.draw()
            
            print(f"✅ 차트 업데이트 완료 ({data_type} 데이터)")
            
        except Exception as e:
            print(f"❌ 차트 업데이트 실패: {e}")
    
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
            
            # 시뮬레이션 상태 업데이트
            self.simulation_status.setText(
                f"데이터 소스 변경됨: {source_type}\n"
                "새로운 소스로 시뮬레이션 준비 완료"
            )
            
            # 메시지 박스로 사용자에게 알림
            QMessageBox.information(
                self, 
                "데이터 소스 변경",
                f"시뮬레이션 데이터 소스가 '{source_type}'로 변경되었습니다.\n"
                "이제 새로운 데이터 소스를 사용하여 시뮬레이션이 실행됩니다."
            )
            
        except Exception as e:
            print(f"❌ 데이터 소스 변경 중 오류: {e}")
            QMessageBox.warning(
                self,
                "오류",
                f"데이터 소스 변경 중 오류가 발생했습니다:\n{e}"
            )
    
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
            # 변수 타입에 따른 적절한 데이터 생성
            if 'rsi' in variable_name.lower():
                # RSI용 데이터 (0-100 범위)
                data_for_chart = self.generate_rsi_data_for_chart(scenario, 50)
                trigger_points = self.calculate_trigger_points(data_for_chart, operator, target_num)
                
                chart_simulation_data = {
                    'scenario': scenario,
                    'price_data': data_for_chart,  # RSI 값들
                    'current_value': current_value,
                    'target_value': target_val,
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
                    'target_value': target_val,
                    'data_type': 'macd'
                }
            else:
                # 가격용 데이터 (기존 로직)
                price_data = self.generate_price_data_for_chart(scenario, 50)
                trigger_points = self.calculate_trigger_points(price_data, operator, target_num)
                
                # target_value 유효성 검사
                target_val = target_num
                if str(target_value).replace('.', '').replace('-', '').isdigit():
                    target_val = float(target_value)
                
                chart_simulation_data = {
                    'scenario': scenario,
                    'price_data': price_data,
                    'current_value': current_value,
                    'target_value': target_val,
                    'data_type': 'price'
                }
            
            trigger_results = {
                'trigger_points': trigger_points,
                'trigger_activated': result,
                'total_signals': len(trigger_points)
            }
            
            print(f"📊 트리거 포인트 계산 완료: {len(trigger_points)}개 신호 발견")
            self.update_chart_with_simulation_results(chart_simulation_data, trigger_results)
        
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
        """실제 가격 데이터를 기반으로 트리거 포인트 계산 - 개선된 버전"""
        trigger_points = []
        
        try:
            if not price_data or len(price_data) == 0:
                print("❌ 가격 데이터가 없습니다")
                return []
            
            target_float = float(target_value)
            
            # 연산자별 조건 확인
            for i, price in enumerate(price_data):
                triggered = False
                
                if operator == '>' and price > target_float:
                    triggered = True
                elif operator == '>=' and price >= target_float:
                    triggered = True
                elif operator == '<' and price < target_float:
                    triggered = True
                elif operator == '<=' and price <= target_float:
                    triggered = True
                elif operator == '~=' and target_float != 0:
                    # 근사값 (±1%)
                    diff_percent = abs(price - target_float) / abs(target_float) * 100
                    if diff_percent <= 1.0:
                        triggered = True
                elif operator == '!=' and price != target_float:
                    triggered = True
                
                if triggered:
                    trigger_points.append(i)
            
            # 연속된 트리거 포인트 필터링 조건 완화
            # 가격 기반 조건(>, >=, <, <=)의 경우 필터링 최소화
            if len(trigger_points) > 1 and operator in ['~=', '!=']:
                # 근사값이나 부등호 조건에서만 필터링 적용
                filtered_points = [trigger_points[0]]
                for point in trigger_points[1:]:
                    if point - filtered_points[-1] > 1:  # 간격을 1로 줄임
                        filtered_points.append(point)
                trigger_points = filtered_points
            # >, >=, <, <= 조건에서는 연속된 신호를 모두 유지
            
            print("🎯 트리거 포인트 계산:")
            print(f"   연산자: {operator}, 대상값: {target_float}")
            print(f"   가격 범위: {min(price_data):.0f} ~ {max(price_data):.0f}")
            print(f"   조건 충족 포인트: {len([p for i, p in enumerate(price_data) if self._check_condition(p, operator, target_float)])}개")
            print(f"   필터링 후 신호: {len(trigger_points)}개")
            print(f"   포인트 위치: {trigger_points[:10]}{'...' if len(trigger_points) > 10 else ''}")
            
            return trigger_points
            
        except Exception as e:
            print(f"❌ 트리거 포인트 계산 오류: {e}")
            return []
    
    def _check_condition(self, value, operator, target):
        """조건 체크 헬퍼 메서드"""
        if operator == '>':
            return value > target
        elif operator == '>=':
            return value >= target
        elif operator == '<':
            return value < target
        elif operator == '<=':
            return value <= target
        elif operator == '~=' and target != 0:
            diff_percent = abs(value - target) / abs(target) * 100
            return diff_percent <= 1.0
        elif operator == '!=':
            return value != target
        return False
    
    def generate_price_data_for_chart(self, scenario, length=50):
        """차트용 실제 가격 데이터 생성 - 업그레이드 버전"""
        try:
            if not CHART_AVAILABLE:
                return []
            
            # 실제 데이터 사용 시도
            try:
                from .real_data_simulation import get_simulation_engine
                
                engine = get_simulation_engine()
                real_data = engine.get_scenario_data(scenario, length=length)
                
                if real_data and 'price_data' in real_data and real_data.get('data_source') == 'real_market_data':
                    print(f"✅ 차트용 실제 시장 데이터 사용: {scenario}")
                    return real_data['price_data']
                else:
                    print(f"⚠️ 차트용 실제 데이터 로드 실패, 시뮬레이션 데이터 사용: {scenario}")
            
            except Exception as e:
                print(f"❌ 차트용 실제 데이터 엔진 오류: {e}")
            
            # 폴백: 시뮬레이션 데이터 생성
            import numpy as np
            
            # 기본 가격 설정 - 5백만원 근처 가격으로 변경
            base_price = 5000000  # 5백만원
            
            # 시나리오별 가격 패턴 생성
            if scenario in ["상승 추세", "Uptrend"]:
                trend = np.linspace(0, 500000, length)  # 50만원 상승
                noise = np.random.randn(length) * 50000  # 5만원 변동
                price_data = base_price + trend + noise
            elif scenario in ["하락 추세", "Downtrend"]:
                trend = np.linspace(0, -300000, length)  # 30만원 하락
                noise = np.random.randn(length) * 50000
                price_data = base_price + trend + noise
            elif scenario in ["급등", "Surge"]:
                # 중간에 급등하는 패턴
                trend = np.concatenate([
                    np.linspace(0, 100000, length // 3),
                    np.linspace(100000, 1000000, length // 3),
                    np.linspace(1000000, 800000, length - 2 * (length // 3))
                ])
                noise = np.random.randn(length) * 80000
                price_data = base_price + trend + noise
            elif scenario in ["급락", "Crash"]:
                # 중간에 급락하는 패턴
                trend = np.concatenate([
                    np.linspace(0, 200000, length // 3),
                    np.linspace(200000, -800000, length // 3),
                    np.linspace(-800000, -600000, length - 2 * (length // 3))
                ])
                noise = np.random.randn(length) * 80000
                price_data = base_price + trend + noise
            elif scenario in ["횡보", "Sideways"]:
                # 횡보 패턴 - 5백만원 근처에서 변동
                noise = np.random.randn(length) * 30000  # 3만원 변동
                price_data = base_price + noise
            elif scenario in ["이동평균 교차", "MA Cross"]:
                # 이동평균 교차 패턴
                noise = np.random.randn(length) * 40000
                price_data = base_price + np.cumsum(noise * 0.01)
            else:
                # 기본 랜덤 패턴 - 5백만원 기준
                noise = np.random.randn(length) * 60000
                price_data = base_price + np.cumsum(noise * 0.02)
            
            # 가격이 음수가 되지 않도록 보정
            price_data = np.maximum(price_data, 100000)  # 최소 10만원
            
            return price_data.tolist()
            
        except Exception as e:
            print(f"❌ 가격 데이터 생성 실패: {e}")
            # 기본 5백만원 근처 랜덤 데이터
            import random
            return [5000000 + random.randint(-200000, 200000) for _ in range(length)]
    
    def generate_rsi_data_for_chart(self, scenario, length=50):
        """RSI용 시뮬레이션 데이터 생성 (0-100 범위)"""
        try:
            import numpy as np
            
            # RSI 기본값 설정
            base_rsi = 50  # 중립값
            
            # 시나리오별 RSI 패턴
            if scenario in ["상승 추세", "Uptrend"]:
                # 상승 추세: RSI가 50에서 70으로 증가
                trend = np.linspace(0, 20, length)
                noise = np.random.randn(length) * 5
                rsi_data = base_rsi + trend + noise
            elif scenario in ["하락 추세", "Downtrend"]:
                # 하락 추세: RSI가 50에서 30으로 감소
                trend = np.linspace(0, -20, length)
                noise = np.random.randn(length) * 5
                rsi_data = base_rsi + trend + noise
            elif scenario in ["급등", "Surge"]:
                # 급등: RSI가 빠르게 과매수 구간(70+)으로
                trend = np.concatenate([
                    np.linspace(0, 10, length // 3),
                    np.linspace(10, 35, length // 3),
                    np.linspace(35, 30, length - 2 * (length // 3))
                ])
                noise = np.random.randn(length) * 3
                rsi_data = base_rsi + trend + noise
            elif scenario in ["급락", "Crash"]:
                # 급락: RSI가 빠르게 과매도 구간(30-)으로
                trend = np.concatenate([
                    np.linspace(0, 5, length // 3),
                    np.linspace(5, -35, length // 3),
                    np.linspace(-35, -30, length - 2 * (length // 3))
                ])
                noise = np.random.randn(length) * 3
                rsi_data = base_rsi + trend + noise
            elif scenario in ["횡보", "Sideways"]:
                # 횡보: RSI 50 근처에서 변동
                noise = np.random.randn(length) * 8
                rsi_data = base_rsi + noise
            else:
                # 기본: RSI 랜덤 변동
                noise = np.random.randn(length) * 10
                rsi_data = base_rsi + np.cumsum(noise * 0.1)
            
            # RSI 범위 제한 (0-100)
            rsi_data = np.clip(rsi_data, 0, 100)
            
            print(f"📊 RSI 데이터 생성: {scenario}, 범위 {rsi_data.min():.1f}-{rsi_data.max():.1f}")
            return rsi_data.tolist()
            
        except Exception as e:
            print(f"❌ RSI 데이터 생성 실패: {e}")
            # 기본 RSI 데이터
            import random
            return [random.uniform(20, 80) for _ in range(length)]
    
    def generate_macd_data_for_chart(self, scenario, length=50):
        """MACD용 시뮬레이션 데이터 생성 (-2 ~ 2 범위)"""
        try:
            import numpy as np
            
            # MACD 기본값 설정
            base_macd = 0  # 중립값
            
            # 시나리오별 MACD 패턴
            if scenario in ["상승 추세", "Uptrend"]:
                # 상승 추세: MACD가 양수로 증가
                trend = np.linspace(0, 1.5, length)
                noise = np.random.randn(length) * 0.1
                macd_data = base_macd + trend + noise
            elif scenario in ["하락 추세", "Downtrend"]:
                # 하락 추세: MACD가 음수로 감소
                trend = np.linspace(0, -1.5, length)
                noise = np.random.randn(length) * 0.1
                macd_data = base_macd + trend + noise
            elif scenario in ["급등", "Surge"]:
                # 급등: MACD가 빠르게 큰 양수로
                trend = np.concatenate([
                    np.linspace(0, 0.5, length // 3),
                    np.linspace(0.5, 2.0, length // 3),
                    np.linspace(2.0, 1.5, length - 2 * (length // 3))
                ])
                noise = np.random.randn(length) * 0.05
                macd_data = base_macd + trend + noise
            elif scenario in ["급락", "Crash"]:
                # 급락: MACD가 빠르게 큰 음수로
                trend = np.concatenate([
                    np.linspace(0, -0.3, length // 3),
                    np.linspace(-0.3, -2.0, length // 3),
                    np.linspace(-2.0, -1.5, length - 2 * (length // 3))
                ])
                noise = np.random.randn(length) * 0.05
                macd_data = base_macd + trend + noise
            elif scenario in ["이동평균 교차", "MA Cross"]:
                # 이동평균 교차: MACD가 0 근처에서 교차
                noise = np.random.randn(length) * 0.2
                macd_data = np.sin(np.linspace(0, 4*np.pi, length)) * 0.5 + noise
            else:
                # 기본: MACD 랜덤 변동
                noise = np.random.randn(length) * 0.3
                macd_data = base_macd + np.cumsum(noise * 0.05)
            
            # MACD 범위 제한 (-2 ~ 2)
            macd_data = np.clip(macd_data, -2, 2)
            
            print(f"📊 MACD 데이터 생성: {scenario}, 범위 {macd_data.min():.2f}-{macd_data.max():.2f}")
            return macd_data.tolist()
            
        except Exception as e:
            print(f"❌ MACD 데이터 생성 실패: {e}")
            # 기본 MACD 데이터
            import random
            return [random.uniform(-1, 1) for _ in range(length)]
    
    def generate_simulation_data(self, scenario, variable_name):
        """시나리오별 실제 데이터 기반 시뮬레이션 - 업그레이드 버전"""
        try:
            # 실제 데이터 시뮬레이션 엔진 사용
            from .real_data_simulation import get_simulation_engine
            
            engine = get_simulation_engine()
            real_data = engine.get_scenario_data(scenario, length=50)
            
            if real_data and real_data.get('data_source') == 'real_market_data':
                # 실제 시장 데이터 사용 성공
                print(f"✅ 실제 시장 데이터 사용: {scenario} ({real_data.get('period', 'Unknown')})")
                
                # 변수 타입에 따른 값 조정
                current_value = real_data['current_value']
                
                if 'rsi' in variable_name.lower():
                    # RSI 시뮬레이션을 위한 값 조정 (0-100 범위)
                    current_value = min(max(current_value % 100, 0), 100)
                elif 'ma' in variable_name.lower() or '이동평균' in variable_name.lower():
                    # 이동평균 관련은 그대로 사용
                    pass
                elif 'macd' in variable_name.lower():
                    # MACD는 -1 ~ 1 범위로 조정
                    current_value = (current_value / 50000) - 1
                
                return {
                    'current_value': current_value,
                    'base_value': real_data['base_value'],
                    'change_percent': real_data['change_percent'],
                    'scenario': scenario,
                    'data_source': 'real_market_data',
                    'period': real_data.get('period', 'Unknown')
                }
            else:
                # 실제 데이터 로드 실패 시 폴백
                print(f"⚠️ 실제 데이터 로드 실패, 시뮬레이션 데이터 사용: {scenario}")
        
        except Exception as e:
            print(f"❌ 실제 데이터 엔진 오류: {e}")
        
        # 폴백: 변수 타입별 시뮬레이션 데이터 생성 (개선된 버전)
        import random
        
        # 변수 타입에 따른 시나리오별 값 생성
        if 'rsi' in variable_name.lower():
            # RSI 시뮬레이션 (0-100 범위)
            if scenario in ["Uptrend", "상승 추세"]:
                base_value = random.uniform(55, 75)  # 상승 시 RSI 높음
            elif scenario in ["Downtrend", "하락 추세"]:
                base_value = random.uniform(25, 45)  # 하락 시 RSI 낮음
            elif scenario in ["Surge", "급등"]:
                base_value = random.uniform(70, 85)  # 급등 시 과매수
            elif scenario in ["Crash", "급락"]:
                base_value = random.uniform(15, 35)  # 급락 시 과매도
            else:
                base_value = random.uniform(40, 60)  # 중립
                
        elif 'macd' in variable_name.lower():
            # MACD 시뮬레이션 (-2 ~ 2 범위)
            if scenario in ["Uptrend", "상승 추세"]:
                base_value = random.uniform(0.2, 1.5)  # 상승 시 양수
            elif scenario in ["Downtrend", "하락 추세"]:
                base_value = random.uniform(-1.5, -0.2)  # 하락 시 음수
            elif scenario in ["Surge", "급등"]:
                base_value = random.uniform(1.0, 2.0)  # 급등 시 큰 양수
            elif scenario in ["Crash", "급락"]:
                base_value = random.uniform(-2.0, -1.0)  # 급락 시 큰 음수
            elif scenario in ["MA Cross", "이동평균 교차"]:
                base_value = random.uniform(-0.3, 0.3)  # 교차점 근처
            else:
                base_value = random.uniform(-0.5, 0.5)  # 중립
                
        elif 'price' in variable_name.lower() or '가격' in variable_name.lower():
            # 가격 시뮬레이션 (5백만원 기준)
            base_price = 5000000
            if scenario in ["Uptrend", "상승 추세"]:
                base_value = base_price * random.uniform(1.05, 1.15)
            elif scenario in ["Downtrend", "하락 추세"]:
                base_value = base_price * random.uniform(0.85, 0.95)
            elif scenario in ["Surge", "급등"]:
                base_value = base_price * random.uniform(1.2, 1.5)
            elif scenario in ["Crash", "급락"]:
                base_value = base_price * random.uniform(0.6, 0.8)
            else:
                base_value = base_price * random.uniform(0.98, 1.02)
                
        elif 'volume' in variable_name.lower() or '거래량' in variable_name.lower():
            # 거래량 시뮬레이션
            if scenario in ["Surge", "급등", "Crash", "급락"]:
                base_value = random.uniform(5000000, 20000000)  # 높은 거래량
            else:
                base_value = random.uniform(1000000, 5000000)  # 일반 거래량
        else:
            # 기타 지표들
            base_value = random.uniform(30, 70)
        
        # 최종 값 반환
        current_value = base_value
        
        return {
            'current_value': current_value,
            'base_value': base_value,
            'change_percent': 0,  # 변경율은 시나리오별 값에 이미 반영됨
            'scenario': scenario,
            'data_source': 'fallback_simulation'
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
            # 편집 모드인지 확인
            if hasattr(self.condition_dialog, 'edit_mode') and self.condition_dialog.edit_mode:
                # 이미 편집 모드인 경우: 편집 저장
                self.condition_dialog.save_condition()
            else:
                # 편집 모드 시작
                if hasattr(self.condition_dialog, 'load_condition'):
                    self.condition_dialog.load_condition(self.selected_condition)
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
        if is_edit_mode:
            # 편집 모드: "편집 저장" 버튼으로 변경
            self.edit_btn.setText("💾 편집 저장")
            self.edit_btn.setStyleSheet("""
                QPushButton {
                    background-color: #fd7e14;
                    color: white;
                    border: none;
                    padding: 6px 12px;
                    border-radius: 4px;
                    font-size: 11px;
                    font-weight: bold;
                }
                QPushButton:hover {
                    background-color: #e8681a;
                }
                QPushButton:pressed {
                    background-color: #d9580d;
                }
            """)
        else:
            # 일반 모드: "편집" 버튼으로 복원
            self.edit_btn.setText("✏️ 편집")
            self.edit_btn.setStyleSheet("")  # 기본 SecondaryButton 스타일 사용
    
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
                    self.storage.delete_condition(condition_id)
                    
                    # UI 업데이트
                    self.load_trigger_list()
                    self.trigger_detail_text.setPlainText("트리거를 선택하면 상세 정보가 표시됩니다.")
                    self.selected_condition = None
                    
                    # 상태 업데이트
                    self.simulation_status.setText(f"🗑️ '{condition_name}' 삭제 완료!")
                    self.add_test_history_item(f"트리거 삭제: {condition_name}", "save")
                    
                    QMessageBox.information(self, "✅ 삭제 완료", f"'{condition_name}' 트리거가 삭제되었습니다.")
                    
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


if __name__ == "__main__":
    from PyQt6.QtWidgets import QApplication
    import sys
    
    app = QApplication(sys.argv)
    
    window = IntegratedConditionManager()
    window.show()
    
    sys.exit(app.exec())
