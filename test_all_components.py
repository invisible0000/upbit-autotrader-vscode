#!/usr/bin/env python3
"""
개별 컴포넌트 상세 테스트 스크립트
"""

from components import (
    VariableDefinitions, 
    ParameterWidgetFactory, 
    ConditionValidator, 
    ConditionBuilder,
    ConditionStorage,
    ConditionLoader,
    PreviewGenerator
)

def test_variable_definitions():
    """변수 정의 컴포넌트 테스트"""
    print("🔧 VariableDefinitions 테스트")
    print("-" * 40)
    
    vd = VariableDefinitions()
    
    # RSI 파라미터 테스트
    rsi_params = vd.get_variable_parameters("RSI")
    print(f"RSI 파라미터 수: {len(rsi_params)}")
    print(f"RSI 기간 기본값: {rsi_params['period']['default']}")
    
    # 카테고리별 변수 테스트
    categories = vd.get_category_variables()
    print(f"카테고리 수: {len(categories)}")
    for cat, vars in categories.items():
        print(f"  {cat}: {len(vars)}개 변수")
    
    print("✅ VariableDefinitions 테스트 완료\n")

def test_parameter_widget_factory():
    """파라미터 위젯 팩토리 테스트"""
    print("🏭 ParameterWidgetFactory 테스트")
    print("-" * 40)
    
    from PyQt6.QtWidgets import QApplication, QWidget, QVBoxLayout
    import sys
    
    # QApplication이 없으면 생성
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
    
    parent = QWidget()
    layout = QVBoxLayout()
    factory = ParameterWidgetFactory()
    
    # RSI 파라미터로 위젯 생성 테스트
    vd = VariableDefinitions()
    rsi_params = vd.get_variable_parameters("RSI")
    
    widgets = factory.create_parameter_widgets("RSI", rsi_params, layout)
    print(f"RSI 파라미터 위젯 생성: {len(widgets)}개")
    
    for param_name, widget in widgets.items():
        print(f"  {param_name}: {type(widget).__name__}")
    
    print("✅ ParameterWidgetFactory 테스트 완료\n")

def test_condition_validator():
    """조건 검증기 테스트"""
    print("✅ ConditionValidator 테스트")
    print("-" * 40)
    
    # 유효한 조건 테스트
    valid_condition = {
        "name": "테스트 조건",
        "description": "테스트용 조건입니다",
        "variable_id": "RSI",
        "variable_params": {"period": 14, "timeframe": "1시간"},
        "operator": ">",
        "comparison_type": "value",
        "target_value": "70"
    }
    
    is_valid, error = ConditionValidator.validate_condition_data(valid_condition)
    print(f"유효한 조건 검증: {is_valid}")
    if error:
        print(f"오류: {error}")
    
    # 이름 검증 테스트
    name_valid, name_error = ConditionValidator.validate_condition_name("")
    print(f"빈 이름 검증: {name_valid} ({name_error})")
    
    # 값 검증 테스트  
    value_valid, value_error = ConditionValidator.validate_target_value("abc", "RSI")
    print(f"잘못된 값 검증: {value_valid} ({value_error})")
    
    print("✅ ConditionValidator 테스트 완료\n")

def test_condition_builder():
    """조건 빌더 테스트"""
    print("🏗️ ConditionBuilder 테스트")
    print("-" * 40)
    
    builder = ConditionBuilder()
    
    # 실제 데이터베이스 구조에 맞는 테스트 조건
    test_condition = {
        "name": "테스트 RSI 조건",
        "description": "RSI 70 초과 시 매도 신호",
        "variable_id": "RSI",
        "variable_name": "RSI 지표",
        "variable_params": {"period": 14, "timeframe": "1시간"},
        "operator": ">",
        "comparison_type": "value",
        "target_value": "70",
        "external_variable": None,
        "trend_direction": None,
        "category": "indicator"
    }
    
    try:
        # Python 코드 생성
        python_code = builder.generate_execution_code(test_condition, language="python")
        print("생성된 Python 코드:")
        print(python_code[:200] + "..." if len(python_code) > 200 else python_code)
        
        # Pine Script 코드 생성
        pine_code = builder.generate_execution_code(test_condition, language="pine_script")
        print(f"\nPine Script 코드 생성: {len(pine_code)} 문자")
        print("✅ ConditionBuilder 테스트 완료\n")
        
    except Exception as e:
        print(f"❌ ConditionBuilder 오류: {str(e)}")
        print("데이터 구조 확인 필요\n")

def test_preview_generator():
    """미리보기 생성기 테스트"""
    print("👁️ PreviewGenerator 테스트")
    print("-" * 40)
    
    # 테스트 조건
    test_condition = {
        "variable_id": "RSI",
        "variable_name": "RSI 지표",
        "variable_params": {"period": 14},
        "operator": ">",
        "comparison_type": "value", 
        "target_value": "70",
        "name": "RSI 과매수 신호"
    }
    
    # 텍스트 미리보기
    text_preview = PreviewGenerator.generate_condition_preview(test_condition)
    print(f"조건 미리보기: {text_preview}")
    
    # 상세 미리보기
    detailed_preview = PreviewGenerator.generate_detailed_preview(test_condition)
    print(f"상세 미리보기 길이: {len(detailed_preview)} 문자")
    
    print("✅ PreviewGenerator 테스트 완료\n")

def test_storage_operations():
    """저장소 연산 테스트"""
    print("💾 Storage Operations 테스트")
    print("-" * 40)
    
    storage = ConditionStorage()
    
    # 새 조건 생성 및 저장 테스트
    new_condition = {
        "name": "테스트 조건 2",
        "description": "자동 테스트로 생성된 조건",
        "variable_id": "SMA",
        "variable_name": "단순이동평균",
        "variable_params": {"period": 20, "timeframe": "1일"},
        "operator": ">=",
        "comparison_type": "external",
        "target_value": None,
        "external_variable": {"variable_id": "EMA", "variable_name": "지수이동평균", "category": "indicator"},
        "trend_direction": "상승",
        "category": "indicator"
    }
    
    success, message, condition_id = storage.save_condition(new_condition)
    print(f"새 조건 저장: {success} (ID: {condition_id})")
    if not success:
        print(f"오류: {message}")
    
    # 총 조건 수 확인
    all_conditions = storage.get_all_conditions()
    print(f"총 저장된 조건 수: {len(all_conditions)}")
    
    print("✅ Storage Operations 테스트 완료\n")

def run_all_tests():
    """모든 테스트 실행"""
    print("🚀 컴포넌트 전체 테스트 시작")
    print("=" * 50)
    
    try:
        test_variable_definitions()
        test_parameter_widget_factory()
        test_condition_validator()
        test_condition_builder()
        test_preview_generator()
        test_storage_operations()
        
        print("🎉 모든 컴포넌트 테스트 성공!")
        
    except Exception as e:
        print(f"❌ 테스트 중 오류 발생: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    run_all_tests()
