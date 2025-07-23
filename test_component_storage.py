#!/usr/bin/env python3
"""
컴포넌트 저장소 테스트 스크립트
"""

from components import ConditionStorage, ConditionLoader

def test_storage_and_loader():
    """저장소와 로더 테스트"""
    print("=" * 50)
    print("📊 컴포넌트 저장소 테스트")
    print("=" * 50)
    
    # 저장소와 로더 초기화
    storage = ConditionStorage()
    loader = ConditionLoader(storage)
    
    print("\n1️⃣ 저장된 조건 확인:")
    conditions = storage.get_all_conditions()
    if conditions:
        for condition in conditions:
            print(f"  - ID {condition['id']}: {condition['name']}")
            print(f"    변수: {condition['variable_name']}")
            print(f"    연산자: {condition['operator']}")
            print(f"    대상값: {condition['target_value']}")
            print()
    else:
        print("  저장된 조건이 없습니다.")
    
    print("\n2️⃣ 실행용 조건 로드 테스트:")
    if conditions:
        condition_id = conditions[0]['id']
        exec_condition = loader.load_condition_for_execution(condition_id)
        if exec_condition:
            print(f"  ✅ 조건 로드 성공: {exec_condition['name']}")
            print(f"  📋 변수 설정: {exec_condition['variable_config']}")
            print(f"  ⚖️ 비교 설정: {exec_condition['comparison']}")
        else:
            print("  ❌ 조건 로드 실패")
    else:
        print("  테스트할 조건이 없습니다.")
    
    print("\n3️⃣ 추천 조건 테스트:")
    recommendations = loader.get_recommended_conditions("RSI")
    if recommendations:
        print("  추천 조건들:")
        for rec in recommendations[:3]:  # 상위 3개만 표시
            print(f"  - {rec['name']}")
    else:
        print("  추천할 조건이 없습니다.")
    
    print("\n4️⃣ 인기 조건 테스트:")
    popular = loader.get_popular_conditions(3)
    if popular:
        print("  인기 조건들:")
        for pop in popular:
            print(f"  - {pop['name']}")
    else:
        print("  인기 조건이 없습니다.")

if __name__ == "__main__":
    test_storage_and_loader()
