"""
트리거 빌더 메인 화면 - Components 전용
"""

import sys
from datetime import datetime
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QGroupBox,
    QPushButton, QLabel, QMessageBox, QApplication,
    QTreeWidgetItem, QListWidgetItem, QTreeWidget, QLineEdit, QComboBox
)
from PyQt6.QtCore import Qt, pyqtSignal, QTimer

# matplotlib 관련 import (차트용)
try:
    import numpy as np
    import pandas as pd
    import traceback
    import random
    ADDITIONAL_LIBS_AVAILABLE = True
except ImportError:
    ADDITIONAL_LIBS_AVAILABLE = False
    print("⚠️ 추가 라이브러리를 사용할 수 없습니다.")

# 공통 스타일 시스템 import (메인 애플리케이션에서 상속받으므로 불필요)
# try:
#     from upbit_auto_trading.ui.desktop.common.styles.style_manager import StyleManager, Theme
#     STYLE_MANAGER_AVAILABLE = True
# except ImportError:
#     STYLE_MANAGER_AVAILABLE = False
#     print("⚠️ 공통 스타일 시스템을 로드할 수 없습니다.")

# Components import
from .components.condition_dialog import ConditionDialog
from .components.trigger_list_widget import TriggerListWidget
from .components.trigger_detail_widget import TriggerDetailWidget
from .components.simulation_control_widget import SimulationControlWidget
from .components.simulation_result_widget import SimulationResultWidget
from .components.chart_visualizer import ChartVisualizer
from .components.trigger_calculator import TriggerCalculator

# Chart variable system import
try:
    from .components.chart_variable_service import get_chart_variable_service
    from .components.variable_display_system import get_variable_registry
    CHART_VARIABLE_SYSTEM_AVAILABLE = True
except ImportError:
    CHART_VARIABLE_SYSTEM_AVAILABLE = False

# Chart availability flag (components handle chart functionality)
CHART_AVAILABLE = True

# matplotlib 한글 폰트 설정 - 강력한 버전
try:
    import matplotlib.pyplot as plt
    import matplotlib.font_manager as fm
    import matplotlib as mpl
    
    # 폰트 캐시 갱신
    fm._rebuild()
    
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
        # matplotlib 전역 설정
        plt.rcParams['font.family'] = selected_font
        plt.rcParams['axes.unicode_minus'] = False
        plt.rcParams['font.sans-serif'] = [selected_font] + plt.rcParams['font.sans-serif']
        
        # matplotlib 백엔드 전체 설정
        mpl.font_manager.fontManager.addfont(
            fm.findfont(fm.FontProperties(family=selected_font))
        )
        
        print(f"✅ matplotlib 한글 폰트 설정: {selected_font}")
    else:
        plt.rcParams['axes.unicode_minus'] = False
        print("⚠️ 한글 폰트를 찾을 수 없어 기본 폰트 사용")
except ImportError:
    print("⚠️ matplotlib를 찾을 수 없습니다.")
except Exception as e:
    print(f"⚠️ matplotlib 한글 폰트 설정 실패: {e}")

# ConditionStorage와 ConditionLoader import
try:
    # 먼저 trigger_builder/components에서 로드 시도 (최신 버전)
    from .components.condition_storage import ConditionStorage
    from .components.condition_loader import ConditionLoader
    print("✅ ConditionStorage, ConditionLoader 로드 성공 (trigger_builder/components)")
except ImportError:
    try:
        # 폴백: strategy_management/components에서 로드
        from upbit_auto_trading.ui.desktop.screens.strategy_management.components.condition_storage import ConditionStorage
        from upbit_auto_trading.ui.desktop.screens.strategy_management.components.condition_loader import ConditionLoader
        print("✅ ConditionStorage, ConditionLoader 로드 성공 (strategy_management/components)")
    except ImportError as e:
        print(f"❌ ConditionStorage, ConditionLoader 로드 실패: {e}")
        # 간단한 폴백 클래스 생성
        class ConditionStorage:
            def get_all_conditions(self):
                return []
            def delete_condition(self, condition_id):
                return False, f"Mock storage - 삭제 불가: {condition_id}"
        
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
        # 메인 윈도우에 맞춘 최소 크기 설정 (1280x720) - 반응형
        self.setMinimumSize(1280, 720)
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
        
        # 메인 애플리케이션의 스타일을 상속받음 (부모에서 적용된 스타일 재적용)
        self.ensure_style_inheritance()
        print("✅ 트리거 빌더는 메인 애플리케이션의 스타일을 상속받습니다")
    
    def ensure_style_inheritance(self):
        """메인 애플리케이션의 스타일 상속 보장"""
        try:
            # QApplication의 현재 스타일시트를 가져와서 적용
            app = QApplication.instance()
            if app:
                current_style = app.styleSheet()
                if current_style:
                    # 현재 테마가 다크인지 확인 (background-color: #2c2c2c가 있으면 다크)
                    is_dark_theme = '#2c2c2c' in current_style
                    
                    # 자신에게는 스타일을 적용하지 않고, 하위 위젯들이 스타일을 상속받도록 함
                    self.update()  # 위젯 업데이트로 스타일 재적용 유도
                    
                    # 차트 배경색 업데이트 (필요시)
                    if hasattr(self, 'figure') and self.figure:
                        self.apply_chart_theme(is_dark_theme)
                    
                    print(f"✅ 애플리케이션 스타일 상속 완료 (다크 테마: {is_dark_theme})")
                else:
                    print("⚠️ 애플리케이션에 적용된 스타일시트가 없습니다")
            else:
                print("⚠️ QApplication 인스턴스를 찾을 수 없습니다")
        except Exception as e:
            print(f"⚠️ 스타일 상속 설정 실패: {e}")
    
    def apply_chart_theme(self, is_dark_theme):
        """차트에 테마 적용"""
        try:
            if hasattr(self, 'figure') and self.figure:
                if is_dark_theme:
                    self.figure.patch.set_facecolor('#2c2c2c')
                else:
                    self.figure.patch.set_facecolor('white')
                self.canvas.draw()
        except Exception as e:
            print(f"⚠️ 차트 테마 적용 실패: {e}")
    
    def showEvent(self, event):
        """화면 표시 시 스타일 재적용"""
        super().showEvent(event)
        # 화면이 표시될 때마다 스타일 상속 보장
        QTimer.singleShot(100, self.ensure_style_inheritance)
    
    def init_ui(self):
        """UI 초기화 - 3x2 그리드 레이아웃"""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(5, 5, 5, 5)  # 마진 늘리기
        main_layout.setSpacing(5)  # 간격 늘리기
        
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
        
        # 그리드 비율 설정 - 조건 빌더 폭을 15% 증가 (2:3:2 → 23:27:20)
        grid_layout.setColumnStretch(0, 25)  # 조건 빌더 (15% 증가)
        grid_layout.setColumnStretch(1, 25)  # 트리거 관리 (조정)
        grid_layout.setColumnStretch(2, 20)  # 시뮬레이션 (유지)
        
        # 행 비율 설정 - 트리거 리스트와 상세 정보를 1:1 비율로 조정
        grid_layout.setRowStretch(0, 1)  # 상단 (트리거 리스트)
        grid_layout.setRowStretch(1, 1)  # 하단 (상세 정보) - 동일한 비율
        
        main_layout.addWidget(grid_widget)
        
        # 기본 상태 메시지 설정
        if hasattr(self, 'simulation_status'):
            self.simulation_status.setText("Status: 트리거를 선택하고 추세 버튼을 누르세요.")
        
        print("✅ 트리거 빌더 UI 초기화 완료")
    
    def create_header(self, layout):
        """헤더 영역 생성"""
        header_layout = QHBoxLayout()
        
        # 타이틀
        title_label = QLabel("🎯 트리거 빌더 v2.0 (완전 리팩토링)")
        title_label.setObjectName("titleLabel")  # CSS 선택자용 이름 설정
        header_layout.addWidget(title_label)
        
        # 상태 표시
        status_label = QLabel("✅ 시스템 준비됨")
        status_label.setObjectName("statusLabel")  # CSS 선택자용 이름 설정
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
            self.condition_dialog.setMaximumWidth(480)  # 최대 너비를 400에서 480으로 증가
            layout.addWidget(self.condition_dialog)
            print("✅ 조건 빌더 다이얼로그 생성 성공")
        except Exception as e:
            print(f"⚠️ 조건 빌더 다이얼로그 생성 실패: {e}")
            # 폴백: 간단한 인터페이스
            fallback_widget = self.create_condition_builder_fallback()
            layout.addWidget(fallback_widget)
        
        group.setLayout(layout)
        group.setMaximumWidth(500)  # 조건 빌더 영역 최대 너비를 450에서 500으로 증가
        return group
    
    def create_condition_builder_fallback(self):
        """조건 빌더 폴백 위젯"""
        fallback_widget = QWidget()
        fallback_layout = QVBoxLayout(fallback_widget)
        
        # 상태 표시
        status_label = QLabel("🔧 조건 빌더 로딩 중...")
        status_label.setObjectName("conditionBuilderFallback")  # CSS 선택자용 이름 설정
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
        """2: 등록된 트리거 리스트 영역 - Components 전용"""
        trigger_list_widget = TriggerListWidget(self)
        
        # 인스턴스 변수로 저장
        self.trigger_list_widget = trigger_list_widget
        
        # 시그널 연결
        trigger_list_widget.trigger_selected.connect(self.on_trigger_selected)
        trigger_list_widget.trigger_edited.connect(self.edit_trigger)
        trigger_list_widget.trigger_deleted.connect(self.delete_trigger)
        trigger_list_widget.trigger_copied.connect(self.copy_trigger)
        trigger_list_widget.trigger_save_requested.connect(self.save_current_condition)
        trigger_list_widget.edit_mode_changed.connect(self.on_edit_mode_changed)
        
        # 기존 위젯 참조 유지 (호환성)
        self.trigger_tree = trigger_list_widget.trigger_tree
        self.save_btn = trigger_list_widget.save_btn
        self.edit_btn = trigger_list_widget.edit_btn
        self.cancel_edit_btn = trigger_list_widget.cancel_edit_btn
        
        return trigger_list_widget
    def create_simulation_area(self):
        """3: 케이스 시뮬레이션 버튼들 영역 - Components 전용"""
        simulation_control_widget = SimulationControlWidget(self)
        
        # 시그널 연결
        simulation_control_widget.simulation_requested.connect(self.run_simulation)
        simulation_control_widget.data_source_changed.connect(self.on_data_source_changed)
        
        # 기존 위젯 참조 유지 (호환성)
        self.simulation_status = simulation_control_widget.simulation_status
        
        return simulation_control_widget
    
    def create_trigger_detail_area(self):
        """5: 선택한 트리거 상세 정보 영역 - Components 전용"""
        trigger_detail_widget = TriggerDetailWidget(self)
        
        # 기존 위젯 참조 유지 (호환성)
        self.detail_text = trigger_detail_widget.detail_text
        
        return trigger_detail_widget

    def create_test_result_area(self):
        """6: 작동 마커 차트 + 작동 기록 영역 - Components 전용"""
        simulation_result_widget = SimulationResultWidget(self)
        
        # 인스턴스 변수로 저장
        self.simulation_result_widget = simulation_result_widget
        
        # 기존 위젯 참조 유지 (호환성)
        self.test_history_list = simulation_result_widget.test_history_list
        
        # 차트 참조 연결
        if hasattr(simulation_result_widget, 'figure'):
            self.figure = simulation_result_widget.figure
            self.canvas = simulation_result_widget.canvas
        
        return simulation_result_widget

    def load_trigger_list(self):
        """트리거 목록 로드 - TriggerListWidget 완전 위임"""
        try:
            if hasattr(self, 'trigger_list_widget'):
                self.trigger_list_widget.load_trigger_list()
                print("✅ TriggerListWidget을 통한 트리거 목록 로드 완료")
            else:
                print("⚠️ TriggerListWidget을 찾을 수 없습니다")
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
        """트리거 삭제 완료 시그널 처리 - TriggerListWidget에서 이미 삭제 완료"""
        try:
            print("� 메인 화면에서 삭제 완료 시그널 수신 - UI 업데이트만 처리")
            
            # 트리거 목록 새로고침 (TriggerListWidget에서 이미 처리했지만 안전을 위해)
            self.load_trigger_list()
            
            # 상세 정보 초기화
            self.detail_text.setPlainText("트리거를 선택하면 상세정보가 표시됩니다.")
            self.selected_condition = None
            
            print("✅ 메인 화면 UI 업데이트 완료")
                        
        except Exception as e:
            print(f"❌ 메인 화면 삭제 시그널 처리 실패: {e}")
            # 실패해도 UI는 계속 동작해야 함
    
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
            self.simulation_status.setText("Status: 트리거를 선택해 주세요.")
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
        self.simulation_status.setText(f"Status: 🧮 계산 중 - {scenario} 시나리오...")
        
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
        
        # 트리거 포인트 기반으로 최종 결과 재계산 (차트의 신호와 일치시킴)
        if len(trigger_points) > 0:
            final_result = True
            final_result_text = "✅ PASS"
            final_status_text = "조건 충족"
        else:
            final_result = False
            final_result_text = "❌ FAIL"
            final_status_text = "조건 불충족"
        
        # 상태 업데이트 (트리거 신호 개수 기반)
        if len(trigger_points) > 0:
            self.simulation_status.setText(f"Status: ✅ PASS - 조건 충족, 신호: {len(trigger_points)}개")
        else:
            self.simulation_status.setText("Status: ❌ FAIL - 조건 충족 없음")
        
        # 테스트 기록에 상세 정보 추가 (신호 개수 기반으로 수정)
        detail_info = f"{final_result_text} {scenario} - {condition_name} ({final_status_text}, {len(trigger_points)}신호)"
        self.add_test_history_item(detail_info, "test")
        
        # SimulationResultWidget에서 개별 트리거 신호들을 처리하도록 위임
        if hasattr(self, 'simulation_result_widget'):
            # 시뮬레이션 데이터와 트리거 포인트를 위젯에 전달
            simulation_result_data = {
                'scenario': scenario,
                'price_data': simulation_data.get('price_data', []),
                'trigger_points': trigger_points,
                'result_text': final_result_text,
                'condition_name': condition_name
            }
            # SimulationResultWidget의 메서드 호출
            if hasattr(self.simulation_result_widget, 'update_trigger_signals'):
                self.simulation_result_widget.update_trigger_signals(simulation_result_data)
        
        # 시그널 발생 (트리거 개수 기반 결과 사용)
        self.condition_tested.emit(self.selected_condition, final_result)
        
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
        
        type_icons = {
            "ready": "🟢",
            "save": "💾",
            "test": "🧪",
            "error": "❌"
        }
        
        icon = type_icons.get(item_type, "ℹ️")
        
        # 트리거 발동 메시지의 경우 이미 인덱스가 포함되어 있으므로 시간 제거
        if "트리거 발동" in text and "[" in text:
            full_text = f"{icon} {text}"
        else:
            # 일반 메시지는 시간 포함
            timestamp = datetime.now().strftime("%H:%M:%S")
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
            
            # matplotlib 한글 폰트 전역 설정 (차트 시작 전에 먼저 설정)
            import matplotlib.pyplot as plt
            import matplotlib.font_manager as fm
            
            # 사용 가능한 한글 폰트 찾기 및 설정
            korean_fonts = ['Malgun Gothic', 'NanumGothic', 'Gulim', 'Dotum']
            font_set = False
            
            for font_name in korean_fonts:
                if font_name in [f.name for f in fm.fontManager.ttflist]:
                    plt.rcParams['font.family'] = font_name
                    plt.rcParams['axes.unicode_minus'] = False
                    print(f"✅ 전역 한글 폰트 설정: {font_name}")
                    font_set = True
                    break
            
            if not font_set:
                print("⚠️ 한글 폰트를 찾을 수 없습니다")
            
            # 폰트 캐시 새로고침
            try:
                fm._rebuild()
                print("✅ 폰트 캐시 새로고침 완료")
            except:
                pass
            
            self.figure.clear()
            ax = self.figure.add_subplot(111)
            
            # 시뮬레이션 결과가 있으면 실제 시뮬레이션 데이터 사용
            if simulation_result and 'price_data' in simulation_result:
                price_data = simulation_result['price_data']
                trigger_points = simulation_result.get('trigger_points', [])
                target_value = simulation_result.get('target_value', 0)
                
                if price_data and len(price_data) > 0:
                    # X축 (시간/인덱스)
                    x_values = range(len(price_data))
                    
                    # 가격 라인 플롯
                    ax.plot(x_values, price_data, 'b-', linewidth=2,
                           label='Price', alpha=0.8)
                    
                    # 목표 가격 라인 표시 - 포인트 배열로 변경 (향후 외부 변수 대응)
                    if target_value > 0:
                        target_data = [target_value] * len(price_data)  # 고정값일 때는 동일한 값으로 배열 생성
                        ax.plot(x_values, target_data, color='orange', linestyle='--',
                               linewidth=1, label='Target', alpha=0.7)
                    
                    # 트리거 포인트 표시
                    if trigger_points and len(trigger_points) > 0:
                        for i, point_idx in enumerate(trigger_points):
                            if 0 <= point_idx < len(price_data):
                                ax.scatter(point_idx, price_data[point_idx], 
                                         c='red', s=50, marker='^', 
                                         label='Trigger' if i == 0 else "",
                                         zorder=5, alpha=0.8)
                    
                    # 차트 스타일링 - 한글 폰트 명시적 적용
                    import matplotlib.font_manager as fm
                    import matplotlib.pyplot as plt
                    
                    # 한글 폰트 직접 로드 및 전역 설정
                    korean_font = None
                    available_fonts = ['Malgun Gothic', 'NanumGothic', 'Gulim', 'Dotum']
                    
                    for font_name in available_fonts:
                        try:
                            # 시스템에 폰트가 있는지 확인
                            if font_name in [f.name for f in fm.fontManager.ttflist]:
                                korean_font = fm.FontProperties(family=font_name)
                                # matplotlib 전역 설정도 함께 변경
                                plt.rcParams['font.family'] = font_name
                                plt.rcParams['axes.unicode_minus'] = False
                                print(f"✅ 한글 폰트 설정 완료: {font_name}")
                                break
                        except Exception as e:
                            print(f"⚠️ {font_name} 폰트 로드 실패: {e}")
                            continue
                    
                    # 폰트를 찾지 못한 경우 기본 폰트 사용
                    if korean_font is None:
                        korean_font = fm.FontProperties()
                        print("⚠️ 한글 폰트를 찾을 수 없어 기본 폰트 사용")
                    
                    # 차트 제목과 축 레이블 제거 (더 큰 차트 공간 확보)
                    # ax.set_title() - 제목 제거
                    # ax.set_xlabel() - X축 라벨 제거
                    # ax.set_ylabel() - Y축 라벨 제거
                    ax.grid(True, alpha=0.3)
                    
                    # 범례에도 한글 폰트 적용
                    legend = ax.legend(loc='upper left', fontsize=8)
                    if legend:
                        for text in legend.get_texts():
                            text.set_fontproperties(korean_font)
                    
                    # Y축 틱 라벨 포맷팅 (3자 이내)
                    def format_y_tick(value, pos):
                        if value >= 1000000:
                            return f"{value / 1000000:.1f}m"
                        elif value >= 1000:
                            return f"{value / 1000:.0f}k"
                        elif value >= 1:
                            return f"{value:.0f}"
                        else:
                            return f"{value:.1f}"
                    
                    from matplotlib.ticker import FuncFormatter
                    ax.yaxis.set_major_formatter(FuncFormatter(format_y_tick))
                    ax.tick_params(axis='y', which='major', labelsize=6)
                    
                    # X축 틱 라벨 포맷팅 (데이터 인덱스 표시)
                    ax.tick_params(axis='x', which='major', labelsize=6)
                    # X축에 몇 개의 틱만 표시 (너무 많으면 겹침)
                    x_tick_positions = range(0, len(price_data), max(1, len(price_data) // 5))
                    ax.set_xticks(x_tick_positions)
                    ax.set_xticklabels([str(i) for i in x_tick_positions])
                    
                    msg = (f"📈 차트 업데이트 완료: {scenario_name}, "
                           f"{len(price_data)}개 데이터포인트, "
                           f"{len(trigger_points) if trigger_points else 0}개 트리거")
                    print(msg)
                    
                else:
                    # 데이터가 없을 때 플레이스홀더
                    ax.text(0.5, 0.5, 'No simulation data',
                            transform=ax.transAxes, ha='center', va='center',
                            fontsize=12, alpha=0.5)
                    ax.set_title('Simulation Result', fontsize=12)
            
            else:
                # 기본 플레이스홀더 차트 - 시나리오명 영어 변환
                scenario_eng = {
                    '상승 추세': 'Bull Market',
                    '하락 추세': 'Bear Market',
                    '횡보': 'Sideways',
                    '급등': 'Surge',
                    '급락': 'Crash'
                }.get(scenario_name, scenario_name)
                
                ax.text(0.5, 0.5, f'{scenario_eng} Scenario\nChart loading...',
                        transform=ax.transAxes, ha='center', va='center',
                        fontsize=12, alpha=0.6)
                # ax.set_title(f'{scenario_eng} Chart', fontsize=12)  # 제목 제거
            
            # 차트 여백 조정 및 다시 그리기
            self.figure.tight_layout(pad=1.0)
            self.canvas.draw()
                
        except Exception as e:
            print(f"❌ 차트 업데이트 중 오류 발생: {e}")
            traceback.print_exc()
            
            # 에러 시 플레이스홀더 표시
            try:
                self.figure.clear()
                ax = self.figure.add_subplot(111)
                ax.text(0.5, 0.5, f'Chart Error\n{str(e)}',
                        transform=ax.transAxes, ha='center', va='center',
                        fontsize=10, alpha=0.5)
                self.figure.tight_layout(pad=1.0)
                self.canvas.draw()
            except Exception:
                pass
    
    def _create_fallback_chart(self, ax, scenario_name):
        """폴백 차트 생성"""
        
        # 기본 가격 패턴 생성
        x_values = list(range(30))
        base_price = 50000000  # 5천만원 기준
        
        # 시나리오명 영어 변환
        scenario_eng = {
            '상승 추세': 'Bull Market',
            '하락 추세': 'Bear Market',
            '횡보': 'Sideways',
            '급등': 'Surge',
            '급락': 'Crash'
        }.get(scenario_name, scenario_name)
        
        if "Bull" in scenario_eng or "Surge" in scenario_eng or "상승" in scenario_name:
            prices = [base_price + i * 1000000 + random.uniform(-500000, 500000) for i in x_values]
        elif "Bear" in scenario_eng or "Crash" in scenario_eng or "하락" in scenario_name:
            prices = [base_price - i * 800000 + random.uniform(-500000, 500000) for i in x_values]
        else:  # Sideways 등
            prices = [base_price + random.uniform(-2000000, 2000000) for _ in x_values]
        
        ax.plot(x_values, prices, 'b-', linewidth=1.5, label='Price')
        
        # 랜덤 트리거 포인트
        trigger_points = random.sample(range(5, 25), random.randint(2, 4))
        for point in trigger_points:
            ax.scatter(point, prices[point], c='red', s=30, marker='^', zorder=5)
            
        # ax.set_title(f'{scenario_eng} (Simulation)', fontsize=10)  # 제목 제거
    
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
                # 차트 생성 실패 시 간단한 라벨만 표시
                chart_label = QLabel("📈 차트 생성 실패\n(matplotlib 필요)")
                chart_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
                chart_label.setStyleSheet("""
                    border: 2px dashed #ccc;
                    border-radius: 8px;
                    padding: 20px;
                    color: #666;
                    min-height: 100px;
                """)
                layout.addWidget(chart_label)
        else:
            # matplotlib이 없을 경우 간단한 라벨만 표시
            chart_label = QLabel("📈 차트 로딩 실패\n(matplotlib 필요)")
            chart_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            chart_label.setStyleSheet("""
                border: 2px dashed #ccc;
                border-radius: 8px;
                padding: 20px;
                color: #666;
                min-height: 100px;
            """)
            layout.addWidget(chart_label)
    
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
                ax.plot(x_values, price_data, 'b-', linewidth=2, label='Price', alpha=0.8)
                
                # 목표 가격 라인 표시 - 포인트 배열로 변경 (향후 외부 변수 대응)
                if target_value > 0:
                    target_data = [target_value] * len(price_data)  # 고정값일 때는 동일한 값으로 배열 생성
                    ax.plot(x_values, target_data, color='orange', linestyle='--', linewidth=1,
                           label='Target', alpha=0.7)
                
                # 트리거 포인트 표시
                if trigger_points and len(trigger_points) > 0:
                    for point_idx in trigger_points:
                        if 0 <= point_idx < len(price_data):
                            ax.scatter(point_idx, price_data[point_idx], 
                                     c='red', s=50, marker='^', 
                                     label='트리거 발동' if point_idx == trigger_points[0] else "",
                                     zorder=5, alpha=0.8)
                
                # 차트 스타일링
                # 차트 제목 제거하여 더 큰 차트 공간 확보  
                # ax.set_title(f'🎯 {scenario} 시뮬레이션 결과', fontsize=12, fontweight='bold', pad=20)
                ax.set_xlabel('시간 (일)', fontsize=10)
                ax.set_ylabel('가격 (원)', fontsize=10)
                ax.grid(True, alpha=0.3)
                ax.legend(loc='upper left', fontsize=8)
                
                # Y축 포맷팅 (3자 이내)
                def format_y_tick(value, pos):
                    if value >= 1000000:
                        return f"{value / 1000000:.1f}m"
                    elif value >= 1000:
                        return f"{value / 1000:.0f}k"
                    elif value >= 1:
                        return f"{value:.0f}"
                    else:
                        return f"{value:.1f}"
                
                from matplotlib.ticker import FuncFormatter
                ax.yaxis.set_major_formatter(FuncFormatter(format_y_tick))
                
                # X축 틱 라벨 포맷팅 (데이터 인덱스 표시)
                x_tick_positions = range(0, len(price_data), max(1, len(price_data) // 5))
                ax.set_xticks(x_tick_positions)
                ax.set_xticklabels([str(i) for i in x_tick_positions])
                
                # 차트 여백 조정
                self.figure.tight_layout(pad=1.0)
                
                # 차트 다시 그리기
                self.canvas.draw()
                
                print(f"📈 차트 업데이트 완료: {scenario}, {len(price_data)}개 데이터포인트, {len(trigger_points) if trigger_points else 0}개 트리거")
                
            else:
                # 데이터가 없을 때 플레이스홀더
                ax.text(0.5, 0.5, 'No simulation data',
                       transform=ax.transAxes, ha='center', va='center',
                       fontsize=12, alpha=0.5)
                # ax.set_title('Simulation Result', fontsize=12)  # 제목 제거
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
