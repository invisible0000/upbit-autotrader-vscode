#!/usr/bin/env python3
"""VOLUME 변수 카테고리 문제 디버깅"""

import sys
import os

# trigger_builder 컴포넌트 경로 추가
trigger_builder_path = r"d:\projects\upbit-autotrader-vscode\upbit_auto_trading\ui\desktop\screens\strategy_management\trigger_builder\components"
if trigger_builder_path not in sys.path:
    sys.path.insert(0, trigger_builder_path)

from compatibility_validator import CompatibilityValidator

def debug_volume_category():
    """VOLUME 변수 카테고리 문제 진단"""
    print("🔍 VOLUME 변수 카테고리 문제 진단")
    print("=" * 50)
    
    validator = CompatibilityValidator()
    
    # 1. legacy_categories에서 VOLUME 확인
    print("1. legacy_categories 확인:")
    print(f"   VOLUME: {validator.legacy_categories.get('VOLUME', 'NOT FOUND')}")
    print(f"   VOLUME_SMA: {validator.legacy_categories.get('VOLUME_SMA', 'NOT FOUND')}")
    
    # 2. variable_types에서 VOLUME 확인
    print("\n2. variable_types 확인:")
    print(f"   VOLUME: {validator.variable_types.get('VOLUME', 'NOT FOUND')}")
    print(f"   VOLUME_SMA: {validator.variable_types.get('VOLUME_SMA', 'NOT FOUND')}")
    
    # 3. legacy_categories 전체 목록
    print("\n3. legacy_categories 전체 목록:")
    for var_id, category in validator.legacy_categories.items():
        print(f"   {var_id}: {category}")
    
    # 4. 호환성 테스트
    print("\n4. 호환성 테스트:")
    result = validator.validate_compatibility('VOLUME', 'RSI')
    print(f"   VOLUME ↔ RSI: {result}")
    
    # 5. 기본 호환성 검증 세부 사항
    print("\n5. 기본 호환성 검증 세부:")
    basic_result = validator._validate_basic_compatibility('VOLUME', 'RSI')
    print(f"   Basic result: {basic_result}")

if __name__ == "__main__":
    debug_volume_category()
