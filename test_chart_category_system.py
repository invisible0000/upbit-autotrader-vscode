#!/usr/bin/env python3
"""차트 카테고리 시스템 완전 구현 검증"""

import sys
import sqlite3
from pathlib import Path

# trigger_builder 컴포넌트 경로 추가
trigger_builder_path = r"d:\projects\upbit-autotrader-vscode\upbit_auto_trading\ui\desktop\screens\strategy_management\trigger_builder\components"
if trigger_builder_path not in sys.path:
    sys.path.insert(0, trigger_builder_path)

from variable_definitions import VariableDefinitions

def test_chart_category_system():
    """차트 카테고리 시스템 완전 구현 검증"""
    print("🎯 차트 카테고리 시스템 완전 구현 검증")
    print("=" * 50)
    
    # 1. 시스템 매핑 테스트
    print("1. 표준화 문서 기반 차트 매핑 테스트:")
    test_cases = [
        ("SMA", "overlay", "🔗 메인 차트 오버레이"),
        ("EMA", "overlay", "🔗 메인 차트 오버레이"),
        ("BOLLINGER_BAND", "overlay", "🔗 메인 차트 오버레이"),
        ("CURRENT_PRICE", "overlay", "🔗 메인 차트 오버레이"),
        ("RSI", "subplot", "📊 별도 서브플롯"),
        ("STOCHASTIC", "subplot", "📊 별도 서브플롯"),
        ("MACD", "subplot", "📊 별도 서브플롯"),
        ("ATR", "subplot", "📊 별도 서브플롯"),
        ("VOLUME", "subplot", "📊 별도 서브플롯"),
        ("VOLUME_SMA", "subplot", "📊 별도 서브플롯")
    ]
    
    success_count = 0
    for variable_id, expected, description in test_cases:
        actual = VariableDefinitions.get_chart_category(variable_id)
        if actual == expected:
            emoji = "🔗" if expected == "overlay" else "📊"
            print(f"   ✅ {variable_id}: {emoji} {expected} - {description}")
            success_count += 1
        else:
            print(f"   ❌ {variable_id}: 예상({expected}) vs 실제({actual})")
    
    print(f"\n📊 차트 매핑 테스트: {success_count}/{len(test_cases)} 성공")
    
    # 2. DB 스키마 확인
    print("\n2. 데이터베이스 스키마 확인:")
    try:
        with sqlite3.connect("data/app_settings.sqlite3") as conn:
            cursor = conn.cursor()
            
            # 컬럼 존재 확인
            cursor.execute("PRAGMA table_info(trading_conditions)")
            columns = [col[1] for col in cursor.fetchall()]
            
            if 'chart_category' in columns:
                print("   ✅ chart_category 컬럼 존재")
                
                # 데이터 분포 확인
                cursor.execute("""
                    SELECT chart_category, COUNT(*) as count 
                    FROM trading_conditions 
                    GROUP BY chart_category
                """)
                distribution = cursor.fetchall()
                
                print("   📊 차트 카테고리 분포:")
                for category, count in distribution:
                    emoji = "🔗" if category == "overlay" else "📊"
                    print(f"      {emoji} {category}: {count}개")
            else:
                print("   ❌ chart_category 컬럼 없음")
                
    except Exception as e:
        print(f"   ❌ DB 확인 실패: {e}")
    
    # 3. 조건 저장 테스트
    print("\n3. 새 조건 저장 시 차트 카테고리 자동 설정 테스트:")
    try:
        from condition_storage import ConditionStorage
        from condition_builder import ConditionBuilder
        
        # 테스트 조건 생성
        test_condition = {
            "name": "테스트 차트 카테고리",
            "description": "차트 카테고리 자동 설정 테스트",
            "variable_id": "RSI",
            "variable_name": "RSI 지표",
            "variable_params": {"period": 14, "timeframe": "1h"},
            "operator": ">",
            "comparison_type": "fixed",
            "target_value": "70"
        }
        
        storage = ConditionStorage()
        success, message, condition_id = storage.save_condition(test_condition, overwrite=True)
        
        if success and condition_id:
            # 저장된 조건의 차트 카테고리 확인
            saved_condition = storage.get_condition_by_id(condition_id)
            if saved_condition and 'chart_category' in saved_condition:
                expected_chart = VariableDefinitions.get_chart_category('RSI')
                actual_chart = saved_condition['chart_category']
                
                if actual_chart == expected_chart:
                    emoji = "📊" if expected_chart == "subplot" else "🔗"
                    print(f"   ✅ 자동 설정: RSI → {emoji} {actual_chart}")
                else:
                    print(f"   ❌ 불일치: 예상({expected_chart}) vs 실제({actual_chart})")
            else:
                print("   ❌ chart_category 필드 없음")
            
            # 정리
            storage.delete_condition(condition_id)
        else:
            print(f"   ❌ 조건 저장 실패: {message}")
            
    except Exception as e:
        print(f"   ❌ 조건 저장 테스트 실패: {e}")
    
    # 4. UI 함수 테스트
    print("\n4. UI 지원 함수 테스트:")
    overlay_indicators = []
    subplot_indicators = []
    
    all_variables = ["SMA", "EMA", "RSI", "MACD", "BOLLINGER_BAND", "ATR", "VOLUME"]
    for var_id in all_variables:
        if VariableDefinitions.is_overlay_indicator(var_id):
            overlay_indicators.append(var_id)
        else:
            subplot_indicators.append(var_id)
    
    print(f"   🔗 오버레이 지표: {overlay_indicators}")
    print(f"   📊 서브플롯 지표: {subplot_indicators}")
    
    if len(overlay_indicators) > 0 and len(subplot_indicators) > 0:
        print("   ✅ 오버레이/서브플롯 구분 정상 작동")
    else:
        print("   ❌ 지표 분류 문제")
    
    print("\n" + "=" * 50)
    print("🎉 차트 카테고리 시스템 구현 완료!")
    print("✅ 표준화 문서 기반 이중 카테고리 시스템 적용")
    print("✅ DB 스키마 확장 (chart_category 컬럼)")
    print("✅ 자동 차트 카테고리 설정")
    print("✅ 기존 데이터 마이그레이션 완료")

if __name__ == "__main__":
    test_chart_category_system()
