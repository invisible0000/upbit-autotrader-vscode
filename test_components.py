#!/usr/bin/env python3
"""
컴포넌트 테스트 스크립트
"""

from components import ConditionStorage, ConditionLoader

def main():
    try:
        storage = ConditionStorage()
        loader = ConditionLoader(storage)

        print('📊 저장된 조건 확인:')
        conditions = storage.get_all_conditions()
        for condition in conditions:
            print(f'  - {condition["id"]}: {condition["name"]} ({condition["variable_name"]})')

        print('\n📈 실행용 조건 로드 테스트:')
        exec_condition = loader.load_condition_for_execution(1)
        if exec_condition:
            if 'error' in exec_condition:
                print(f'  ❌ 조건 로드 오류: {exec_condition["message"]}')
            else:
                print(f'  ✅ 조건 로드 성공: {exec_condition["name"]}')
                print(f'  📋 변수 설정: {exec_condition["variable_config"]}')
                print(f'  ⚖️ 비교 설정: {exec_condition["comparison"]}')
        else:
            print('  ❌ 조건 로드 실패')

        print('\n📈 통계 정보:')
        stats = storage.get_condition_statistics()
        print(f'  - 총 조건 수: {stats.get("total_conditions", 0)}')
        print(f'  - 카테고리별 분포: {stats.get("category_distribution", {})}')
        print(f'  - 변수별 분포: {stats.get("variable_distribution", {})}')

    except Exception as e:
        print(f'❌ 오류 발생: {str(e)}')
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
