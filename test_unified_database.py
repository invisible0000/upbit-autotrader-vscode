#!/usr/bin/env python3
"""
통합 데이터베이스 테스트 스크립트
"""

import sys
import os

# 프로젝트 루트를 경로에 추가
sys.path.append('.')

from components.condition_storage import ConditionStorage

def test_unified_database():
    """통합 데이터베이스 테스트"""
    
    print("🧪 통합 데이터베이스 테스트 시작")
    print("=" * 50)
    
    try:
        # ConditionStorage 인스턴스 생성
        storage = ConditionStorage()
        print("✅ ConditionStorage 인스턴스 생성 성공")
        
        # 모든 조건 조회
        conditions = storage.get_all_conditions()
        print(f"📋 로드된 조건: {len(conditions)}개")
        
        for i, condition in enumerate(conditions, 1):
            name = condition.get('name', 'Unknown')
            category = condition.get('category', 'Unknown')
            variable = condition.get('variable_name', 'Unknown')
            print(f"  {i}. {name} ({category}) - {variable}")
        
        # 카테고리별 조건 조회 테스트
        print("\n📊 카테고리별 조건:")
        categories = ['indicator', 'custom', 'technical']
        
        for category in categories:
            cat_conditions = storage.get_conditions_by_category(category)
            print(f"  {category}: {len(cat_conditions)}개")
        
        print("\n✅ 통합 데이터베이스 테스트 성공!")
        return True
        
    except Exception as e:
        print(f"❌ 테스트 실패: {str(e)}")
        return False

def test_original_database():
    """기존 데이터베이스와 비교 테스트"""
    
    print("\n🔍 기존 데이터베이스와 비교...")
    
    try:
        # 기존 데이터베이스로 테스트
        old_storage = ConditionStorage("data/trading_conditions.db")
        old_conditions = old_storage.get_all_conditions()
        
        # 통합 데이터베이스로 테스트
        new_storage = ConditionStorage("upbit_trading_unified.db")
        new_conditions = new_storage.get_all_conditions()
        
        print(f"  기존 DB 조건 수: {len(old_conditions)}개")
        print(f"  통합 DB 조건 수: {len(new_conditions)}개")
        
        # 조건 이름 비교
        old_names = set(c.get('name', '') for c in old_conditions)
        new_names = set(c.get('name', '') for c in new_conditions)
        
        missing_in_new = old_names - new_names
        extra_in_new = new_names - old_names
        
        if missing_in_new:
            print(f"  ⚠️ 통합 DB에서 누락된 조건: {missing_in_new}")
        
        if extra_in_new:
            print(f"  ℹ️ 통합 DB에만 있는 조건: {extra_in_new}")
        
        if not missing_in_new and not extra_in_new:
            print("  ✅ 모든 조건이 올바르게 마이그레이션됨")
        
        return len(missing_in_new) == 0
        
    except Exception as e:
        print(f"  ❌ 비교 테스트 실패: {str(e)}")
        return False

if __name__ == "__main__":
    # 통합 데이터베이스 테스트
    unified_test_ok = test_unified_database()
    
    # 기존 데이터베이스와 비교
    comparison_ok = test_original_database()
    
    print("\n" + "=" * 50)
    if unified_test_ok and comparison_ok:
        print("🎉 모든 테스트 통과!")
        print("✅ 통합 데이터베이스를 사용할 준비가 완료되었습니다.")
    else:
        print("❌ 일부 테스트 실패")
        print("⚠️ 문제를 해결한 후 다시 테스트하세요.")
