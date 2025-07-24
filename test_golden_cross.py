#!/usr/bin/env python3
"""
골든크로스 트리거 실제 동작 테스트
"""

import sqlite3
import json
import sys
import os

# 프로젝트 루트 경로 추가
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_condition_loading():
    """조건 로딩 테스트"""
    print("🔍 골든크로스 트리거 로딩 테스트")
    print("=" * 50)
    
    try:
        # condition_dialog import 시도
        from upbit_auto_trading.ui.desktop.screens.strategy_management.components.condition_dialog import ConditionDialog
        from upbit_auto_trading.ui.desktop.screens.strategy_management.components.condition_builder import ConditionBuilder
        from upbit_auto_trading.ui.desktop.screens.strategy_management.components.condition_storage import ConditionStorage
        
        print("✅ 모듈 import 성공")
        
        # DB에서 골든크로스 트리거 로드
        storage = ConditionStorage()
        
        # ID 9번 트리거 (골든크로스) 로드
        condition_id = 9
        condition_data = storage.load_condition_by_id(condition_id)
        
        if condition_data:
            print(f"\n📋 트리거 ID {condition_id} 로드 결과:")
            print(f"   이름: {condition_data.get('name')}")
            print(f"   변수 ID: {condition_data.get('variable_id')}")
            print(f"   비교값: {condition_data.get('target_value')}")
            print(f"   비교타입: {condition_data.get('comparison_type')}")
            print(f"   외부변수: {condition_data.get('external_variable')}")
            
            # 조건 빌더로 실행 코드 생성 시도
            builder = ConditionBuilder()
            
            print(f"\n🔧 조건 빌더 테스트:")
            
            try:
                execution_code = builder.generate_execution_code(condition_data)
                print("✅ 실행 코드 생성 성공:")
                print("   " + execution_code.replace("\n", "\n   "))
            except Exception as e:
                print(f"❌ 실행 코드 생성 실패: {e}")
                import traceback
                traceback.print_exc()
            
            # UI 로딩 시뮬레이션
            print(f"\n🖥️  UI 로딩 시뮬레이션:")
            
            comparison_type = condition_data.get('comparison_type', 'fixed')
            external_variable = condition_data.get('external_variable')
            target_value = condition_data.get('target_value')
            
            if comparison_type == 'external' and external_variable:
                print("   → 외부변수 모드로 로드됨")
                ext_var = json.loads(external_variable) if isinstance(external_variable, str) else external_variable
                print(f"   → 외부변수: {ext_var}")
            else:
                print("   → 고정값 모드로 로드됨")
                print(f"   → 비교값 입력창에 표시될 값: '{target_value}'")
                
                if target_value and any(char.isalpha() for char in str(target_value)):
                    print("   ⚠️  비교값에 문자가 포함되어 있습니다!")
                    print("   ⚠️  이는 변수명일 가능성이 있으나 고정값으로 처리됩니다.")
        else:
            print(f"❌ 트리거 ID {condition_id}를 찾을 수 없습니다.")
            
    except ImportError as e:
        print(f"❌ 모듈 import 실패: {e}")
    except Exception as e:
        print(f"❌ 테스트 실패: {e}")
        import traceback
        traceback.print_exc()

def test_cross_type_handling():
    """cross_up/cross_down 타입 처리 테스트"""
    print("\n🔍 cross_up/cross_down 타입 처리 분석")
    print("=" * 50)
    
    try:
        from upbit_auto_trading.ui.desktop.screens.strategy_management.components.condition_builder import ConditionBuilder
        
        builder = ConditionBuilder()
        
        # 골든크로스 트리거 시뮬레이션
        test_condition = {
            "name": "테스트 골든크로스",
            "description": "테스트용 골든크로스",
            "variable_id": "ma_cross_20_60",
            "variable_name": "20-60일 MA 크로스",
            "variable_params": {"short_period": 20, "long_period": 60},
            "operator": ">",
            "comparison_type": "cross_up",
            "target_value": "ma_60",
            "external_variable": None,
            "trend_direction": "static",
            "category": "custom"
        }
        
        print("📋 테스트 조건:")
        for key, value in test_condition.items():
            print(f"   {key}: {value}")
        
        print("\n🔧 실행 코드 생성 시도:")
        
        try:
            execution_code = builder.generate_execution_code(test_condition)
            print("✅ 성공!")
            print("📄 생성된 코드:")
            print("   " + execution_code.replace("\n", "\n   "))
        except Exception as e:
            print(f"❌ 실패: {e}")
            print("💡 이는 ma_cross_20_60 변수가 정의되지 않았기 때문일 수 있습니다.")
            
    except Exception as e:
        print(f"❌ 테스트 실패: {e}")

def analyze_conclusion():
    """분석 결론"""
    print("\n" + "=" * 60)
    print("📊 분석 결론")
    print("=" * 60)
    
    print("""
🎯 발견된 사실들:

1. 데이터베이스 저장 방식:
   - 골든크로스(ID:9): comparison_type='cross_up', target_value='ma_60'
   - 데드크로스(ID:10): comparison_type='cross_down', target_value='ma_60'
   - 이는 정상적인 'external' 타입과 다른 특별한 방식

2. 변수 정의 누락:
   - variable_definitions.py에 'ma_cross_20_60' 변수가 정의되지 않음
   - 'cross_up', 'cross_down' 비교 타입도 표준 UI에서 지원하지 않음

3. UI 로딩 동작:
   - comparison_type이 'external'이 아니므로 고정값 모드로 로드
   - target_value 'ma_60'이 비교값 입력창에 그대로 표시됨
   - 사용자에게는 이상하게 보이지만 시스템적으로는 '동작'함

🤔 추론:

A) 에이전트의 직접 DB 조작:
   - 에이전트가 표준 UI를 거치지 않고 DB에 직접 트리거를 삽입
   - 'cross_up', 'cross_down'은 에이전트만의 특별한 비교 타입
   - 실제 실행 엔진에서는 이를 처리하는 별도 로직이 있을 수 있음

B) 미완성된 크로스 기능:
   - 크로스 패턴을 지원하려던 기능이 중간에 중단됨
   - UI에서는 지원하지 않지만 DB 스키마나 백엔드에는 잔재가 남음

C) 실제 동작하지 않을 가능성:
   - target_value 'ma_60'을 문자열로 비교하면 오류 발생
   - 해당 트리거들은 실제로는 동작하지 않을 수 있음

🎯 권장사항:

1. 올바른 외부변수 방식으로 재생성:
   - 기존 골든크로스/데드크로스 트리거 삭제
   - 표준 UI의 외부변수 기능을 사용해서 재등록
   - SMA(20) > SMA(60) 형태로 구성

2. 테스트 실행:
   - 기존 트리거들이 실제로 동작하는지 백테스트로 확인
   - 오류 발생 시 즉시 삭제하고 재등록

3. 시스템 정리:
   - 미지원 comparison_type들에 대한 명확한 처리 방안 수립
   - 에이전트의 직접 DB 조작 방지 방안 검토
    """)

if __name__ == "__main__":
    print("🚀 골든크로스 트리거 실제 동작 테스트 시작!")
    test_condition_loading()
    test_cross_type_handling()
    analyze_conclusion()
    print("\n✅ 테스트 완료!")
