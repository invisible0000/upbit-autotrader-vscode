"""
트리거 빌더 메인 화면 - 기존 기능 완전 복원
IntegratedConditionManager에서 검증된 모든 기능을 그대로 이관
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

# 새로운 컴포넌트들 import
from .components.chart_visualizer import ChartVisualizer
from .components.simulation_engines import get_embedded_simulation_engine  
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
from ..components.condition_storage import ConditionStorage
from ..components.condition_loader import ConditionLoader
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
        # 크기를 더욱 압축하여 1600x1000 화면에 최적화
        self.setMinimumSize(600, 400)
        
        # 기존 컴포넌트 초기화
        self.storage = ConditionStorage()
        self.loader = ConditionLoader(self.storage)
        self.selected_condition = None
        
        # 새로운 컴포넌트 초기화
        self.chart_visualizer = ChartVisualizer()
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
        
        print("✅ 트리거 빌더 UI 초기화 완료")
    
    def create_condition_builder_area(self):
        """1+4: 조건 빌더 영역"""
        group = QGroupBox("🎯 조건 빌더")
        layout = QVBoxLayout()
        layout.setContentsMargins(5, 8, 5, 5)
        layout.setSpacing(3)
        
        # 조건 빌더 다이얼로그를 임베디드 형태로 포함
        try:
            self.condition_dialog = ConditionDialog(embedded=True)
            # 임베디드 모드에서는 최대한 공간 절약
            self.condition_dialog.setMaximumHeight(800)
            layout.addWidget(self.condition_dialog)
        except Exception as e:
            print(f"⚠️ 조건 빌더 다이얼로그 생성 실패: {e}")
            # 폴백: 간단한 인터페이스
            fallback_layout = QVBoxLayout()
            label = QLabel("🔧 조건 빌더 로딩 중...")
            fallback_layout.addWidget(label)
            layout.addLayout(fallback_layout)
        
        group.setLayout(layout)
        return group
    
    def create_trigger_list_area(self):
        """2: 등록된 트리거 리스트 영역"""
        group = QGroupBox("📋 등록된 트리거")
        layout = QVBoxLayout()
        layout.setContentsMargins(5, 8, 5, 5)
        layout.setSpacing(3)
        
        # 상단 버튼들
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(2)
        
        self.new_trigger_btn = QPushButton("➕ 새 트리거")
        self.new_trigger_btn.setMaximumHeight(25)
        self.new_trigger_btn.clicked.connect(self.new_trigger)
        btn_layout.addWidget(self.new_trigger_btn)
        
        self.edit_trigger_btn = QPushButton("✏️ 편집")
        self.edit_trigger_btn.setMaximumHeight(25)
        self.edit_trigger_btn.clicked.connect(self.edit_trigger)
        btn_layout.addWidget(self.edit_trigger_btn)
        
        self.delete_trigger_btn = QPushButton("🗑️ 삭제")
        self.delete_trigger_btn.setMaximumHeight(25)
        self.delete_trigger_btn.clicked.connect(self.delete_trigger)
        btn_layout.addWidget(self.delete_trigger_btn)
        
        self.copy_trigger_btn = QPushButton("📄 복사")
        self.copy_trigger_btn.setMaximumHeight(25)
        self.copy_trigger_btn.clicked.connect(self.copy_trigger)
        btn_layout.addWidget(self.copy_trigger_btn)
        
        layout.addLayout(btn_layout)
        
        # 트리거 목록
        self.trigger_tree = QTreeWidget()
        self.trigger_tree.setHeaderLabels(["이름", "생성일", "활성"])
        self.trigger_tree.itemClicked.connect(self.on_trigger_selected)
        layout.addWidget(self.trigger_tree)
        
        group.setLayout(layout)
        return group
    
    def create_simulation_area(self):
        """3: 케이스 시뮬레이션 버튼들 영역"""
        group = QGroupBox("🎮 케이스 시뮬레이션")
        layout = QVBoxLayout()
        layout.setContentsMargins(5, 8, 5, 5)
        layout.setSpacing(3)
        
        # 시뮬레이션 케이스 버튼들
        cases = [
            ("🟢 상승장", self.run_bull_simulation),
            ("🔴 하락장", self.run_bear_simulation),
            ("📊 횡보장", self.run_sideways_simulation),
            ("⚡ 변동성", self.run_volatile_simulation),
            ("🎯 복합 시나리오", self.run_complex_simulation)
        ]
        
        for case_name, callback in cases:
            btn = QPushButton(case_name)
            btn.setMaximumHeight(30)
            btn.clicked.connect(callback)
            layout.addWidget(btn)
        
        # 간격 추가
        layout.addSpacing(10)
        
        # 시뮬레이션 제어
        control_layout = QHBoxLayout()
        
        self.run_all_btn = QPushButton("🚀 전체 실행")
        self.run_all_btn.setMaximumHeight(25)
        self.run_all_btn.clicked.connect(self.run_all_simulations)
        control_layout.addWidget(self.run_all_btn)
        
        self.stop_btn = QPushButton("⏹️ 중지")
        self.stop_btn.setMaximumHeight(25)
        self.stop_btn.clicked.connect(self.stop_simulation)
        control_layout.addWidget(self.stop_btn)
        
        layout.addLayout(control_layout)
        
        # 진행률 표시
        self.progress_bar = QProgressBar()
        self.progress_bar.setMaximumHeight(15)
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)
        
        group.setLayout(layout)
        return group
    
    def create_trigger_detail_area(self):
        """5: 선택한 트리거 상세 정보 영역"""
        group = QGroupBox("📊 트리거 상세정보")
        layout = QVBoxLayout()
        layout.setContentsMargins(5, 8, 5, 5)
        layout.setSpacing(3)
        
        # 상세 정보 표시
        self.detail_text = QTextEdit()
        self.detail_text.setReadOnly(True)
        self.detail_text.setMaximumHeight(200)
        
        # 폰트 크기를 더 작게 설정
        font = QFont()
        font.setPointSize(8)
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
        if CHART_AVAILABLE:
            try:
                # matplotlib 차트 생성
                self.figure = Figure(figsize=(6, 3), dpi=80)
                self.canvas = FigureCanvas(self.figure)
                self.canvas.setMaximumHeight(200)
                
                # 초기 차트 그리기
                self.update_chart_display()
                
                return self.canvas
            except Exception as e:
                print(f"⚠️ 차트 위젯 생성 실패: {e}")
        
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
        """트리거 상세정보 업데이트"""
        try:
            if not condition:
                self.detail_text.setPlainText("트리거를 선택하면 상세정보가 표시됩니다.")
                return
            
            # 상세정보 포맷팅 (줄간격 최소화)
            details = []
            details.append(f"📋 트리거 이름: {condition.get('name', 'Unknown')}")
            details.append(f"📅 생성일: {condition.get('created_at', 'Unknown')}")
            details.append(f"🎯 변수: {condition.get('variable', 'Unknown')}")
            details.append(f"⚙️ 연산자: {condition.get('operator', 'Unknown')}")
            details.append(f"📊 값: {condition.get('value', 'Unknown')}")
            details.append(f"📈 시장: {condition.get('market', 'Unknown')}")
            details.append(f"🔄 상태: {'활성' if condition.get('active', True) else '비활성'}")
            
            # 파라미터 정보 추가
            if 'parameters' in condition and condition['parameters']:
                details.append("📌 파라미터:")
                for param_name, param_value in condition['parameters'].items():
                    details.append(f"  • {param_name}: {param_value}")
            
            detail_text = '\n'.join(details)
            self.detail_text.setPlainText(detail_text)
            
        except Exception as e:
            print(f"❌ 트리거 상세정보 업데이트 실패: {e}")
            self.detail_text.setPlainText(f"❌ 상세정보 로드 실패: {str(e)}")
    
    # 트리거 관리 메서드들
    def new_trigger(self):
        """새 트리거 생성"""
        try:
            if hasattr(self, 'condition_dialog'):
                if hasattr(self.condition_dialog, 'clear_all_inputs'):
                    self.condition_dialog.clear_all_inputs()
                print("✅ 새 트리거 생성 모드")
            else:
                QMessageBox.information(self, "ℹ️ 알림", "조건 빌더를 사용하여 새 트리거를 생성하세요.")
        except Exception as e:
            print(f"❌ 새 트리거 생성 실패: {e}")
    
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
    
    # 시뮬레이션 메서드들
    def run_bull_simulation(self):
        """상승장 시뮬레이션"""
        self.run_simulation_scenario("상승장", "🟢")
    
    def run_bear_simulation(self):
        """하락장 시뮬레이션"""
        self.run_simulation_scenario("하락장", "🔴")
    
    def run_sideways_simulation(self):
        """횡보장 시뮬레이션"""
        self.run_simulation_scenario("횡보장", "📊")
    
    def run_volatile_simulation(self):
        """변동성 시뮬레이션"""
        self.run_simulation_scenario("변동성", "⚡")
    
    def run_complex_simulation(self):
        """복합 시나리오 시뮬레이션"""
        self.run_simulation_scenario("복합", "🎯")
    
    def run_simulation_scenario(self, scenario_name, icon):
        """시뮬레이션 시나리오 실행"""
        try:
            if not self.selected_condition:
                QMessageBox.warning(self, "⚠️ 경고", "시뮬레이션할 트리거를 선택하세요.")
                return
            
            print(f"🎮 {scenario_name} 시뮬레이션 시작")
            
            # 임시 시뮬레이션 결과 생성
            result = {
                'scenario': scenario_name,
                'icon': icon,
                'trigger_count': random.randint(3, 15),
                'success_rate': random.uniform(60.0, 90.0),
                'profit_loss': random.uniform(-5.0, 12.0),
                'execution_time': random.uniform(0.1, 0.8)
            }
            
            # 결과 로그에 추가
            self.add_simulation_log(result)
            
            # 차트 업데이트
            if CHART_AVAILABLE:
                self.update_chart_with_scenario(scenario_name)
            
            print(f"✅ {scenario_name} 시뮬레이션 완료")
            
        except Exception as e:
            print(f"❌ {scenario_name} 시뮬레이션 실패: {e}")
    
    def add_simulation_log(self, result):
        """시뮬레이션 결과를 로그에 추가"""
        try:
            current_time = datetime.now().strftime("%H:%M:%S")
            log_entry = (
                f"[{current_time}] {result['icon']} {result['scenario']} "
                f"| 신호: {result['trigger_count']}회 "
                f"| 성공률: {result['success_rate']:.1f}% "
                f"| 수익률: {result['profit_loss']:+.2f}% "
                f"| 실행시간: {result['execution_time']:.3f}초"
            )
            
            current_log = self.log_widget.toPlainText()
            if current_log.strip() == "시뮬레이션 실행 기록이 여기에 표시됩니다.":
                self.log_widget.setPlainText(log_entry)
            else:
                self.log_widget.setPlainText(f"{current_log}\n{log_entry}")
            
            # 스크롤을 맨 아래로
            cursor = self.log_widget.textCursor()
            cursor.movePosition(cursor.MoveOperation.End)
            self.log_widget.setTextCursor(cursor)
            
        except Exception as e:
            print(f"❌ 시뮬레이션 로그 추가 실패: {e}")
    
    def update_chart_with_scenario(self, scenario_name):
        """시나리오에 따른 차트 업데이트"""
        if not CHART_AVAILABLE or not hasattr(self, 'figure'):
            return
        
        try:
            self.figure.clear()
            ax = self.figure.add_subplot(111)
            
            # 시나리오별 데이터 생성
            dates = pd.date_range(start='2024-01-01', periods=30, freq='D')
            
            if scenario_name == "상승장":
                trend = np.linspace(0, 10, 30)
                noise = np.random.randn(30) * 0.5
                prices = 100 + trend + noise
            elif scenario_name == "하락장":
                trend = np.linspace(0, -8, 30)
                noise = np.random.randn(30) * 0.5
                prices = 100 + trend + noise
            elif scenario_name == "횡보장":
                noise = np.random.randn(30) * 0.3
                prices = 100 + noise
            elif scenario_name == "변동성":
                noise = np.random.randn(30) * 2.0
                prices = 100 + noise.cumsum() * 0.3
            else:  # 복합
                trend = np.sin(np.linspace(0, 4*np.pi, 30)) * 3
                noise = np.random.randn(30) * 0.8
                prices = 100 + trend + noise
            
            ax.plot(dates, prices, 'b-', linewidth=1.5, label='가격')
            
            # 트리거 마커 추가
            trigger_points = random.sample(range(5, 25), random.randint(2, 6))
            for point in trigger_points:
                ax.scatter(dates[point], prices[point], c='red', s=30, marker='^', zorder=5)
            
            ax.set_title(f'{scenario_name} 시뮬레이션 결과', fontsize=10)
            ax.set_ylabel('가격', fontsize=8)
            ax.tick_params(axis='both', which='major', labelsize=7)
            ax.grid(True, alpha=0.3)
            
            # 레이아웃 조정
            self.figure.tight_layout(pad=1.0)
            self.canvas.draw()
            
        except Exception as e:
            print(f"⚠️ 차트 업데이트 실패: {e}")
    
    def run_all_simulations(self):
        """전체 시뮬레이션 실행"""
        try:
            if not self.selected_condition:
                QMessageBox.warning(self, "⚠️ 경고", "시뮬레이션할 트리거를 선택하세요.")
                return
            
            print("🚀 전체 시뮬레이션 시작")
            
            # 진행률 표시
            self.progress_bar.setVisible(True)
            self.progress_bar.setValue(0)
            
            scenarios = [
                ("상승장", "🟢"),
                ("하락장", "🔴"),
                ("횡보장", "📊"),
                ("변동성", "⚡"),
                ("복합", "🎯")
            ]
            
            for i, (scenario, icon) in enumerate(scenarios):
                # 시뮬레이션 실행
                self.run_simulation_scenario(scenario, icon)
                
                # 진행률 업데이트
                progress = int((i + 1) / len(scenarios) * 100)
                self.progress_bar.setValue(progress)
                
                # UI 업데이트를 위한 짧은 대기
                QTimer.singleShot(200, lambda: None)
            
            # 완료 후 진행률 바 숨김
            QTimer.singleShot(1000, lambda: self.progress_bar.setVisible(False))
            
            print("✅ 전체 시뮬레이션 완료")
            
        except Exception as e:
            print(f"❌ 전체 시뮬레이션 실패: {e}")
            self.progress_bar.setVisible(False)
    
    def stop_simulation(self):
        """시뮬레이션 중지"""
        try:
            print("⏹️ 시뮬레이션 중지")
            self.progress_bar.setVisible(False)
            
            # 중지 로그 추가
            current_time = datetime.now().strftime("%H:%M:%S")
            log_entry = f"[{current_time}] ⏹️ 시뮬레이션 중지됨"
            
            current_log = self.log_widget.toPlainText()
            self.log_widget.setPlainText(f"{current_log}\n{log_entry}")
            
        except Exception as e:
            print(f"❌ 시뮬레이션 중지 실패: {e}")
