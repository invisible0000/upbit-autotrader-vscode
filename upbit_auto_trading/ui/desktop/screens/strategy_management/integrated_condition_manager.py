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

from components.condition_dialog import ConditionDialog
from components.condition_storage import ConditionStorage
from components.condition_loader import ConditionLoader

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
                padding-top: 10px;  /* 상단 패딩 줄이기 */
                margin: 1px;        /* 마진 줄이기 */
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
                background-color: white;
                color: #333333;
                font-size: 11px;    /* 폰트 크기 줄이기 */
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
                padding-top: 10px;  /* 상단 패딩 줄이기 */
                margin: 1px;        /* 마진 줄이기 */
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
                background-color: white;
                color: #333333;
                font-size: 11px;    /* 폰트 크기 줄이기 */
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
        layout.setContentsMargins(8, 8, 8, 8)  # 패딩 줄이기
        layout.setSpacing(3)  # 간격 줄이기
        
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
        
        # 미니 차트 영역 (모의)
        chart_label = QLabel("📊 미니 차트 영역")
        chart_label.setStyleSheet("""
            border: 3px dashed #fd7e14;
            border-radius: 12px;
            padding: 30px;
            text-align: center;
            color: #fd7e14;
            font-weight: bold;
            font-size: 14px;
            background-color: #fff8f0;
            min-height: 120px;
        """)
        chart_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(chart_label)
        
        # 작동 기록 리스트
        self.test_history_list = QListWidget()
        self.test_history_list.setStyleSheet("""
            QListWidget {
                border: 2px solid #ddd;
                border-radius: 8px;
                background-color: white;
                max-height: 180px;
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
                margin: 2px;        /* 마진 줄이기 */
                padding-top: 10px;  /* 상단 패딩 줄이기 */
                background-color: #fafafa;
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                left: 15px;
                padding: 0 8px 0 8px;
                background-color: white;
                color: {color};
                font-size: 11px;     /* 폰트 크기 줄이기 */
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
        
        # 상세 정보 표시
        detail_text = f"""
🎯 조건명: {condition_data.get('name', 'Unknown')}
📝 설명: {condition_data.get('description', 'No description')}

📊 변수 정보:
  • 변수: {condition_data.get('variable_name', 'Unknown')}
  • 파라미터: {condition_data.get('variable_params', {})}

⚖️ 비교 설정:
  • 연산자: {condition_data.get('operator', 'Unknown')}
  • 비교 타입: {condition_data.get('comparison_type', 'Unknown')}
  • 대상값: {condition_data.get('target_value', 'Unknown')}

🏷️ 카테고리: {condition_data.get('category', 'Unknown')}
🕐 생성일: {condition_data.get('created_at', 'Unknown')}
        """
        
        self.trigger_detail_text.setPlainText(detail_text.strip())
        
        # 시뮬레이션 상태 업데이트
        self.simulation_status.setText(f"🎯 '{condition_data.get('name', 'Unknown')}' 선택됨 - 시나리오를 클릭하세요")
        
        print(f"📊 트리거 선택: {condition_data.get('name', 'Unknown')}")
    
    def run_simulation(self, scenario):
        """시뮬레이션 실행 - 실제 조건 로직 기반"""
        if not self.selected_condition:
            QMessageBox.warning(self, "⚠️ 경고", "먼저 트리거를 선택해주세요.")
            return
        
        condition_name = self.selected_condition.get('name', 'Unknown')
        variable_name = self.selected_condition.get('variable_name', 'Unknown')
        operator = self.selected_condition.get('operator', '>')
        target_value = self.selected_condition.get('target_value', '0')
        
        # 시뮬레이션 상태 업데이트
        self.simulation_status.setText(f"🔄 {scenario} 시나리오 실행 중...")
        
        # 시나리오별 가상 데이터 생성
        simulation_data = self.generate_simulation_data(scenario, variable_name)
        
        # 조건 평가
        try:
            target_num = float(target_value)
            current_value = simulation_data['current_value']
            
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
                diff_percent = abs(current_value - target_num) / target_num * 100
                result = diff_percent <= 1.0
            elif operator == '!=':
                result = current_value != target_num
            else:
                result = False
                
        except (ValueError, ZeroDivisionError):
            result = False
            current_value = 0
        
        # 결과 표시
        result_emoji = "✅" if result else "❌"
        status_text = "조건 만족" if result else "조건 불만족"
        
        self.simulation_status.setText(
            f"{result_emoji} {scenario}: {status_text}\n"
            f"현재값: {current_value:.2f} {operator} {target_value}"
        )
        
        # 상세 로그
        detail_log = (
            f"{result_emoji} {scenario} 시뮬레이션\n"
            f"변수: {variable_name}\n"
            f"조건: {current_value:.2f} {operator} {target_value}\n"
            f"결과: {status_text}"
        )
        
        # 테스트 기록 추가
        self.add_test_history_item(f"{result_emoji} {scenario} - {condition_name} ({status_text})", "test")
        
        # 시그널 발생
        self.condition_tested.emit(self.selected_condition, result)
        
        print(f"🎮 시뮬레이션 실행: {scenario} → {result} (값: {current_value})")
    
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
            # 조건 다이얼로그에 현재 조건 로드
            if hasattr(self.condition_dialog, 'load_condition'):
                self.condition_dialog.load_condition(self.selected_condition)
                QMessageBox.information(self, "✅ 편집", "1. 조건 빌더에 설정이 Load 되었습니다.\n2. 수정 후 저장하세요.")
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
