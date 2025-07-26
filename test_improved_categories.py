#!/usr/bin/env python3
"""표준화 문서 기반 카테고리 개선 테스트"""

import sys
import os
from pathlib import Path

# trigger_builder 컴포넌트 경로 추가
trigger_builder_path = r"d:\projects\upbit-autotrader-vscode\upbit_auto_trading\ui\desktop\screens\strategy_management\trigger_builder\components"
if trigger_builder_path not in sys.path:
    sys.path.insert(0, trigger_builder_path)

from variable_definitions import VariableDefinitions
from compatibility_validator import CompatibilityValidator

def test_improved_categories():
    """개선된 카테고리 시스템 테스트"""
    print("🎯 표준화 문서 기반 카테고리 개선 테스트")
    print("=" * 50)
    
    # 1. 새로운 카테고리 구조 확인
    vd = VariableDefinitions()
    categories = vd.get_category_variables()
    
    print("1. 개선된 카테고리 분포:")
    for category, variables in categories.items():
        count = len(variables)
        status = "✅" if count >= 2 else "⚠️" if count == 1 else "❌"
        print(f"   {status} {category}: {count}개 - {[var[0] for var in variables]}")
    
    # 2. volume 카테고리 개선 확인
    volume_vars = categories.get('volume', [])
    print(f"\n2. volume 카테고리 개선:")
    print(f"   이전: 1개 (VOLUME만)")
    print(f"   현재: {len(volume_vars)}개 - {[var[0] for var in volume_vars]}")
    
    # 3. 호환성 검증 테스트
    validator = CompatibilityValidator()
    print(f"\n3. 호환성 검증 테스트:")
    
    test_cases = [
        ("VOLUME", "VOLUME_SMA", True, "같은 volume 카테고리"),
        ("SMA", "EMA", True, "같은 trend 카테고리"),
        ("RSI", "STOCHASTIC", True, "같은 momentum 카테고리"),
        ("ATR", "BOLLINGER_BAND", True, "같은 volatility 카테고리"),
        ("VOLUME", "RSI", False, "다른 카테고리 (volume vs momentum)")
    ]
    
    success_count = 0
    for var1, var2, expected, description in test_cases:
        try:
            is_compatible, score, reason = validator.validate_compatibility(var1, var2)
            if is_compatible == expected:
                status = "✅"
                success_count += 1
            else:
                status = "❌"
            print(f"   {status} {var1} ↔ {var2}: {is_compatible} - {description}")
        except Exception as e:
            print(f"   ❌ {var1} ↔ {var2}: 오류 - {e}")
    
    print(f"\n📊 호환성 테스트: {success_count}/{len(test_cases)} 성공")
    
    # 4. 표준화 문서 준수 확인
    print(f"\n4. 표준화 문서 준수 확인:")
    
    # 최소 카테고리 크기 확인 (2개 이상)
    sufficient_categories = sum(1 for vars in categories.values() if len(vars) >= 2)
    total_categories = len(categories)
    
    print(f"   📊 충분한 그룹 크기: {sufficient_categories}/{total_categories} 카테고리")
    print(f"   🎯 권장 지표 배치: trend(2), momentum(3), volatility(2), volume(2), price(4)")
    
    # 5. 향후 확장 가능성
    print(f"\n5. 향후 확장 가능성:")
    future_volume_indicators = ["OBV", "MFI", "VWAP"]
    print(f"   🚧 추가 예정 volume 지표: {future_volume_indicators}")
    print(f"   📈 최종 volume 카테고리 크기: {len(volume_vars) + len(future_volume_indicators)}개")

if __name__ == "__main__":
    test_improved_categories()
