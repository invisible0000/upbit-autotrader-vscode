#!/usr/bin/env python3
"""
Step 4.1: 조건 다이얼로그 연동 테스트
새로운 지표들(ATR, VOLUME_SMA)이 조건 다이얼로그에서 정상적으로 인식되고 작동하는지 테스트
"""

import sys
import os
from pathlib import Path

# 프로젝트 루트 경로 추가
sys.path.insert(0, str(Path(__file__).parent))

from PyQt6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QPushButton, QMessageBox
from PyQt6.QtCore import Qt

# 조건 다이얼로그 import
try:
    from upbit_auto_trading.ui.desktop.screens.strategy_management.trigger_builder.components.condition_dialog import ConditionDialog
    from upbit_auto_trading.ui.desktop.screens.strategy_management.trigger_builder.components.variable_definitions import VariableDefinitions
except ImportError as e:
    print(f"❌ 조건 다이얼로그 import 실패: {e}")
    sys.exit(1)

class TestConditionDialogWindow(QMainWindow):
    """조건 다이얼로그 테스트용 메인 윈도우"""
    
    def __init__(self):
        super().__init__()
        
        self.setWindowTitle("🧪 조건 다이얼로그 지표 연동 테스트")
        self.setGeometry(100, 100, 800, 600)
        
        # 중앙 위젯
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        layout = QVBoxLayout()
        central_widget.setLayout(layout)
        
        # 테스트 버튼들
        self.create_test_buttons(layout)
        
        # 조건 다이얼로그
        self.condition_dialog = ConditionDialog()
        layout.addWidget(self.condition_dialog)
        
        # 변수 정의 인스턴스
        self.var_definitions = VariableDefinitions()
        
    def create_test_buttons(self, layout):
        """테스트 버튼들 생성"""
        
        # 1. 지표 범주 확인
        btn_categories = QPushButton("📊 1. 지표 범주 확인")
        btn_categories.clicked.connect(self.test_indicator_categories)
        layout.addWidget(btn_categories)
        
        # 2. 새 지표 인식 확인
        btn_new_indicators = QPushButton("🆕 2. 새 지표 인식 확인 (ATR, VOLUME_SMA)")
        btn_new_indicators.clicked.connect(self.test_new_indicators)
        layout.addWidget(btn_new_indicators)
        
        # 3. 지표 파라미터 확인
        btn_parameters = QPushButton("⚙️ 3. 지표 파라미터 확인")
        btn_parameters.clicked.connect(self.test_indicator_parameters)
        layout.addWidget(btn_parameters)
        
        # 4. 호환성 검증 확인
        btn_compatibility = QPushButton("🔗 4. 호환성 검증 확인")
        btn_compatibility.clicked.connect(self.test_compatibility_check)
        layout.addWidget(btn_compatibility)
        
        # 5. 종합 테스트
        btn_comprehensive = QPushButton("🎯 5. 종합 테스트 실행")
        btn_comprehensive.clicked.connect(self.run_comprehensive_test)
        layout.addWidget(btn_comprehensive)
        
    def test_indicator_categories(self):
        """지표 범주 확인 테스트"""
        try:
            category_variables = self.var_definitions.get_category_variables()
            
            # 결과 분석
            total_categories = len(category_variables)
            indicator_count = len(category_variables.get('indicator', []))
            
            result = f"""
📊 **지표 범주 테스트 결과**

✅ 전체 범주 수: {total_categories}
✅ 지표 범주 변수 수: {indicator_count}

📋 **지표 범주 세부 목록**:
"""
            
            if 'indicator' in category_variables:
                for var_id, var_name in category_variables['indicator']:
                    result += f"  • {var_id}: {var_name}\n"
            else:
                result += "  ❌ 지표 범주가 없습니다!"
            
            self.show_result("지표 범주 테스트", result)
            
        except Exception as e:
            self.show_error("지표 범주 테스트 실패", str(e))
    
    def test_new_indicators(self):
        """새 지표 인식 확인 테스트"""
        try:
            category_variables = self.var_definitions.get_category_variables()
            indicator_vars = category_variables.get('indicator', [])
            
            # 새 지표 확인
            new_indicators = ['ATR', 'VOLUME_SMA']
            found_indicators = []
            missing_indicators = []
            
            for var_id, var_name in indicator_vars:
                if var_id in new_indicators:
                    found_indicators.append(f"{var_id}: {var_name}")
                    
            for indicator in new_indicators:
                if not any(var_id == indicator for var_id, _ in indicator_vars):
                    missing_indicators.append(indicator)
            
            result = f"""
🆕 **새 지표 인식 테스트 결과**

✅ 발견된 새 지표 ({len(found_indicators)}/2):
"""
            for indicator in found_indicators:
                result += f"  • {indicator}\n"
            
            if missing_indicators:
                result += f"\n❌ 누락된 지표 ({len(missing_indicators)}):\n"
                for indicator in missing_indicators:
                    result += f"  • {indicator}\n"
            else:
                result += "\n🎉 모든 새 지표가 정상 인식됨!"
            
            self.show_result("새 지표 인식 테스트", result)
            
        except Exception as e:
            self.show_error("새 지표 인식 테스트 실패", str(e))
    
    def test_indicator_parameters(self):
        """지표 파라미터 확인 테스트"""
        try:
            test_indicators = ['ATR', 'VOLUME_SMA', 'SMA', 'EMA']
            
            result = "⚙️ **지표 파라미터 테스트 결과**\n\n"
            
            for indicator in test_indicators:
                params = self.var_definitions.get_variable_parameters(indicator)
                
                if params:
                    result += f"✅ **{indicator}**:\n"
                    for param_name, param_config in params.items():
                        param_type = param_config.get('type', 'unknown')
                        default_val = param_config.get('default', 'N/A')
                        result += f"  • {param_name} ({param_type}): {default_val}\n"
                    result += "\n"
                else:
                    result += f"❌ **{indicator}**: 파라미터 정의 없음\n\n"
            
            self.show_result("지표 파라미터 테스트", result)
            
        except Exception as e:
            self.show_error("지표 파라미터 테스트 실패", str(e))
    
    def test_compatibility_check(self):
        """호환성 검증 확인 테스트"""
        try:
            # 통합된 호환성 검증기 사용 (프로젝트 루트에서 import)
            import sys
            sys.path.insert(0, os.path.dirname(__file__))
            from compatibility_validator import CompatibilityValidator
            
            validator = CompatibilityValidator()
            
            # 조건 다이얼로그의 실제 변수 정의 확인
            category_variables = self.var_definitions.get_category_variables()
            indicator_vars = category_variables.get('indicator', [])
            
            result = "🔗 **호환성 검증 테스트 결과**\n\n"
            result += f"📊 **사용 가능한 지표들** ({len(indicator_vars)}개):\n"
            for var_id, var_name in indicator_vars:
                result += f"  • {var_id}: {var_name}\n"
            result += "\n"
            
            # 실제 존재하는 지표들로 테스트
            if len(indicator_vars) >= 2:
                # 첫 번째와 두 번째 지표로 호환성 테스트
                var1_id, var1_name = indicator_vars[0]
                var2_id, var2_name = indicator_vars[1]
                
                is_compatible, score, reason = validator.validate_compatibility(var1_id, var2_id)
                
                status = "✅" if is_compatible else "❌"
                result += f"{status} **{var1_name} ↔ {var2_name} 호환성**\n"
                result += f"  • 호환성: {is_compatible} (점수: {score}%)\n"
                result += f"  • 사유: {reason}\n\n"
                
                # ATR과 VOLUME_SMA가 있는지 확인
                atr_found = any(var_id == 'ATR' for var_id, _ in indicator_vars)
                volume_sma_found = any(var_id == 'VOLUME_SMA' for var_id, _ in indicator_vars)
                
                result += f"🆕 **새 지표 호환성 테스트**:\n"
                result += f"  • ATR 발견: {'✅' if atr_found else '❌'}\n"
                result += f"  • VOLUME_SMA 발견: {'✅' if volume_sma_found else '❌'}\n"
                
                if atr_found and len(indicator_vars) > 2:
                    other_var_id, other_var_name = indicator_vars[2]
                    is_compatible, score, reason = validator.validate_compatibility('ATR', other_var_id)
                    result += f"  • ATR ↔ {other_var_name}: {is_compatible} ({score}%)\n"
            else:
                result += "❌ 테스트할 지표가 부족합니다."
            
            self.show_result("호환성 검증 테스트", result)
            
        except ImportError as e:
            self.show_error("호환성 검증 테스트 실패", f"모듈 import 실패: {e}")
        except Exception as e:
            self.show_error("호환성 검증 테스트 실패", str(e))
    
    def run_comprehensive_test(self):
        """종합 테스트 실행"""
        try:
            results = []
            
            # 1. 지표 범주 확인
            category_variables = self.var_definitions.get_category_variables()
            indicator_count = len(category_variables.get('indicator', []))
            results.append(f"지표 변수 수: {indicator_count}")
            
            # 2. 새 지표 확인
            new_indicators = ['ATR', 'VOLUME_SMA']
            found_count = 0
            for var_id, _ in category_variables.get('indicator', []):
                if var_id in new_indicators:
                    found_count += 1
            results.append(f"새 지표 인식: {found_count}/2")
            
            # 3. 파라미터 확인
            param_indicators = ['ATR', 'VOLUME_SMA']
            param_count = 0
            for indicator in param_indicators:
                params = self.var_definitions.get_variable_parameters(indicator)
                if params:
                    param_count += 1
            results.append(f"파라미터 정의: {param_count}/2")
            
            # 4. 호환성 검증
            try:
                import sys
                sys.path.insert(0, os.path.dirname(__file__))
                from compatibility_validator import CompatibilityValidator
                validator = CompatibilityValidator()
                is_compatible, _, _ = validator.validate_compatibility("RSI", "SMA")
                compatibility_status = "작동" if is_compatible is not None else "실패"
                results.append(f"호환성 검증: {compatibility_status}")
            except Exception:
                results.append("호환성 검증: 실패")
            
            # 결과 종합
            success_count = len([r for r in results if not r.endswith("실패") and not r.endswith("0/2")])
            total_tests = len(results)
            
            result = f"""
🎯 **종합 테스트 결과**

📊 **성공률**: {success_count}/{total_tests} ({success_count/total_tests*100:.1f}%)

📋 **세부 결과**:
"""
            for test_result in results:
                status = "✅" if not test_result.endswith("실패") and not test_result.endswith("0/2") else "❌"
                result += f"  {status} {test_result}\n"
            
            if success_count == total_tests:
                result += "\n🎉 **모든 테스트 통과! 조건 다이얼로그 연동 성공!**"
            else:
                result += f"\n⚠️ **{total_tests - success_count}개 테스트 실패. 추가 점검 필요.**"
            
            self.show_result("종합 테스트", result)
            
        except Exception as e:
            self.show_error("종합 테스트 실패", str(e))
    
    def show_result(self, title, message):
        """결과 표시"""
        msg_box = QMessageBox()
        msg_box.setWindowTitle(title)
        msg_box.setText(message)
        msg_box.setIcon(QMessageBox.Icon.Information)
        msg_box.exec()
    
    def show_error(self, title, error):
        """에러 표시"""
        msg_box = QMessageBox()
        msg_box.setWindowTitle(title)
        msg_box.setText(f"❌ 오류 발생:\n{error}")
        msg_box.setIcon(QMessageBox.Icon.Critical)
        msg_box.exec()

def main():
    """메인 함수"""
    app = QApplication(sys.argv)
    
    # 애플리케이션 설정
    app.setApplicationName("조건 다이얼로그 지표 연동 테스트")
    app.setApplicationVersion("1.0")
    
    try:
        # 메인 윈도우 생성 및 표시
        window = TestConditionDialogWindow()
        window.show()
        
        print("🧪 조건 다이얼로그 지표 연동 테스트 시작")
        print("   - ATR, VOLUME_SMA 지표 인식 확인")
        print("   - 파라미터 정의 확인") 
        print("   - 호환성 검증 확인")
        print("   - UI 연동 상태 확인")
        
        sys.exit(app.exec())
        
    except Exception as e:
        print(f"❌ 애플리케이션 시작 실패: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
