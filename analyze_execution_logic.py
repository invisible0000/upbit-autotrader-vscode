#!/usr/bin/env python3
"""
전략 실행 엔진의 조건 해석 로직 조사
비교값에 'ma_60'과 같은 변수명이 있을 때 어떻게 처리되는지 확인
"""

import os
import sys

def find_strategy_execution_files():
    """전략 실행 관련 파일들 찾기"""
    print("🔍 전략 실행 엔진 파일 검색 중...")
    
    search_patterns = [
        "strategy_execution",
        "condition_evaluator", 
        "condition_checker",
        "trading_engine",
        "backtest_engine",
        "condition_interpreter"
    ]
    
    found_files = []
    
    # 프로젝트 루트에서 검색
    for root, dirs, files in os.walk("."):
        for file in files:
            if file.endswith(".py"):
                file_path = os.path.join(root, file)
                file_name_lower = file.lower()
                
                for pattern in search_patterns:
                    if pattern in file_name_lower:
                        found_files.append(file_path)
                        break
    
    return found_files

def analyze_condition_parsing():
    """조건 파싱 로직 분석"""
    files = find_strategy_execution_files()
    
    print(f"📋 발견된 관련 파일: {len(files)}개")
    for file in files:
        print(f"   - {file}")
    
    print("\n" + "=" * 60)
    print("🔍 주요 분석 포인트:")
    print("=" * 60)
    
    print("""
1. 비교값 해석 로직:
   - target_value='ma_60'을 문자열로 처리하는가?
   - 아니면 변수명으로 인식해서 해당 변수의 값을 가져오는가?

2. comparison_type별 처리:
   - 'cross_up', 'cross_down': 크로스 패턴 전용 타입인가?
   - 'external': 외부변수를 참조하는 타입
   - 'fixed': 고정값 비교 타입
   - 'value': 일반 값 비교 타입

3. 예상 시나리오:
   A) 'ma_60'을 문자열로 해석 → 오류 발생 또는 비교 실패
   B) 'ma_60'을 변수명으로 해석 → 60일 이동평균 값을 가져와서 비교
   C) cross_up/cross_down 타입에서는 특별한 처리 로직이 있을 수 있음

4. 발견된 패턴:
   - ID 9,10: ma_cross_20_60 변수에서 ma_60과 비교 (골든크로스/데드크로스)
   - ID 13,14: macd_12_26_9 변수에서 macd_signal과 비교 (MACD 크로스)
   
   이는 '크로스' 패턴을 위한 특별한 구현 방식일 가능성이 높음!
    """)

def check_variable_definitions():
    """변수 정의에서 크로스 관련 로직 확인"""
    print("\n" + "=" * 60)  
    print("🔍 variable_definitions.py 확인")
    print("=" * 60)
    
    var_def_path = "upbit_auto_trading/ui/desktop/screens/strategy_management/components/variable_definitions.py"
    
    if os.path.exists(var_def_path):
        print(f"✅ {var_def_path} 파일 발견")
        print("📋 ma_cross_20_60 변수가 정의되어 있는지 확인해야 함")
        print("📋 해당 변수가 ma_60을 내부적으로 참조하는 로직이 있는지 확인 필요")
    else:
        print(f"❌ {var_def_path} 파일을 찾을 수 없음")

def analyze_cross_pattern():
    """크로스 패턴 분석"""
    print("\n" + "=" * 60)
    print("🎯 크로스 패턴 동작 방식 추론")
    print("=" * 60)
    
    print("""
📊 발견된 크로스 트리거 분석:

1. 골든크로스 (ID: 9):
   - variable_id: ma_cross_20_60
   - target_value: ma_60
   - comparison_type: cross_up
   - 의미: 20일 MA가 60일 MA를 상향 돌파

2. 데드크로스 (ID: 10): 
   - variable_id: ma_cross_20_60
   - target_value: ma_60
   - comparison_type: cross_down
   - 의미: 20일 MA가 60일 MA를 하향 돌파

🤔 동작 방식 추론:

A) 첫 번째 가능성 - 내장 크로스 로직:
   - ma_cross_20_60 변수가 자체적으로 20일 MA와 60일 MA의 관계를 계산
   - target_value 'ma_60'은 실제로는 무시되거나 참조값으로만 사용
   - comparison_type이 'cross_up'/'cross_down'일 때 특별한 크로스 검출 로직 실행

B) 두 번째 가능성 - 동적 변수 참조:
   - target_value 'ma_60'을 실제 변수명으로 해석
   - 런타임에 60일 이동평균 값을 계산해서 가져옴
   - ma_cross_20_60에서 20일 MA를 구하고, ma_60에서 60일 MA를 구해서 비교

C) 세 번째 가능성 - 에이전트의 임시 구현:
   - 정상적인 시스템 설계가 아닌 임시방편으로 구현된 방식
   - 실제로는 동작하지 않거나 오류가 발생할 수 있음

🎯 검증 방법:
1. 전략 실행 엔진에서 해당 트리거들이 실제로 실행되는지 확인
2. 로그를 통해 ma_60이 어떻게 해석되는지 확인  
3. 크로스 패턴이 정상적으로 검출되는지 백테스트로 확인
    """)

if __name__ == "__main__":
    print("🚀 전략 실행 엔진 조건 해석 로직 조사 시작!")
    find_strategy_execution_files()
    analyze_condition_parsing()
    check_variable_definitions()
    analyze_cross_pattern()
    print("\n✅ 분석 완료!")
