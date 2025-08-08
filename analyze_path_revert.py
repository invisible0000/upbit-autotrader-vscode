#!/usr/bin/env python3
"""
경로 변경 후 원래 경로로 돌아가는 문제 분석 스크립트
DDD 시스템의 로직을 추적합니다.
"""

import yaml
import sys
import os

def analyze_path_revert_issue():
    print("=== 경로 변경 후 원래 경로 복귀 문제 분석 ===\n")

    # 1. 현재 database_config.yaml 상태 확인
    print("1️⃣ database_config.yaml 현재 상태")
    try:
        with open('config/database_config.yaml', 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)

        databases = config.get('databases', {})
        for db_type, conf in databases.items():
            path = conf.get('path', 'N/A')
            last_modified = conf.get('last_modified', 'N/A')
            print(f"   {db_type}: {path}")
            print(f"     마지막 수정: {last_modified}")
        print()
    except Exception as e:
        print(f"❌ 설정 파일 읽기 실패: {e}\n")

    # 2. DDD 서비스에서 실제 로드하는 경로 확인
    print("2️⃣ DDD DatabasePathService 실제 경로")
    try:
        sys.path.append('.')
        from upbit_auto_trading.domain.services.database_path_service import DatabasePathService

        service = DatabasePathService()
        paths = service.get_all_database_paths()

        print(f"   서비스 인스턴스: {type(service).__name__}")
        print(f"   로드된 경로 수: {len(paths)}")

        for db_type, path in paths.items():
            print(f"   {db_type}: {path}")
        print()

    except Exception as e:
        print(f"❌ DDD 서비스 확인 실패: {e}\n")

    # 3. config.yaml의 database 섹션 확인
    print("3️⃣ config.yaml의 database 섹션 확인")
    try:
        with open('config/config.yaml', 'r', encoding='utf-8') as f:
            main_config = yaml.safe_load(f)

        database_section = main_config.get('database', {})
        if database_section:
            print(f"   database 섹션 존재: {len(database_section)} 항목")
            for key, value in database_section.items():
                print(f"   {key}: {value}")
        else:
            print("   database 섹션 없음")
        print()

    except Exception as e:
        print(f"❌ config.yaml 확인 실패: {e}\n")

    # 4. Repository 클래스의 로직 확인
    print("4️⃣ DatabaseConfigRepository 로직 확인")
    try:
        from upbit_auto_trading.infrastructure.repositories.database_config_repository import DatabaseConfigRepository

        repo = DatabaseConfigRepository()
        print(f"   Repository 인스턴스: {type(repo).__name__}")

        # 모든 구성 로드
        all_configs = repo.get_all_database_configurations()
        print(f"   로드된 구성 수: {len(all_configs)}")

        for db_type, config_obj in all_configs.items():
            print(f"   {db_type}: {config_obj.path}")
        print()

    except Exception as e:
        print(f"❌ Repository 확인 실패: {e}\n")

    # 5. 테스트 파일 존재 확인
    print("5️⃣ 테스트 파일 존재 확인")
    test_files = [
        'data/settings_test01.sqlite3',
        'data/strategies_test01.sqlite3',
        'data/market_data_test01.sqlite3'
    ]

    for test_file in test_files:
        if os.path.exists(test_file):
            size = os.path.getsize(test_file)
            print(f"   ✅ {test_file} ({size:,} bytes)")
        else:
            print(f"   ❌ {test_file} 없음")
    print()

    # 6. 잠재적 원인 분석
    print("6️⃣ 경로 복귀 가능한 원인들")
    print("   🔍 가능한 원인들:")
    print("   1. DatabasePathService 싱글톤에서 캐시된 값 사용")
    print("   2. config.yaml의 database 섹션이 우선순위를 가짐")
    print("   3. Repository에서 설정 파일 저장 실패")
    print("   4. UI에서 변경 후 자동 새로고침/복원 로직")
    print("   5. 다른 컴포넌트에서 원래 경로로 덮어쓰기")

    print("\n=== 분석 완료 ===")

if __name__ == "__main__":
    analyze_path_revert_issue()
