#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
변수 호환성 검증 구현 패치

조건 다이얼로그와 트리거 빌더에 실시간 변수 호환성 검증 기능을 추가합니다.
"""

import os
import sys
from typing import Optional, Tuple

# 프로젝트 루트 추가
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
sys.path.insert(0, project_root)

try:
    from upbit_auto_trading.ui.desktop.screens.strategy_management.trigger_builder.components.chart_variable_service import (
        get_chart_variable_service
    )
    CHART_VARIABLE_SERVICE_AVAILABLE = True
except ImportError:
    CHART_VARIABLE_SERVICE_AVAILABLE = False


class VariableCompatibilityValidator:
    """변수 호환성 검증 클래스"""
    
    def __init__(self):
        if CHART_VARIABLE_SERVICE_AVAILABLE:
            self.service = get_chart_variable_service()
        else:
            self.service = None
            print("⚠️ 차트 변수 서비스를 사용할 수 없습니다.")
    
    def validate_compatibility(self, base_variable_id: str, 
                             external_variable_id: str) -> Tuple[bool, str, str]:
        """
        변수 호환성 검증
        
        Returns:
            (is_compatible, user_message, log_message)
        """
        if not self.service:
            return True, "", "차트 변수 서비스 비활성화"
        
        if not base_variable_id or not external_variable_id:
            return True, "", "변수 ID 없음"
        
        try:
            is_compatible, reason = self.service.is_compatible_external_variable(
                base_variable_id, external_variable_id
            )
            
            if is_compatible:
                user_message = f"✅ {base_variable_id}와(과) {external_variable_id}는 호환됩니다."
                log_message = f"호환성 검증 성공: {base_variable_id} ↔ {external_variable_id}"
                return True, user_message, log_message
            else:
                user_message = self._generate_user_friendly_message(
                    base_variable_id, external_variable_id, reason
                )
                log_message = f"호환성 검증 실패: {base_variable_id} ↔ {external_variable_id} - {reason}"
                return False, user_message, log_message
                
        except Exception as e:
            user_message = f"⚠️ 호환성 검사 중 오류가 발생했습니다: {str(e)}"
            log_message = f"호환성 검증 오류: {base_variable_id} ↔ {external_variable_id} - {e}"
            return False, user_message, log_message
    
    def _generate_user_friendly_message(self, base_var: str, external_var: str, 
                                      reason: str) -> str:
        """사용자 친화적인 오류 메시지 생성"""
        
        # 변수 이름 매핑 (ID -> 사용자 친화적 이름)
        var_names = {
            'rsi': 'RSI',
            'macd': 'MACD',
            'stochastic': '스토캐스틱',
            'current_price': '현재가',
            'moving_average': '이동평균',
            'bollinger_band': '볼린저밴드',
            'volume': '거래량'
        }
        
        base_name = var_names.get(base_var, base_var)
        external_name = var_names.get(external_var, external_var)
        
        # 특정 조합에 대한 맞춤 메시지
        specific_messages = {
            ('rsi', 'macd'): f"❌ {base_name}(오실레이터)와 {external_name}(모멘텀 지표)는 서로 다른 카테고리로 비교할 수 없습니다.\n\n💡 제안: RSI와 비교하려면 같은 오실레이터인 '스토캐스틱'을 선택해보세요.",
            ('rsi', 'volume'): f"❌ {base_name}(0-100% 지표)와 {external_name}(거래량)은 완전히 다른 단위로 의미있는 비교가 불가능합니다.\n\n💡 제안: RSI와 비교하려면 같은 퍼센트 지표인 '스토캐스틱'을 선택해보세요.",
            ('current_price', 'rsi'): f"❌ {base_name}(원화)와 {external_name}(퍼센트)는 단위가 달라 비교할 수 없습니다.\n\n💡 제안: 현재가와 비교하려면 같은 가격 지표인 '이동평균'이나 '볼린저밴드'를 선택해보세요.",
            ('current_price', 'volume'): f"❌ {base_name}(가격)과 {external_name}(거래량)은 의미가 달라 비교할 수 없습니다.\n\n💡 제안: 현재가와 비교하려면 같은 가격 지표인 '이동평균'을 선택해보세요.",
            ('macd', 'rsi'): f"❌ {base_name}(모멘텀 지표)와 {external_name}(오실레이터)는 서로 다른 카테고리로 비교할 수 없습니다.\n\n💡 제안: MACD와 비교할 수 있는 모멘텀 지표를 추가로 등록하거나, 다른 변수를 선택해보세요."
        }
        
        key = (base_var, external_var)
        if key in specific_messages:
            return specific_messages[key]
        
        # 기본 메시지
        return f"❌ {base_name}와(과) {external_name}는 호환되지 않습니다.\n\n사유: {reason}\n\n💡 제안: 같은 카테고리나 호환되는 단위의 변수를 선택해주세요."
    
    def get_compatible_variables(self, base_variable_id: str) -> list:
        """기본 변수와 호환되는 외부변수 목록 반환"""
        if not self.service:
            return []
        
        try:
            all_variables = self.service.get_available_variables_by_category()
            compatible_vars = []
            
            for var_config in all_variables:
                if var_config.variable_id == base_variable_id:
                    continue  # 자기 자신 제외
                
                is_compatible, _ = self.service.is_compatible_external_variable(
                    base_variable_id, var_config.variable_id
                )
                
                if is_compatible:
                    compatible_vars.append({
                        'id': var_config.variable_id,
                        'name': var_config.variable_name,
                        'category': var_config.category
                    })
            
            return compatible_vars
            
        except Exception as e:
            print(f"❌ 호환 변수 목록 조회 실패: {e}")
            return []
    
    def generate_compatibility_report(self) -> str:
        """전체 변수 호환성 보고서 생성"""
        if not self.service:
            return "차트 변수 서비스를 사용할 수 없습니다."
        
        try:
            all_variables = self.service.get_available_variables_by_category()
            report = ["📊 변수 호환성 보고서", "=" * 50, ""]
            
            for base_var in all_variables:
                compatible_vars = self.get_compatible_variables(base_var.variable_id)
                
                report.append(f"🎯 {base_var.variable_name} ({base_var.variable_id})")
                report.append(f"   카테고리: {base_var.category}")
                
                if compatible_vars:
                    report.append(f"   ✅ 호환 변수 ({len(compatible_vars)}개):")
                    for var in compatible_vars:
                        report.append(f"      - {var['name']} ({var['category']})")
                else:
                    report.append("   ❌ 호환 변수 없음")
                
                report.append("")
            
            return "\n".join(report)
            
        except Exception as e:
            return f"보고서 생성 실패: {e}"


def test_compatibility_validation():
    """호환성 검증 테스트"""
    print("🧪 변수 호환성 검증 테스트 시작")
    print("-" * 50)
    
    validator = VariableCompatibilityValidator()
    
    test_cases = [
        ("rsi", "stochastic", True, "같은 오실레이터"),
        ("rsi", "macd", False, "다른 카테고리"),
        ("current_price", "moving_average", True, "같은 가격 오버레이"),
        ("current_price", "volume", False, "완전 다른 단위"),
        ("rsi", "volume", False, "의미없는 비교"),
    ]
    
    for base_var, external_var, expected, description in test_cases:
        is_compatible, user_msg, log_msg = validator.validate_compatibility(
            base_var, external_var
        )
        
        status = "✅ PASS" if (is_compatible == expected) else "❌ FAIL"
        print(f"{status} {base_var} ↔ {external_var} ({description})")
        
        if not is_compatible:
            print(f"   메시지: {user_msg.split(chr(10))[0]}")  # 첫 번째 줄만
        
        print(f"   로그: {log_msg}")
        print()
    
    # 호환 변수 목록 테스트
    print("📋 호환 변수 목록 테스트:")
    for base_var in ["rsi", "current_price", "macd"]:
        compatible_vars = validator.get_compatible_variables(base_var)
        print(f"   {base_var}: {len(compatible_vars)}개 호환 변수")
        for var in compatible_vars:
            print(f"      - {var['name']}")
    
    print("\n✅ 테스트 완료!")


def generate_ui_integration_example():
    """UI 통합 예제 코드 생성"""
    example_code = '''
# 조건 다이얼로그에 추가할 호환성 검증 코드 예제

class EnhancedConditionDialog(QWidget):
    def __init__(self):
        super().__init__()
        self.compatibility_validator = VariableCompatibilityValidator()
        self.setup_ui()
    
    def setup_ui(self):
        # 기존 UI 설정...
        
        # 외부변수 콤보박스에 시그널 연결
        self.external_variable_combo.currentTextChanged.connect(
            self.on_external_variable_changed
        )
        
        # 기본 변수 콤보박스에 시그널 연결  
        self.base_variable_combo.currentTextChanged.connect(
            self.on_base_variable_changed
        )
        
        # 호환성 상태 라벨
        self.compatibility_status_label = QLabel()
        self.compatibility_status_label.setWordWrap(True)
        layout.addWidget(self.compatibility_status_label)
    
    def on_base_variable_changed(self, variable_name):
        """기본 변수 변경 시 호환 가능한 외부변수만 표시"""
        if not variable_name:
            return
        
        # 변수명을 ID로 변환 (실제 구현에서는 매핑 테이블 필요)
        base_variable_id = self.get_variable_id_by_name(variable_name)
        
        # 호환 가능한 변수들만 외부변수 콤보박스에 추가
        compatible_vars = self.compatibility_validator.get_compatible_variables(
            base_variable_id
        )
        
        self.external_variable_combo.clear()
        self.external_variable_combo.addItem("선택하세요", "")
        
        for var in compatible_vars:
            self.external_variable_combo.addItem(var['name'], var['id'])
        
        # 상태 업데이트
        self.update_compatibility_status()
    
    def on_external_variable_changed(self, external_variable_name):
        """외부변수 변경 시 호환성 검사"""
        self.update_compatibility_status()
    
    def update_compatibility_status(self):
        """호환성 상태 업데이트"""
        base_var_name = self.base_variable_combo.currentText()
        external_var_name = self.external_variable_combo.currentText()
        
        if not base_var_name or not external_var_name or external_var_name == "선택하세요":
            self.compatibility_status_label.setText("")
            return
        
        # 변수명을 ID로 변환
        base_var_id = self.get_variable_id_by_name(base_var_name)
        external_var_id = self.get_variable_id_by_name(external_var_name)
        
        if not base_var_id or not external_var_id:
            return
        
        # 호환성 검증
        is_compatible, user_msg, log_msg = self.compatibility_validator.validate_compatibility(
            base_var_id, external_var_id
        )
        
        if is_compatible:
            self.compatibility_status_label.setText(
                f'<span style="color: green;">{user_msg}</span>'
            )
            self.save_button.setEnabled(True)
        else:
            self.compatibility_status_label.setText(
                f'<span style="color: red;">{user_msg}</span>'
            )
            self.save_button.setEnabled(False)  # 저장 버튼 비활성화
        
        print(log_msg)  # 로깅
    
    def get_variable_id_by_name(self, variable_name):
        """변수명으로 ID 조회 (실제 구현 필요)"""
        name_to_id = {
            "RSI": "rsi",
            "MACD": "macd", 
            "스토캐스틱": "stochastic",
            "현재가": "current_price",
            "이동평균": "moving_average",
            "볼린저밴드": "bollinger_band",
            "거래량": "volume"
        }
        return name_to_id.get(variable_name, "")
    
    def save_condition(self):
        """조건 저장 (호환성 재검증 포함)"""
        # 최종 호환성 재검증
        base_var_id = self.get_variable_id_by_name(self.base_variable_combo.currentText())
        external_var_id = self.get_variable_id_by_name(self.external_variable_combo.currentText())
        
        if external_var_id:
            is_compatible, user_msg, log_msg = self.compatibility_validator.validate_compatibility(
                base_var_id, external_var_id
            )
            
            if not is_compatible:
                QMessageBox.warning(self, "호환성 오류", user_msg)
                return False
        
        # 기존 저장 로직 계속...
        return super().save_condition()
'''
    
    with open("variable_compatibility_ui_example.py", "w", encoding="utf-8") as f:
        f.write(example_code)
    
    print("📝 UI 통합 예제 코드가 'variable_compatibility_ui_example.py'에 저장되었습니다.")


def main():
    """메인 실행"""
    print("🔧 변수 호환성 검증 시스템")
    print("=" * 50)
    
    # 1. 테스트 실행
    test_compatibility_validation()
    
    # 2. 호환성 보고서 생성
    validator = VariableCompatibilityValidator()
    report = validator.generate_compatibility_report()
    
    # 보고서 파일로 저장
    with open("variable_compatibility_report.txt", "w", encoding="utf-8") as f:
        f.write(report)
    
    print(f"\n📋 호환성 보고서가 'variable_compatibility_report.txt'에 저장되었습니다.")
    
    # 3. UI 통합 예제 생성
    generate_ui_integration_example()
    
    print("\n🎯 다음 단계:")
    print("1. UI 통합 예제를 참고하여 실제 조건 다이얼로그에 호환성 검증 추가")
    print("2. 사용자 테스트를 통한 UX 개선")
    print("3. 성능 최적화 및 캐싱 구현")


if __name__ == "__main__":
    main()
