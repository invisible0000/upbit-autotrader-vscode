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
from upbit_auto_trading.utils.debug_logger import get_logger

# matplotlib 관련 import (차트용)
try:
    import numpy as np
    import pandas as pd
    import traceback
    import random
    ADDITIONAL_LIBS_AVAILABLE = True
except ImportError:
    ADDITIONAL_LIBS_AVAILABLE = False

# TriggerBuilder Core Components import
from .components.core.condition_dialog import ConditionDialog
from .components.core.trigger_list_widget import TriggerListWidget
from .components.core.trigger_detail_widget import TriggerDetailWidget

# Shared Simulation Components import (NEW)
from ..shared_simulation.charts.simulation_control_widget import SimulationControlWidget
from ..shared_simulation.charts.simulation_result_widget import SimulationResultWidget
from ..shared_simulation.charts.chart_visualizer import ChartVisualizer
from .components.shared.trigger_calculator import TriggerCalculator

# Chart variable system import
try:
    # chart_variable_service moved to _legacy
    # from .components.shared.chart_variable_service import get_chart_variable_service
    from .components.shared.variable_display_system import get_variable_registry
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
    else:
        plt.rcParams['axes.unicode_minus'] = False
except ImportError:
    pass  # matplotlib 없으면 건너뛰기
except Exception:
    pass  # 폰트 설정 실패해도 건너뛰기

# ConditionStorage import - 정확한 경로 사용
from .components.core.condition_storage import ConditionStorage
# Note: ConditionLoader was unused and moved to legacy

# DataSourceSelectorWidget - shared_simulation에서 임포트
from ..shared_simulation.data_sources.data_source_selector import DataSourceSelectorWidget

# 기존 UI 컴포넌트 임포트 - 폴백 제거, 정확한 경로 필요
from upbit_auto_trading.ui.desktop.common.components import (
    CardWidget, StyledTableWidget, PrimaryButton, SecondaryButton,
    StyledLineEdit, StyledComboBox
)

class TriggerBuilderScreen(QWidget):
    """트리거 빌더 메인 화면 - 기존 기능 완전 복원"""
    
    # 시그널 정의
    condition_tested = pyqtSignal(dict, bool)  # 조건, 테스트 결과
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("🎯 트리거 빌더 v2.0 (완전 리팩토링)")
        self.logger = get_logger("TriggerBuilder")
        
        # 메인 윈도우에 맞춘 최소 크기 설정 (1280x720) - 반응형
        self.setMinimumSize(1280, 720)
        self.resize(1600, 1000)  # 초기 크기 설정
        
        # 기존 컴포넌트 초기화
        self.storage = ConditionStorage()
        # Note: ConditionLoader was unused and removed
        self.selected_condition = None
        
        # 새로운 컴포넌트 초기화
        self.chart_visualizer = ChartVisualizer()
        self.trigger_calculator = TriggerCalculator()
        
        # 시뮬레이션 엔진 초기화 (NEW shared_simulation)
        from ..shared_simulation.engines.simulation_engines import get_embedded_engine
        self.simulation_engine = get_embedded_engine()
        
        # 차트 변수 카테고리 시스템 초기화
        if CHART_VARIABLE_SYSTEM_AVAILABLE:
            try:
                # chart_variable_service moved to _legacy, only use variable_registry
                # self.chart_variable_service = get_chart_variable_service()
                self.chart_variable_service = None  # Legacy service disabled
                self.variable_registry = get_variable_registry()
                self.logger.debug("차트 변수 시스템 로드 완료 (레거시 서비스 비활성화)")
            except Exception as e:
                self.logger.warning(f"차트 변수 시스템 초기화 실패: {e}")
                self.chart_variable_service = None
                self.variable_registry = None
        else:
            self.chart_variable_service = None
            self.variable_registry = None
        
        self.init_ui()
        self.load_trigger_list()
        
        # 메인 애플리케이션의 스타일을 상속받음 (부모에서 적용된 스타일 재적용)
        self.ensure_style_inheritance()
        self.logger.debug("트리거 빌더 초기화 완료")
    
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
                    
                    self.logger.debug(f"애플리케이션 스타일 상속 완료 (다크 테마: {is_dark_theme})")
                else:
                    self.logger.warning("애플리케이션에 적용된 스타일시트가 없습니다")
            else:
                self.logger.warning("QApplication 인스턴스를 찾을 수 없습니다")
        except Exception as e:
            self.logger.warning(f"스타일 상속 설정 실패: {e}")
    
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
            self.logger.warning(f"차트 테마 적용 실패: {e}")
    
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
        self.simulation_area.setMinimumWidth(300)
        grid_layout.addWidget(self.simulation_area, 0, 2, 1, 1)
        
        # 5: 선택한 트리거 상세 정보 (중앙 하단)
        self.trigger_detail_area = self.create_trigger_detail_area()
        grid_layout.addWidget(self.trigger_detail_area, 1, 1, 1, 1)
        
        # 6: 작동 마커 차트 + 작동 기록 (우측 하단)
        self.test_result_area = self.create_test_result_area()
        self.test_result_area.setMinimumWidth(300)
        grid_layout.addWidget(self.test_result_area, 1, 2, 1, 1)
        
        # 그리드 비율 설정 (35:40:25) - 트리거 관리 영역을 더 크게
        grid_layout.setColumnStretch(0, 35)  # 조건 빌더 (40→35)
        grid_layout.setColumnStretch(1, 35)  # 트리거 관리 (35→40)
        grid_layout.setColumnStretch(2, 30)  # 시뮬레이션 (30→25)

        # 행 비율 설정
        grid_layout.setRowStretch(0, 1)  # 상단
        grid_layout.setRowStretch(1, 1)  # 하단
        
        main_layout.addWidget(grid_widget)
        
        # 기본 상태 메시지 설정
        if hasattr(self, 'simulation_status'):
            self.simulation_status.setText("Status: 트리거를 선택하고 추세 버튼을 누르세요.")
        
        self.logger.debug("트리거 빌더 UI 초기화 완료")
    
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
        
        # 조건 빌더 다이얼로그를 임베디드 형태로 포함 - 폴백 제거
        self.condition_dialog = ConditionDialog()
        layout.addWidget(self.condition_dialog)
        self.logger.debug("조건 빌더 다이얼로그 생성 성공")
        
        # 조건 저장 시그널 연결 - 트리거 리스트 새로고침을 위해 필수
        if hasattr(self.condition_dialog, 'condition_saved'):
            self.condition_dialog.condition_saved.connect(self.on_condition_saved)
            self.logger.debug("조건 저장 시그널 연결 완료")
        
        group.setLayout(layout)
        group.setMinimumWidth(400)  # 최소 너비 증가 (300→400)
        return group
    
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
        
        # 위젯 참조 저장
        self.trigger_detail_widget = trigger_detail_widget
        
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
        """트리거 상세정보 업데이트 - 위젯 메소드 호출, 폴백 제거"""
        # 트리거 디테일 위젯의 메소드 호출 - 실패시 에러 발생
        self.trigger_detail_widget.update_trigger_detail(condition)
    
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
    
    def on_condition_saved(self, condition_data):
        """조건 저장 완료 시그널 처리 - 트리거 리스트 새로고침"""
        try:
            print(f"✅ 조건 저장 시그널 수신: {condition_data.get('name', 'Unknown')}")
            # 트리거 리스트 새로고침
            self.load_trigger_list()
            print("✅ 트리거 리스트 새로고침 완료")
        except Exception as e:
            print(f"❌ 조건 저장 시그널 처리 실패: {e}")
    
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
        """시뮬레이션 실행 - 실제 트리거 계산 로직 사용 (NEW)"""
        if not self.selected_condition:
            self.simulation_status.setText("Status: 트리거를 선택해 주세요.")
            print("⚠️ 트리거를 선택하세요.")
            return
        
        try:
            print(f"🚀 실제 트리거 시뮬레이션 시작: {scenario}")
            
            # 실제 트리거 시뮬레이션 서비스 사용 (NEW)
            from .components.shared.trigger_simulation_service import (
                TriggerSimulationService, TriggerSimulationRequest
            )
            
            # 시뮬레이션 요청 생성
            request = TriggerSimulationRequest(
                condition=self.selected_condition,
                scenario=scenario,
                data_source="real_db",
                data_limit=100  # 100개 데이터 포인트
            )
            
            # 시뮬레이션 실행
            simulation_service = TriggerSimulationService()
            result = simulation_service.run_simulation(request)
            
            # 결과 처리
            self._process_simulation_result(result, scenario)
            
        except Exception as e:
            # 폴백 제거 - 에러가 발생하면 명확히 표시
            print(f"❌ 시뮬레이션 실행 완전 실패: {e}")
            import traceback
            traceback.print_exc()
            
            # 사용자에게 명확한 에러 표시
            self.simulation_status.setText(f"Status: ❌ 시뮬레이션 실패 - {str(e)}")
            
            # 차트에 에러 메시지 표시 (클리어하지 않고)
            if hasattr(self, 'simulation_result_widget'):
                self.simulation_result_widget.test_history_list.clear()
                # 에러 메시지 추가
                self.add_test_history_item(f"❌ 시뮬레이션 실패: {str(e)}", "error")
                
                # 차트에 에러 표시 (클리어 대신)
                if hasattr(self.simulation_result_widget, 'figure'):
                    self.simulation_result_widget.figure.clear()
                    ax = self.simulation_result_widget.figure.add_subplot(111)
                    ax.text(0.5, 0.5, f"❌ 시뮬레이션 실패\n\n{str(e)[:100]}...", 
                           horizontalalignment='center', verticalalignment='center',
                           transform=ax.transAxes, fontsize=12, color='red',
                           bbox=dict(boxstyle="round,pad=0.3", facecolor="white", edgecolor="red"))
                    ax.set_xticks([])
                    ax.set_yticks([])
                    self.simulation_result_widget.canvas.draw()
            
            # 에러를 다시 발생시켜 디버깅 가능하도록
            raise
    
    def _process_simulation_result(self, result, scenario):
        """시뮬레이션 결과 처리 - 깔끔한 분리 (NEW dict 지원)"""
        # Dict 형태 결과 처리
        if isinstance(result, dict):
            if not result.get('success', False):
                error_msg = result.get('error', '알 수 없는 오류')
                self.simulation_status.setText(f"Status: ❌ {error_msg}")
                return
            
            # 상태 업데이트 (dict 형태)
            records = result.get('records', 0)
            engine_name = result.get('engine', 'Unknown')
            status_text = "✅ PASS" if records > 0 else "❌ FAIL"
            self.simulation_status.setText(
                f"Status: {status_text} - {scenario} 시나리오, 엔진: {engine_name}, 데이터: {records}개"
            )
            
            # Dict 형태 결과 처리 - 실제 시뮬레이션 데이터만 사용, 폴백 제거
            price_data = result.get('price_data', [])
            trigger_points = result.get('trigger_points', [])
            
            # 데이터가 없으면 에러 발생 (폴백 제거)
            if not price_data:
                raise ValueError(f"시뮬레이션 결과에 price_data가 없습니다: {result}")
            
            # 실제 외부 변수 데이터만 사용
            external_data = result.get('external_variable_data')
            base_variable_data = result.get('base_variable_data')
            
            # 트리거 포인트가 없으면 실제 계산
            if not trigger_points and base_variable_data and external_data:
                # 교차 지점 찾기 (SMA_20 > SMA_60)
                for i in range(1, min(len(base_variable_data), len(external_data))):
                    prev_base = base_variable_data[i-1]
                    curr_base = base_variable_data[i]
                    prev_ext = external_data[i-1]
                    curr_ext = external_data[i]
                    
                    if prev_base <= prev_ext and curr_base > curr_ext:  # 골든 크로스
                        trigger_points.append(i)
            
            if hasattr(self, 'simulation_result_widget'):
                chart_data = {
                    'scenario': scenario,
                    'price_data': price_data,
                    'base_variable_data': base_variable_data,
                    'external_variable_data': external_data,
                    'current_value': price_data[-1] if price_data else 93000000,
                    'target_value': external_data[-1] if external_data else 93000000,
                    'variable_info': {'variable_name': self.selected_condition.get('variable_name', 'SMA_20') if self.selected_condition else 'SMA_20'},
                    'external_variable_info': {'variable_name': self.selected_condition.get('external_variable', {}).get('variable_name', 'SMA_60') if self.selected_condition else 'SMA_60'},
                    'condition_name': self.selected_condition.get('name', 'Unknown') if self.selected_condition else 'Unknown'
                }
                
                trigger_results = {
                    'trigger_points': trigger_points,
                    'trigger_activated': len(trigger_points) > 0,
                    'total_signals': len(trigger_points)
                }
                
                self.simulation_result_widget.update_chart_with_simulation_results(chart_data, trigger_results)
            
            # 로그 추가 (dict 형태도 지원)
            result_text = f"{scenario} 시뮬레이션 - {status_text}, {records}개 데이터"
            self.add_test_history_item(result_text, "test")
            
            # 시그널 발생 (dict 형태도 지원)
            self.condition_tested.emit(self.selected_condition or {}, records > 0)
            
            print(f"✅ Dict 형태 시뮬레이션 완료: {result_text}")
            return
            
        # 기존 객체 형태 결과 처리
        if not result.success:
            self.simulation_status.setText(f"Status: ❌ {result.error_message}")
            return
        
        # 상태 업데이트
        trigger_count = len(result.trigger_points)
        status_text = "✅ PASS" if trigger_count > 0 else "❌ FAIL"
        self.simulation_status.setText(
            f"Status: {status_text} - {result.condition_name}, 신호: {trigger_count}개"
        )
        
        # 차트 업데이트 - 실제 시뮬레이션 데이터 사용, 폴백 제거
        if hasattr(self, 'simulation_result_widget') and self.simulation_result_widget:
            # 트리거 결과를 (triggered, _) 형태로 변환
            trigger_results_paired = [(point in result.trigger_points, 0) for point in range(len(result.price_data))]
            
            # 올바른 메서드 호출 - update_simulation_chart 사용, 폴백 제거
            self.simulation_result_widget.update_simulation_chart(
                result.scenario,                      # scenario
                result.price_data,                    # price_data
                trigger_results_paired,               # trigger_results
                result.base_variable_data,            # base_variable_data
                result.external_variable_data,        # external_variable_data
                result.variable_info,                 # variable_info
                result.target_value                   # comparison_value
            )
            
            print(f"✅ 시뮬레이션 차트 업데이트 완료: {result.scenario}")
        
        # 로그 추가
        self.add_test_history_item(result.result_text, "test")
        
        # 시그널 발생
        self.condition_tested.emit(self.selected_condition, trigger_count > 0)
        
        print(f"✅ 시뮬레이션 완료: {result.result_text}")
    
    
    def _get_variable_chart_info(self, variable_name):
        """차트 변수 카테고리 시스템을 통한 변수 정보 가져오기 - 올바른 ID 매핑"""
        if not variable_name:
            return {}
            
        try:
            # 먼저 이모지 포함 UI 텍스트를 실제 변수 ID로 변환
            actual_variable_id = self._map_ui_text_to_variable_id(variable_name)
            
            if hasattr(self, 'variable_registry') and self.variable_registry:
                # variable_registry를 통한 변수 정보 조회로 변경
                config = self.variable_registry.get_variable_config(actual_variable_id)
                
                if config:
                    return {
                        'variable_id': config.variable_id,
                        'variable_name': config.variable_name,
                        'category': config.category,
                        'display_type': config.display_type,
                        'scale_min': config.scale_min,
                        'scale_max': config.scale_max,
                        'unit': config.unit,
                        'default_color': config.default_color
                    }
            
            # 폴백: 하드코딩된 변수 정보 (올바른 ID 사용)
            fallback_mapping = {
                'RSI': {'variable_id': 'RSI', 'category': 'oscillator', 'display_type': 'line', 'scale_min': 0, 'scale_max': 100},
                'MACD': {'variable_id': 'MACD', 'category': 'momentum', 'display_type': 'line', 'scale_min': -10, 'scale_max': 10},
                'VOLUME': {'variable_id': 'VOLUME', 'category': 'volume', 'display_type': 'histogram', 'scale_min': 0, 'scale_max': None},
                'PRICE': {'variable_id': 'PRICE', 'category': 'price_overlay', 'display_type': 'line', 'scale_min': None, 'scale_max': None},
                'SMA': {'variable_id': 'SMA', 'category': 'price_overlay', 'display_type': 'line', 'scale_min': None, 'scale_max': None},
                'EMA': {'variable_id': 'EMA', 'category': 'price_overlay', 'display_type': 'line', 'scale_min': None, 'scale_max': None},
                'BOLLINGER': {'variable_id': 'BOLLINGER', 'category': 'price_overlay', 'display_type': 'band', 'scale_min': None, 'scale_max': None},
                'STOCHASTIC': {'variable_id': 'STOCHASTIC', 'category': 'oscillator', 'display_type': 'line', 'scale_min': 0, 'scale_max': 100}
            }
            
            # 실제 변수 ID로 매핑 확인
            if actual_variable_id in fallback_mapping:
                info = fallback_mapping[actual_variable_id].copy()
                info['variable_name'] = variable_name  # UI에 표시된 이름 유지
                print(f"📊 변수 매핑: '{variable_name}' → ID: '{actual_variable_id}' → 카테고리: {info.get('category', 'unknown')}")
                return info
            
            # 기본값 반환
            print(f"⚠️ 알 수 없는 변수: '{variable_name}' → ID: '{actual_variable_id}', 기본 price_overlay 사용")
            return {
                'variable_id': actual_variable_id,
                'variable_name': variable_name,
                'category': 'price_overlay',
                'display_type': 'line',
                'scale_min': None,
                'scale_max': None
            }
            
        except Exception as e:
            print(f"⚠️ 변수 정보 가져오기 실패: {e}")
            return {
                'variable_id': variable_name.upper().replace(' ', '_'),
                'variable_name': variable_name,
                'category': 'price_overlay',
                'display_type': 'line'
            }
    
    def _map_ui_text_to_variable_id(self, ui_text):
        """UI 텍스트(이모지 포함)를 실제 변수 ID로 매핑"""
        if not ui_text:
            return ''
        
        # UI 텍스트 → 변수 ID 매핑 테이블
        ui_to_id_mapping = {
            # 이모지 포함된 UI 텍스트 → 실제 변수 ID
            '🔹 RSI 지표': 'RSI',
            '🔸 RSI 지표': 'RSI',
            '🔺 RSI 지표': 'RSI',
            'RSI 지표': 'RSI',
            'RSI': 'RSI',
            
            '🔹 MACD 지표': 'MACD',
            '🔸 MACD 지표': 'MACD', 
            '🔺 MACD 지표': 'MACD',
            'MACD 지표': 'MACD',
            'MACD': 'MACD',
            
            '🔹 단순이동평균': 'SMA',
            '🔸 단순이동평균': 'SMA',
            '🔺 단순이동평균': 'SMA',
            '단순이동평균': 'SMA',
            'SMA': 'SMA',
            
            '🔹 지수이동평균': 'EMA',
            '🔸 지수이동평균': 'EMA',
            '🔺 지수이동평균': 'EMA',
            '지수이동평균': 'EMA',
            'EMA': 'EMA',
            
            '🔹 거래량': 'VOLUME',
            '🔸 거래량': 'VOLUME',
            '🔺 거래량': 'VOLUME',
            '거래량': 'VOLUME',
            'VOLUME': 'VOLUME',
            
            '🔹 현재가': 'PRICE',
            '🔸 현재가': 'PRICE',
            '🔺 현재가': 'PRICE',
            '현재가': 'PRICE',
            'PRICE': 'PRICE',
            
            '🔹 볼린저밴드': 'BOLLINGER',
            '🔸 볼린저밴드': 'BOLLINGER',
            '🔺 볼린저밴드': 'BOLLINGER',
            '볼린저밴드': 'BOLLINGER',
            'BOLLINGER': 'BOLLINGER',
            
            '🔹 스토캐스틱': 'STOCHASTIC',
            '🔸 스토캐스틱': 'STOCHASTIC',
            '🔺 스토캐스틱': 'STOCHASTIC',
            '스토캐스틱': 'STOCHASTIC',
            'STOCHASTIC': 'STOCHASTIC'
        }
        
        # 정확한 매칭 우선
        if ui_text in ui_to_id_mapping:
            mapped_id = ui_to_id_mapping[ui_text]
            print(f"🎯 UI 텍스트 매핑: '{ui_text}' → '{mapped_id}'")
            return mapped_id
        
        # 부분 매칭 시도 (이모지 제거 후)
        clean_text = ui_text.replace('🔹 ', '').replace('🔸 ', '').replace('🔺 ', '').strip()
        if clean_text in ui_to_id_mapping:
            mapped_id = ui_to_id_mapping[clean_text]
            print(f"🎯 정리된 텍스트 매핑: '{ui_text}' → '{clean_text}' → '{mapped_id}'")
            return mapped_id
        
        # 키워드 기반 매핑
        clean_upper = clean_text.upper()
        if 'RSI' in clean_upper:
            return 'RSI'
        elif 'MACD' in clean_upper:
            return 'MACD'
        elif '단순이동평균' in clean_text or 'SMA' in clean_upper:
            return 'SMA'
        elif '지수이동평균' in clean_text or 'EMA' in clean_upper:
            return 'EMA'
        elif '거래량' in clean_text or 'VOLUME' in clean_upper:
            return 'VOLUME'
        elif '현재가' in clean_text or 'PRICE' in clean_upper:
            return 'PRICE'
        elif '볼린저' in clean_text or 'BOLLINGER' in clean_upper:
            return 'BOLLINGER'
        elif '스토캐스틱' in clean_text or 'STOCHASTIC' in clean_upper:
            return 'STOCHASTIC'
        
        # 매핑되지 않은 경우 기본 처리
        fallback_id = clean_text.upper().replace(' ', '_')
        print(f"⚠️ 매핑되지 않은 변수: '{ui_text}' → '{fallback_id}' (fallback)")
        return fallback_id
    
    def _calculate_variable_data(self, variable_name, price_data, custom_parameters=None):
        """변수명에 따라 실제 계산된 데이터 반환 - 올바른 변수 ID 기반 + 커스텀 파라미터 지원"""
        if not variable_name or not price_data:
            return None
        
        # UI 텍스트를 실제 변수 ID로 변환
        variable_id = self._map_ui_text_to_variable_id(variable_name)
        
        try:
            if variable_id == 'SMA':
                # SMA 계산 (커스텀 파라미터 우선 사용)
                period = self._extract_period_from_parameters(custom_parameters, variable_name, default=20)
                print(f"   🔹 SMA 계산: period={period} (커스텀 파라미터: {custom_parameters})")
                return self.trigger_calculator.calculate_sma(price_data, period)
            
            elif variable_id == 'EMA':
                # EMA 계산 (커스텀 파라미터 우선 사용)
                period = self._extract_period_from_parameters(custom_parameters, variable_name, default=12)
                print(f"   🔸 EMA 계산: period={period} (커스텀 파라미터: {custom_parameters})")
                return self.trigger_calculator.calculate_ema(price_data, period)
            
            elif variable_id == 'RSI':
                # RSI 계산 (커스텀 파라미터 우선 사용)
                period = self._extract_period_from_parameters(custom_parameters, variable_name, default=14)
                print(f"   🔺 RSI 계산: period={period} (커스텀 파라미터: {custom_parameters})")
                return self.trigger_calculator.calculate_rsi(price_data, period)
            
            elif variable_id == 'MACD':
                # MACD 계산 (TriggerCalculator 사용)
                return self.trigger_calculator.calculate_macd(price_data)
            
            elif variable_id == 'VOLUME':
                # 거래량 데이터는 별도 처리 필요
                return self._generate_volume_data(len(price_data))
                
            elif variable_id == 'PRICE':
                # 현재가는 가격 데이터 그대로
                return price_data
            
            else:
                # 알 수 없는 변수는 가격 데이터 그대로 반환
                print(f"⚠️ 알 수 없는 변수 ID: {variable_id} (원본: {variable_name}), 가격 데이터 사용")
                return price_data
        
        except Exception as e:
            print(f"⚠️ 변수 계산 실패 ({variable_name} → {variable_id}): {e}")
            return price_data  # 폴백으로 가격 데이터 반환
    
    def _extract_period_from_parameters(self, custom_parameters, variable_name, default):
        """커스텀 파라미터 또는 변수명에서 기간 추출"""
        # 1. 커스텀 파라미터에서 우선 추출
        if custom_parameters and isinstance(custom_parameters, dict):
            if 'period' in custom_parameters:
                period = custom_parameters['period']
                print(f"   📋 커스텀 파라미터에서 period 추출: {period}")
                return int(period)
        
        # 2. 변수명에서 추출 (폴백)
        period = self._extract_period_from_name(variable_name, default)
        print(f"   📋 변수명에서 period 추출: {period} (기본값: {default})")
        return period
    
    def _extract_period_from_name(self, variable_name, default=20):
        """변수명에서 기간 추출 (예: SMA(20) -> 20)"""
        import re
        match = re.search(r'\((\d+)\)', variable_name)
        if match:
            return int(match.group(1))
        return default
    
    def _calculate_sma(self, prices, period):
        """단순이동평균 계산 - TriggerCalculator로 위임"""
        return self.trigger_calculator.calculate_sma(prices, period)
    
    def _calculate_ema(self, prices, period):
        """지수이동평균 계산 - TriggerCalculator로 위임"""
        return self.trigger_calculator.calculate_ema(prices, period)
    
    def _calculate_rsi(self, prices, period=14):
        """RSI 계산 - TriggerCalculator로 위임"""
        return self.trigger_calculator.calculate_rsi(prices, period)
    
    def _calculate_macd(self, prices):
        """MACD 계산 - TriggerCalculator로 위임"""
        return self.trigger_calculator.calculate_macd(prices)
    
    def _generate_volume_data(self, length):
        """가상 거래량 데이터 생성"""
        import random
        base_volume = 2000000
        return [base_volume + random.randint(-500000, 1000000) for _ in range(length)]
    
    def _calculate_cross_trigger_points(self, base_data, external_data, operator):
        """두 변수간 크로스 트리거 포인트 계산 - TriggerCalculator 활용"""
        if not base_data or not external_data:
            return []
        
        trigger_points = []
        min_length = min(len(base_data), len(external_data))
        
        for i in range(1, min_length):  # 이전값과 비교하므로 1부터 시작
            prev_base = base_data[i-1]
            curr_base = base_data[i]
            prev_external = external_data[i-1]
            curr_external = external_data[i]
            
            # 크로스 감지
            if operator == '>':
                # 골든 크로스: 기본 변수가 외부 변수를 위로 돌파
                if prev_base <= prev_external and curr_base > curr_external:
                    trigger_points.append(i)
            elif operator == '<':
                # 데드 크로스: 기본 변수가 외부 변수를 아래로 돌파
                if prev_base >= prev_external and curr_base < curr_external:
                    trigger_points.append(i)
            elif operator == '>=':
                if prev_base < prev_external and curr_base >= curr_external:
                    trigger_points.append(i)
            elif operator == '<=':
                if prev_base > prev_external and curr_base <= curr_external:
                    trigger_points.append(i)
        
        return trigger_points
    
    def generate_oscillator_data_for_chart(self, scenario, length=50, scale_min=0, scale_max=100):
        """오실레이터 데이터 생성 (RSI, 스토캐스틱 등)"""
        try:
            # 시뮬레이션 엔진 사용
            market_data = self.simulation_engine.load_market_data(length)
            if market_data is not None and 'rsi' in market_data.columns:
                # 실제 RSI 데이터가 있으면 사용
                rsi_data = market_data['rsi'].tolist()
                # 스케일 조정
                if scale_min != 0 or scale_max != 100:
                    adjusted_data = []
                    for value in rsi_data:
                        # 0-100을 scale_min-scale_max로 변환
                        adjusted_value = scale_min + (value / 100.0) * (scale_max - scale_min)
                        adjusted_data.append(adjusted_value)
                    return adjusted_data
                return rsi_data
        except Exception as e:
            print(f"⚠️ 실제 오실레이터 데이터 로드 실패: {e}")
        
        # 폴백: 가상 데이터 생성
        import random
        data = []
        mid_value = (scale_min + scale_max) / 2
        range_size = scale_max - scale_min
        
        for i in range(length):
            # 시나리오별 경향성 반영
            if scenario in ['상승 추세', '급등']:
                base_value = mid_value + random.uniform(0.1, 0.4) * range_size
            elif scenario in ['하락 추세', '급락']:
                base_value = mid_value - random.uniform(0.1, 0.4) * range_size
            else:  # 횡보
                base_value = mid_value + random.uniform(-0.2, 0.2) * range_size
            
            # 노이즈 추가
            noise = random.uniform(-0.1, 0.1) * range_size
            final_value = max(scale_min, min(scale_max, base_value + noise))
            data.append(final_value)
        
        return data
    
    def generate_momentum_data_for_chart(self, scenario, length=50, scale_min=-10, scale_max=10):
        """모멘텀 데이터 생성 (MACD 등)"""
        try:
            # 시뮬레이션 엔진 사용
            market_data = self.simulation_engine.load_market_data(length)
            if market_data is not None and 'macd' in market_data.columns:
                # 실제 MACD 데이터가 있으면 사용
                macd_data = market_data['macd'].tolist()
                # 스케일 조정 (필요시)
                if scale_min != -10 or scale_max != 10:
                    adjusted_data = []
                    for value in macd_data:
                        # -10~10을 scale_min~scale_max로 변환
                        ratio = (value + 10) / 20.0  # 0~1로 정규화
                        adjusted_value = scale_min + ratio * (scale_max - scale_min)
                        adjusted_data.append(adjusted_value)
                    return adjusted_data
                return macd_data
        except Exception as e:
            print(f"⚠️ 실제 모멘텀 데이터 로드 실패: {e}")
        
        # 폴백: 가상 데이터 생성
        import random
        data = []
        range_size = scale_max - scale_min
        
        for i in range(length):
            # 시나리오별 경향성 반영
            if scenario in ['상승 추세', '급등']:
                base_value = random.uniform(0.2, 0.8) * scale_max
            elif scenario in ['하락 추세', '급락']:
                base_value = random.uniform(0.2, 0.8) * scale_min
            else:  # 횡보
                base_value = random.uniform(-0.3, 0.3) * range_size
            
            # 노이즈 추가
            noise = random.uniform(-0.1, 0.1) * range_size
            final_value = max(scale_min, min(scale_max, base_value + noise))
            data.append(final_value)
        
        return data
    
    def generate_volume_data_for_chart(self, scenario, length=50):
        """거래량 데이터 생성"""
        try:
            # 시뮬레이션 엔진 사용
            market_data = self.simulation_engine.load_market_data(length)
            if market_data is not None and 'volume' in market_data.columns:
                return market_data['volume'].tolist()
        except Exception as e:
            print(f"⚠️ 실제 거래량 데이터 로드 실패: {e}")
        
        # 폴백: 가상 데이터 생성
        import random
        data = []
        base_volume = 2000000  # 200만
        
        for i in range(length):
            # 시나리오별 거래량 패턴
            if scenario in ['급등', '급락']:
                volume = base_volume * random.uniform(2, 5)  # 급변동시 거래량 증가
            elif scenario in ['상승 추세', '하락 추세']:
                volume = base_volume * random.uniform(1.2, 2.5)
            else:  # 횡보
                volume = base_volume * random.uniform(0.5, 1.5)
            
            data.append(int(volume))
        
        return data

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
            
            if hasattr(self, 'logger'):
                self.logger.debug("전체 컴포넌트 새로고침 완료")
            
        except Exception as e:
            error_msg = f"컴포넌트 새로고침 실패: {e}"
            if hasattr(self, 'logger'):
                self.logger.error(error_msg)
            else:
                print(f"❌ {error_msg}")
    
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
            
            if hasattr(self, 'logger'):
                self.logger.debug("모든 결과 초기화 완료")
            
        except Exception as e:
            error_msg = f"결과 초기화 실패: {e}"
            if hasattr(self, 'logger'):
                self.logger.error(error_msg)
            else:
                print(f"❌ {error_msg}")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    window = TriggerBuilderScreen()
    window.show()
    
    sys.exit(app.exec())
