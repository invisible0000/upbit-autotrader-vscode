"""
트리거 상세정보 위젯 - 기존 기능 정확 복제
integrated_condition_manager.py의 create_trigger_detail_area() 완전 복제
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QGroupBox, QTextEdit, QPushButton, QHBoxLayout, QSizePolicy
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont

# 디버그 로깅 시스템
from upbit_auto_trading.utils.debug_logger import get_logger

logger = get_logger("TriggerDetail")


class TriggerDetailWidget(QWidget):
    """트리거 상세정보 위젯 - 기존 기능 정확 복제"""
    
    # 시그널 정의
    trigger_copied = pyqtSignal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_trigger = None
        self.setup_ui()
        self.initialize_default_state()
    
    def setup_ui(self):
        """UI 구성 - integrated_condition_manager.py와 정확히 동일"""
        # 메인 그룹박스 (스타일은 애플리케이션 테마를 따름)
        self.group = QGroupBox("📊 트리거 상세정보")
        # 하드코딩된 스타일 제거 - 애플리케이션 테마를 따름
        
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addWidget(self.group)
        
        layout = QVBoxLayout(self.group)
        layout.setContentsMargins(6, 6, 6, 6)  # 표준 마진
        layout.setSpacing(4)  # 표준 간격
        
        # 그룹박스 크기 정책도 Expanding으로 설정
        self.group.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        
        # 상세 정보 표시 (원본과 정확히 동일)
        self.detail_text = QTextEdit()
        self.detail_text.setReadOnly(True)
        # setMaximumHeight 제거하여 텍스트 박스가 꽉 차게 함
        # self.detail_text.setMaximumHeight(200)
        
        # 크기 정책을 Expanding으로 설정하여 최대한 확장
        self.detail_text.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        
        # 최소 높이 제한 제거하여 레이아웃 비율이 1:1이 되도록 함
        # self.detail_text.setMinimumHeight(150)
        
        # 폰트 크기를 더 작게 설정 (원본과 동일)
        font = QFont()
        font.setPointSize(9)  # 8 → 9로 살짝 증가
        self.detail_text.setFont(font)
        
        # 문서 여백을 줄여서 줄간격 최소화 (원본과 동일)
        document = self.detail_text.document()
        if document:
            document.setDocumentMargin(3)
        
        # 스타일은 애플리케이션 테마를 따름 (하드코딩 제거)
        layout.addWidget(self.detail_text, 1)  # stretch=1 추가하여 남은 공간을 모두 차지
        
        # 액션 버튼들 (원본에는 없지만 유용한 기능)
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(2)
        
        self.copy_detail_btn = QPushButton("📄 복사")
        self.copy_detail_btn.setMaximumHeight(25)
        self.copy_detail_btn.clicked.connect(self.copy_detail_to_clipboard)
        btn_layout.addWidget(self.copy_detail_btn)
        
        # JSON 형태로 보기 버튼 추가
        self.json_view_btn = QPushButton("📋 JSON")
        self.json_view_btn.setMaximumHeight(25)
        self.json_view_btn.clicked.connect(self.show_json_popup)
        btn_layout.addWidget(self.json_view_btn)
        
        btn_layout.addStretch()  # 버튼들을 왼쪽으로 정렬
        
        layout.addLayout(btn_layout)
    
    def initialize_default_state(self):
        """기본 상태 초기화 - 원본과 동일"""
        self.detail_text.setPlainText("트리거를 선택하면 상세정보가 표시됩니다.")
    
    def update_trigger_detail(self, trigger_data):
        """트리거 상세정보 업데이트 - 원본 기능 복제"""
        try:
            if not trigger_data:
                self.detail_text.setPlainText("트리거를 선택하면 상세정보가 표시됩니다.")
                self.current_trigger = None
                return
            
            self.current_trigger = trigger_data
            
            # 상세정보 포맷팅 (원본 스타일)
            detail_text = self._format_trigger_detail(trigger_data)
            self.detail_text.setPlainText(detail_text)
            
        except Exception as e:
            logger.error(f"트리거 상세정보 업데이트 실패: {e}")
            self.detail_text.setPlainText(f"상세정보 로드 중 오류 발생: {e}")
    
    def _format_trigger_detail(self, trigger_data):
        """트리거 상세정보 포맷팅 - 개선된 DB 스키마 지원"""
        name = trigger_data.get('name', 'Unknown')
        created_at = trigger_data.get('created_at', 'Unknown')
        # 실제 DB 스키마에서는 is_active 키를 사용함
        active = trigger_data.get('is_active', trigger_data.get('active', False))
        
        # 기본 정보
        detail_text = f"""
🏷️ 이름: {name}
📅 생성일: {created_at}
🔄 상태: {'✅ 활성' if active else '⏸️ 비활성'}

"""
        
        # 변수 정보 및 카테고리 정보 (개선된 DB 스키마 지원)
        # 다양한 가능한 키 확인
        variable_id = (trigger_data.get('variable_id') or
                       trigger_data.get('variable') or
                       trigger_data.get('base_variable') or
                       'Unknown')
        
        if variable_id != 'Unknown':
            detail_text += "📊 기본 변수 정보:\n"
            detail_text += f"  🔍 변수 ID: {variable_id}\n"
            
            # 변수 한글명 표시
            variable_name = self._get_variable_display_name(variable_id)
            detail_text += f"  📝 변수명: {variable_name}\n"
            
            # 카테고리 정보 표시 (3중 카테고리 시스템) - 더 상세하게
            purpose_category = self._get_purpose_category(variable_id)
            chart_category = self._get_chart_category(variable_id)
            
            detail_text += "📂 카테고리 정보:\n"
            detail_text += f"  📁 용도: {purpose_category}\n"
            detail_text += f"  📈 차트: {chart_category}\n"
            
            # DB에서 가져온 카테고리 정보도 표시 (있는 경우)
            db_category = trigger_data.get('category', trigger_data.get('chart_category'))
            if db_category and db_category != '자동감지':
                detail_text += f"  🏷️ DB 카테고리: {db_category}\n"
            
            # 변수 파라미터 정보 (실제 DB 스키마에 맞게)
            parameters = (trigger_data.get('variable_params') or
                         trigger_data.get('parameters') or
                         trigger_data.get('params') or {})
            if parameters:
                detail_text += f"  ⚙️ 파라미터: {parameters}\n"
            
            detail_text += "\n"
        
        # 조건 정보 (실제 DB 스키마에 맞게)
        operator = trigger_data.get('operator', 'Unknown')
        value = (trigger_data.get('target_value') or
                trigger_data.get('value') or
                trigger_data.get('comparison_value') or
                'Unknown')
        
        # 추세 방향성 정보 준비
        trend_direction = trigger_data.get('trend_direction', 'both')
        trend_names = {
            'rising': '📈 상승 추세',
            'falling': '📉 하락 추세', 
            'both': '📊 추세 무관'
        }
        
        detail_text += f"""🎯 비교 조건:
  📊 기본 변수: {variable_name if 'variable_name' in locals() else variable_id}
  ⚖️ 연산자: {self._format_operator(operator)}
  📈 추세 방향성: {trend_names.get(trend_direction, trend_direction)}
  🎯 비교값: {value}

"""
        
        # 외부 변수 정보 (골든크로스 등) - 실제 DB 구조에 맞게
        external_variable = trigger_data.get('external_variable')
        
        if external_variable and isinstance(external_variable, dict):
            detail_text += "🔗 외부 변수 정보:\n"
            external_variable_id = external_variable.get('variable_id', 'Unknown')
            external_variable_name = external_variable.get('variable_name', self._get_variable_display_name(external_variable_id))
            detail_text += f"  🔍 변수 ID: {external_variable_id}\n"
            detail_text += f"  📝 변수명: {external_variable_name}\n"
            
            # 외부 변수 카테고리 정보
            ext_purpose_category = self._get_purpose_category(external_variable_id)
            ext_chart_category = self._get_chart_category(external_variable_id)
            
            detail_text += f"  📁 용도 카테고리: {ext_purpose_category}\n"
            detail_text += f"  📈 차트 카테고리: {ext_chart_category}\n"
            
            # 외부 변수 파라미터
            external_parameters = external_variable.get('variable_params', external_variable.get('parameters', {}))
            if external_parameters:
                detail_text += f"  ⚙️ 파라미터: {external_parameters}\n"
            
            detail_text += "\n"
        
        # 차트 카테고리 정보 (DB 스키마)
        db_chart_category = trigger_data.get('chart_category', '자동감지')
        detail_text += f"🎨 차트 표시: {self._format_chart_category(db_chart_category)}\n\n"
        
        # 메타데이터 및 기타 정보
        description = trigger_data.get('description')
        if description:
            detail_text += f"📝 설명: {description}\n\n"
        
        # 호환성 정보 (있는 경우)
        compatibility_score = trigger_data.get('compatibility_score')
        if compatibility_score is not None:
            detail_text += f"� 호환성 점수: {compatibility_score}%\n\n"
        
        return detail_text.strip()
    
    def _get_variable_display_name(self, variable_id):
        """변수 ID의 한글 표시명 반환"""
        try:
            from .variable_definitions import VariableDefinitions
            var_def = VariableDefinitions()
            category_variables = var_def.get_category_variables()
            
            for category, variables in category_variables.items():
                for var_id, var_name in variables:
                    if var_id == variable_id:
                        return var_name
            
        except Exception as e:
            logger.warning(f"변수 정의 시스템 사용 실패: {e}")
        
        # 하드코딩 폴백 (더 많은 변수 추가)
        name_mapping = {
            'SMA': '단순이동평균',
            'EMA': '지수이동평균',
            'RSI': 'RSI 지표',
            'STOCHASTIC': '스토캐스틱',
            'MACD': 'MACD 지표',
            'BOLLINGER_BAND': '볼린저밴드',
            'CURRENT_PRICE': '현재가',
            'VOLUME': '거래량',
            'ATR': 'ATR 지표',
            'VOLUME_SMA': '거래량 이동평균'
        }
        return name_mapping.get(variable_id, variable_id)
    
    def _get_purpose_category(self, variable_id):
        """변수의 용도 카테고리 반환"""
        try:
            from .variable_definitions import VariableDefinitions
            var_def = VariableDefinitions()
            # 용도 카테고리 매핑 (추후 VariableDefinitions에서 가져올 수 있도록 개선)
            category_mapping = {
                'SMA': '📈 추세',
                'EMA': '📈 추세', 
                'BOLLINGER_BAND': '🔥 변동성',
                'RSI': '⚡ 모멘텀',
                'STOCHASTIC': '⚡ 모멘텀',
                'MACD': '⚡ 모멘텀',
                'ATR': '🔥 변동성',
                'VOLUME': '📦 거래량',
                'VOLUME_SMA': '📦 거래량',
                'CURRENT_PRICE': '💰 시장가'
            }
            return category_mapping.get(variable_id, '📊 기타')
        except:
            return '📊 기타'
    
    def _get_chart_category(self, variable_id):
        """변수의 차트 카테고리 반환"""
        try:
            from .variable_definitions import VariableDefinitions
            chart_category = VariableDefinitions.get_chart_category(variable_id)
            return '🔗 오버레이' if chart_category == 'overlay' else '📊 서브플롯'
        except Exception as e:
            logger.warning(f"차트 카테고리 확인 실패: {e}")
            # 폴백
            overlay_vars = ['SMA', 'EMA', 'BOLLINGER_BAND', 'CURRENT_PRICE', 'OPEN_PRICE', 'HIGH_PRICE', 'LOW_PRICE']
            return '🔗 오버레이' if variable_id in overlay_vars else '📊 서브플롯'
    
    def _format_operator(self, operator):
        """연산자 포맷팅"""
        operator_names = {
            '>': '> (초과)',
            '>=': '>= (이상)',
            '<': '< (미만)',
            '<=': '<= (이하)',
            '==': '== (같음)',
            '!=': '!= (다름)',
            '~=': '~= (근사값)'
        }
        return operator_names.get(operator, operator)
    
    def _format_chart_category(self, chart_category):
        """차트 카테고리 포맷팅"""
        if chart_category == 'overlay':
            return '🔗 오버레이 (메인 차트)'
        elif chart_category == 'subplot':
            return '📊 서브플롯 (별도 차트)'
        else:
            return f'🎯 {chart_category} (자동감지)'
    
    def copy_detail_to_clipboard(self):
        """상세정보를 클립보드에 복사"""
        try:
            from PyQt6.QtWidgets import QApplication
            clipboard = QApplication.clipboard()
            clipboard.setText(self.detail_text.toPlainText())
            logger.debug("트리거 상세정보가 클립보드에 복사되었습니다.")
        except Exception as e:
            logger.error(f"클립보드 복사 실패: {e}")
    
    def clear_detail(self):
        """상세정보 초기화"""
        self.detail_text.setPlainText("트리거를 선택하면 상세정보가 표시됩니다.")
        self.current_trigger = None
    
    def get_current_trigger(self):
        """현재 트리거 반환"""
        return self.current_trigger
    
    def has_trigger_selected(self) -> bool:
        """트리거가 선택되었는지 확인"""
        return self.current_trigger is not None
    
    # 스타일 정의 - integrated_condition_manager.py에서 정확히 복사
    def _get_original_group_style(self):
        """원본 get_groupbox_style("#6f42c1")와 동일"""
        return """
            QGroupBox {
                background-color: white;
                border: 1px solid #6f42c1;
                border-radius: 8px;
                font-weight: bold;
                padding-top: 15px;
                margin: 3px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
                background-color: white;
                color: #6f42c1;
                font-size: 12px;
            }
        """
    
    def _get_original_text_style(self):
        """원본 텍스트 에디터 스타일과 정확히 동일"""
        return """
            QTextEdit {
                border: 2px solid #ddd;
                border-radius: 8px;
                padding: 8px;
                font-size: 8px;
                background-color: white;
                font-family: 'Consolas', 'Monaco', monospace;
            }
        """
    
    def show_json_popup(self):
        """JSON 형태의 트리거 데이터를 팝업으로 표시"""
        if not self.current_trigger:
            from PyQt6.QtWidgets import QMessageBox
            QMessageBox.information(self, "ℹ️ 알림", "표시할 트리거가 선택되지 않았습니다.")
            return
        
        try:
            import json
            from PyQt6.QtWidgets import QDialog, QVBoxLayout, QTextEdit, QPushButton, QHBoxLayout
            
            # JSON 팝업 다이얼로그 생성
            dialog = QDialog(self)
            dialog.setWindowTitle(f"📋 JSON 데이터 - {self.current_trigger.get('name', 'Unknown')}")
            dialog.setMinimumSize(600, 500)
            dialog.resize(800, 600)
            
            layout = QVBoxLayout(dialog)
            
            # JSON 데이터 표시용 텍스트 에디터
            json_text = QTextEdit()
            json_text.setReadOnly(True)
            json_text.setFont(QFont("Consolas", 10))
            
            # JSON 데이터 포맷팅 (들여쓰기 추가)
            json_str = json.dumps(self.current_trigger, ensure_ascii=False, indent=2, sort_keys=True)
            json_text.setPlainText(json_str)
            
            layout.addWidget(json_text)
            
            # 버튼 레이아웃
            btn_layout = QHBoxLayout()
            
            # JSON 복사 버튼
            copy_json_btn = QPushButton("📋 JSON 복사")
            copy_json_btn.clicked.connect(lambda: self._copy_json_to_clipboard(json_str))
            btn_layout.addWidget(copy_json_btn)
            
            btn_layout.addStretch()
            
            # 닫기 버튼
            close_btn = QPushButton("❌ 닫기")
            close_btn.clicked.connect(dialog.accept)
            btn_layout.addWidget(close_btn)
            
            layout.addLayout(btn_layout)
            
            # 다이얼로그 표시
            dialog.exec()
            
        except Exception as e:
            from PyQt6.QtWidgets import QMessageBox
            QMessageBox.critical(self, "❌ 오류", f"JSON 팝업 생성 중 오류가 발생했습니다:\n{e}")
    
    def _copy_json_to_clipboard(self, json_str):
        """JSON 문자열을 클립보드에 복사"""
        try:
            from PyQt6.QtWidgets import QApplication, QMessageBox
            clipboard = QApplication.clipboard()
            clipboard.setText(json_str)
            QMessageBox.information(self, "✅ 복사 완료", "JSON 데이터가 클립보드에 복사되었습니다.")
        except Exception as e:
            from PyQt6.QtWidgets import QMessageBox
            QMessageBox.warning(self, "⚠️ 경고", f"클립보드 복사 실패: {e}")


if __name__ == "__main__":
    # 테스트용 코드
    from PyQt6.QtWidgets import QApplication
    import sys
    
    app = QApplication(sys.argv)
    
    widget = TriggerDetailWidget()
    widget.show()
    
    # 테스트 트리거 설정
    test_trigger = {
        'name': 'RSI 과매수 테스트',
        'created_at': '2024-01-01 10:30:00',
        'active': True,
        'variable': 'rsi',
        'operator': '>',
        'value': '70',
        'external_variables': {
            'rsi_period': {'type': 'int', 'value': 14},
            'threshold': {'type': 'float', 'value': 70.0}
        },
        'metadata': {
            'description': 'RSI 70 초과 시 매도 신호',
            'category': 'technical_indicator'
        }
    }
    
    widget.update_trigger_detail(test_trigger)
    
    sys.exit(app.exec())
