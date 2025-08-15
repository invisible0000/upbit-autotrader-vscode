#!/usr/bin/env python3
"""
YAML 파일의 잘못된 parameter_type을 수정하는 스크립트
"""

import yaml
from pathlib import Path
import shutil
from datetime import datetime

def fix_yaml_parameter_types():
    """YAML 파일의 잘못된 parameter_type 수정"""

    yaml_file = Path("data_info/tv_variable_parameters.yaml")
    if not yaml_file.exists():
        print(f"❌ 파일 없음: {yaml_file}")
        return

    # 백업 생성
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_file = yaml_file.parent / f"{yaml_file.stem}_backup_{timestamp}.yaml"
    shutil.copy2(yaml_file, backup_file)
    print(f"📁 백업 생성: {backup_file.name}")

    # YAML 로드
    with open(yaml_file, 'r', encoding='utf-8') as f:
        data = yaml.safe_load(f)

    if 'variable_parameters' not in data:
        print("❌ variable_parameters 섹션이 없습니다.")
        return

    # 타입 매핑 정의
    type_mappings = {
        'enum': 'string',           # 열거형 → 문자열
        'float': 'decimal',         # 부동소수점 → 정밀 소수
        'range': 'decimal',         # 범위 → 정밀 소수
        'percentage': 'decimal',    # 백분율 → 정밀 소수
        'timeframe': 'string',      # 시간프레임 → 문자열
        'factor': 'decimal'         # 팩터 → 정밀 소수
    }

    print("\n=== YAML Parameter Type 수정 ===")

    fixed_count = 0
    parameters = data['variable_parameters']

    for param_key, param_data in parameters.items():
        old_type = param_data.get('parameter_type', '')

        # 매핑에 있는 잘못된 타입인지 확인
        if old_type in type_mappings:
            new_type = type_mappings[old_type]
            param_data['parameter_type'] = new_type
            fixed_count += 1
            print(f"  ✅ {param_key}: {old_type} → {new_type}")

        # 기타 잘못된 타입들 수정
        elif old_type not in {'boolean', 'integer', 'string', 'decimal'}:
            # 기본적으로 string으로 변경
            param_data['parameter_type'] = 'string'
            fixed_count += 1
            print(f"  🔧 {param_key}: {old_type} → string (기본값)")

    if fixed_count == 0:
        print("  ✅ 수정할 타입이 없습니다.")
        return

    # 수정된 내용 저장
    with open(yaml_file, 'w', encoding='utf-8') as f:
        yaml.dump(data, f, allow_unicode=True, default_flow_style=False,
                 sort_keys=False, indent=2)

    print(f"\n✅ 총 {fixed_count}개 파라미터 타입이 수정되었습니다.")
    print(f"📄 파일 저장: {yaml_file}")

    # 검증
    verify_fixed_types(yaml_file)

def verify_fixed_types(yaml_file):
    """수정된 타입들 검증"""
    print("\n=== 수정 결과 검증 ===")

    with open(yaml_file, 'r', encoding='utf-8') as f:
        data = yaml.safe_load(f)

    parameters = data.get('variable_parameters', {})
    valid_types = {'boolean', 'integer', 'string', 'decimal'}

    invalid_count = 0
    for param_key, param_data in parameters.items():
        param_type = param_data.get('parameter_type', '')
        if param_type not in valid_types:
            print(f"  ❌ 여전히 잘못된 타입: {param_key} = {param_type}")
            invalid_count += 1

    if invalid_count == 0:
        print("  ✅ 모든 parameter_type이 유효합니다!")
    else:
        print(f"  ⚠️  {invalid_count}개의 잘못된 타입이 남아있습니다.")

def show_parameter_type_statistics():
    """파라미터 타입 통계 표시"""
    yaml_file = Path("data_info/tv_variable_parameters.yaml")

    with open(yaml_file, 'r', encoding='utf-8') as f:
        data = yaml.safe_load(f)

    parameters = data.get('variable_parameters', {})
    type_counts = {}

    for param_data in parameters.values():
        param_type = param_data.get('parameter_type', 'unknown')
        type_counts[param_type] = type_counts.get(param_type, 0) + 1

    print("\n=== Parameter Type 통계 ===")
    for param_type, count in sorted(type_counts.items()):
        print(f"  {param_type}: {count}개")

if __name__ == "__main__":
    print("YAML Parameter Type 수정 도구")
    print("=" * 40)

    # 현재 상태 확인
    show_parameter_type_statistics()

    # 타입 수정
    fix_yaml_parameter_types()

    # 수정 후 상태 확인
    show_parameter_type_statistics()
