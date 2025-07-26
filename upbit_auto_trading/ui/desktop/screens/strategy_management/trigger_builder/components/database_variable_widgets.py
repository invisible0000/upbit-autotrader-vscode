#!/usr/bin/env python3
"""
DB 기반 변수 선택 위젯

기존 하드코딩된 변수 목록을 DB 기반 동적 시스템으로 대체하는 UI 컴포넌트
"""

import sys
from typing import Dict, List, Optional, Tuple, Any
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QComboBox, QLabel, 
    QGroupBox, QPushButton, QApplication, QMessageBox
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QIcon

# 트레이딩 변수 관리 시스템 import
try:
    from upbit_auto_trading.utils.trading_variables import SimpleVariableManager
    VARIABLE_MANAGER_AVAILABLE = True
except ImportError:
    VARIABLE_MANAGER_AVAILABLE = False
    print("⚠️ 변수 관리 시스템을 찾을 수 없습니다. 하드코딩된 변수를 사용합니다.")

# 공통 스타일 컴포넌트 import
try:
    from upbit_auto_trading.ui.desktop.common.components import StyledComboBox, StyledGroupBox
    STYLED_COMPONENTS_AVAILABLE = True
except ImportError:
    StyledComboBox = QComboBox
    StyledGroupBox = QGroupBox
    STYLED_COMPONENTS_AVAILABLE = False


class DatabaseVariableComboBox(QWidget):
    """DB 기반 변수 선택 콤보박스 위젯"""
    
    # 신호 정의
    variableChanged = pyqtSignal(str, str)  # (variable_id, display_name)
    compatibilityChanged = pyqtSignal(bool, str)  # (is_compatible, reason)
    
    def __init__(self, 
                 variable_type: str = "all",  # "basic", "external", "all"
                 category_filter: Optional[List[str]] = None,  # ["trend", "momentum"] 등
                 base_variable_id: Optional[str] = None,  # 호환성 검증용 기준 변수
                 parent=None):
        super().__init__(parent)
        
        self.variable_type = variable_type
        self.category_filter = category_filter or []
        self.base_variable_id = base_variable_id
        self.vm = None
        
        # UI 초기화
        self._init_ui()
        self._init_db_connection()
        self._load_variables()
    
    def _init_ui(self):
        """UI 초기화"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # 메인 콤보박스
        self.combo = StyledComboBox() if STYLED_COMPONENTS_AVAILABLE else QComboBox()
        self.combo.currentTextChanged.connect(self._on_variable_changed)
        
        # 호환성 상태 라벨
        self.compatibility_label = QLabel()
        self.compatibility_label.setVisible(False)
        
        layout.addWidget(self.combo)
        layout.addWidget(self.compatibility_label)
    
    def _init_db_connection(self):
        """DB 연결 초기화"""
        if not VARIABLE_MANAGER_AVAILABLE:
            return
        
        try:
            self.vm = SimpleVariableManager('trading_variables.db')
        except Exception as e:
            print(f"❌ DB 연결 실패: {e}")
            self.vm = None
    
    def _load_variables(self):
        """변수 목록 로드"""
        if not self.vm:
            self._load_hardcoded_variables()
            return
        
        try:
            # DB에서 변수 목록 가져오기
            variables = self.vm.get_all_variables(active_only=True)
            
            # 카테고리 필터 적용
            if self.category_filter:
                variables = [v for v in variables if v['purpose_category'] in self.category_filter]
            
            # 카테고리별로 그룹화하여 표시
            self._populate_grouped_combo(variables)
            
        except Exception as e:
            print(f"❌ 변수 로드 실패: {e}")
            self._load_hardcoded_variables()
    
    def _populate_grouped_combo(self, variables: List[Dict]):
        """카테고리별 그룹화된 콤보박스 구성"""
        self.combo.clear()
        
        # 카테고리별 그룹화
        groups = {}
        for var in variables:
            category = var['purpose_category']
            if category not in groups:
                groups[category] = []
            groups[category].append(var)
        
        # 카테고리 아이콘 매핑
        category_icons = {
            'trend': '📈',
            'momentum': '⚡',
            'volatility': '🔥', 
            'volume': '📦',
            'price': '💰',
            'support_resistance': '🎯'
        }
        
        # 카테고리 이름 매핑
        category_names = {
            'trend': '추세 지표',
            'momentum': '모멘텀 지표',
            'volatility': '변동성 지표',
            'volume': '거래량 지표',
            'price': '가격 데이터',
            'support_resistance': '지지/저항'
        }
        
        # 그룹별로 추가
        for category, vars_list in sorted(groups.items()):
            icon = category_icons.get(category, '📊')
            name = category_names.get(category, category)
            
            # 그룹 헤더 추가 (선택 불가)
            group_header = f"── {icon} {name} ──"
            self.combo.addItem(group_header)
            self.combo.model().item(self.combo.count()-1).setEnabled(False)
            
            # 변수들 추가
            for var in sorted(vars_list, key=lambda x: x['display_name_ko']):
                chart_icon = "🔗" if var['chart_category'] == 'overlay' else "📊"
                display_text = f"  {chart_icon} {var['display_name_ko']}"
                
                self.combo.addItem(display_text)
                # 실제 variable_id를 데이터로 저장
                self.combo.setItemData(self.combo.count()-1, var['variable_id'])
    
    def _load_hardcoded_variables(self):
        """DB 사용 불가 시 하드코딩된 변수 목록 사용"""
        hardcoded_vars = [
            ("SMA", "🔗 단순이동평균"),
            ("EMA", "🔗 지수이동평균"),
            ("RSI", "📊 RSI 지표"),
            ("STOCH", "📊 스토캐스틱"),
            ("MACD", "📊 MACD 지표"),
            ("VOLUME", "📊 거래량"),
            ("CURRENT_PRICE", "🔗 현재가")
        ]
        
        self.combo.clear()
        self.combo.addItem("── 📋 기본 지표 ──")
        self.combo.model().item(0).setEnabled(False)
        
        for var_id, display_name in hardcoded_vars:
            self.combo.addItem(display_name)
            self.combo.setItemData(self.combo.count()-1, var_id)
    
    def _on_variable_changed(self):
        """변수 선택 변경 시 호출"""
        current_index = self.combo.currentIndex()
        if current_index < 0:
            return
        
        # 실제 variable_id 가져오기
        variable_id = self.combo.itemData(current_index)
        if not variable_id:
            return  # 그룹 헤더 선택 시 무시
        
        display_name = self.combo.currentText().strip()
        
        # 변수 변경 신호 발생
        self.variableChanged.emit(variable_id, display_name)
        
        # 호환성 검증 (기준 변수가 있는 경우)
        if self.base_variable_id and self.vm:
            self._check_compatibility(variable_id)
    
    def _check_compatibility(self, selected_variable_id: str):
        """호환성 검증 및 UI 업데이트"""
        if not self.vm or not self.base_variable_id:
            return
        
        try:
            result = self.vm.check_compatibility(self.base_variable_id, selected_variable_id)
            
            if result['compatible']:
                self.compatibility_label.setText(f"✅ {result['reason']}")
                self.compatibility_label.setStyleSheet("color: green; font-weight: bold;")
            else:
                self.compatibility_label.setText(f"❌ {result['reason']}")
                self.compatibility_label.setStyleSheet("color: red; font-weight: bold;")
            
            self.compatibility_label.setVisible(True)
            self.compatibilityChanged.emit(result['compatible'], result['reason'])
            
        except Exception as e:
            print(f"❌ 호환성 검증 실패: {e}")
    
    def set_base_variable(self, base_variable_id: str):
        """기준 변수 설정 (호환성 검증용)"""
        self.base_variable_id = base_variable_id
        
        # 현재 선택된 변수가 있으면 호환성 재검증
        current_variable_id = self.get_selected_variable_id()
        if current_variable_id:
            self._check_compatibility(current_variable_id)
    
    def get_selected_variable_id(self) -> Optional[str]:
        """현재 선택된 변수 ID 반환"""
        current_index = self.combo.currentIndex()
        if current_index < 0:
            return None
        return self.combo.itemData(current_index)
    
    def get_selected_display_name(self) -> str:
        """현재 선택된 변수의 표시 이름 반환"""
        return self.combo.currentText().strip()
    
    def set_variable(self, variable_id: str):
        """특정 변수로 설정"""
        for i in range(self.combo.count()):
            if self.combo.itemData(i) == variable_id:
                self.combo.setCurrentIndex(i)
                break
    
    def get_compatible_variables(self) -> List[Tuple[str, str]]:
        """현재 기준 변수와 호환되는 변수 목록 반환"""
        if not self.vm or not self.base_variable_id:
            return []
        
        try:
            return self.vm.get_compatible_variables(self.base_variable_id)
        except Exception as e:
            print(f"❌ 호환 변수 조회 실패: {e}")
            return []
    
    def filter_compatible_only(self, enabled: bool = True):
        """호환 가능한 변수만 표시 (필터링)"""
        if not enabled or not self.vm or not self.base_variable_id:
            return
        
        # 호환 가능한 변수 목록 가져오기
        compatible_vars = self.get_compatible_variables()
        compatible_ids = {var_id for var_id, _ in compatible_vars}
        
        # 콤보박스 아이템들을 비활성화/활성화
        for i in range(self.combo.count()):
            item_data = self.combo.itemData(i)
            if item_data:  # 실제 변수인 경우
                is_compatible = item_data in compatible_ids
                self.combo.model().item(i).setEnabled(is_compatible)
    
    def closeEvent(self, event):
        """위젯 종료 시 DB 연결 해제"""
        if self.vm:
            self.vm.close()
        super().closeEvent(event)


class CompatibilityAwareVariableSelector(QWidget):
    """호환성 인식 변수 선택 위젯 (기본 + 외부 변수 쌍)"""
    
    # 신호 정의
    selectionChanged = pyqtSignal(str, str, bool)  # (base_var, external_var, compatible)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._init_ui()
    
    def _init_ui(self):
        """UI 초기화"""
        layout = QVBoxLayout(self)
        
        # 기본 변수 선택
        basic_group = StyledGroupBox("기본 변수") if STYLED_COMPONENTS_AVAILABLE else QGroupBox("기본 변수")
        basic_layout = QVBoxLayout(basic_group)
        
        self.basic_combo = DatabaseVariableComboBox(variable_type="basic")
        self.basic_combo.variableChanged.connect(self._on_basic_variable_changed)
        basic_layout.addWidget(self.basic_combo)
        
        # 외부 변수 선택
        external_group = StyledGroupBox("외부 변수") if STYLED_COMPONENTS_AVAILABLE else QGroupBox("외부 변수")
        external_layout = QVBoxLayout(external_group)
        
        self.external_combo = DatabaseVariableComboBox(variable_type="external")
        self.external_combo.variableChanged.connect(self._on_external_variable_changed)
        self.external_combo.compatibilityChanged.connect(self._on_compatibility_changed)
        external_layout.addWidget(self.external_combo)
        
        layout.addWidget(basic_group)
        layout.addWidget(external_group)
        
        # 호환성 필터링 버튼
        self.filter_button = QPushButton("🔍 호환 가능한 것만 표시")
        self.filter_button.setCheckable(True)
        self.filter_button.toggled.connect(self._toggle_compatibility_filter)
        layout.addWidget(self.filter_button)
    
    def _on_basic_variable_changed(self, variable_id: str, display_name: str):
        """기본 변수 변경 시"""
        # 외부 변수 콤보박스에 기준 변수 설정
        self.external_combo.set_base_variable(variable_id)
        
        # 필터링이 활성화되어 있으면 적용
        if self.filter_button.isChecked():
            self.external_combo.filter_compatible_only(True)
        
        self._emit_selection_changed()
    
    def _on_external_variable_changed(self, variable_id: str, display_name: str):
        """외부 변수 변경 시"""
        self._emit_selection_changed()
    
    def _on_compatibility_changed(self, is_compatible: bool, reason: str):
        """호환성 상태 변경 시"""
        self._emit_selection_changed()
    
    def _toggle_compatibility_filter(self, enabled: bool):
        """호환성 필터링 토글"""
        self.external_combo.filter_compatible_only(enabled)
        
        if enabled:
            self.filter_button.setText("✅ 호환 가능한 것만 표시")
        else:
            self.filter_button.setText("🔍 호환 가능한 것만 표시")
    
    def _emit_selection_changed(self):
        """선택 변경 신호 발생"""
        basic_var = self.basic_combo.get_selected_variable_id()
        external_var = self.external_combo.get_selected_variable_id()
        
        # 호환성 확인
        compatible = False
        if basic_var and external_var and self.basic_combo.vm:
            try:
                result = self.basic_combo.vm.check_compatibility(basic_var, external_var)
                compatible = result['compatible']
            except:
                compatible = False
        
        self.selectionChanged.emit(basic_var or "", external_var or "", compatible)
    
    def get_selection(self) -> Dict[str, Any]:
        """현재 선택 상태 반환"""
        return {
            'basic_variable': {
                'id': self.basic_combo.get_selected_variable_id(),
                'name': self.basic_combo.get_selected_display_name()
            },
            'external_variable': {
                'id': self.external_combo.get_selected_variable_id(),
                'name': self.external_combo.get_selected_display_name()
            },
            'compatible': self._is_current_selection_compatible()
        }
    
    def _is_current_selection_compatible(self) -> bool:
        """현재 선택이 호환되는지 확인"""
        basic_var = self.basic_combo.get_selected_variable_id()
        external_var = self.external_combo.get_selected_variable_id()
        
        if not basic_var or not external_var or not self.basic_combo.vm:
            return False
        
        try:
            result = self.basic_combo.vm.check_compatibility(basic_var, external_var)
            return result['compatible']
        except:
            return False


# 테스트용 메인 함수
def main():
    """테스트용 메인 함수"""
    app = QApplication(sys.argv)
    
    # 단일 콤보박스 테스트
    print("🧪 DB 기반 변수 콤보박스 테스트")
    
    widget = CompatibilityAwareVariableSelector()
    widget.setWindowTitle("DB 기반 변수 선택 위젯 테스트")
    widget.resize(400, 300)
    widget.show()
    
    def on_selection_changed(basic, external, compatible):
        status = "✅ 호환" if compatible else "❌ 비호환"
        print(f"선택: {basic} ↔ {external} ({status})")
    
    widget.selectionChanged.connect(on_selection_changed)
    
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
