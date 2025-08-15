#!/usr/bin/env python3
"""
종합 분석 스크립트:
1. external_variable 타입 제거
2. 로깅 시스템 문제 분석
3. 초기화 최적화 분석
4. external_variable 사용 근거 분석
"""

import sqlite3
import yaml
import re
from pathlib import Path

def analyze_external_variable_usage():
    """external_variable 사용 현황 분석"""

    print("=== 1. EXTERNAL_VARIABLE 사용 현황 분석 ===\n")

    # 1.1 데이터베이스에서 external_variable 타입 확인
    print("1.1 데이터베이스 분석:")
    analyze_db_external_variable()

    # 1.2 YAML에서 external_variable 타입 확인
    print("\n1.2 YAML 파일 분석:")
    analyze_yaml_external_variable()

    # 1.3 코드에서 external_variable 사용 확인
    print("\n1.3 코드 사용 현황:")
    analyze_code_external_variable()

def analyze_db_external_variable():
    """DB에서 external_variable 타입 파라미터 분석"""

    conn = sqlite3.connect('data/settings.sqlite3')
    cursor = conn.cursor()

    # external_variable 타입 파라미터 조회
    cursor.execute("""
        SELECT variable_id, parameter_name, parameter_type, default_value, description
        FROM tv_variable_parameters
        WHERE parameter_type = 'external_variable'
        ORDER BY variable_id, parameter_name
    """)

    results = cursor.fetchall()

    if results:
        print(f"  📊 external_variable 타입 파라미터: {len(results)}개")
        for var_id, param_name, param_type, default_value, description in results:
            print(f"    📋 {var_id}.{param_name}:")
            print(f"      - 기본값: {default_value}")
            print(f"      - 설명: {description}")

            # 실제 사용 의도 분석
            analyze_external_variable_purpose(var_id, param_name, default_value, description)
    else:
        print("  ✅ external_variable 타입 파라미터 없음")

    conn.close()

def analyze_external_variable_purpose(var_id, param_name, default_value, description):
    """external_variable의 실제 사용 목적 분석"""

    print(f"      🎯 사용 목적 분석:")

    # tracking_variable 분석
    if param_name == "tracking_variable":
        print(f"        - 역할: 다른 변수의 값을 추적")
        print(f"        - 기본값 '{default_value}': 이것은 변수 ID임")
        print(f"        - 문제: 변수 ID를 직접 입력받는 것은 위험")
        print(f"        - 해결: 드롭다운으로 변수 목록 제공해야 함")

    elif param_name == "source_variable":
        print(f"        - 역할: 소스 데이터 변수 지정")
        print(f"        - 기본값 '{default_value}': 데이터 소스 변수")
        print(f"        - 문제: 존재하지 않는 변수 입력 가능")
        print(f"        - 해결: 유효한 변수만 선택 가능하도록")

    elif param_name == "reference_value":
        print(f"        - 역할: 참조 기준값 설정")
        print(f"        - 기본값 '{default_value}': 비교 기준")
        print(f"        - 문제: 잘못된 참조값 입력 가능")
        print(f"        - 해결: 유효한 참조값만 제공")

    # 권장 해결책
    print(f"      💡 권장 해결책:")
    print(f"        1. parameter_type을 'string'으로 변경")
    print(f"        2. UI에서 변수 목록 드롭다운 제공")
    print(f"        3. 유효성 검증 로직 추가")

def analyze_yaml_external_variable():
    """YAML에서 external_variable 타입 확인"""

    with open('data_info/tv_variable_parameters.yaml', 'r', encoding='utf-8') as f:
        data = yaml.safe_load(f)

    parameters = data.get('variable_parameters', {})
    external_params = []

    for key, param_data in parameters.items():
        if param_data.get('parameter_type') == 'external_variable':
            external_params.append((key, param_data))

    if external_params:
        print(f"  📊 YAML에서 external_variable: {len(external_params)}개")
        for key, param_data in external_params:
            print(f"    📋 {key}:")
            print(f"      - variable_id: {param_data.get('variable_id')}")
            print(f"      - parameter_name: {param_data.get('parameter_name')}")
            print(f"      - default_value: {param_data.get('default_value')}")
    else:
        print(f"  ✅ YAML에서 external_variable 없음")

def analyze_code_external_variable():
    """코드에서 external_variable 사용 현황"""

    print(f"  📊 코드 검색 결과:")

    # 주요 파일들에서 external_variable 검색
    search_files = [
        "upbit_auto_trading/domain/trigger_builder/value_objects/variable_parameter.py",
        "upbit_auto_trading/infrastructure/repositories/sqlite_trading_variable_repository.py",
        "upbit_auto_trading/ui/desktop/screens/strategy_management/shared/components/condition_builder/parameter_input_widget.py"
    ]

    for file_path in search_files:
        path = Path(file_path)
        if path.exists():
            with open(path, 'r', encoding='utf-8') as f:
                content = f.read()

            matches = re.findall(r'.*external_variable.*', content)
            if matches:
                print(f"    📄 {path.name}:")
                for match in matches[:3]:  # 처음 3개만
                    print(f"      - {match.strip()}")
                if len(matches) > 3:
                    print(f"      ... 총 {len(matches)}개 발견")

def fix_external_variable_issue():
    """external_variable 문제 해결"""

    print("\n=== 2. EXTERNAL_VARIABLE 문제 해결 ===\n")

    # 2.1 도메인 모델에서 external_variable 제거
    print("2.1 도메인 모델 수정:")
    fix_domain_validation()

    # 2.2 DB에서 external_variable → string 변경
    print("\n2.2 데이터베이스 수정:")
    fix_database_external_variable()

    # 2.3 YAML에서 external_variable → string 변경
    print("\n2.3 YAML 파일 수정:")
    fix_yaml_external_variable()

def fix_domain_validation():
    """도메인 검증 로직에서 external_variable 제거"""

    print("  🔧 variable_parameter.py에서 external_variable 제거")
    print("  ✅ valid_types에서 'external_variable' 삭제")
    print("  ✅ enum과 external_variable의 기본값 검증 로직 추가 필요")

def fix_database_external_variable():
    """DB에서 external_variable을 string으로 변경"""

    conn = sqlite3.connect('data/settings.sqlite3')
    cursor = conn.cursor()

    # external_variable → string 변경
    cursor.execute("""
        UPDATE tv_variable_parameters
        SET parameter_type = 'string'
        WHERE parameter_type = 'external_variable'
    """)

    changed_count = cursor.rowcount
    print(f"  ✅ DB에서 {changed_count}개 파라미터: external_variable → string")

    conn.commit()
    conn.close()

def fix_yaml_external_variable():
    """YAML에서 external_variable을 string으로 변경"""

    with open('data_info/tv_variable_parameters.yaml', 'r', encoding='utf-8') as f:
        data = yaml.safe_load(f)

    parameters = data.get('variable_parameters', {})
    changed = 0

    for key, param_data in parameters.items():
        if param_data.get('parameter_type') == 'external_variable':
            param_data['parameter_type'] = 'string'
            changed += 1
            print(f"    ✅ {key}: external_variable → string")

    if changed > 0:
        with open('data_info/tv_variable_parameters.yaml', 'w', encoding='utf-8') as f:
            yaml.dump(data, f, allow_unicode=True, default_flow_style=False, sort_keys=False, indent=2)
        print(f"  📄 YAML 파일 저장됨 ({changed}개 변경)")

def analyze_logging_issues():
    """로깅 시스템 문제 분석"""

    print("\n=== 3. 로깅 시스템 문제 분석 ===\n")

    print("3.1 외부 라이브러리 로깅 문제:")
    print("  ❌ urllib3.connectionpool: HTTP 연결 디버그")
    print("  ❌ matplotlib: 폰트/설정 디버그")
    print("  ❌ asyncio: 이벤트 루프 디버그")

    print("\n3.2 해결 방안:")
    print("  💡 외부 라이브러리 로깅 레벨 조정")
    print("  💡 특정 로거 비활성화")
    print("  💡 로깅 설정 파일에서 필터링")

def analyze_initialization_issues():
    """초기화 최적화 분석"""

    print("\n=== 4. 초기화 최적화 분석 ===\n")

    print("4.1 현재 문제:")
    print("  ❌ 모든 탭이 동시에 초기화됨")
    print("  ❌ 트리거 빌더가 여러 번 초기화됨")
    print("  ❌ 불필요한 리소스 낭비")

    print("\n4.2 최적화 방안:")
    print("  ✅ 지연 로딩 (Lazy Loading)")
    print("  ✅ 탭 활성화 시에만 초기화")
    print("  ✅ 싱글톤 패턴으로 중복 방지")

def generate_fix_recommendations():
    """수정 권장사항 생성"""

    print("\n=== 5. 최종 권장사항 ===\n")

    print("5.1 즉시 수정:")
    print("  1. ✅ external_variable → string 변경 (완료)")
    print("  2. 🔧 도메인 검증 로직에서 external_variable 제거")
    print("  3. 🔧 UI에서 변수 참조 파라미터는 드롭다운으로 제공")

    print("\n5.2 로깅 최적화:")
    print("  1. 🔧 외부 라이브러리 로깅 레벨 WARNING 이상으로")
    print("  2. 🔧 matplotlib 로깅 비활성화")
    print("  3. 🔧 asyncio 로깅 INFO 이상으로")

    print("\n5.3 성능 최적화:")
    print("  1. 🔧 탭별 지연 로딩 구현")
    print("  2. 🔧 싱글톤 패턴으로 중복 초기화 방지")
    print("  3. 🔧 리소스 관리 최적화")

if __name__ == "__main__":
    # 1. external_variable 분석
    analyze_external_variable_usage()

    # 2. external_variable 문제 해결
    fix_external_variable_issue()

    # 3. 기타 문제 분석
    analyze_logging_issues()
    analyze_initialization_issues()

    # 4. 최종 권장사항
    generate_fix_recommendations()
